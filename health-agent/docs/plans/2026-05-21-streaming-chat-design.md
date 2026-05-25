# AI 对话流式响应 + 富交互技术方案

**日期**: 2026-05-21
**作者**: Claude
**状态**: Design Review
**关联问题**: 当前 `/api/v1/ai/chat` 同步阻塞 15s 后被前端掐断，AI 对话本身耗时 5-30s 属正常，需要改造为流式 + 富交互架构

---

## 1. 背景与问题分析

### 现状

```
前端 → POST /api/v1/ai/chat → 后端跑完整 LangGraph (5-30s) → 返回完整 JSON → 前端渲染
                              ↑ 客户端 15s 超时直接报"服务不可用"
```

### 三个根本问题

1. **超时问题**: HTTP 请求生命周期内必须等到完整响应。LangGraph 多个节点串联（识别意图 → 检索记忆 → 检索知识 → 调 LLM → 写记忆），单次请求轻松 10-20s
2. **体验问题**: 用户看到的是"转圈圈 → 完整答案"，没有"正在思考"的反馈，感知慢
3. **交互问题**: 当前协议只支持"一次性返回 text + cards"，无法支持"AI 中途问用户餐次是早餐还是午餐 → 用户选了之后继续生成"这种澄清式对话

### 目标

- 解决超时（**智能 idle timeout**：只要服务端在持续吐数据就不超时；连续 N 秒没事件才判定挂了）
- 提供"流式打字机"体感，提升感知速度
- 支持卡片、选项、表单、自由输入混合的多轮交互
- 与业界主流 AI 产品（ChatGPT、Claude、豆包、通义、Kimi）对齐
- **所有调 LLM 的接口**都改为流式（不只是 chat，还有 suggestions/plans）
- **首页多接口并行加载**，先返回的先展示，不互相等

---

## 2. 业界主流方案对比

| 产品 | 传输协议 | 流式粒度 | 富交互形式 | 关键观察 |
|------|---------|---------|-----------|---------|
| **ChatGPT** | SSE | token | 工具调用折叠块 + 引用卡片 + 建议追问 | 工具调用过程实时显示状态 |
| **Claude.ai** | SSE | token | Artifact 侧栏 + 思维链折叠 | 长内容自动外置到 Artifact |
| **豆包（字节）** | SSE | token | 卡片 + 快捷回复 chips + 搜索引用 | 答案下方追加"还想问的问题" |
| **通义千问** | SSE | token | 数据卡片 + 表单 + 步骤进度 | 多轮槽位填充对话 |
| **Kimi** | SSE | token | 搜索引用卡片 + Markdown 渲染 | 边搜边答，引用编号实时插入 |
| **Gemini** | SSE | token | 多模态卡片 + 应用集成 | 与 Workspace 表单深度集成 |

### 关键共性

1. **全部用 SSE**（Server-Sent Events），没人用 WebSocket
2. **token 级流式** 是基础体验，必须有
3. **状态指示**（"正在搜索..."、"正在分析..."）通过事件流实时上报
4. **卡片插入消息时间线** 是默认形态，不是弹窗
5. **多轮交互 = 让用户的下一句消息接住上一个 AI 问题**，不是表单提交

### 为什么不是 WebSocket

| 维度 | SSE | WebSocket |
|------|-----|-----------|
| 协议 | 标准 HTTP | 升级握手 |
| 方向 | 单向（够用） | 双向（不需要） |
| 反向代理 | 透明 | 需配置 |
| HTTP/2 | 多路复用 | 不复用 |
| 自动重连 | 浏览器内置 | 需手写 |
| 鉴权 | Header 直传 | 子协议复杂 |

**结论：选 SSE**。聊天场景客户端 → 服务端就是 HTTP POST 起一次会话，服务端 → 客户端用 SSE 推送，单向语义就够。

---

## 3. 总体架构

```
┌─────────────────┐         POST /api/v1/ai/chat/stream
│   Mobile App    │  ──────────────────────────────────►  ┌──────────────────┐
│  (RN + SSE)     │                                       │   FastAPI        │
│                 │  ◄── event: meta\ndata: {...}\n\n     │   StreamingResp  │
│  EventSource    │  ◄── event: status\ndata: {...}       │                  │
│                 │  ◄── event: text_delta\ndata: {...}   │   ┌──────────┐   │
│  - 累积 text    │  ◄── event: tool_call\ndata: {...}    │   │LangGraph │   │
│  - 累积 cards   │  ◄── event: card\ndata: {...}         │   │astream_  │   │
│  - 渲染 status  │  ◄── event: choice\ndata: {...}       │   │events v2 │   │
│  - 渲染 choices │  ◄── event: done\ndata: {...}         │   └──────────┘   │
└─────────────────┘  ◄── event: error\ndata: {...}        └──────────────────┘
```

### 三层职责

| 层 | 职责 |
|---|------|
| **LangGraph 层** | 节点编排，业务逻辑。通过 `astream_events()` 暴露 token 流和节点状态 |
| **流式转换层** | 把 LangGraph 事件翻译成业务事件协议；处理心跳、超时、取消 |
| **前端消费层** | SSE 客户端 + 消息累积器 + 渲染器（text / card / chips） |

