# 课程 23：LangChain 架构深度剖析（基于 LangChain 1.0）

## 学习目标
1. 深入理解 LangChain 1.0 的核心架构和设计原理
2. 掌握 Runnable 协议的本质和实现机制
3. 理解 LCEL（LangChain Expression Language）的设计思想
4. 学会阅读 LangChain 源码，理解内部工作流程
5. 了解 ChatOpenAI 底层接的是 Chat Completions API 及其原因
6. 了解 LangChain 1.0 新特性（create_agent、Middleware、标准内容块）

## 为什么这节课重要？

LangChain 是目前最流行的 Agent 框架，但很多人只会用 API，不理解内部原理：
- **知其然不知其所以然**：遇到问题不知道如何调试
- **无法深度定制**：框架不满足需求时无法扩展
- **性能优化困难**：不理解执行流程，无法优化性能

这节课带你深入 LangChain 1.0 内核，从架构师视角理解框架设计。

## 版本说明

本课程基于 **LangChain 1.0**（2025 年 10 月发布）。1.0 是第一个稳定版本，核心变化：
- Runnable、LCEL、Callbacks 等核心概念保留并强化
- 旧式 Chain 类（LLMChain、SequentialChain 等）移到 `langchain-classic`
- 新增 `create_agent`、Middleware、标准内容块等特性
- 要求 Python 3.10+

## 课程内容

### 1. LangChain 架构全景（25 分钟）

#### 1.1 整体架构分层

```
LangChain 架构（自底向上）：
┌─────────────────────────────────────────┐
│  应用层：Agent、Chain、RAG Pipeline      │
├─────────────────────────────────────────┤
│  组件层：LLM、Memory、VectorStore、Tools│
├─────────────────────────────────────────┤
│  协议层：Runnable、LCEL、Callbacks       │
├─────────────────────────────────────────┤
│  集成层：OpenAI、Anthropic、Chroma...   │
└─────────────────────────────────────────┘
```

**类比 Spring 架构**：
- 应用层 ≈ Spring MVC（Controller、Service）
- 组件层 ≈ Spring Beans
- 协议层 ≈ Spring Core（IoC、AOP）
- 集成层 ≈ Spring Data、Spring Cloud

#### 1.2 核心模块依赖关系

```
langchain/
├─ langchain-core/          # 核心协议（Runnable、LCEL）
├─ langchain-community/     # 社区集成（各种 LLM、DB）
├─ langchain/               # 主包（Agent、Chain、Memory）
└─ langgraph/               # 图编排（独立包，下节课讲）

依赖关系：
langchain → langchain-core
langchain-community → langchain-core
langgraph → langchain-core
```

#### 1.3 设计理念：一切皆 Runnable

```python
# LangChain 的核心设计理念
class Runnable(ABC):
    """所有组件的基类（类比 Java 的 Runnable 接口）"""
    
    @abstractmethod
    def invoke(self, input: Input) -> Output:
        """同步执行"""
        pass
    
    async def ainvoke(self, input: Input) -> Output:
        """异步执行"""
        pass
    
    def stream(self, input: Input) -> Iterator[Output]:
        """流式执行"""
        pass
    
    def batch(self, inputs: List[Input]) -> List[Output]:
        """批量执行"""
        pass

# 所有组件都实现 Runnable 协议：
# - LLM 是 Runnable
# - Prompt 是 Runnable
# - OutputParser 是 Runnable
# - Chain 也是 Runnable（组合模式）
```

**为什么这样设计？**
- **统一接口**：所有组件用同样的方式调用
- **可组合性**：Runnable 可以嵌套组合
- **多种执行模式**：同步/异步/流式/批量
- **类比 Java Stream API**：map、filter、flatMap 的链式调用

### 2. Runnable 协议深度解析（35 分钟）

#### 2.1 Runnable 的核心方法

