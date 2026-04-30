# 课程 23 学习笔记：LangChain 架构深度剖析

---

## 1. LangChain 1.0 的核心变化

LangChain 1.0 于 2025 年 10 月发布，是第一个稳定版本。

**保留的核心**（位于 `langchain-core`）：
- Runnable 协议 — 依然是框架灵魂
- LCEL（`|` 操作符、链式组合）— 完全保留
- Callbacks — 回调机制保留
- 导入路径 — `langchain_core`、`langchain_openai` 等不变

**移到 `langchain-classic` 的旧功能**：
- `LLMChain`、`SequentialChain`、`TransformChain` 等旧式 Chain 类
- `ConversationBufferMemory` 等旧式 Memory 类
- 部分 Retriever 和 Index API

**1.0 新增**：
- `create_agent` — 新的 Agent 创建 API，替代 `langgraph.prebuilt.create_react_agent`
- Middleware 机制 — 在 Agent loop 各阶段插入控制逻辑（类比 Spring Filter/Interceptor）
- 标准内容块（Standard Content Blocks）— 统一不同 provider 的响应格式
- 要求 Python 3.10+

---

## 2. OpenAI 的两类 API：Chat Completions vs Responses

| | Chat Completions | Responses |
|---|---|---|
| 端点 | `/v1/chat/completions` | `/v1/responses` |
| 推出时间 | 2023 年 | 2025 年 3 月 |
| 状态管理 | **无状态**，每次请求带完整对话历史 | **有状态**，服务端帮你管对话历史 |
| 兼容性 | 行业标准，通义千问/DeepSeek/Moonshot 等都兼容 | OpenAI 独有 |
| 定位 | 通用 | 面向 Agent 场景 |

**一句话区别**：Chat Completions 是"你管状态"，Responses 是"OpenAI 帮你管状态"。

### LangChain（ChatOpenAI）底层接的是 Chat Completions API

原因：
1. **兼容性** — 换 `base_url` 就能切模型，通义千问等厂商都支持
2. **架构一致** — LangChain 自己管状态（Memory/Runnable），不需要 OpenAI 帮忙管
3. **厂商中立** — 框架不能绑死在一家 provider

> 我们用通义千问 DashScope，它兼容 Chat Completions 格式，完全不用关心 Responses API。

---

## 3. LangChain 的 Runnable 不是 Java 的 Runnable

Python 标准库里**没有** Runnable，这是 LangChain 自己定义的类（位于 `langchain_core.runnables`）。

**和 Java Runnable 的区别**：

| | Java `Runnable` | LangChain `Runnable` |
|---|---|---|
| 核心方法 | `void run()` | `Output invoke(Input)` |
| 有输入？ | 没有 | 有 |
| 有返回值？ | 没有 | 有 |
| 设计目的 | 线程中执行的代码 | 有输入输出的可组合处理单元 |

**真正对应的 Java 概念是 `Function<Input, Output>`**，而且是加强版：

```
invoke()   → Function.apply()          同步执行
ainvoke()  → CompletableFuture         异步执行
stream()   → Stream<T>                 流式执行
batch()    → parallelStream().map()    批量执行
```

Java 需要四个东西才能覆盖的能力，LangChain 一个 `Runnable` 接口全包了。

---

## 4. invoke 的参数取决于链的第一个 Runnable

invoke 没有固定的参数类型，**第一个 Runnable 期望什么，就传什么**：

- **ChatPromptTemplate** 开头 → 传字典 `{"topic": "RAG"}`（填充模板变量）
- **RunnableLambda(func)** 开头 → 取决于 func 接受什么
- **直接调用 LLM** → 传消息列表 `[{"role": "user", "content": "你好"}]`

第二个参数 `config` 是可选的框架配置（callbacks、tags 等），不是业务数据。

---

## 5. ChatPromptTemplate 的 from_template + invoke 是两步操作

### 容易混淆的点

`from_template("解释{topic}")` 传的是字符串模板，`invoke({"topic": "RAG"})` 传的是字典。为什么字典能映射到字符串里？

**答案：这是两步操作**：
1. `from_template()` — 定义模板，记住"我有一个变量叫 topic"
2. `invoke()` — 填值，用字典的 key-value 替换占位符

```python
# 本质上就是 Python 的 str.format()
"解释{topic}".format(**{"topic": "RAG"})  # → "解释RAG"
```

类比 Java 的 `MessageFormat.format(template, args)` 或 Spring 的 `${placeholder}` 替换。

### 两种创建方式

```python
# 快捷方式：只生成一条 user 消息
prompt = ChatPromptTemplate.from_template("解释{topic}")
# invoke → [HumanMessage("解释RAG")]

# 完整方式：指定多条消息和角色
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是{role}"),
    ("user", "{question}"),
])
# invoke → [SystemMessage("你是健康顾问"), HumanMessage("每天喝多少水？")]
```

### 在链中的职责

```
chain = prompt         |    llm           |    parser
       Dict→消息列表       消息列表→AIMessage    AIMessage→字符串
       构造 messages       调用 API             提取文本
```

ChatPromptTemplate 是链的"入口翻译官"：把字典变量填进模板，生成 LLM 能理解的消息列表。

---

## 6. Chain（Runnable）常用 API 速查

### 四种执行方法

| 方法 | 用途 | Java 类比 |
|------|------|-----------|
| `invoke(input)` | 同步执行，返回完整结果 | `Function.apply()` |
| `stream(input)` | 流式执行，逐块返回（聊天场景必用） | `Stream<T>` |
| `batch(inputs)` | 批量并发执行（内部用线程池） | `parallelStream()` |
| `ainvoke(input)` | 异步执行（Web 框架中用） | `CompletableFuture` |

### 组合方法

| 方法 | 用途 | 示例 |
|------|------|------|
| `\|` 操作符 | 顺序连接 | `prompt \| llm \| parser` |
| `pipe()` | 和 `\|` 完全一样，方法调用形式 | `prompt.pipe(llm).pipe(parser)` |

### 输入输出处理

| 方法 | 用途 | 说明 |
|------|------|------|
| `RunnablePassthrough.assign(key=func)` | 追加字段 | 保留原始输入，额外计算新字段 |
| `pick("field")` | 提取字段 | 从字典结果中只取需要的字段 |
| `RunnableLambda(func)` | 普通函数变 Runnable | 自定义处理逻辑插入链中 |

### 可靠性方法

| 方法 | 用途 | Java 类比 |
|------|------|-----------|
| `with_retry(stop_after_attempt=3)` | 自动重试 | `@Retryable` |
| `with_fallbacks([backup])` | 降级备选 | Hystrix fallback |
| `with_config(callbacks=[...])` | 绑定默认配置 | `@Configuration` |

### 调试方法

| 方法 | 用途 |
|------|------|
| `get_graph().print_ascii()` | 打印链的结构图 |
| `input_schema.schema()` | 查看需要什么输入 |
| `output_schema.schema()` | 查看输出格式 |