---

## 4. 事件协议设计（核心）

### 4.1 协议格式

标准 SSE：每条事件由 `event:`、`data:` 组成，`\n\n` 分隔。

```
event: text_delta
data: {"content": "今天"}

event: text_delta
data: {"content": "中午"}

event: card
data: {"card": {"id": "c1", "type": "diet_parse", ...}}

event: done
data: {"message_id": "m_xxx"}
```

### 4.2 事件类型完整清单

| event | 时机 | data 字段 | 前端处理 |
|-------|------|----------|---------|
| `meta` | 流开始第一条 | `{message_id, session_id, started_at}` | 创建占位消息 |
| `status` | 节点切换时 | `{node, label, phase: "start"\|"end"}` | 顶部 chip 显示"正在分析饮食..." |
| `tool_call` | 工具调用开始 | `{tool, args_summary}` | 显示"🔍 查找食物营养中..." |
| `tool_result` | 工具调用结束 | `{tool, result_summary}` | 替换上面的 chip 为完成态 |
| `text_delta` | LLM token 流 | `{content}` | 追加到当前消息文本 |
| `card` | 节点产出卡片 | `{card: ChatCard}` | 在消息时间线中插入卡片 |
| `choice` | 需要用户选择 | `{prompt_id, question, options, allow_free_text}` | 渲染选项 chips |
| `error` | 异常 | `{code, message, retriable}` | 标红提示，不自动重试 |
| `done` | 流结束 | `{message_id, full_text, cards, suggestions}` | 完成消息存到 history，关闭连接 |
| `heartbeat` | 每 15s | `{}` | 忽略，保活用 |

### 4.3 卡片数据结构升级

当前：

```ts
ChatCard { type, payload, actions }
```

新：

```ts
interface ChatCard {
  id: string;                    // 卡片唯一 ID，跨多轮引用
  type: 'diet_parse' | 'choice_prompt' | 'form' | 'plan_draft' | 'progress';
  status: 'pending' | 'submitted' | 'cancelled' | 'expired';
  payload: Record<string, unknown>;
  actions: ChatCardAction[];
  expires_at?: string;           // 过期时间，过期变灰
}

interface ChatCardAction {
  id: string;                    // action_id，回调时带上
  kind: 'submit' | 'choice' | 'navigate' | 'free_text';
  label: string;
  value?: unknown;               // 如选项的实际值
  prefill?: Record<string, unknown>;  // 跳转表单时预填
  confirmation?: string;         // "确认删除？" 二次确认
  variant?: 'primary' | 'secondary' | 'danger';
}
```

### 4.4 用户回应协议

用户除了发自由文本，还可以"接住"AI 的卡片/选项。前端发起新请求时支持：

```
POST /api/v1/ai/chat/stream
{
  "session_id": "...",
  "type": "text" | "card_action" | "choice_response",

  // type=text 时
  "message": "今天吃了鸡胸肉",

  // type=card_action 时（点了卡片按钮）
  "card_id": "c1",
  "action_id": "a_confirm",
  "action_payload": {...},

  // type=choice_response 时（选了一个 chip）
  "prompt_id": "p1",
  "selected_value": "lunch",       // 选项值
  "free_text": null                // 或自由文本
}
```

后端把这些都转成统一的 ChatState 输入，让 LangGraph 据此继续流转。

---

## 5. 后端实现方案

### 5.1 新端点：`POST /api/v1/ai/chat/stream`

```python
# app/api/v1/ai_stream.py

from fastapi.responses import StreamingResponse

@router.post("/chat/stream")
async def chat_stream(
    payload: ChatStreamRequest,
    user: CurrentUserDep,
    chat_agent: ChatAgentDep,
    chat_service: ChatServiceDep,
    diet_service: DietServiceDep,
    memory_service: MemoryServiceDep,
    rag_service: RagServiceDep,
):
    return StreamingResponse(
        _stream_chat(payload, user, chat_agent, ...),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx 不要缓冲
            "Connection": "keep-alive",
        },
    )
```

### 5.2 LangGraph → SSE 翻译层

LangGraph 0.2+ 的 `astream_events(version="v2")` 已经把所有节点事件、LLM token 都流化了，直接用：

