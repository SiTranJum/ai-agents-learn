import os
"""
课程 26：框架选型实战 — 同一需求的四种实现

本文件用同一个需求在四种方式下实现，直观对比差异：
1. 手写版本（基线）
2. LangChain LCEL 版本
3. LangGraph 版本
4. CrewAI 版本

需求：健康饮食分析 Agent
- 接收用户的饮食描述
- 分析营养摄入
- 给出改善建议
"""

# ============================================================
# 实现 1：手写版本（基线）
# ============================================================

def demo_handwritten():
    """
    手写版本：最直接，最简单

    优点：没有依赖，完全可控
    缺点：没有流式、重试、组合能力
    """
    print("=" * 60)
    print("实现 1：手写版本")
    print("=" * 60)

    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    def analyze_diet(user_input: str) -> str:
        """手写的饮食分析函数"""
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {
                    "role": "system",
                    "content": "你是营养师。分析用户饮食，估算热量，给出2条改善建议。回答简洁。"
                },
                {"role": "user", "content": user_input}
            ],
        )
        return response.choices[0].message.content

    # 测试
    result = analyze_diet("早餐：牛奶+面包，午餐：米饭+红烧肉+青菜")
    print(f"\n结果：\n{result}")
    print(f"\n代码量：约 15 行")


# ============================================================
# 实现 2：LangChain LCEL 版本
# ============================================================

def demo_langchain():
    """
    LangChain LCEL 版本：声明式，可组合

    优点：自动支持 stream/batch/async，可加 retry/fallback
    缺点：对于简单需求，和手写差别不大
    """
    print("\n" + "=" * 60)
    print("实现 2：LangChain LCEL 版本")
    print("=" * 60)

    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    llm = ChatOpenAI(
        model="qwen-plus",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # LCEL 链：声明式组合
    chain = (
        ChatPromptTemplate.from_messages([
            ("system", "你是营养师。分析用户饮食，估算热量，给出2条改善建议。回答简洁。"),
            ("user", "{input}"),
        ])
        | llm
        | StrOutputParser()
    )

    # 同步调用
    result = chain.invoke({"input": "早餐：牛奶+面包，午餐：米饭+红烧肉+青菜"})
    print(f"\n同步结果：\n{result}")

    # 流式调用（自动支持）
    print(f"\n流式输出：")
    for chunk in chain.stream({"input": "早餐：牛奶+面包"}):
        print(chunk, end="", flush=True)
    print()

    print(f"\n代码量：约 15 行（但自动支持流式、批量、异步）")


# ============================================================
# 实现 3：LangGraph 版本
# ============================================================

def demo_langgraph():
    """
    LangGraph 版本：图编排，状态管理

    优点：状态清晰，可加 Checkpoint、条件分支、Human-in-the-loop
    缺点：对于简单需求，明显过度设计
    """
    print("\n" + "=" * 60)
    print("实现 3：LangGraph 版本")
    print("=" * 60)

    from langgraph.graph import StateGraph, START, END
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from typing import TypedDict, Annotated
    from operator import add

    llm = ChatOpenAI(
        model="qwen-plus",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 定义状态
    class DietState(TypedDict):
        messages: Annotated[list, add]
        analysis: str
        suggestions: str

    # 定义节点
    def analyze(state: DietState) -> dict:
        """分析饮食"""
        user_msg = state["messages"][-1].content
        response = llm.invoke([
            SystemMessage(content="分析以下饮食的营养摄入，估算总热量。用2-3句话回答。"),
            HumanMessage(content=user_msg),
        ])
        return {"analysis": response.content}

    def suggest(state: DietState) -> dict:
        """给出建议"""
        response = llm.invoke([
            SystemMessage(content="根据以下饮食分析，给出2条改善建议。"),
            HumanMessage(content=state["analysis"]),
        ])
        return {"suggestions": response.content}

    # 构建图
    graph = StateGraph(DietState)
    graph.add_node("analyze", analyze)
    graph.add_node("suggest", suggest)
    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "suggest")
    graph.add_edge("suggest", END)

    app = graph.compile()

    # 执行
    result = app.invoke({
        "messages": [HumanMessage(content="早餐：牛奶+面包，午餐：米饭+红烧肉+青菜")],
        "analysis": "",
        "suggestions": "",
    })

    print(f"\n分析结果：\n{result['analysis']}")
    print(f"\n改善建议：\n{result['suggestions']}")
    print(f"\n代码量：约 40 行（但支持复杂流程控制）")


# ============================================================
# 实现 4：CrewAI 版本
# ============================================================

def demo_crewai():
    """
    CrewAI 版本：角色驱动

    优点：角色定义清晰，Multi-Agent 扩展方便
    缺点：单 Agent 场景下比较重
    """
    print("\n" + "=" * 60)
    print("实现 4：CrewAI 版本")
    print("=" * 60)

    from crewai import Agent, Task, Crew, LLM

    llm = LLM(
        model="openai/qwen-plus",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    )

    # 定义 Agent
    analyst = Agent(
        role="营养分析师",
        goal="分析饮食，估算热量，给出建议",
        backstory="你是注册营养师，擅长饮食分析。回答简洁。",
        llm=llm,
        verbose=False,  # 关闭详细日志，输出更简洁
    )

    # 定义 Task
    task = Task(
        description="分析这份饮食记录：早餐：牛奶+面包，午餐：米饭+红烧肉+青菜。估算热量并给出2条建议。",
        expected_output="热量估算 + 2条改善建议",
        agent=analyst,
    )

    # 组建 Crew
    crew = Crew(agents=[analyst], tasks=[task], verbose=False)

    # 执行
    result = crew.kickoff()
    print(f"\n结果：\n{result.raw}")
    print(f"\n代码量：约 20 行（角色模型清晰，Multi-Agent 扩展方便）")


# ============================================================
# 对比总结
# ============================================================

def print_comparison():
    """打印四种实现的对比"""
    print("\n" + "=" * 60)
    print("四种实现的对比总结")
    print("=" * 60)

    print("""
    | 维度         | 手写  | LangChain | LangGraph | CrewAI |
    |-------------|-------|-----------|-----------|--------|
    | 代码量       | ~15行 | ~15行     | ~40行     | ~20行  |
    | 学习成本     | 最低  | 低        | 中        | 中     |
    | 流式输出     | 需自己实现 | 自动支持 | 自动支持 | 支持   |
    | 状态管理     | 需自己实现 | 需自己实现 | 内置     | 内置   |
    | Multi-Agent  | 需自己实现 | 需自己编排 | 需自己编排 | 原生支持 |
    | 适合场景     | 简单调用 | 通用链式 | 复杂流程 | 角色协作 |

    核心结论：
    - 简单需求（单 LLM 调用）→ 手写 或 LangChain LCEL
    - 中等需求（多步骤 + 工具调用）→ LangChain + LangGraph
    - 复杂需求（Multi-Agent + 状态管理）→ LangGraph + CrewAI
    """)


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("框架选型实战 — 同一需求的四种实现\n")

    demo_handwritten()
    demo_langchain()
    demo_langgraph()
    demo_crewai()
    print_comparison()

    print("\n" + "=" * 60)
    print("练习任务")
    print("=" * 60)
    print("""
    练习 1：用 LangGraph 重构之前的 Multi-Agent 系统
    - 将课程 21 的手写 Multi-Agent 用 LangGraph 重写
    - 对比代码量和可维护性的变化

    练习 2：为健康管家设计框架使用方案
    - 列出健康管家的所有功能模块
    - 为每个模块选择合适的框架
    - 画出整体架构图
    """)
