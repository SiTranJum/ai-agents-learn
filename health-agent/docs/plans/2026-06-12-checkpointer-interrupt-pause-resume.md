# Checkpointer + interrupt() 改造：真正的对话暂停 / 恢复

> 日期：2026-06-12
> 状态：设计 / 待实施
> 目标：把现有"伪暂停"（每次重跑 graph + PendingAction + transcript 重建）改造成
> LangGraph 原生的 **Checkpointer（Postgres）+ interrupt()** 暂停/恢复机制。

---

## 一、背景与问题

### 1.1 现状：没有 checkpointer，所以没有真正的暂停

当前所有"向用户提问让用户选择"的流程，都是**无状态重跑**：

1. AI 节点产出 `choice_prompts`（选项）或带 `actions` 的卡片；
2. 通过 SSE `CHOICE` / `CARD` 事件推给前端，graph 跑到 `END` 结束；
3. 用户回答后，前端发**一个全新的请求**（`type=choice_response` 或 `card_action`）；
4. 后端**从头重跑 graph**，靠两样东西"假装"接上了上下文：
   - `PendingActionStore`（进程内 dict）保存上一轮的部分解析结果（仅 diet 餐次在用）；
   - `plan` 草案靠从 `chat_history` 里反序列化 `[plan_draft] {...}` 文本重建。

### 1.2 这套机制的痛点

- **状态靠重建，脆弱**：plan 草案塞进 chat_history 文本里再 parse 回来；diet 靠进程内 dict（重启即丢、多实例不共享）。
- **重复计算 / 重复 LLM 调用**：恢复时整条 graph 重跑，已经做过的解析、召回可能再做一遍。
- **前端要回传大 payload**：卡片确认时前端要把整个 `foods` / `draft` 复制回来，state 没有服务端真相源。
- **无法跨进程/重启恢复**：`InMemoryPendingActionStore` 注释里已写明"生产切 Redis"。
- **逻辑散落**：暂停点逻辑分散在 `wrap_response`、`conversation.py` 的一堆 `_clarify_*` 函数、`ai.py` 的 card_action 快速路径里。

### 1.3 目标方案

用 LangGraph 原生能力替换：

- **Checkpointer（AsyncPostgresSaver）**：把 graph 的完整 state 按 `thread_id` 持久化到 Postgres，天然支持跨请求/跨进程/重启恢复。
- **`interrupt(value)`**：在节点内部"就地暂停"，把 `value`（问题/选项/卡片）抛给调用方；用户回答后用 `Command(resume=answer)` 从**中断点原地继续**，`interrupt()` 直接返回用户的回答。

改造后，提问流程从"两次独立请求 + 状态重建"变成"一次 graph 执行被暂停再恢复"，state 不丢、不重算、前端只回传"决定"而非全量数据。

---

## 二、需要改造的提问 / 选择点清单

下面是当前所有"询问用户、等用户选择/确认再继续"的 graph 节点和流程。改造后它们统一变成"节点内 `interrupt()` 暂停 → 用户回答 → `Command(resume=...)` 恢复"。

| # | 位置 | 触发条件 | 当前机制 | 改造后 |
|---|------|---------|---------|--------|
| 1 | `chat/nodes.py:wrap_response`（diet 餐次澄清） | diet 解析出食物但 `meal_type` 缺失，且非效率模式 | 产出 `choice_prompts`(餐次) + 写 `PendingAction.diet_partial`，graph 结束 | diet 子图内 `interrupt({kind:"choice", prompt:"餐次", options:[...]})`，恢复后拿到餐次继续走保存 |
| 2 | diet 确认卡片 | 确认/学习模式，解析后等用户保存 | `wrap_response` 出确认卡片 → `card_action: confirm_create_diet_record`，走 `ai.py` 快速路径直接落库 | diet 子图内 `interrupt({kind:"card", card:diet_parse})`，恢复值为 `{action:"confirm"|"edit"}`，确认则节点内落库 |
| 3 | body 确认卡片 | 解析身体数据后等用户保存 | `wrap_response` 出 body_parse 卡片 → `card_action: confirm_create_body_record`，走快速路径落库 | body 子图内 `interrupt({kind:"card", card:body_parse})`，恢复值 `{action:"confirm"|"cancel"}` |
| 4 | `plan/conversation.py:_clarify_plan_intent_response` | 计划意图不明 / 只是打招呼 | `choice_prompts: plan_intent` | plan 子图内 `interrupt({kind:"choice", prompt:"想做哪类计划"})` |
| 5 | `plan/conversation.py:_clarify_missing_details_response` / `_starter_choice_prompts` | 缺具体目标或周期 | `choice_prompts: plan_starter / plan_duration` | plan 子图内 `interrupt({kind:"choice", ...})`，多轮澄清串成一连串 interrupt |
| 6 | plan 草案确认卡片 | 草案生成后等确认 | 出 `plan_draft` 卡片 → `card_action: accept/revise`，草案从 transcript 文本重建 | plan 子图内 `interrupt({kind:"card", card:plan_draft})`，草案存在 checkpoint state，恢复值 `{action:"accept"|"revise"|"edit", patch?}` |
| 7 | plan 安全校验调整确认 | 草案违反安全规则被自动调整 | 出带 `violations` 的 plan_draft 卡片，同 #6 路径 | 同 #6，interrupt 携带 `violations`，恢复值 `{action:"accept"|"revise"}` |