```python
async def _stream_chat(payload, user, agent, ...) -> AsyncIterator[bytes]:
    state = build_initial_state(payload, user, ...)
    message_id = uuid.uuid4().hex

    yield _sse("meta", {
        "message_id": message_id,
        "session_id": str(state["session_id"]),
        "started_at": datetime.now(UTC).isoformat(),
    })

    # 心跳任务
    heartbeat_task = asyncio.create_task(_heartbeat_loop())

    try:
        async for event in agent.astream_events(state, version="v2"):
            kind = event["event"]
            name = event.get("name", "")

            # 节点开始/结束 → status 事件
            if kind == "on_chain_start" and name in NODE_LABELS:
                yield _sse("status", {
                    "node": name,
                    "label": NODE_LABELS[name],   # "正在识别意图..."
                    "phase": "start",
                })

            # LLM token 流 → text_delta
            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield _sse("text_delta", {"content": chunk.content})

            # 工具调用
            elif kind == "on_tool_start":
                yield _sse("tool_call", {
                    "tool": name,
                    "args_summary": _summarize(event["data"]["input"]),
                })
            elif kind == "on_tool_end":
                yield _sse("tool_result", {
                    "tool": name,
                    "result_summary": _summarize(event["data"]["output"]),
                })

            # 节点结束时检查产出（卡片/选项）
            elif kind == "on_chain_end" and name == "wrap_response":
                output = event["data"]["output"]
                for card in output.get("response_cards", []):
                    yield _sse("card", {"card": card})
                for choice in output.get("choice_prompts", []):
                    yield _sse("choice", choice)

        # 全部完成
        await _persist_message(chat_service, ...)
        yield _sse("done", {"message_id": message_id, ...})

    except asyncio.CancelledError:
        # 客户端主动断开（关闭 App / 切页面）
        logger.info("chat stream cancelled by client")
        raise
    except Exception as exc:
        logger.exception("chat stream failed")
        yield _sse("error", {
            "code": "STREAM_ERROR",
            "message": "AI 对话出错，请稍后重试",
            "retriable": True,
        })
    finally:
        heartbeat_task.cancel()


def _sse(event: str, data: dict) -> bytes:
    """格式化 SSE 帧。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode()
```

### 5.3 节点改造要点

为了让 SSE 流出有意义的事件：

1. **节点必须用 `temperature` + 流式模型**：`get_chat_model(streaming=True)`，否则没有 token 流
2. **节点产出卡片时填 `response_cards`**（已有）
3. **新增 `choice_prompts` state 字段**用于多轮澄清
4. **后台任务（trigger_memory_extract）保持**，但通过 `copy_context()` 隔离 request_id

### 5.4 心跳

```python
async def _heartbeat_loop(queue: asyncio.Queue):
    while True:
        await asyncio.sleep(15)
        await queue.put(_sse("heartbeat", {}))
```

或者更简单：在主循环里 `select` 等下一个事件，如果 15s 没事件就 yield heartbeat。

### 5.5 取消与超时

- **客户端断开** → FastAPI 触发 `asyncio.CancelledError` → 我们的 `finally` 清理资源
- **服务端硬超时**：用 `asyncio.wait_for(astream_events, timeout=120)` 包一层防失控
- **重要：不要在异常里继续调 LLM**，避免烧 token

---

## 6. 前端实现方案

### 6.1 SSE 客户端（React Native）

RN 原生 fetch 的 ReadableStream 在 iOS 上不稳，用 `react-native-sse`：

```bash
yarn add react-native-sse
```

```ts
// src/features/ai/services/streamingChat.ts
import EventSource from 'react-native-sse';

interface StreamHandlers {
  onMeta: (data: MetaEvent) => void;
  onStatus: (data: StatusEvent) => void;
  onTextDelta: (data: { content: string }) => void;
  onCard: (data: { card: ChatCard }) => void;
  onChoice: (data: ChoiceEvent) => void;
  onToolCall: (data: ToolCallEvent) => void;
  onDone: (data: DoneEvent) => void;
  onError: (data: ErrorEvent) => void;
}

export function startChatStream(
  payload: ChatStreamRequest,
  token: string,
  handlers: StreamHandlers,
): { close: () => void } {
  const source = new EventSource(`${API_BASE}/api/v1/ai/chat/stream`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    pollingInterval: 0,  // SSE 一次性，不轮询
  });

  source.addEventListener('meta', e => handlers.onMeta(JSON.parse(e.data)));
  source.addEventListener('status', e => handlers.onStatus(JSON.parse(e.data)));
  source.addEventListener('text_delta', e => handlers.onTextDelta(JSON.parse(e.data)));
  source.addEventListener('card', e => handlers.onCard(JSON.parse(e.data)));
  source.addEventListener('choice', e => handlers.onChoice(JSON.parse(e.data)));
  source.addEventListener('tool_call', e => handlers.onToolCall(JSON.parse(e.data)));
  source.addEventListener('tool_result', e => handlers.onToolCall(JSON.parse(e.data)));
  source.addEventListener('done', e => {
    handlers.onDone(JSON.parse(e.data));
    source.close();
  });
  source.addEventListener('error', e => {
    handlers.onError(e as any);
    source.close();
  });

  return { close: () => source.close() };
}
```

### 6.2 消息组装 Hook