```python
# 源码简化版（langchain-core/runnables/base.py）
class Runnable(Generic[Input, Output]):
    """
    Runnable 是 LangChain 的核心抽象
    类比：
    - Java 的 Function<Input, Output>
    - JavaScript 的 (input) => output
    - Unix 的管道 |
    """
    
    def invoke(self, input: Input, config: RunnableConfig = None) -> Output:
        """
        同步执行（最常用）
        
        参数：
        - input: 输入数据
        - config: 运行时配置（callbacks、tags、metadata）
        
        返回：
        - output: 输出数据
        """
        pass
    
    def __or__(self, other: Runnable) -> RunnableSequence:
        """
        重载 | 操作符，实现链式组合
        
        chain = runnable1 | runnable2 | runnable3
        等价于：
        RunnableSequence([runnable1, runnable2, runnable3])
        """
        return RunnableSequence(self, other)
    
    def __ror__(self, other: Any) -> RunnableSequence:
        """
        支持左侧非 Runnable 对象
        
        chain = {"input": "hello"} | runnable
        会自动转换为：
        RunnablePassthrough.assign(input="hello") | runnable
        """
        pass
```

#### 2.2 Runnable 的组合模式

**RunnableSequence（顺序执行）**：
```python
# 源码简化
class RunnableSequence(Runnable):
    """
    顺序执行多个 Runnable
    类比：Unix 管道 cmd1 | cmd2 | cmd3
    """
    
    def __init__(self, *steps: Runnable):
        self.steps = steps
    
    def invoke(self, input):
        # 依次执行每个步骤，前一个的输出是后一个的输入
        result = input
        for step in self.steps:
            result = step.invoke(result)
        return result

# 使用示例
chain = prompt | llm | output_parser
# 等价于：
# step1: prompt.invoke(input) -> formatted_prompt
# step2: llm.invoke(formatted_prompt) -> llm_output
# step3: output_parser.invoke(llm_output) -> parsed_result
```

**RunnableParallel（并行执行）**：
```python
class RunnableParallel(Runnable):
    """
    并行执行多个 Runnable，合并结果
    类比：Java 的 CompletableFuture.allOf()
    """
    
    def __init__(self, **branches: Runnable):
        self.branches = branches
    
    def invoke(self, input):
        # 并行执行所有分支
        results = {}
        for key, runnable in self.branches.items():
            results[key] = runnable.invoke(input)
        return results

# 使用示例
parallel = RunnableParallel(
    summary=summarize_chain,
    translation=translate_chain,
    sentiment=sentiment_chain
)
# 输入同时发给三个 chain，输出合并为字典
```

**RunnableBranch（条件分支）**：
```python
class RunnableBranch(Runnable):
    """
    条件分支执行
    类比：if-elif-else
    """
    
    def __init__(self, *branches: Tuple[Callable, Runnable]):
        self.branches = branches
    
    def invoke(self, input):
        for condition, runnable in self.branches:
            if condition(input):
                return runnable.invoke(input)
        return self.default.invoke(input)

# 使用示例
branch = RunnableBranch(
    (lambda x: x["type"] == "question", qa_chain),
    (lambda x: x["type"] == "summary", summary_chain),
    default_chain  # 默认分支
)
```

#### 2.3 Runnable 的执行模式

**同步 vs 异步**：
```python
# 同步执行（阻塞）
result = chain.invoke({"input": "hello"})

# 异步执行（非阻塞，适合 Web 应用）
result = await chain.ainvoke({"input": "hello"})
```

**流式执行**：
```python
# 流式输出（适合聊天场景）
for chunk in chain.stream({"input": "hello"}):
    print(chunk, end="", flush=True)
```

**批量执行**：
```python
# 批量处理（自动并发优化）
inputs = [{"input": f"question {i}"} for i in range(10)]
results = chain.batch(inputs)
```

### 3. LCEL（LangChain Expression Language）深度解析（30 分钟）

#### 3.1 LCEL 的设计思想

```
LCEL 的本质：声明式的 Runnable 组合语法

类比：
- SQL：声明式查询语言
- React JSX：声明式 UI
- LCEL：声明式 Agent 流程

优势：
- 代码简洁：用表达式代替命令式代码
- 易于理解：流程一目了然
- 自动优化：框架可以优化执行计划
```

#### 3.2 LCEL 语法详解

**基础语法**：
```python
# 1. 管道操作符 |（顺序执行）
chain = prompt | llm | parser

# 2. 字典语法（并行执行）
chain = {
    "context": retriever | format_docs,
    "question": RunnablePassthrough()
} | prompt | llm

# 3. 嵌套组合
chain = (
    {
        "context": (
            itemgetter("question")  # 提取 question 字段
            | retriever             # 检索相关文档
            | format_docs           # 格式化文档
        ),
        "question": itemgetter("question")
    }
    | prompt
    | llm
    | StrOutputParser()
)
```