> 注：`identify_intent` 等纯计算节点不需要 interrupt。只有"必须等人类输入才能继续"的点才改造。

### 2.1 统一的 interrupt 载荷协议

为了让前端用一套渲染逻辑处理所有暂停点，定义统一的 interrupt value schema：

```python
# app/agents/interrupts.py（新增）
class HumanPrompt(BaseModel):
    """所有 interrupt() 抛出的统一载荷。"""
    kind: Literal["choice", "card"]          # choice=选项 chips / card=富卡片
    prompt_id: str                            # 稳定标识，前端用于匹配回答
    question: str | None = None               # choice 的提问文案
    options: list[ChoiceOption] = []          # choice 的选项
    allow_free_text: bool = False             # choice 是否允许自由文本
    card: dict[str, Any] | None = None        # card 模式的卡片数据
    domain: Literal["diet", "body", "plan"]   # 用于前端归类 / 埋点
```

恢复时调用方传入的 `Command(resume=...)` 载荷协议：

```python
# 用户对 choice 的回答
{"prompt_id": "...", "value": "lunch"}              # 选了某项
{"prompt_id": "...", "free_text": "下午茶"}          # 自由文本

# 用户对 card 的回答
{"prompt_id": "...", "action": "confirm"}            # 点了主操作
{"prompt_id": "...", "action": "edit", "patch": {...}}  # 编辑后提交
{"prompt_id": "...", "action": "cancel"}             # 取消
```

`interrupt()` 在节点内的返回值就是上面这个 dict，节点据此决定下一步。

---

## 三、目标架构

### 3.1 Checkpointer 接入（Postgres）

LangGraph 官方提供 `langgraph-checkpoint-postgres`，含 `AsyncPostgresSaver`。本项目已用
`postgresql+asyncpg`（Supabase）。注意：

- `AsyncPostgresSaver` 底层用 **psycopg(3)** 连接字符串，**不是 asyncpg**。需要一个
  `postgresql://...` 形式的 DSN（去掉 `+asyncpg`），单独给 checkpointer 用，与业务 ORM 引擎分开。
- checkpointer 会在 Postgres 建几张表（`checkpoints`、`checkpoint_writes`、`checkpoint_blobs` 等），
  首次需调用 `await saver.setup()` 建表（幂等）。Supabase 连接数有限（pool=5），checkpointer 用
  独立小连接池（如 max_size=3）。

```python
# app/agents/checkpointer.py（新增）
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

_pool: AsyncConnectionPool | None = None
_saver: AsyncPostgresSaver | None = None

def _checkpointer_dsn() -> str:
    # 把 postgresql+asyncpg://... 转成 psycopg 用的 postgresql://...
    return settings.database_url.replace("+asyncpg", "")

async def get_checkpointer() -> AsyncPostgresSaver:
    global _pool, _saver
    if _saver is None:
        _pool = AsyncConnectionPool(
            conninfo=_checkpointer_dsn(),
            max_size=3,
            kwargs={"autocommit": True, "prepare_threshold": 0},  # Supabase pgbouncer 兼容
            open=False,
        )
        await _pool.open()
        _saver = AsyncPostgresSaver(_pool)
        await _saver.setup()  # 幂等建表
    return _saver
```

