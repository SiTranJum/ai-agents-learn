# 课程 23：LangChain 架构深度剖析

---

## 重要说明：本课程基于 LangChain 1.0

**LangChain 1.0 于 2025 年 10 月发布**，是第一个稳定版本，承诺在 2.0 之前不会有 breaking changes。

### 1.0 的核心变化

**保留的核心**（本课重点）：
- ✅ **Runnable 协议** — 依然是 LangChain 的灵魂，位于 `langchain-core`
- ✅ **LCEL（LangChain Expression Language）** — `|` 操作符、链式组合完全保留
- ✅ **Callbacks** — 回调机制保留
- ✅ **导入路径** — `langchain_core`、`langchain_openai` 等包结构不变

**移到 `langchain-classic` 的旧功能**：
- ⚠️ `LLMChain`、`SequentialChain` 等旧式 Chain 类（已被 LCEL 替代）
- ⚠️ `ConversationBufferMemory` 等旧式 Memory 类
- ⚠️ 部分 Retriever 和 Index API

**1.0 新增的核心特性**（后续课程会讲）：
- 🆕 `create_agent` — 新的 Agent 创建 API
- 🆕 Middleware 机制 — 在 Agent loop 各阶段插入控制逻辑
- 🆕 标准内容块 — 统一跨 provider 的 LLM 功能访问

### 本课程的定位

本课程聚焦 **LangChain 1.0 的核心架构**（Runnable、LCEL、Callbacks），这些是理解框架的基础，也是 1.0 保留并强化的部分。

旧式 Chain 类（如 `LLMChain`）我们会简单提及，但**不推荐使用**，因为 LCEL 更简洁强大。

---

## 开场：从使用者到理解者

上节课我们建立了框架的全局认知。这节课深入 LangChain 内核。

目标不是教你"怎么用 LangChain"（文档就能学会），而是让你理解：
- **Runnable 协议为什么这样设计？**
- **LCEL 的 `|` 操作符背后发生了什么？**
- **Chain 内部的执行流程是怎样的？**

理解了这些，你遇到问题时能看源码调试，需要定制时能扩展框架。

---

## 第一部分：LangChain 的模块结构

### 包的拆分

```
langchain 生态的包结构：

langchain-core          # 核心协议层（最重要）
├─ runnables/           #   Runnable 基类、LCEL
├─ language_models/     #   LLM 抽象接口
├─ prompts/             #   Prompt 模板
├─ output_parsers/      #   输出解析器
├─ tools/               #   工具抽象
├─ messages/            #   消息类型
└─ callbacks/           #   回调机制

langchain               # 主包（高级抽象）
├─ agents/              #   Agent 实现
├─ chains/              #   Chain 实现
└─ memory/              #   Memory 实现

langchain-community     # 社区集成
├─ chat_models/         #   各种 LLM 适配器
├─ vectorstores/        #   各种向量数据库适配器
└─ tools/               #   各种工具集成

langchain-openai        # OpenAI 专用集成
├─ ChatOpenAI           #   OpenAI Chat 模型
└─ OpenAIEmbeddings     #   OpenAI Embedding
```

**为什么要拆包？**

类比 Spring 的模块化：
- `spring-core` = `langchain-core`（核心抽象）
- `spring-web` = `langchain`（高级功能）
- `spring-data-jpa` = `langchain-community`（具体集成）

好处：
- 只用核心功能时不需要装一堆依赖
- 社区可以独立开发集成包
- 版本管理更灵活

---

## 第二部分：Runnable 协议 — LangChain 的灵魂

### Runnable 是什么？

