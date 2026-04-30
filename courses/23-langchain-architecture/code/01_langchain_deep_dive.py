"""
课程 23：LangChain 架构深度剖析 — 代码实践

本文件通过代码演示 LangChain 的核心机制：
1. Runnable 协议的四种执行模式
2. LCEL 的组合模式
3. 自定义 Runnable
4. Callbacks 调试

运行前安装依赖：
pip install langchain langchain-openai langchain-core
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableLambda,
    RunnableParallel,
)
from langchain_core.callbacks import BaseCallbackHandler
import time

# ============================================================
# 初始化 LLM（通义千问 DashScope API）
# ============================================================

# ChatOpenAI 是 LangChain 对 OpenAI 兼容 API 的封装
# 因为通义千问提供了 OpenAI 兼容接口，所以直接用这个类
# 内部实现：ChatOpenAI 继承自 BaseChatModel，BaseChatModel 继承自 Runnable
# 所以 llm 本身就是一个 Runnable，可以用 | 操作符组合
llm = ChatOpenAI(
    model="qwen-plus",  # 通义千问 qwen-plus 模型
    api_key="sk-a4ae611c3f9c4df89a133e621b2b7851",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7,
)


# ============================================================
# 示例 1：Runnable 的四种执行模式
# ============================================================

def demo_execution_modes():
    """
    演示 Runnable 的四种执行模式：invoke / stream / batch / ainvoke

    这四种模式是 Runnable 协议的核心
    所有 LangChain 组件都支持这四种模式
    """
    print("=" * 60)
    print("示例 1：Runnable 的四种执行模式")
    print("=" * 60)

    # 构建一个简单的 LCEL 链
    # ChatPromptTemplate 是 Runnable
    # llm 是 Runnable
    # StrOutputParser 是 Runnable
    # 用 | 连接后得到 RunnableSequence，也是 Runnable
    chain = (
            ChatPromptTemplate.from_template("用一句话解释什么是{topic}")
            | llm
            | StrOutputParser()  # 从 AIMessage 中提取纯文本
    )

    # --- 模式 1：invoke（同步执行） ---
    # 最常用的模式，阻塞等待结果
    # 类比 Java: String result = function.apply(input);
    print("\n--- invoke（同步执行）---")
    result = chain.invoke({"topic": "向量数据库"})
    print(f"结果: {result}")

    # --- 模式 2：stream（流式执行） ---
    # 适合聊天场景，逐字输出
    # 类比 Java: Stream<String> stream = function.stream(input);
    # 内部原理：只有最后一个 Runnable（这里是 LLM）真正流式输出
    # 前面的步骤（Prompt 格式化）正常执行
    print("\n--- stream（流式执行）---")
    print("结果: ", end="")
    for chunk in chain.stream({"topic": "RAG"}):
        print(chunk, end="", flush=True)  # flush=True 确保立即输出
    print()

    # --- 模式 3：batch（批量执行） ---
    # 适合批处理场景，内部用线程池并发执行
    # 类比 Java: List<String> results = inputs.parallelStream().map(f).collect();
    print("\n--- batch（批量执行）---")
    topics = [{"topic": "AI Agent"}, {"topic": "Prompt Engineering"}, {"topic": "MCP"}]
    results = chain.batch(topics)
    for topic, result in zip(topics, results):
        print(f"  {topic['topic']}: {result}")

    # --- 模式 4：ainvoke（异步执行） ---
    # 适合 Web 应用（FastAPI、Django 等）
    # 类比 Java: CompletableFuture<String> future = function.applyAsync(input);
    print("\n--- ainvoke（异步执行，需要在 async 环境中运行）---")
    print("  提示：在 FastAPI 等异步框架中使用 await chain.ainvoke(...)")


# ============================================================
# 示例 2：LCEL 组合模式
# ============================================================

def demo_lcel_patterns():
    """
    演示 LCEL 的各种组合模式

    LCEL 的本质：用 Python 操作符重载实现的声明式编排语法
    """
    print("\n" + "=" * 60)
    print("示例 2：LCEL 组合模式")
    print("=" * 60)

    # --- 模式 1：基础链（顺序执行） ---
    # prompt | llm | parser
    # 内部创建 RunnableSequence
    print("\n--- 模式 1：基础链 ---")
    basic_chain = (
            ChatPromptTemplate.from_template("用一句话解释{topic}")
            | llm
            | StrOutputParser()
    )
    print(basic_chain.invoke({"topic": "LangChain"}))

    # --- 模式 2：并行执行（RunnableParallel） ---
    # 多个任务同时执行，结果合并为字典
    # 内部用 ThreadPoolExecutor 并发
    print("\n--- 模式 2：并行执行 ---")

    # 定义两个不同的处理链
    explain_chain = (
            ChatPromptTemplate.from_template("用一句话解释{topic}")
            | llm
            | StrOutputParser()
    )
    example_chain = (
            ChatPromptTemplate.from_template("给{topic}举一个实际应用的例子")
            | llm
            | StrOutputParser()
    )

    # RunnableParallel：两个链并行执行
    # 输入 {"topic": "RAG"} 同时发给两个链
    # 输出 {"explanation": "...", "example": "..."}
    parallel_chain = RunnableParallel(
        explanation=explain_chain,
        example=example_chain,
    )

    result = parallel_chain.invoke({"topic": "RAG"})
    print(f"  解释: {result['explanation']}")
    print(f"  示例: {result['example']}")

    # --- 模式 3：RunnableLambda（自定义函数） ---
    # 把普通 Python 函数包装成 Runnable
    # 这样就能用 | 操作符和其他 Runnable 组合
    print("\n--- 模式 3：RunnableLambda ---")

    def add_health_context(input_dict: dict) -> dict:
        """自定义预处理：添加健康领域上下文"""
        input_dict["context"] = "你是一个专业的健康顾问"
        return input_dict

    chain_with_lambda = (
            RunnableLambda(add_health_context)  # 自定义预处理
            | ChatPromptTemplate.from_template("{context}。请回答：{question}")
            | llm
            | StrOutputParser()
    )

    result = chain_with_lambda.invoke({"question": "每天应该喝多少水？"})
    print(f"  结果: {result}")

    # --- 模式 4：RunnablePassthrough（透传） ---
    # 不做任何处理，直接把输入传给下一步
    # 常用于 RAG 场景：检索结果和原始问题需要同时传递
    print("\n--- 模式 4：RunnablePassthrough ---")

    # 模拟 RAG 场景
    def fake_retriever(query: dict) -> str:
        """模拟检索器"""
        return "苹果每100g含52kcal热量，富含维生素C和膳食纤维。"

    rag_chain = (
            {
                # context: 输入经过检索器处理
                "context": RunnableLambda(lambda x: fake_retriever(x)),
                # question: 输入直接透传（RunnablePassthrough）
                "question": RunnablePassthrough(),
            }
            | ChatPromptTemplate.from_template(
        "根据以下信息回答问题。\n信息：{context}\n问题：{question}"
    )
            | llm
            | StrOutputParser()
    )

    result = rag_chain.invoke("苹果的热量是多少？")
    print(f"  结果: {result}")


# ============================================================
# 示例 3：自定义 Runnable
# ============================================================

def demo_custom_runnable():
    """
    演示如何实现自定义 Runnable

    理解了 Runnable 协议，你就能扩展 LangChain 的任何部分
    """
    print("\n" + "=" * 60)
    print("示例 3：自定义 Runnable")
    print("=" * 60)

    from langchain_core.runnables import Runnable
    from typing import Any

    class NutritionScorer(Runnable):
        """
        自定义 Runnable：营养评分器

        接收食物描述文本，输出营养评分
        演示如何实现 Runnable 协议

        类比 Java：实现 Function<String, Dict> 接口
        """

        def invoke(self, input: str, config=None) -> dict:
            """
            同步执行：分析文本中的关键词，给出营养评分

            参数：
            - input: 食物描述文本
            - config: 运行时配置（可选）

            返回：
            - dict: 包含评分和建议
            """
            score = 50  # 基础分

            # 简单的关键词评分逻辑
            positive_keywords = ["蔬菜", "水果", "蛋白质", "全麦", "低脂"]
            negative_keywords = ["油炸", "高糖", "碳酸", "零食", "甜点"]

            for kw in positive_keywords:
                if kw in input:
                    score += 10

            for kw in negative_keywords:
                if kw in input:
                    score -= 10

            score = max(0, min(100, score))

            return {
                "text": input,
                "score": score,
                "level": "优秀" if score >= 80 else "良好" if score >= 60 else "需改善"
            }

    # 使用自定义 Runnable
    scorer = NutritionScorer()

    # 单独使用
    result = scorer.invoke("今天吃了蔬菜沙拉和全麦面包，搭配水果")
    print(f"  评分: {result['score']}（{result['level']}）")

    # 组合到 LCEL 链中
    # 自定义 Runnable 可以和 LangChain 的任何组件组合
    chain = (
            scorer  # 先评分
            | RunnableLambda(
        lambda x: {
            "score": x["score"],
            "level": x["level"],
            "food": x["text"]
        }
    )
            | ChatPromptTemplate.from_template(
        "用户今天的饮食：{food}\n营养评分：{score}分（{level}）\n请给出简短的改善建议。"
    )
            | llm
            | StrOutputParser()
    )

    result = chain.invoke("今天吃了油炸鸡腿和碳酸饮料")
    print(f"  建议: {result}")


# ============================================================
# 示例 4：Callbacks 调试
# ============================================================

def demo_callbacks():
    """
    演示 Callbacks 机制

    Callbacks 类比 Spring AOP：
    - on_llm_start ≈ @Before
    - on_llm_end ≈ @After
    - on_llm_error ≈ @AfterThrowing
    """
    print("\n" + "=" * 60)
    print("示例 4：Callbacks 调试追踪")
    print("=" * 60)

    class DebugCallbackHandler(BaseCallbackHandler):
        """
        自定义回调处理器：追踪 Chain 的执行过程

        类比 Spring 的 HandlerInterceptor：
        - preHandle → on_chain_start
        - postHandle → on_chain_end
        - afterCompletion → on_chain_error
        """

        def on_chain_start(self, serialized, inputs, **kwargs):
            """Chain 开始执行时触发"""
            # serialized 有时候是 None，需要保护
            chain_name = serialized.get("name", "Unknown") if serialized else "Unknown"
            print(f"  [Chain 开始] {chain_name}")
            print(f"    输入: {str(inputs)[:100]}...")

        def on_chain_end(self, outputs, **kwargs):
            """Chain 执行结束时触发"""
            print(f"  [Chain 结束] 输出: {str(outputs)[:100]}...")

        def on_llm_start(self, serialized, prompts, **kwargs):
            """LLM 开始调用时触发"""
            # serialized 有时候是 None，需要保护
            model_name = "unknown"
            if serialized and isinstance(serialized, dict):
                model_name = serialized.get('kwargs', {}).get('model_name', 'unknown')
            print(f"  [LLM 开始] 模型: {model_name}")

        def on_llm_end(self, response, **kwargs):
            """LLM 调用结束时触发"""
            # response.generations 是 LLM 的输出
            # 可以在这里统计 token 用量
            print(f"  [LLM 结束]")

    # 构建链
    chain = (
            ChatPromptTemplate.from_template("用一句话解释{topic}")
            | llm
            | StrOutputParser()
    )

    # 使用 Callbacks 执行
    # config 参数传入回调处理器列表
    # 执行过程中会自动触发对应的回调方法
    print("\n执行追踪：")
    result = chain.invoke(
        {"topic": "LangChain 的 Runnable 协议"},
        config={"callbacks": [DebugCallbackHandler()]}
    )
    print(f"\n最终结果: {result}")


# ============================================================
# 主程序
# ============================================================

# ============================================================
# 练习 1：实现 JsonParserRunnable
# ============================================================

def demo_json_parser_runnable():
    """
    练习：实现一个 JsonParserRunnable
    - 继承 Runnable
    - invoke 接收 JSON 字符串，返回 Python 字典
    - 处理解析错误（返回错误信息而不是抛异常）
    - 组合到 LCEL 链中使用
    """
    from langchain_core.runnables import Runnable
    import json

    class JsonParserRunnable(Runnable[str, dict]):
        """
        自定义 Runnable：解析 JSON 字符串

        输入：JSON 字符串
        输出：Python 字典（解析成功）或错误信息字典（解析失败）
        """

        def invoke(self, input: str, config=None) -> dict:
            """同步执行：解析 JSON"""
            try:
                return json.loads(input)
            except json.JSONDecodeError as e:
                return {"error": f"JSON 解析失败: {str(e)}"}

    print("=" * 60)
    print("练习 1：JsonParserRunnable 示例")
    print("=" * 60)

    # 创建一个链：让 LLM 返回 JSON，然后解析
    chain = (
        ChatPromptTemplate.from_template("请以 JSON 格式回答：{question}")
        | llm
        | StrOutputParser()
        | JsonParserRunnable()  # 解析 LLM 输出的 JSON 字符串
    )

    result = chain.invoke({"question": "什么是 LangChain？用 JSON 格式回答，包含 name 和 description 字段"})
    print(f"\n解析结果: {result}")
    print(f"类型: {type(result)}")


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("LangChain 架构深度剖析 — 代码实践\n")

    # 依次运行示例
    demo_execution_modes()
    demo_lcel_patterns()
    demo_custom_runnable()
    demo_callbacks()

    # 运行练习
    demo_json_parser_runnable()

    print("\n" + "=" * 60)
    print("练习任务")
    print("=" * 60)
    print("""
    练习 1：实现一个 JsonParserRunnable ✅ 已完成（见上方示例）
    - 继承 Runnable
    - invoke 接收 JSON 字符串，返回 Python 字典
    - 处理解析错误（返回错误信息而不是抛异常）
    - 组合到 LCEL 链中使用

    练习 2：用 LCEL 实现一个健康问答链
    - 输入：用户的健康问题
    - 步骤：预处理 → 添加健康上下文 → LLM 回答 → 后处理
    - 使用 RunnableLambda 实现预处理和后处理
    - 使用 Callbacks 追踪执行过程

    练习 3：阅读 LangChain 源码
    - 找到 RunnableSequence 的 __or__ 方法
    - 理解 stream 方法为什么只对最后一步流式
    - 画出 invoke 的调用链路图
    """)