```ts
// src/features/ai/hooks/useStreamingChat.ts
export function useStreamingChat() {
  const { addMessage, updateMessage } = useAIStore();
  const [streaming, setStreaming] = useState<StreamingMessage | null>(null);
  const sourceRef = useRef<{ close: () => void } | null>(null);

  const send = useCallback((payload: ChatStreamRequest) => {
    // 立刻把用户消息加入 history
    addMessage({ role: 'user', text: payload.message, ... });

    // 创建占位 AI 消息
    const placeholder: StreamingMessage = {
      id: 'pending',
      role: 'assistant',
      text: '',
      cards: [],
      choices: [],
      status: null,
      tools: [],
    };
    setStreaming(placeholder);

    sourceRef.current = startChatStream(payload, token, {
      onMeta: m => setStreaming(s => ({ ...s!, id: m.message_id })),

      onStatus: s => setStreaming(prev => ({
        ...prev!,
        status: s.phase === 'start' ? s.label : null,
      })),

      onTextDelta: d => setStreaming(prev => ({
        ...prev!,
        text: prev!.text + d.content,
      })),

      onCard: c => setStreaming(prev => ({
        ...prev!,
        cards: [...prev!.cards, c.card],
      })),

      onChoice: ch => setStreaming(prev => ({
        ...prev!,
        choices: [...prev!.choices, ch],
      })),

      onToolCall: t => setStreaming(prev => ({
        ...prev!,
        tools: [...prev!.tools.filter(x => x.tool !== t.tool), t],
      })),

      onDone: d => {
        addMessage({ ...streaming!, id: d.message_id, status: null });
        setStreaming(null);
      },

      onError: e => {
        addMessage({
          role: 'assistant',
          text: '⚠️ AI 出错了，可以再试一次',
          error: true,
        });
        setStreaming(null);
      },
    });
  }, [addMessage]);

  const cancel = useCallback(() => {
    sourceRef.current?.close();
    setStreaming(null);
  }, []);

  return { send, cancel, streaming };
}
```

### 6.3 渲染层

```tsx
// 消息列表渲染
{messages.map(msg => <Message key={msg.id} {...msg} />)}

{/* 当前正在流式的消息 */}
{streaming && (
  <View>
    {/* 状态 chip */}
    {streaming.status && <StatusChip text={streaming.status} />}

    {/* 工具调用 */}
    {streaming.tools.map(t => <ToolChip key={t.tool} {...t} />)}

    {/* 流式文本（带光标动画） */}
    <Text>{streaming.text}<BlinkingCursor /></Text>

    {/* 卡片 */}
    {streaming.cards.map(c => <ChatCardView key={c.id} card={c} />)}

    {/* 选项 chips */}
    {streaming.choices.map(ch => (
      <ChoicePrompt
        key={ch.prompt_id}
        prompt={ch}
        onSelect={(value, freeText) => send({
          type: 'choice_response',
          prompt_id: ch.prompt_id,
          selected_value: value,
          free_text: freeText,
          session_id: currentSession,
        })}
      />
    ))}
  </View>
)}
```

---

## 7. 富交互 UX 模式（重点）

### 7.1 四种澄清模式

| 模式 | 适用 | 协议 | 示例 |
|------|------|------|------|
| **A. Choice chips** | 2-4 个明确选项 | `event: choice` | "早餐还是午餐？[早餐][午餐][加餐]" |
| **B. Free text + chips** | 选项 + 自由输入 | `event: choice` with `allow_free_text: true` | "什么时候吃的？[12:00][13:00][自己输入]" |
| **C. 卡片表单** | 多字段录入 | `event: card` type=form | 直接弹饮食编辑卡片 |
| **D. 自然多轮** | 复杂目标分解 | 纯 `text_delta` + 续问 | "了解，再告诉我你的体重目标？" |

**推荐默认策略**：

- AI 主动澄清 → 用 A 或 B（chips 形式）
- 用户表达"我想编辑这个" → 用 C（卡片）
- 不确定 → 用 D（让 LLM 自然续问）

### 7.2 卡片插入消息时间线（不是弹窗）

```
[AI] 我识别到 2 项食物，餐次暂定为 lunch:

  ┌──────────────────────┐
  │ 🍱 lunch              │
  │ • 鸡胸肉 200g  300kcal│
  │ • 米饭   150g  175kcal│
  │ ─────────────────     │
  │ [确认保存] [编辑]      │
  └──────────────────────┘

  请确认后再保存。
```

卡片是消息的一部分，跟着上下滚动；不要做 modal/sheet（除非编辑时弹全屏）。

### 7.3 选项 chips 的两种交互

**点击 chip = 发一条用户消息**（保持 history 自然）：

```
[AI] 想记录哪一餐？  [早餐] [午餐] [晚餐]
                        ↓ 点击
[USER] 午餐   ← 自动作为用户消息
[AI] 好的，告诉我午餐吃了什么？
```

后端收到时是 `type=choice_response`，但渲染时显示成普通用户消息。这样用户后续看历史时阅读连贯。

### 7.4 卡片状态机

```
pending  ──[用户点确认]──→  submitted (变灰，显示 ✓)
   │
   ├──[用户点取消]──→  cancelled (变灰)
   │
   ├──[用户点编辑]──→  expires + 触发跳转编辑页
   │
   └──[超过 expires_at]──→  expired (变灰，"已过期")
```

新对话或 30 分钟后老卡片变灰，避免用户翻到 3 天前的卡片误点。

---

## 8. 多轮状态联动

### 关键挑战

AI 问"哪一餐？"，用户答"午餐"——后端怎么知道这是在回答上一个问题，而不是新话题？

### 方案：会话级 pending_action

```python
class ChatState(TypedDict):
    session_id: UUID
    user_message: str
    chat_history: list[Message]
    pending_action: PendingAction | None   # 新增
    ...

class PendingAction(BaseModel):
    prompt_id: str
    expected: Literal['meal_type', 'date', 'plan_goal', ...]
    options: list[str] | None
    expires_at: datetime
    raw_choice_value: str | None  # 用户点 chip 的原始值
    raw_free_text: str | None
```