**高级语法**：
```python
# 1. RunnablePassthrough（透传输入）
chain = {
    "original": RunnablePassthrough(),  # 保留原始输入
    "processed": some_chain
} | final_chain

# 2. RunnableLambda（自定义函数）
def custom_logic(x):
    return x.upper()

chain = RunnableLambda(custom_logic) | llm

# 3. RunnableBranch（条件分支）
chain = RunnableBranch(
    (lambda x: len(x) > 100, long_text_chain),
    (lambda x: len(x) > 10, medium_text_chain),
    short_text_chain
)

# 4. itemgetter（提取字段）
from operator import itemgetter

chain = {
    "answer": itemgetter("question") | qa_chain,
    "source": itemgetter("context")
}
```

#### 3.3 LCEL 的执行流程

```python
# LCEL 表达式
chain = prompt | llm | parser

# 编译后的内部结构
RunnableSequence(
    steps=[
        PromptTemplate(...),
        ChatOpenAI(...),
        StrOutputParser()
    ]
)

# 执行流程
input = {"question": "什么是 AI？"}
↓
step1: prompt.invoke(input)
→ "请回答：什么是 AI？"
↓
step2: llm.invoke("请回答：什么是 AI？")
→ AIMessage(content="AI 是人工智能...")
↓
step3: parser.invoke(AIMessage(...))
→ "AI 是人工智能..."
```

### 4. Chain 的内部机制 → ⚠️ 已移到 langchain-classic（20 分钟）

> **注意**：LangChain 1.0 中，旧式 Chain 类（LLMChain、SequentialChain 等）已移到 `langchain-classic` 包。
> 新项目应使用 LCEL 替代。这里简单了解即可，重点理解"为什么 LCEL 更好"。

#### 4.1 旧式 Chain 的本质（了解即可）

```python
# Chain 也是 Runnable，但设计较老
class Chain(Runnable):
    @property
    def input_keys(self) -> List[str]: ...
    @property
    def output_keys(self) -> List[str]: ...
    def _call(self, inputs: Dict) -> Dict: ...
```

#### 4.2 旧式 Chain vs LCEL 对比

```python
# ❌ 旧式写法（已移到 langchain-classic，不推荐）
from langchain_classic.chains import LLMChain
chain = LLMChain(prompt=prompt, llm=llm)

# ✅ 新式写法（LCEL，推荐）
chain = prompt | llm
```

**LCEL 的优势**：
- 更简洁：一行代码代替多行
- 更灵活：可以任意组合
- 更强大：自动支持流式、异步、批量
- 更易维护：声明式代码更清晰

### 5. LangChain 的高级特性（25 分钟）

#### 5.1 Callbacks（回调机制） — 1.0 保留

```python
# Callbacks 用于监控和调试
from langchain_core.callbacks import BaseCallbackHandler

class MyCallbackHandler(BaseCallbackHandler):
    """自定义回调（类比 Spring 的 Interceptor）"""
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """LLM 开始调用时触发"""
        print(f"LLM 开始: {prompts}")
    
    def on_llm_end(self, response, **kwargs):
        """LLM 结束调用时触发"""
        print(f"LLM 结束: {response}")
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """工具开始调用时触发"""
        print(f"工具开始: {input_str}")

# 使用
chain.invoke(
    {"input": "..."},
    config={"callbacks": [MyCallbackHandler()]}
)
```

#### 5.2 Memory — ⚠️ 旧 API 已移到 langchain-classic

> **注意**：`ConversationBufferMemory` 等旧 Memory 类已移到 `langchain-classic`。
> 1.0 中推荐通过 LangGraph 的状态管理 + 中间件来实现会话记忆。

```python
# ❌ 旧方式（已移到 langchain-classic）
from langchain_classic.memory import ConversationBufferMemory
memory = ConversationBufferMemory()
chain = LLMChain(llm=llm, prompt=prompt, memory=memory)

# ✅ 1.0 推荐方式：用 LangGraph 状态 + create_agent 的 middleware
# （后续课程会详细讲解）
```

#### 5.3 Retriever（检索器） — 1.0 核心接口保留在 langchain-core