```python
# 简化版源码（langchain-core/runnables/base.py）
class Runnable(Generic[Input, Output], ABC):
    """
    LangChain 中所有可执行组件的基类
    
    类比：
    - Java: Function<Input, Output> 接口
    - 更准确地说：一个同时支持同步/异步/流式/批量的 Function
    """
    
    @abstractmethod
    def invoke(self, input: Input, config: RunnableConfig = None) -> Output:
        """同步执行（最常用）"""
        ...
    
    async def ainvoke(self, input: Input, config: RunnableConfig = None) -> Output:
        """异步执行（Web 应用场景）"""
        # 默认实现：在线程池中运行 invoke
        return await asyncio.get_event_loop().run_in_executor(
            None, self.invoke, input, config
        )
    
    def stream(self, input: Input, config: RunnableConfig = None) -> Iterator[Output]:
        """流式执行（聊天场景，逐字输出）"""
        # 默认实现：invoke 后一次性 yield
        yield self.invoke(input, config)
    
    def batch(self, inputs: List[Input], config: RunnableConfig = None) -> List[Output]:
        """批量执行（批处理场景）"""
        # 默认实现：用线程池并发执行 invoke
        with ThreadPoolExecutor() as executor:
            return list(executor.map(lambda x: self.invoke(x, config), inputs))
```

**四种执行模式的使用场景**：

| 模式 | 方法 | 场景 | Java 类比 |
|------|------|------|----------|
| 同步 | `invoke()` | 普通调用 | `function.apply()` |
| 异步 | `ainvoke()` | Web 服务 | `CompletableFuture.supplyAsync()` |
| 流式 | `stream()` | 聊天 UI | `Stream<T>` |
| 批量 | `batch()` | 批处理 | `parallelStream().map()` |

### `|` 操作符的秘密

```python
# 当你写 prompt | llm | parser 时，发生了什么？

class Runnable:
    def __or__(self, other):
        """
        Python 的 __or__ 方法重载了 | 操作符
        
        类比 Java：
        如果 Java 支持操作符重载，相当于：
        public RunnableSequence or(Runnable other) {
            return new RunnableSequence(this, other);
        }
        """
        return RunnableSequence(first=self, last=other)
    
    def __ror__(self, other):
        """
        当左侧不是 Runnable 时触发
        比如：{"key": "value"} | runnable
        会把字典自动包装成 RunnableParallel
        """
        if isinstance(other, dict):
            return RunnableSequence(
                first=RunnableParallel(other),
                last=self
            )
        return NotImplemented
```

**执行流程**：
```python
# 这行代码
chain = prompt | llm | parser

# 等价于
chain = RunnableSequence(
    first=RunnableSequence(
        first=prompt,    # PromptTemplate（Runnable）
        last=llm         # ChatOpenAI（Runnable）
    ),
    last=parser          # StrOutputParser（Runnable）
)

# 调用 chain.invoke({"question": "什么是AI？"}) 时：
# 1. prompt.invoke({"question": "什么是AI？"})
#    → ChatPromptValue("请回答：什么是AI？")
#
# 2. llm.invoke(ChatPromptValue(...))
#    → AIMessage(content="AI是人工智能...")
#
# 3. parser.invoke(AIMessage(...))
#    → "AI是人工智能..."
```

### RunnableSequence 源码解析

```python
class RunnableSequence(Runnable):
    """
    顺序执行多个 Runnable
    
    核心逻辑非常简单：
    前一个的输出 = 后一个的输入
    
    类比：
    - Unix: cat file | grep "error" | sort
    - Java Stream: list.stream().map(f1).map(f2).collect()
    """
    
    first: Runnable    # 第一个步骤
    middle: List[Runnable] = []  # 中间步骤
    last: Runnable     # 最后一个步骤
    
    def invoke(self, input, config=None):
        # 依次执行，传递结果
        result = self.first.invoke(input, config)
        for step in self.middle:
            result = step.invoke(result, config)
        return self.last.invoke(result, config)
    
    def stream(self, input, config=None):
        """
        流式执行的关键：只有最后一步需要流式
        前面的步骤正常执行，最后一步流式输出
        
        为什么？因为用户只关心最终输出的流式效果
        中间步骤（如 Prompt 格式化）不需要流式
        """
        # 前面的步骤正常执行
        result = self.first.invoke(input, config)
        for step in self.middle:
            result = step.invoke(result, config)
        # 最后一步流式输出
        yield from self.last.stream(result, config)
```

### RunnableParallel 源码解析