新一轮请求进来：

```python
async def identify_intent(state: ChatState):
    pending = state.get("pending_action")
    if pending and not pending.is_expired():
        # 走"答澄清问题"分支，不重新分类意图
        return {"intent": "continue_pending", "pending_value": ...}
    # 否则走原有意图识别
```

### Pending 存哪里

不要存数据库（太重），存 session 级 Redis 或 in-memory dict（key=session_id）：

```python
# app/services/chat_session_state.py
_pending_actions: dict[UUID, PendingAction] = {}  # 简单内存版
# 生产改用 Redis 带 TTL
```

---

## 9. 错误处理与边界

### 9.1 客户端断开

```python
except asyncio.CancelledError:
    # FastAPI/uvicorn 自动触发，我们只需清理
    logger.info("client disconnected mid-stream")
    raise
```

**重要**：取消时立刻停止 LLM 调用，避免烧 token。LangGraph 0.2+ 会自动传播 cancellation。

### 9.2 LLM API 失败

按节点处理：

- `identify_intent` 失败 → fallback 关键词规则（已有）
- `parse_text` 失败 → 返回 error 卡片让用户重试
- `call_llm` 失败 → emit `event: error` 关闭流

### 9.3 心跳丢失

客户端 30s 没收到任何事件 → 主动 close + 提示"连接异常，请重试"。

### 9.4 重复发送防御

用户连点两次 → 前端 `streaming` 状态非空时禁用输入框。

### 9.5 超时硬上限

```python
async with asyncio.timeout(180):  # 3 分钟硬顶
    async for event in agent.astream_events(...):
        ...
```

---

## 10. 实现优先级

| 优先级 | 内容 | 价值 |
|-------|------|------|
| P0 | SSE 端点骨架 + LangGraph astream_events 接入 + text_delta | 解决超时问题 |
| P0 | 前端 SSE 消费 + 流式文本渲染 | 看得到"打字" |
| P1 | status / tool_call 事件 + 前端 chip 渲染 | 提升感知速度 |
| P1 | 卡片事件 + 现有卡片复用 | 不破坏已有功能 |
| P2 | choice 事件 + chips 交互 | 多轮澄清 |
| P2 | pending_action 状态机 | 多轮状态联动 |
| P3 | 心跳 + 取消 + 超时硬顶 | 生产级健壮性 |

**注**：本项目为新项目，无需灰度切换。直接改造现有端点为流式，删除旧实现即可。

---

## 11. 验收标准

- [ ] AI 对话不再因 15s 超时报错
- [ ] 用户能看到 token 流式输出（每秒 ≥ 5 token 视觉感知）
- [ ] 节点切换时显示状态 chip（"正在分析饮食..."）
- [ ] 饮食卡片在流结束前能正常出现
- [ ] 用户点选项 chip 等价于发一条文本消息，AI 能续接
- [ ] 用户中途关闭页面，后端 LLM 调用立即停止（看日志）
- [ ] 弱网下连接断了，前端有清晰错误提示且可重试

---

## 13. 风险与未决问题

1. **SSE 在 React Native iOS 后台**：App 切到后台 SSE 连接会断，恢复时怎么处理？倾向"丢弃，让用户重发"
2. **token 消耗失控**：流式中用户多次取消重发可能浪费 token。需加用户级速率限制
3. **海外 LLM 延迟**：DashScope 国内可控，但 token 间隔可能不均匀。前端用 buffer + 平滑动画
4. **断线重连**：SSE 标准支持 `Last-Event-ID`，但 LLM 流不可幂等重放。结论：**不重连，让用户重发**
5. **服务端推送多个并发流**：同一 user 同时开多个对话窗 → 需要 session_id 级互斥
6. **日志噪声**：流式后每个 token 都打日志会刷屏。建议 token 级日志走 DEBUG，节点级走 INFO

---

## 14. 参考实现

- LangGraph 流式：https://langchain-ai.github.io/langgraph/how-tos/stream-tokens/
- FastAPI SSE：https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- react-native-sse：https://github.com/binaryminds/react-native-sse
- Anthropic Streaming（参考事件类型设计）：https://docs.anthropic.com/claude/reference/messages-streaming

---

## 15. 方案确认补充（基于评审反馈）

本节是 2026-05-21 评审反馈后对前面章节的修订与延伸。

### 15.1 超时策略修订（修订 §1 目标）

**之前的描述"永久不超时"是错的**。正确策略：

| 超时类型 | 触发条件 | 行为 |
|---------|---------|------|
| **Idle timeout** | 连续 30s 没收到任何 SSE 事件（含 heartbeat） | 客户端关闭连接，弹"后端无响应"提示 |
| **Total timeout** | 单次流总时长超过 180s | 服务端主动关闭，防止 LLM 死循环烧 token |
| **Heartbeat** | 服务端每 15s 发 `event: heartbeat` | 重置客户端 idle 计时器 |

**前端实现要点**：

