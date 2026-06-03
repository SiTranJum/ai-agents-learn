# LangGraph 进阶：持久化、人机交互、State 流转与底层机制

> 本文结合 `health-agent` 真实代码，讲解 LangGraph 的进阶用法与底层逻辑。
> 覆盖四个主题：
> 1. 是否需要结合 `MemorySaver` 实现持久化（及如何实现）
> 2. LangGraph 进阶用法与底层机制（Checkpointer / 子图 / 人机交互 / Reducers）
> 3. 人机交互如何与「问用户问题」结合，现状有没有相关 node
> 4. State 流转逻辑：state 有什么、node 怎么与 state 交互、有哪些 hook
>
> 配套阅读：
> - `health-agent/docs/agent-optimization-guide.md`
> - `courses/28-langsmith-observability/langsmith-tutorial.md`

---

## 0. 你项目的现状（先对齐事实）

| 维度 | 现状 | 代码位置 |
|------|------|---------|
| Checkpointer | **没有用**，`compile()` 无参数 | `app/agents/chat/graph.py:55` |
| 图单例 | 进程内单例复用编译产物 | `app/dependencies.py:228` |
| 调用方式 | `astream_events(state, version="v2")`，每次传完整 state | `app/api/v1/ai.py:361` |
| 跨请求状态 | **自研** `PendingActionStore`（内存 dict，计划 Redis） | `app/services/pending_action_store.py` |
| 对话历史 | **手动**存 DB，再每次查出来塞进 state | `app/services/chat_service.py` + `ai.py:296` |
| 依赖注入 | service 通过 state 字段 / `config["configurable"]` 注入 | `ai.py:305` / `diet/nodes.py:53` |
| 人机交互 | **自研** choice_prompts + pending_action，非原生 interrupt | `chat/nodes.py:218` + `ai.py:301-384` |

**一句话总结**：你现在用「手动 DB 历史 + 自研 PendingActionStore」实现了
**本来 LangGraph Checkpointer 可以帮你做的事**。这不是错，下面分析要不要切换。

---

## 1. 是否需要结合 MemorySaver 实现持久化？

### 1.1 先搞清楚 Checkpointer 到底持久化什么

LangGraph 的 Checkpointer（`MemorySaver` 是其内存实现）持久化的是
**图的运行状态快照（checkpoint）**——即每个 super-step 之后整个 `State` 的值。
它带来三个能力：

1. **会话记忆**：同一个 `thread_id` 的多次调用，自动累积 state（尤其是
   `messages` 这类带 reducer 的字段），不用每次手动把历史塞回去。
2. **断点续跑 / 时间旅行**：可以从任意 checkpoint 恢复、回放、改写历史重跑。
3. **人机交互（interrupt）**：图可以在中途「暂停」并把状态存盘，等用户输入后
   用同一个 `thread_id` 恢复执行（见第 3 节）。

### 1.2 MemorySaver vs 你现在的方案

| | MemorySaver（内存） | 你的 PendingActionStore（内存） |
|---|---|---|
| 存什么 | 整个 State 快照 + 每步历史 | 只存一个 pending_action |
| 进程重启 | **丢失** | **丢失** |
| 多实例共享 | **不行**（各进程独立内存） | **不行** |
| 适用 | 单进程开发/demo | 单进程开发/demo |

**关键结论**：`MemorySaver` 和你现在的内存方案**持久化级别完全一样**（都是进程内、
重启即失、不能多实例共享）。所以**为了「持久化」而引入 MemorySaver 没有意义**——
真正要持久化得用 `PostgresSaver`（你本来就有 Postgres）。

### 1.3 那要不要上 Checkpointer（Postgres 版）？

分场景判断：

**支持上 Checkpointer 的理由：**
- 你已经在**手动**做 Checkpointer 的工作（查历史 → 塞 state → 存回 DB），
  用 `PostgresSaver` 可以把这套样板代码删掉，`messages` 自动累积。
- 如果未来要做**真正的人机交互**（中途暂停等用户回答），
  原生 `interrupt()` + Checkpointer 比你现在的 pending_action 自研机制更干净。