```python
class RunnableParallel(Runnable):
    """
    并行执行多个 Runnable，结果合并为字典
    
    类比：
    - Java: CompletableFuture.allOf(future1, future2, future3)
    - 然后把结果合并到一个 Map 中
    """
    
    steps: Dict[str, Runnable]
    
    def invoke(self, input, config=None):
        # 并行执行所有分支
        with ThreadPoolExecutor() as executor:
            futures = {
                key: executor.submit(step.invoke, input, config)
                for key, step in self.steps.items()
            }
            return {
                key: future.result()
                for key, future in futures.items()
            }

# 使用示例：RAG 中的并行检索
chain = {
    "context": retriever,           # 检索文档
    "question": RunnablePassthrough()  # 透传问题
} | prompt | llm

# 执行时：
# 1. retriever 和 RunnablePassthrough 并行执行
# 2. 结果合并为 {"context": docs, "question": "原始问题"}
# 3. 传给 prompt 格式化
# 4. 传给 llm 生成回答
```

---

## 第三部分：LCEL 深度解析

### LCEL 的设计思想

```
LCEL = LangChain Expression Language

本质：一种声明式的 Runnable 组合语法

声明式 vs 命令式：
- 命令式（手写）：一步步告诉计算机"怎么做"
- 声明式（LCEL）：描述"要什么"，框架决定"怎么做"

类比：
- SQL 是声明式的：SELECT * FROM users WHERE age > 18
  你不需要告诉数据库怎么遍历、怎么过滤
- LCEL 也是声明式的：prompt | llm | parser
  你不需要告诉框架怎么传递数据、怎么处理错误
```

### LCEL 常用模式

**模式 1：基础链**
```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 最简单的 LCEL 链
chain = ChatPromptTemplate.from_template("用一句话解释{topic}") | llm | StrOutputParser()

result = chain.invoke({"topic": "向量数据库"})
```

**模式 2：RAG 链**
```python
from langchain_core.runnables import RunnablePassthrough

# RAG 的经典 LCEL 写法
rag_chain = (
    {
        "context": retriever | format_docs,    # 检索 + 格式化
        "question": RunnablePassthrough()       # 透传问题
    }
    | prompt
    | llm
    | StrOutputParser()
)
```

**模式 3：条件分支**
```python
from langchain_core.runnables import RunnableBranch

# 根据输入长度选择不同处理链
chain = RunnableBranch(
    (lambda x: len(x["text"]) > 1000, summarize_chain),  # 长文本 → 摘要
    (lambda x: len(x["text"]) > 100, analyze_chain),     # 中等文本 → 分析
    short_answer_chain                                     # 短文本 → 直接回答
)
```

**模式 4：RunnableLambda（自定义函数）**
```python
from langchain_core.runnables import RunnableLambda

# 把普通函数包装成 Runnable
def add_context(input_dict):
    """自定义处理逻辑"""
    input_dict["timestamp"] = "2024-01-01"
    return input_dict

chain = RunnableLambda(add_context) | prompt | llm
```

---

## 第四部分：Callbacks — LangChain 的 AOP

### Callbacks 的作用

```
Callbacks = 在组件执行的各个阶段插入自定义逻辑

类比 Spring AOP：
- @Before → on_llm_start, on_tool_start
- @After → on_llm_end, on_tool_end
- @AfterThrowing → on_llm_error, on_tool_error

用途：
- 日志记录
- 性能监控
- Token 计数
- 调试追踪
```

### Callback 事件

```python
class BaseCallbackHandler:
    """回调处理器基类"""
    
    # --- LLM 相关 ---
    def on_llm_start(self, serialized, prompts, **kwargs):
        """LLM 开始调用"""
    
    def on_llm_new_token(self, token, **kwargs):
        """LLM 生成新 token（流式场景）"""
    
    def on_llm_end(self, response, **kwargs):
        """LLM 调用结束"""
    
    def on_llm_error(self, error, **kwargs):
        """LLM 调用出错"""
    
    # --- Tool 相关 ---
    def on_tool_start(self, serialized, input_str, **kwargs):
        """工具开始调用"""
    
    def on_tool_end(self, output, **kwargs):
        """工具调用结束"""
    
    # --- Chain 相关 ---
    def on_chain_start(self, serialized, inputs, **kwargs):
        """Chain 开始执行"""
    
    def on_chain_end(self, outputs, **kwargs):
        """Chain 执行结束"""
```