```ts
let idleTimer: NodeJS.Timeout;
const IDLE_TIMEOUT = 30_000;

const resetIdleTimer = () => {
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => {
    source.close();
    onError({ code: 'IDLE_TIMEOUT', message: '后端无响应，请重试' });
  }, IDLE_TIMEOUT);
};

// 任何事件到达都 reset（含 heartbeat）
['meta', 'status', 'text_delta', 'card', 'choice', 'tool_call',
 'tool_result', 'heartbeat', 'done'].forEach(evt => {
  source.addEventListener(evt, () => resetIdleTimer());
});
```

**后端实现要点**：

```python
async with asyncio.timeout(180):  # total timeout 兜底
    async for event in agent.astream_events(state, version="v2"):
        ...
```

### 15.2 SSE 实现选型（细化 §6.1）

**关键问题**：标准 `EventSource` 只支持 GET，但我们的请求需要 POST + body。

三种方案对比：

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| A. POST 起会话拿 token，GET 流 | 标准 EventSource 即可 | 两次往返 + 服务端要存中间态 | ❌ 复杂 |
| B. `react-native-sse` 直接 POST | 一次往返 | 依赖第三方库 | ✅ **推荐** |
| C. fetch + ReadableStream 手动解析 | 零依赖 | iOS 上不稳定 | ❌ 风险 |

**选 B**：`react-native-sse` 库支持 POST + body + 自定义 header，足够稳定。

```ts
const source = new EventSource('/api/v1/ai/chat/stream', {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
  body: JSON.stringify({ message: '今天吃了鸡胸肉', session_id }),
});
```

**鉴权方式**：保持 Bearer header，跟普通 HTTP 一致。SSE 走标准 HTTP 协议，不需要像 WebSocket 那样用子协议绕开。

### 15.3 全 AI 接口改 SSE + 首页多接口并行（新增需求）

**两个独立但相关的需求，分开处理。**

#### A. 哪些接口改 SSE

需要改的（都直接调 LLM）：

| 当前接口 | 改为流式 | 备注 |
|---------|---------|------|
| `POST /api/v1/ai/chat` | SSE | 直接改造，删除旧实现 |
| `GET /api/v1/suggestions/daily` | SSE | 直接改造，删除旧实现 |
| `GET /api/v1/suggestions/meal` | SSE | 直接改造，删除旧实现 |
| `GET /api/v1/suggestions/insights` | SSE | 直接改造，删除旧实现 |
| `POST /api/v1/plans` | SSE | 直接改造，删除旧实现 |

**纯 CRUD 不改**：diet/body/users 等不调 LLM 的接口保持普通 JSON 响应。

**注**：本项目为新项目，无需保留旧端点或灰度切换。直接改造现有端点为流式即可。

#### B. 首页多接口并行 + 渐进展示

这跟 SSE **无关**，是前端 query 组织问题。

**问题**：首页同时请求 4 个接口（饮食日汇总、身体数据 today、AI 建议、计划进度），目前可能用 `Promise.all` 等所有完成才停止 loading，导致 AI 建议慢就拖累全屏转圈。

**正确做法**：每个 query 独立的 loading 态 + 骨架屏，谁先回来谁先显示：

```ts
const dietQuery = useQuery(['home/diet'], fetchDietSummary);
const bodyQuery = useQuery(['home/body'], fetchBodyToday);
const suggestionQuery = useQuery(['home/suggestion'], fetchSuggestion);  // 慢
const planQuery = useQuery(['home/plan'], fetchPlanProgress);

return (
  <>
    {dietQuery.isLoading ? <DietSkeleton /> : <DietCard data={dietQuery.data} />}
    {bodyQuery.isLoading ? <BodySkeleton /> : <BodyCard data={bodyQuery.data} />}
    {suggestionQuery.isLoading ? <SuggestionSkeleton /> : <SuggestionCard ... />}
    {planQuery.isLoading ? <PlanSkeleton /> : <PlanCard ... />}
  </>
);
```

**收益**：饮食/身体可能 200ms 就出来，建议慢慢转圈但不影响其他卡片可见。
**叠加 SSE 后**：建议接口能边流边显示（"正在分析..." → 部分文本 → 完整建议）。

### 15.4 一轮对话多事件如何处理（新增章节，关键设计抉择）

**核心问题**：AI 流出文本 → 弹选项问"哪一餐？" → 用户选"午餐" → AI 继续 → 最终输出卡片。这一整个流程怎么组织？

#### 设计抉择：每次请求是独立 SSE 流，靠 session 状态串联

**不是**用一个长连接 hold 着等用户回答。

| 场景 | 长连接（不选） | 多次连接（选） |
|------|---------------|---------------|
| 用户 5 分钟后才点选项 | 服务端必须 hold 连接，资源浪费 | 优雅 |
| 用户切走再回来 | 连接断了状态丢 | 状态在 session_id 里，回来也能续 |
| 用户主动关 App | 服务端要 cleanup 半状态 | 自然结束 |
| 实现复杂度 | 状态机 + 队列 | 直来直去 |

#### 流转图