> Supabase 若走 transaction-mode pgbouncer，需 `prepare_threshold=0` 禁用预编译语句，否则报错。
> 这是接入时第一个最可能踩的坑，先验证连接再写业务。

### 3.2 graph 编译时挂 checkpointer

```python
# app/agents/chat/graph.py
def build_chat_agent(checkpointer=None):
    graph = StateGraph(ChatState)
    ...
    return graph.compile(checkpointer=checkpointer)
```

`dependencies.py` 的单例构造改成异步、注入 checkpointer：

```python
async def get_chat_agent():
    global _chat_agent_singleton
    if _chat_agent_singleton is None:
        cp = await get_checkpointer()
        _chat_agent_singleton = build_chat_agent(checkpointer=cp)
    return _chat_agent_singleton
```

> 子图（diet/body/plan subgraph）作为父图节点挂载时，**继承父图 checkpointer**，
> 子图内的 `interrupt()` 会冒泡到父图层面暂停。子图自身 `compile()` 不需要单独 checkpointer。

### 3.3 thread_id 设计

checkpointer 用 `config.configurable.thread_id` 标识一条可恢复的会话线。

- **方案**：`thread_id = session_id`。一个 chat session 就是一条 LangGraph 线程。
- 每次请求带 `config={"configurable": {"thread_id": session_id}}`。
- 同一 session 的暂停状态自动按 session 串起来，无需 PendingAction。

> 含义：同一会话同时只能有一个挂起的 interrupt。这符合健康助手的对话式 UX
> （一次问一件事），也简化前端。若未来要并发多问题，可改 `thread_id = f"{session_id}:{turn_id}"`。

### 3.4 执行 / 恢复的判定

LangGraph 在命中 `interrupt()` 时，`astream_events` / `ainvoke` 结束后，
state 的 `__interrupt__` 字段（或 `get_state(config).next` 非空）表示"被中断、等待恢复"。

- **新消息（text）**：用 `state` 作为输入正常 invoke。
- **恢复（choice_response / card_action）**：用 `Command(resume=<答案>)` 作为输入 invoke，
  **不传完整 state**，LangGraph 从 checkpoint 恢复。

判定逻辑：

```python
snapshot = await agent.aget_state(config)
is_resuming = bool(snapshot.next)  # 有待执行节点 = 处于中断态
graph_input = Command(resume=resume_payload) if is_resuming else state
```

---

## 四、流式（SSE）层改造

### 4.1 把 interrupt 翻译成 CHOICE / CARD 事件

现在 `translator.py` 只在 `wrap_response` 的 `on_chain_end` 里抓 `choice_prompts` / `response_cards`。
改造后，暂停信号来自 LangGraph 的 **interrupt 事件**，需要在 translator 里识别它。

`astream_events(version="v2")` 命中 `interrupt()` 时，会在流末尾产生带 `__interrupt__` 的 chunk
（不同 langgraph 版本暴露方式略有差异：可能是 `on_chain_end` 顶层 output 里带 `__interrupt__`，
也可能需要在流结束后 `aget_state` 读 `snapshot.next` + `snapshot.tasks[].interrupts`）。
**实现时以 `aget_state` 为准最稳**：

```python
async def stream_chat(agent, graph_input, config):
    async for ev in translate_langgraph_events(agent, graph_input, config=config):
        yield ev
    # 流跑完后检查是否处于中断态
    snapshot = await agent.aget_state(config)
    if snapshot.next:  # 被 interrupt 暂停了
        for hp in _collect_interrupts(snapshot):     # 取 tasks[].interrupts[].value
            if hp["kind"] == "choice":
                yield StreamEvent(type=CHOICE, data={...})
            else:  # card
                yield StreamEvent(type=CARD, data={"card": hp["card"]})
        yield StreamEvent(type=PAUSED, data={"prompt_id": ...})  # 见 4.2
    else:
        yield StreamEvent(type=DONE, data={...})
```

### 4.2 新增 `PAUSED` 事件类型（推荐）

现有 `StreamEventType` 没有"流暂停、等待用户"的语义，前端靠"收到 CHOICE/CARD 就当作结束"。
显式区分更清晰：