---

## 第五部分：ChatModel 的内部实现

### ChatOpenAI 如何实现 Runnable

```python
# 简化版源码
class BaseChatModel(Runnable):
    """
    所有 Chat 模型的基类
    实现了 Runnable 协议
    """
    
    def invoke(self, input, config=None):
        """
        invoke 的内部流程：
        1. 将输入转换为消息列表
        2. 调用 _generate 方法（子类实现）
        3. 触发 Callbacks
        4. 返回 AIMessage
        """
        messages = self._convert_input(input)
        
        # 触发 on_chat_model_start 回调
        self._call_callbacks("on_chat_model_start", messages)
        
        try:
            result = self._generate(messages)  # 子类实现
            self._call_callbacks("on_chat_model_end", result)
            return result.generations[0].message
        except Exception as e:
            self._call_callbacks("on_chat_model_error", e)
            raise

class ChatOpenAI(BaseChatModel):
    """
    OpenAI 兼容的 Chat 模型
    通义千问的 DashScope API 也走这个类
    """
    
    model: str = "gpt-3.5-turbo"
    api_key: str
    base_url: str
    
    def _generate(self, messages):
        """
        实际调用 API 的地方
        内部使用 openai SDK
        """
        client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=self._convert_messages(messages)
        )
        return self._create_result(response)
```

**关键理解**：
- `ChatOpenAI` 是 `Runnable` 的子类
- 所以它可以用 `|` 操作符和其他 Runnable 组合
- `invoke` 方法内部调用 OpenAI API
- 通义千问的 DashScope 因为兼容 OpenAI 格式，所以直接用 `ChatOpenAI` 就行

### ChatOpenAI 底层接的是什么 API？

**答案：Chat Completions API**（`/v1/chat/completions`）

OpenAI 提供了两类 HTTP API：

| API | 端点 | 特点 | 适用场景 |
|-----|------|------|---------|
| **Chat Completions** | `/v1/chat/completions` | 无状态，每次请求带完整对话历史 | 行业标准，几乎所有 LLM 厂商兼容 |
| **Responses** | `/v1/responses` | 有状态，服务端管理对话历史 | OpenAI 独有，面向 Agent 场景 |

**LangChain 为什么选择 Chat Completions？**

1. **兼容性** — Chat Completions 是行业标准，通义千问、DeepSeek、Moonshot 等国内厂商都兼容这个格式。你只需要改 `base_url` 就能切换模型
2. **LangChain 自己管状态** — LangChain 的 Memory、Runnable 链本身就在做状态管理，不需要 OpenAI 服务端帮忙
3. **Responses API 是 OpenAI 独有的** — 其他厂商不支持，LangChain 作为框架不能绑死在一家

**Chat Completions API 的请求格式**：
```python
# 这就是为什么通义千问能直接用 ChatOpenAI
client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"}
    ]
)
```

**对你的影响**：
- 我们用的通义千问 DashScope 兼容 Chat Completions 格式
- 所以 `ChatOpenAI` 可以无缝对接
- 不用关心 Responses API（那是 OpenAI 独有的）

---

## 第六部分：Tool 的内部实现

### @tool 装饰器做了什么？

```python
# 当你写：
@tool
def query_food(food_name: str) -> str:
    """查询食物营养信息"""
    return FOOD_DB.get(food_name, "未找到")

# 框架内部做了这些事：
# 1. 解析函数签名 → 得到参数名和类型
# 2. 解析 docstring → 得到工具描述
# 3. 生成 JSON Schema（和我们手写的一样）
# 4. 创建一个 StructuredTool 对象（也是 Runnable）

# 等价于手动创建：
tool_obj = StructuredTool(
    name="query_food",
    description="查询食物营养信息",
    func=query_food,
    args_schema={
        "type": "object",
        "properties": {
            "food_name": {"type": "string"}
        },
        "required": ["food_name"]
    }
)
```