```
=== 第 1 次连接 ===
用户发: "今天吃了鸡胸肉"
↓
[流开始] event: meta
         event: status "正在分析饮食..."
         event: text_delta "我识别到鸡胸肉..."
         event: text_delta "请问是哪一餐？"
         event: choice { options: [早餐, 午餐, 晚餐, 加餐] }
         event: done
[流关闭]                               ← 此时连接断开

=== 第 2 次连接 ===
用户点了"午餐"（前端发新请求，body 中带 prompt_id 和 selected_value）
↓
[流开始] event: meta
         event: status "正在生成卡片..."
         event: text_delta "好的，午餐已记录："
         event: card { type: 'diet_parse', ... }
         event: done
[流关闭]
```

#### 状态如何串联：session 级 pending_action

```python
# Redis（生产）/ 内存 dict（开发）
pending_actions: dict[session_id, PendingAction] = {}

class PendingAction(BaseModel):
    prompt_id: str
    expected_kind: Literal['choice', 'free_text']
    options: list[ChoiceOption]
    diet_partial: dict | None  # 已识别但未确定餐次的饮食信息
    expires_at: datetime  # 30 分钟过期
```

**第一次请求**：

1. LLM 决定要问"哪一餐"
2. 后端 emit `event: choice` 到前端
3. 同时 `pending_actions[session_id] = PendingAction(diet_partial={foods: [...]}, ...)`
4. 流关闭

**第二次请求**（body 带 `prompt_id='p1', selected_value='lunch'`）：

1. 后端读 `pending_actions[session_id]`
2. 合并 `diet_partial + meal_type=lunch` → 完整饮食数据
3. 进入"生成卡片"分支（跳过意图识别）
4. emit `text_delta` + `card`
5. 删除 pending_action

#### 前端视角：一段连续对话，由多个 segment 组成

```ts
interface AIMessage {
  id: string;
  segments: Segment[];   // 一轮对话由多段构成，可跨多次 SSE 连接
}

type Segment =
  | { kind: 'text'; content: string }
  | { kind: 'card'; card: ChatCard }
  | { kind: 'choice'; prompt: ChoicePrompt; selected?: string };
```

**用户看到的 UI**（视觉连续，技术上是两次连接）：

```
[AI] 我识别到鸡胸肉 200g。请问是哪一餐？
     [早餐] [✓ 午餐] [晚餐] [加餐]   ← 已选高亮
[AI] 好的，午餐已记录：
     ┌─────────────────────┐
     │ 🍱 lunch             │
     │ • 鸡胸肉 200g 330kcal│
     │ [确认保存] [编辑]      │
     └─────────────────────┘
```

---

## 16. Mock 演示方案（先验交互形态再投入真实开发）

### 16.1 目标

让用户在**不改后端**的前提下，通过纯前端 mock 直观体验"流式 + 富交互"形态，再决定是否投入真实开发。

### 16.2 隔离原则（不动什么）

- 后端 0 改动
- 现有 `/api/v1/ai/chat` 端点不动
- `AIDialogScreen.tsx` 现有逻辑不动
- 现有 chat store / hook / 类型不动

### 16.3 新增文件清单

| 路径 | 作用 |
|------|------|
| `src/features/ai/demo/streamingMock.ts` | Mock 事件序列定义 + setTimeout 调度器，模拟 SSE 流 |
| `src/features/ai/demo/StreamingDemoScreen.tsx` | 独立 demo 页面，完整渲染流式 UI |
| `src/features/ai/demo/components/StatusChip.tsx` | "正在分析..." 状态条 |
| `src/features/ai/demo/components/ToolCallChip.tsx` | "🔍 查找鸡胸肉营养中..." 工具调用条 |
| `src/features/ai/demo/components/ChoicePromptView.tsx` | 选项 chips（含自由输入 fallback） |
| `src/features/ai/demo/components/StreamingText.tsx` | 带光标的流式文本 |
| `AppNavigator` 加路由 `/streaming-demo` | dev 入口 |

整个 demo 自成一块，跑完直接删除即可，零污染。

### 16.4 Mock 事件脚本（演示完整一轮多事件对话）

#### 第 1 段：用户发"今天中午吃了鸡胸肉"

```
t=0ms      event: meta              { message_id: "m1", session_id: "s1" }
t=200ms    event: status            { label: "正在识别意图..." }
t=600ms    event: status            { label: "正在分析饮食..." }
t=900ms    event: tool_call         { tool: "search_food", label: "查找鸡胸肉营养..." }
t=1700ms   event: tool_result       { tool: "search_food", summary: "✓ 已找到" }
t=1900ms   event: text_delta        { content: "我" }
t=1950ms   event: text_delta        { content: "识别" }
... (token by token, 每 50ms 一个)
t=3500ms   event: text_delta        { content: "鸡胸肉 200g。" }
t=3700ms   event: text_delta        { content: "请问是哪一餐？" }
t=4000ms   event: choice            {
                                       prompt_id: "p1",
                                       options: [
                                         { value: "breakfast", label: "早餐" },
                                         { value: "lunch", label: "午餐" },
                                         { value: "dinner", label: "晚餐" },
                                         { value: "snack", label: "加餐" },
                                       ],
                                       allow_free_text: true,
                                     }
t=4100ms   event: done              { message_id: "m1" }
```

→ 流关闭，等用户操作。

#### 第 2 段：用户点了"午餐"