```python
class StreamEventType(str, Enum):
    ...
    PAUSED = "paused"   # 新增：graph 已暂停，等待用户对 prompt_id 作答
```

`PausedPayload`：`{prompt_id, kind, domain}`。前端收到 `PAUSED` 就知道：本轮 AI 暂停了，
下一条用户输入要走"恢复"通道（带上 prompt_id）。

> 兼容策略：保留 `DONE` 作为正常结束，`PAUSED` 仅在中断时发。前端两者都处理。

---

## 五、API 层改造（`api/v1/ai.py`）

### 5.1 三种入口统一为"新输入 vs 恢复"

当前 `ai.py` 对 `text` / `card_action` / `choice_response` 分别构造 state，还有 plan 的
card_action 快速路径。改造后收敛为两类：

```python
config = {"configurable": {"thread_id": req.session_id, **runtime_deps}}
snapshot = await agent.aget_state(config)
is_resuming = bool(snapshot.next)

if req.type == "text" and not is_resuming:
    graph_input = build_initial_state(req, deps)          # 全新一轮
elif req.type in ("choice_response", "card_action") and is_resuming:
    graph_input = Command(resume=build_resume_payload(req))  # 恢复：只回传"决定"
else:
    # 边界：中断态又发普通 text（等于放弃上一个问题）
    # 先 Command(resume={"action":"cancel"}) 清掉中断，再起新一轮（见 §7.4）
    ...
```

### 5.2 `build_resume_payload`

把 `ChatStreamRequest` 字段映射成 §2.1 的 resume 协议：

```python
def build_resume_payload(req) -> dict:
    if req.type == "choice_response":
        if req.free_text:
            return {"prompt_id": req.prompt_id, "free_text": req.free_text}
        return {"prompt_id": req.prompt_id, "value": req.selected_value}
    return {                                  # card_action
        "prompt_id": req.card_id or req.prompt_id,
        "action": _action_kind_to_verb(req.action_id),  # confirm/edit/cancel/accept/revise
        "patch": req.action_payload,
    }
```

### 5.3 注入依赖（services）的难题与解法

**问题**：service 对象（`diet_service`、`plan_service` 等）当前塞进 state 传给节点，
但 checkpointer 会**序列化整个 state**——service 含 DB session，不可序列化。

**解法**：把不可序列化依赖从 checkpoint state 剥离，改用 LangGraph 的
**`config.configurable` 运行时注入**（不被 checkpoint 持久化）：

```python
config = {"configurable": {
    "thread_id": session_id,
    "diet_service": diet_service,   # 运行时依赖，不进 checkpoint
    "plan_service": plan_service,
    "memory_service": memory_service,
}}
```

节点签名从 `(state)` 改成 `(state, config)`，从 config 取 service：

```python
async def save_record(state: ChatState, config: RunnableConfig) -> dict:
    diet_service = config["configurable"]["diet_service"]
    ...
```

> 这是本次改造**最大的结构性改动**：所有用到 service 的节点签名要改，ChatState 里的
> `*_service` 字段移除。好处：state 变得可序列化、干净，满足 checkpointer 要求。

---

## 六、节点逐个改造细则

### 6.1 diet 子图

在 `infer_meal_type` 之后、`save_record` 之前插入（或改造 `save_or_end`）一个决策节点：

```python
async def confirm_or_clarify(state, config) -> Command:
    mode = state.get("interaction_mode") or "confirmation"
    pr = state["diet_parse_result"]

    # 餐次缺失 → 选项 interrupt（替换原 wrap_response 的餐次澄清 #1）
    if pr.meal_type is None and mode != "efficiency":
        answer = interrupt(HumanPrompt(
            kind="choice", prompt_id="diet_meal_type", domain="diet",
            question="请问是哪一餐？",
            options=[{"value": "breakfast", "label": "早餐"}, ...],
            allow_free_text=True,
        ).model_dump())
        meal = answer.get("value") or _map_free_text(answer.get("free_text"))
        pr = pr.model_copy(update={"meal_type": meal})

    if mode == "efficiency":
        return Command(goto="save_record", update={"diet_parse_result": pr})

    # 确认/学习模式 → 卡片 interrupt（替换原 confirm_create_diet_record 快速路径 #2）
    decision = interrupt(HumanPrompt(
        kind="card", prompt_id="diet_confirm", domain="diet",
        card=_parse_result_to_card(pr, ...).model_dump(),
    ).model_dump())
    if decision["action"] == "edit":
        pr = _apply_patch(pr, decision.get("patch"))
    if decision["action"] == "cancel":
        return Command(goto="__end__")
    return Command(goto="save_record", update={"diet_parse_result": pr})
```