**暂时不上的理由：**
- 你的对话历史**已经存在业务表**（`ChatMessage`），有完整的分页/软删/权限隔离
  （`chat_service.py`），Checkpointer 的 state 表是另一套存储，**会造成双写/数据重复**。
- Checkpointer 存的是「LangGraph 内部 state 快照」，结构是面向框架的，
  不如你的业务表适合直接查询展示。
- 你的 state 里塞了大量**不可序列化的依赖**（`diet_service` / `memory_service` /
  `embedding_client`，见 `ai.py:314-317`），Checkpointer 要求 state 可序列化，
  直接开会**报错或存一堆无意义对象**。必须先把这些依赖移到 `config["configurable"]`
  才能用 Checkpointer。

### 1.4 推荐方案（务实路线）

**短期：不引入 Checkpointer**，保持现状。原因：你的业务表已经解决了历史持久化，
强行引入会双写。

**中期：若要做原生人机交互**，再按以下步骤引入 `PostgresSaver`：

```python
# 第 1 步：把依赖从 state 移到 config（Checkpointer 不持久化 config）
# 原来（ai.py）：state 里塞 service ——不可序列化
state = {..., "memory_service": memory_service, ...}

# 改为：
config = {
    "configurable": {
        "thread_id": session_id,          # ← 同一会话用同一 thread_id
        "memory_service": memory_service, # 依赖放这里，不进 checkpoint
        "rag_service": rag_service,
    }
}

# 第 2 步：编译时挂 PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async with AsyncPostgresSaver.from_conn_string(DB_URL) as saver:
    graph = build_chat_agent(checkpointer=saver)   # compile(checkpointer=saver)

# 第 3 步：调用时带 thread_id，messages 自动累积
await graph.ainvoke({"user_message": text}, config=config)
```

**注意**：节点里读依赖也要从 `config` 拿，不再从 state 拿
（参考你 `diet/nodes.py:53` 已经在用 `config["configurable"]` 的写法）。

---

## 2. LangGraph 进阶用法与底层机制

### 2.1 Checkpointer（检查点 / 持久化层）

**底层逻辑**：LangGraph 把执行分成一个个 **super-step**（超步）。每个超步执行完，
Checkpointer 把当前 `State` 序列化存成一个 checkpoint，带 `thread_id` + `checkpoint_id`。

```
super-step 1 (identify_intent) → 存 checkpoint_1
super-step 2 (recall_memories) → 存 checkpoint_2
...
```

- `MemorySaver`：存内存 dict（开发用）
- `SqliteSaver` / `PostgresSaver`：存数据库（生产用）

**能力**：`graph.get_state(config)` 读当前状态，`graph.get_state_history(config)`
看历史，`graph.update_state(config, values)` 手动改状态（时间旅行）。

### 2.2 子图（Subgraph）

**你已经在用**：`diet` 子图作为主图的一个节点挂载
（`chat/graph.py:34` → `build_diet_subgraph()`），`memory` 子图独立编译异步跑
（`chat/nodes.py:174`）。

**两种子图通信方式**：
1. **共享 state schema**（你 diet 子图用的就是这种）：子图直接读写父图的
   `ChatState`，字段用 `diet_` 前缀隔离（`diet/subgraph.py` 注释有说明）。
2. **不同 state schema**：父子 state 结构不同时，要在 `add_node` 时包一层函数
   做 state 转换（你的 memory 子图用的是独立 `MemoryExtractionState`，
   通过手动构造输入 dict 调用，见 `chat/nodes.py:176`）。

**子图式打印 / 可视化**：

```python
graph = build_chat_agent()

# 打印 ASCII 结构
print(graph.get_graph().draw_ascii())

# 展开子图（xray=True 会把 diet 子图内部节点也画出来）
print(graph.get_graph(xray=True).draw_ascii())

# 生成 Mermaid（可贴到 markdown 渲染）
print(graph.get_graph(xray=True).draw_mermaid())

# 生成 PNG
graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")
```

> `xray=True` 就是你说的「子图式打印」——把作为节点的子图展开成内部细节，
> 对你这种 diet 子图嵌套的结构特别有用。

### 2.3 人机交互（Human-in-the-loop）

**底层依赖 Checkpointer**（没有 checkpointer 就没法暂停/恢复）。核心是 `interrupt()`：