```python
# Retriever 也是 Runnable
class BaseRetriever(Runnable):
    """
    检索器抽象（用于 RAG）
    """
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """子类实现检索逻辑"""
        pass
    
    def invoke(self, input: str) -> List[Document]:
        return self._get_relevant_documents(input)

# 使用（LCEL 组合）
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

### 6. ChatOpenAI 底层 API 解析（15 分钟）

#### OpenAI 的两类 API

| API | 端点 | 状态管理 | 兼容性 | 定位 |
|-----|------|---------|--------|------|
| Chat Completions | `/v1/chat/completions` | 无状态，客户端管 | 行业标准 | 通用 |
| Responses | `/v1/responses` | 有状态，服务端管 | OpenAI 独有 | Agent |

#### LangChain 选择 Chat Completions 的原因

1. **兼容性** — 通义千问、DeepSeek 等都支持，换 `base_url` 即可切换
2. **架构一致** — LangChain 自己管状态（Memory/Runnable），不需要 OpenAI 帮忙管
3. **厂商中立** — 框架不能绑死在一家 provider

### 6. 源码阅读实践（25 分钟）

#### 6.1 如何阅读 LangChain 源码

**源码结构**：
```
langchain-core/
├─ runnables/
│   ├─ base.py          # Runnable 基类
│   ├─ config.py        # 配置管理
│   ├─ passthrough.py   # RunnablePassthrough
│   └─ branch.py        # RunnableBranch
├─ prompts/
│   └─ base.py          # PromptTemplate
├─ language_models/
│   └─ base.py          # LLM 抽象
└─ output_parsers/
    └─ base.py          # OutputParser 抽象
```

**阅读路径**：
1. 从 `Runnable` 基类开始
2. 看 `RunnableSequence` 的实现（理解 | 操作符）
3. 看 `PromptTemplate` 如何实现 Runnable
4. 看 `ChatOpenAI` 如何实现 Runnable
5. 看 `Agent` 如何组合这些组件

#### 6.2 实践：手写一个简单的 Runnable

```python
# 实现一个自定义 Runnable
from langchain_core.runnables import Runnable

class UpperCaseRunnable(Runnable[str, str]):
    """
    将输入转为大写
    演示如何实现 Runnable 协议
    """
    
    def invoke(self, input: str, config=None) -> str:
        """同步执行"""
        return input.upper()
    
    async def ainvoke(self, input: str, config=None) -> str:
        """异步执行"""
        return input.upper()
    
    def stream(self, input: str, config=None):
        """流式执行（逐字符输出）"""
        for char in input.upper():
            yield char

# 使用
runnable = UpperCaseRunnable()
result = runnable.invoke("hello")  # "HELLO"

# 组合到 Chain 中
chain = UpperCaseRunnable() | llm
```

#### 6.3 实践：调试 LCEL 执行流程

```python
# 使用 Callbacks 追踪执行流程
from langchain_core.callbacks import StdOutCallbackHandler

chain = prompt | llm | parser

# 开启调试模式
result = chain.invoke(
    {"input": "hello"},
    config={"callbacks": [StdOutCallbackHandler()]}
)

# 输出：
# > Entering new PromptTemplate chain...
# > Prompt: ...
# > Entering new ChatOpenAI chain...
# > LLM output: ...
# > Entering new StrOutputParser chain...
# > Parsed output: ...
```

### 7. 实战练习（30 分钟）

#### 练习 1：实现一个自定义 Runnable
要求：实现一个 `JsonParserRunnable`，将 JSON 字符串解析为字典

#### 练习 2：用 LCEL 实现 RAG Pipeline
要求：
- 输入：用户问题
- 步骤：检索 → 格式化 → 生成答案
- 输出：答案 + 来源文档

#### 练习 3：阅读源码
要求：
- 找到 `RunnableSequence` 的源码
- 理解 `__or__` 方法的实现
- 画出执行流程图

## 预计时长
- 架构讲解：约 80 分钟
- ChatOpenAI API 解析：约 15 分钟
- 源码阅读：约 25 分钟
- 实战练习：约 30 分钟
- 总计：约 2.5 小时

## 完成标准
- 理解 Runnable 协议的设计思想
- 能用 LCEL 编写复杂的 Chain
- 理解 ChatOpenAI 底层接的是 Chat Completions API 及其原因
- 能阅读 LangChain 源码并理解执行流程
- 能实现自定义 Runnable 组件
- 了解 LangChain 1.0 的核心变化和新特性

## 下节预告
课程 24：LangGraph 状态机编排 — 用图和状态机实现复杂 Agent 流程