要点：
- `interrupt()` 第一次执行抛出暂停；恢复后**整个节点从头重跑**，但这次 `interrupt()` 直接返回答案。
  因此节点内 `interrupt()` **之前**的代码必须**幂等**（不要在 interrupt 前落库 / 发副作用）。
- 一个节点里多个 interrupt 串行时，LangGraph 按出现顺序匹配各自的 resume 值，需保证顺序稳定。

### 6.2 body 子图

`parse_body_text` 之后插入卡片 interrupt（#3），恢复值 `confirm` → 调 `body_service` 落库；
`cancel` → 结束并给取消文案。`body_service` 同样从 state 移到 config。

### 6.3 plan 子图（改造量最大）

`conversation.py` 现在是**一个大函数里 if/else 返回 choice_prompts/卡片**，没有真正的多轮暂停。
改造为 plan 子图内多个 interrupt 点：

1. 意图澄清（#4）：`interrupt(choice: plan_intent)`。
2. 缺目标/周期（#5）：可能**连续多个** `interrupt(choice)`，每问一项。
3. 草案确认（#6/#7）：`interrupt(card: plan_draft)`，草案存 state（不再塞 transcript 文本）。
   - resume `accept` → 节点内调 `plan_service.create_plan_from_draft`（service 来自 config）。
   - resume `revise` → 回到草案生成节点，带用户修改诉求再生成（循环边）。
   - resume `edit` + `patch` → 直接改草案字段后再确认。

`run_plan_conversation` 退化为"纯计算"辅助（生成草案、安全校验），**暂停决策搬进节点**。
`_latest_plan_draft_from_transcript`、`_message_from_action` 等重建逻辑可删除。

### 6.4 删除 / 退役的旧机制

- `PendingActionStore` / `InMemoryPendingActionStore` 及 state 字段 `pending_action`。
- `wrap_response` 里 diet 餐次澄清那段（#1）。
- `ai.py` 里 plan / diet 的 card_action 快速路径。
- `choice_prompts` state 字段（改由 interrupt 承载；SSE 的 CHOICE 事件保留，由 §4.1 产生）。

---

## 七、前端交互改造

> 前端工程尚未建立（当前仓库只有 backend + docs）。以下为**契约设计**，落地时按此实现。

### 7.1 会话状态机

```
IDLE ──发送 text──▶ STREAMING
STREAMING ──收到 DONE──▶ IDLE
STREAMING ──收到 PAUSED(prompt_id, kind)──▶ WAITING_INPUT(prompt_id)
WAITING_INPUT ──选 chip / 提交卡片──▶ RESUMING ──▶ STREAMING
WAITING_INPUT ──改发普通消息──▶（带 cancel 恢复后）STREAMING
```

关键：`WAITING_INPUT` 时前端记住 `prompt_id`。用户作答后发的请求**必须带 prompt_id**，
后端据此走"恢复"通道。

### 7.2 渲染

- `CHOICE` 事件 → 选项 chips（横向按钮组）+ 可选自由输入框（`allow_free_text`）。
- `CARD` 事件（`kind=card`）→ 富卡片（diet_parse / body_parse / plan_draft），按钮来自 `card.actions`。
- `PAUSED` → 锁定/提示输入框（如"请选择上面的选项"），或允许忽略直接打字（触发 cancel 恢复）。

### 7.3 用户作答的请求体

| 用户动作 | 请求 |
|---------|------|
| 点选项 chip | `{type:"choice_response", session_id, prompt_id, selected_value}` |
| 选项里自由输入 | `{type:"choice_response", session_id, prompt_id, free_text}` |
| 点卡片主按钮（确认/接受） | `{type:"card_action", session_id, card_id:prompt_id, action_id:"confirm"}` |
| 卡片编辑后提交 | `{type:"card_action", ..., action_id:"edit", action_payload:{patch}}` |
| 卡片取消 | `{type:"card_action", ..., action_id:"cancel"}` |