```python
from langgraph.types import interrupt, Command

def ask_meal_type(state):
    # 执行到这里图会"暂停"，把 value 抛给调用方，并存 checkpoint
    answer = interrupt({"question": "请问是哪一餐？", "options": [...]})
    # 恢复后，answer 就是用户的回答
    return {"diet_meal_type": answer}

# 调用方：第一次跑到 interrupt 会停下
result = graph.invoke(state, config)   # result 里含 __interrupt__

# 用户回答后，用 Command(resume=...) 恢复，同一个 thread_id
graph.invoke(Command(resume="lunch"), config)
```

详见第 3 节与你现状的对比。

### 2.4 Reducers（状态合并函数）—— 重点概念

**Reducer 决定「节点返回的字段值，如何合并进现有 state」。**

默认行为是**覆盖**（overwrite）。但有些字段你想**追加**而不是覆盖，
就要用 `Annotated[type, reducer_function]` 指定合并策略。

**你代码里就有一个例子**（`chat/state.py:48`）：

```python
class ChatState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]  # ← add_messages 是 reducer
    user_id: str                                          # ← 无 reducer = 覆盖
    recalled_memories: list[dict[str, Any]]               # ← 覆盖
```

- `messages` 字段：reducer 是 `add_messages`，节点返回新消息时**追加合并**
  （而不是替换整个列表），这是 LangChain 对话图的标准模式。
- 其它字段：没标 reducer，节点返回就**整个覆盖**旧值。

**Reducer 的底层意义**：

```
节点返回 {"messages": [new_msg]}
        ↓
LangGraph 查 messages 字段的 reducer = add_messages
        ↓
new_state["messages"] = add_messages(old_messages, [new_msg])  # 追加
```

**为什么并行节点必须关注 reducer**（呼应优化文档第 4 点）：
当两个并行分支**同时写同一个字段**时，没有 reducer 会冲突报错；
有 reducer（如 `operator.add`）才能把两个分支的结果合并。
你计划并行的 `recall_memories` / `search_knowledge` 写的是**不同字段**，
所以暂时不需要加 reducer。

**自定义 reducer 示例**：

```python
import operator
from typing import Annotated

class State(TypedDict):
    # 多个节点返回的 list 自动拼接
    collected: Annotated[list[str], operator.add]
    # 自定义：取最大值
    max_score: Annotated[int, lambda old, new: max(old, new)]
```

---

## 3. 人机交互如何与「问用户问题」结合？现状有没有 node？

### 3.1 现状：你已经实现了「问用户问题」，但用的是自研机制（非原生 interrupt）

**有没有 node？** —— 有，就是 `wrap_response`（`chat/nodes.py:207`）。

它在饮食场景里，当识别到食物但 `meal_type` 缺失时，**产出一个 choice_prompt**
反问用户「请问是哪一餐？」（`chat/nodes.py:218-239`）：

```python
# chat/nodes.py wrap_response 节点
if parse_result.meal_type is None and state.get("pending_action") is None:
    choice_prompt = {
        "prompt_id": prompt_id,
        "question": "请选择餐次",
        "options": [{"value": "breakfast", "label": "早餐"}, ...],
    }
    return {"ai_response": "...请问是哪一餐？", "choice_prompts": [choice_prompt]}
```

### 3.2 现状的完整交互闭环（自研版人机交互）

```
第 1 次请求（用户："我午饭吃了鸡胸肉"）
   ↓ chat agent 跑完
   wrap_response 发现 meal_type 缺失 → emit choice_prompt
   ↓ ai.py:377 把它存成 pending_action（PostgresActionStore）
   ↓ SSE 推 choice 事件给前端，前端弹选项 chips
   ── 图执行结束（没有"暂停"，是彻底跑完了）──

第 2 次请求（用户点了"午餐" → type=choice_response）
   ↓ ai.py:302 读出 pending_action
   ↓ ai.py:324-334 把用户选的 meal_type 合并进 diet_partial，删除 pending_action
   ↓ 重新跑一遍 chat agent（这次 meal_type 有了）→ 出卡片
```

**本质**：你用「**两次独立的图调用** + 外部 pending_action 存储」模拟了人机交互。
图本身没有「暂停」，每次都是从头跑完。