### Tool 也是 Runnable

```python
class BaseTool(Runnable):
    """工具基类，也实现了 Runnable 协议"""
    
    name: str
    description: str
    
    def invoke(self, input, config=None):
        """调用工具"""
        return self._run(input)
    
    @abstractmethod
    def _run(self, input):
        """子类实现具体逻辑"""
        ...

# 因为 Tool 是 Runnable，所以可以组合：
chain = some_parser | query_food_tool | format_result
```

---

## 小结

### LangChain 架构的核心设计

1. **Runnable 协议**：统一接口，一切皆可组合
   - `invoke` / `ainvoke` / `stream` / `batch`
   - `|` 操作符实现链式组合

2. **LCEL**：声明式编排语法
   - `|` = 顺序执行
   - `{}` = 并行执行
   - `RunnableBranch` = 条件分支

3. **Callbacks**：AOP 式的横切关注点
   - 日志、监控、调试

4. **分层架构**：
   - 协议层（Runnable）→ 组件层（LLM、Tool）→ 应用层（Agent、Chain）

5. **ChatOpenAI 底层接的是 Chat Completions API**：
   - 行业标准，所有兼容厂商（通义千问、DeepSeek 等）都能用
   - Responses API 是 OpenAI 独有的，LangChain 不绑定

### 类比总结

| LangChain | Java/Spring |
|-----------|-------------|
| Runnable | Function<T, R> |
| LCEL `\|` | Stream.map().filter() |
| RunnableSequence | 方法链调用 |
| RunnableParallel | CompletableFuture.allOf() |
| Callbacks | Spring AOP / Interceptor |
| ChatOpenAI | JdbcTemplate（封装底层调用） |
| @tool | @RequestMapping（注解驱动） |

---

## 附录：LangChain 1.0 新特性预览

> 以下内容作为了解，后续课程会深入讲解。

### 1. `create_agent` — 新的 Agent 创建方式

```python
# 1.0 新 API：一行代码创建 Agent
from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-4o",   # 1.0 支持 "provider:model" 简写
    tools=[search_tool, calculator_tool],
    prompt="你是一个有用的助手",
)

# 基于 LangGraph runtime，自动支持持久化、流式、人工审批
result = agent.invoke({"input": "今天北京天气怎么样？"})
```

**类比**：如果说 Runnable + LCEL 是 Spring Core，那 `create_agent` 就是 Spring Boot — 约定优于配置，快速启动。

### 2. Middleware — Agent 执行的拦截器

```python
# 类比 Spring 的 Filter / Interceptor
# 在 Agent loop 的各个阶段插入自定义逻辑

from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[
        # 内置中间件：PII 脱敏
        PIIMiddleware(),
        # 内置中间件：对话摘要（防止上下文过长）
        SummarizationMiddleware(),
        # 自定义中间件
        MyCustomMiddleware(),
    ]
)
```

**类比 Spring**：
- `PIIMiddleware` ≈ 一个 Filter，在请求进入前脱敏
- `SummarizationMiddleware` ≈ 一个 Interceptor，在对话过长时自动摘要

### 3. 标准内容块（Standard Content Blocks）

```python
# 1.0 新增：统一不同 provider 的响应格式
response = llm.invoke("解释量子计算")

# 新属性：content_blocks
# 统一访问 reasoning traces、citations、tool calls 等
for block in response.content_blocks:
    if block.type == "reasoning":
        print(f"推理过程: {block.content}")
    elif block.type == "text":
        print(f"回答: {block.content}")
```

**解决的问题**：以前不同 provider（OpenAI、Anthropic、Google）返回格式不同，现在统一了。

### 4. 旧功能迁移到 `langchain-classic`

```bash
# 如果你需要使用旧 API（不推荐，但兼容）
pip install langchain-classic

# 旧导入方式
from langchain_classic.chains import LLMChain, SequentialChain
from langchain_classic.memory import ConversationBufferMemory
```

**建议**：新项目直接用 LCEL + `create_agent`，不要用旧 Chain 类。