> 前端**不再回传** foods/draft 全量数据——服务端 checkpoint 是真相源，只传"决定 + 可选 patch"。

### 7.4 边界 UX

- 用户在 `WAITING_INPUT` 时直接打新消息：前端提示"你还没回答上一个问题，是否放弃？"，
  确认后发普通 text（后端先 cancel 旧中断再起新一轮，§5.1 边界分支）。
- 刷新页面：reload 时调 `GET /chat/sessions/{id}/state`（新增轻量端点，读 `aget_state`），
  若处于中断态，重新渲染挂起的 CHOICE/CARD，恢复 `WAITING_INPUT`。

---

## 八、实施任务拆解（建议顺序）

| 阶段 | 任务 | 验收 |
|------|------|------|
| T1 | 加依赖 `langgraph-checkpoint-postgres`、`psycopg[binary,pool]`；写 `checkpointer.py`；本地验证 `setup()` 建表、`prepare_threshold=0` 连得上 Supabase | 单测：建 saver、写读一个 checkpoint |
| T2 | service 依赖从 state 迁到 `config.configurable`；用 service 的节点签名改 `(state, config)`；ChatState 移除 `*_service` 字段 | 现有 e2e 测试在"无 checkpointer"下仍通过 |
| T3 | `interrupts.py` 定义 `HumanPrompt` + resume 协议；graph `compile(checkpointer=...)`；`dependencies.get_chat_agent` 改异步注入 | graph 能编译、能 invoke |
| T4 | diet 子图接 interrupt（餐次 + 确认）；删 wrap_response 餐次段 + diet 快速路径 | 单测：跑到 interrupt 暂停 → `Command(resume)` 恢复保存 |
| T5 | body 子图接 interrupt | 同上 |
| T6 | plan 子图重构为多轮 interrupt；退役 transcript 草案重建 + plan 快速路径 | 单测：意图澄清→缺项追问→草案确认全链路 |
| T7 | translator/SSE：`aget_state` 检测中断 → 发 CHOICE/CARD + 新增 PAUSED 事件 | 流式 e2e：中断处收到 PAUSED |
| T8 | `ai.py`：新输入 vs 恢复判定、`build_resume_payload`、边界 cancel；删 PendingActionStore | 集成测试：两次请求完成一次暂停-恢复 |
| T9 | 新增 `GET /chat/sessions/{id}/state` 供前端刷新恢复 | 返回挂起的 prompt |
| T10 | 前端（工程建立后）：状态机 + 渲染 + 作答请求体 + 刷新恢复 | 手测三类暂停点 |

### 风险与回滚

- **最大风险**：service 出 state（T2）牵动所有节点签名，量大但机械。建议单独 PR、先全绿再继续。
- **Supabase pgbouncer 兼容**（T1）：若 `prepare_threshold=0` 仍报错，退路是 checkpointer 连
  Supabase 的 **session-mode 端口（5432 直连）** 而非 transaction-mode（6543）。
- **回滚**：T3 的 `compile(checkpointer=None)` 可关闭 checkpointer 退回旧行为；interrupt 节点
  在无 checkpointer 时会报错，故 T4–T8 与 T3 绑定上线，不可单独半套。

---

## 九、关键概念备忘（学习用）

- **Checkpointer**：LangGraph 的"存档点"。每个 super-step 后把 state 快照存库，按 `thread_id`
  归档。没有它，`interrupt()` 无处保存现场，无法恢复——这就是"没 checkpointer 就没法暂停/恢复"。
- **`interrupt(value)`**：节点内调用即暂停整条 graph，把 `value` 抛给调用方；下次用
  `Command(resume=x)` 进来时，**该节点从头重跑**，但这次 `interrupt()` 直接返回 `x`。
  ⇒ interrupt 之前的代码必须幂等、无副作用。
- **`Command(resume=...)`**：恢复输入。不是新 state，而是"喂给上次那个 interrupt 的答案"。
- **`aget_state(config).next`**：非空 ⇒ 有节点待执行 ⇒ 处于中断态。这是后端判断"该恢复还是
  起新一轮"的依据。