### 3.3 原生 interrupt 方案对比（如果未来想切换）

```python
# 用原生 interrupt，wrap_response 改成：
from langgraph.types import interrupt

def ask_meal_type(state):
    if state["diet_parse_result"].meal_type is None:
        # 图在这里真正"暂停"并存 checkpoint
        meal = interrupt({"question": "请问是哪一餐？", "options": [...]})
        return {"diet_meal_type": meal}
    return {}

# API 层：同一个 thread_id 恢复，不用重新跑前面的节点
graph.invoke(Command(resume="lunch"), config={"configurable": {"thread_id": session_id}})
```

| | 你的自研方案 | 原生 interrupt |
|---|---|---|
| 依赖 Checkpointer | 否 | **是**（必须） |
| 第二次是否重跑全图 | **是**（从头跑） | 否（从断点恢复） |
| 跨进程/实例 | 看 store 实现 | 看 checkpointer 实现 |
| 实现复杂度 | 自己管 pending_action | 框架管，但要先上 checkpointer |
| 适合场景 | 简单一问一答（你现在够用） | 多步审批、复杂中断恢复 |

### 3.4 建议

**你现在的场景（一次澄清餐次）用自研方案完全够用，不需要切 interrupt。**
只有当出现「图执行到一半要等人工审批、且不想重跑前面昂贵节点」的场景时，
才值得引入 Checkpointer + interrupt。届时最大的收益是
**避免重复跑 identify_intent / 解析等节点**，省 token 和时间。

---

## 4. State 流转逻辑：state 有什么、node 怎么交互、有哪些 hook

### 4.1 State 里有什么

`ChatState`（`chat/state.py:44`）是一个 `TypedDict`，按用途分组：

| 分组 | 字段 | 说明 |
|------|------|------|
| 对话核心 | `messages` / `user_message` / `chat_history` / `ai_response` / `prompt_messages` | `messages` 带 `add_messages` reducer |
| 路由 | `intent` | identify_intent 写入，条件边据此分流 |
| 记忆/RAG | `recalled_memories` / `knowledge` / `long_term_profile` | 召回结果 |
| 领域（diet） | `diet_input_text` / `diet_parse_result` / `diet_meal_type` ... | 带 `diet_` 前缀隔离 |
| 依赖注入 | `memory_service` / `rag_service` / `embedding_client` / `diet_service` | **不可序列化**，按请求注入 |
| 元信息 | `request_id` / `error` | |
| 流式交互 | `pending_action` / `choice_prompts` | 人机交互用 |

> ⚠️ 注意「依赖注入」那组字段——它们是把 service 对象塞进了 state。
> 这是当前能跑但**不利于上 Checkpointer** 的设计（见第 1.3 节）。

### 4.2 Node 怎么和 State 交互（核心机制）

**铁律：节点只返回「要更新的字段」，不返回整个 state；返回的 dict 由框架合并。**

```python
@log_node
async def recall_memories(state: ChatState) -> dict[str, Any]:
    query = state.get("user_message") or ""        # ① 读：从 state 取输入
    recalled = await recall_memories_tool(...)     # ② 算：业务逻辑
    return {"recalled_memories": recalled,         # ③ 写：只返回要更新的字段
            "long_term_profile": []}
```

完整流转（呼应第 2.4 节 reducer）：

```
框架把当前 state 传给节点（只读视角）
        ↓
节点返回 {"recalled_memories": [...]}   ← 局部更新
        ↓
框架对每个返回字段查 reducer：
  - 有 reducer（如 messages）→ 合并
  - 无 reducer → 覆盖
        ↓
生成新 state，传给下一个节点
```

**条件边**也读 state 决定走向（`chat/nodes.py:79` `route_after_intent`）：

```python
def route_after_intent(state: ChatState) -> str:
    return "diet" if state.get("intent") == "diet" else "general"
# graph.add_conditional_edges("identify_intent", route_after_intent, {...})
```

### 4.3 有哪些 hook / 钩子

LangGraph 没有 Spring 那种「全局 AOP 注解」，但提供了几类切入点：

**A. 框架级 hook（LangGraph 原生）**