```
t=0ms      event: meta              { message_id: "m2" }
t=300ms    event: status            { label: "正在生成饮食卡片..." }
t=900ms    event: text_delta        { content: "好的," }
... (流式 tokens)
t=2200ms   event: text_delta        { content: "准备好午餐卡片：" }
t=2400ms   event: card              {
                                       card: {
                                         id: "c1",
                                         type: "diet_parse",
                                         payload: {
                                           foods: [{ name: "鸡胸肉", quantity: 200, unit: "g", calories: 330, protein: 62 }],
                                           meal_type: "lunch",
                                         },
                                         actions: [
                                           { id: "save", label: "确认保存", kind: "submit", variant: "primary" },
                                           { id: "edit", label: "修改食物", kind: "navigate" },
                                         ],
                                       },
                                     }
t=2500ms   event: done              { message_id: "m2" }
```

### 16.5 视觉时间线（用户看到的）

```
┌─────────────────────────────────────────┐
│ [USER] 今天中午吃了鸡胸肉                  │
│                                          │
│ [AI]  ⏳ 正在识别意图...                   │  ← status chip
│       ⏳ 正在分析饮食...                   │  ← status 切换
│       🔍 查找鸡胸肉营养...                 │  ← tool chip
│       ✓ 已找到                            │  ← tool 完成
│                                          │
│       我识别到了鸡胸肉 200g。             │  ← 流式打字
│       请问是哪一餐？▌                     │
│                                          │
│       [早餐] [午餐] [晚餐] [加餐] [自己输入] │  ← 选项 chips
│                                          │
│ ─── 用户点了"午餐" ───                    │
│                                          │
│ [USER] 午餐                              │  ← 选项渲染成用户消息
│                                          │
│ [AI]  ⏳ 正在生成饮食卡片...               │
│       好的，已为你准备好午餐卡片：▌         │
│       ┌─────────────────────────┐        │
│       │ 🍱 lunch                 │        │  ← 卡片
│       │ • 鸡胸肉 200g            │        │
│       │   330 kcal · 62g 蛋白    │        │
│       │ ─────────────────────    │        │
│       │ [确认保存] [修改食物]      │        │
│       └─────────────────────────┘        │
└─────────────────────────────────────────┘
```

### 16.6 关键交互演示点

| 演示点 | 验证什么 |
|--------|---------|
| 状态 chip 替换 | 节点切换有清晰反馈 |
| 工具调用进度 | 慢操作有"正在做啥"提示 |
| token 流式 | 打字机感受 |
| 选项点击变成用户消息 | 历史阅读连贯，不是表单提交感 |
| 选项支持自由输入 | "我没列出来想自己说" 兜底 |
| 卡片插入消息流 | 不是弹窗、不打断对话 |
| 流式中可以中途取消 | 加"停止"按钮验证 |
| Idle 超时模拟 | 加"模拟挂起"按钮，30s 没事件后报错 |

### 16.7 入口设计（开发期临时）

候选方案：

- **A. 设置页隐藏入口**：连点 5 次版本号触发
- **B. dev 模式首页浮动按钮** `🧪 Streaming Demo`（**推荐**，最简单）
- **C. 单独 `/dev` 路由**：列出所有 demo

**推荐 B**，跑完直接删除。

### 16.8 Mock 调度器实现思路（不写真实代码，只描述）

```
class MockEventStream {
  events: ScheduledEvent[]    // 预定义事件 + 延迟
  listeners: Map<EventType, Handler[]>
  cancelled: boolean
  idleTimer: Timer

  start() {
    schedule(events).forEach(e => {
      setTimeout(() => {
        if (cancelled) return
        listeners.get(e.type).forEach(h => h(e.data))
        resetIdleTimer()
      }, e.delay)
    })
  }

  cancel() {
    cancelled = true
    clearAllTimeouts()
  }

  resetIdleTimer() {
    clearTimeout(idleTimer)
    idleTimer = setTimeout(() => emit('error', { code: 'IDLE_TIMEOUT' }), 30000)
  }
}
```

API 模拟成跟真实 SSE 一样，将来换成真 EventSource 时上层 hook 不需要改。

### 16.9 完成 Mock 后的下一步

1. 跑起来 demo 页，亲自体验完整流式 + 选项 + 卡片流程
2. 决定是否走这条路
3. 决定 UX 细节（chip 颜色 / 卡片样式 / 文案）
4. 确认之后才动后端 + 真实 SSE 客户端

### 16.10 待用户确认的开放问题

- 入口位置选 A / B / C？
- 演示脚本是否需要补充更多场景？
  - "失败重试"演示
  - "中途取消"演示
  - "用户输入自由文本而不是选 chip"演示
  - "连续多轮卡片确认"演示
- 视觉风格（chip 配色、卡片布局）有偏好吗？

---

## 17. 修订记录

| 日期 | 修订内容 |
|------|---------|
| 2026-05-21 v1 | 初稿（§1-§14） |
| 2026-05-21 v2 | 评审反馈：§1 修正超时目标；新增 §15（超时策略 + SSE 选型 + 全 AI 接口 + 首页并行 + 一轮对话多事件）；新增 §16（Mock 演示方案） |