| Hook | 作用 | 你项目是否用 |
|------|------|-------------|
| `astream_events(version="v2")` | 监听所有节点/LLM 的细粒度事件 | ✅ `ai.py:361` + `translator.py` |
| Checkpointer | 每个 super-step 后存盘（生命周期 hook） | ❌ 未用 |
| `interrupt()` | 节点内中断/恢复 | ❌ 未用（用自研） |
| `config["configurable"]` | 按调用注入依赖/参数 | ✅ `diet/nodes.py:53` |
| `RunnableConfig` callbacks | LangChain 回调（on_llm_start 等） | 间接（LangSmith 用） |

**B. 你自研的「节点级 hook」（装饰器模式）**

你用装饰器实现了类似 AOP 的横切逻辑（`app/agents/_logging.py`）：

```python
@log_node          # ← 包裹每个节点：自动打日志、计时、错误捕获
async def recall_memories(state): ...

async with llm_call("identify_intent", "qwen-plus", ...):  # ← LLM 调用 hook
    result = await model.ainvoke(...)
```

- `@log_node`：节点进入/退出/异常的统一日志钩子（横切所有节点）。
- `llm_call(...)` 上下文管理器：每次 LLM 调用的计时/日志钩子。
- 这俩是你**自己实现的 hook 机制**，等价于「节点 AOP」。

**C. 事件流 hook（翻译层）**

`translator.py` 的 `translate_langgraph_events` 本质是一个**事件拦截器**：
监听 `astream_events` 吐出的 `on_chain_start` / `on_chat_model_stream` /
`on_tool_start` 等底层事件，翻译成业务事件。这就是你接「节点级可观测性」的 hook 点。

### 4.4 一张图总结 state 流转

```
API 层 (ai.py) 构造初始 state（含依赖注入）
        ↓ astream_events(state, version="v2")
┌─────────────────────────────────────────────┐
│ identify_intent ──(条件边读 intent)──┐        │
│   读 user_message → 写 intent        │        │
│                                      ▼        │
│   ┌── diet 子图 ──┐    recall_memories        │
│   │ (共享 state) │    读 user_message→写 memories
│   └──────┬───────┘         ▼                  │
│          │           search_knowledge         │
│          │                 ▼                  │
│          │           assemble_prompt          │
│          │                 ▼                  │
│          │           call_llm（流式）→写 ai_response
│          │                 ▼                  │
│          │       trigger_memory_extract（异步fire）
│          ▼                 ▼                  │
│        wrap_response（可 emit choice_prompt）  │
│   每个节点：读 state → 返回局部 dict → reducer 合并 │
│   每个节点被 @log_node 包裹（自研 hook）         │
└─────────────────────────────────────────────┘
        ↓ 事件经 translator 翻译
        ↓ SSE 推给前端；choice_prompt 存 pending_action
```

---

## 5. 总结与行动建议

1. **MemorySaver 不解决持久化**（它也是内存的）。要持久化用 `PostgresSaver`，
   但你已有业务表存历史，**短期不建议引入**，避免双写。
2. **上 Checkpointer 的前置条件**：先把 `memory_service` 等不可序列化依赖
   从 state 移到 `config["configurable"]`（你 diet 子图已有此范式）。
3. **人机交互你已实现**（choice_prompt + pending_action），一问一答场景够用；
   只有「中途暂停免重跑昂贵节点」才值得换原生 `interrupt()` + Checkpointer。
4. **Reducer 是并行的前提**：并行写同字段必须配 reducer；你计划的并行检索
   写不同字段，暂时安全。
5. **可视化**：用 `graph.get_graph(xray=True).draw_mermaid()` 把含子图的结构
   画出来，贴进文档维护。
6. **Hook 现状**：你用 `@log_node` + `llm_call` + `translator` 自研了
   三层切面，已覆盖日志/计时/事件翻译，工程上很完整。

| 行动 | 优先级 | 前置条件 |
|------|--------|---------|
| 维持现状（历史用业务表 + 自研 pending_action） | — | 无 |
| 把依赖从 state 迁到 config["configurable"] | ⭐⭐ | 重构 ai.py + 各节点读取处 |
| 引入 PostgresSaver + interrupt（仅当需要复杂中断） | ⭐ | 上一条完成 |
| 用 xray draw_mermaid 维护架构图 | ⭐⭐ | 无，随时可做 |

