# AI 流式响应 + 富交互 实施任务清单

**日期**: 2026-05-22
**作者**: Claude
**状态**: Ready to Execute
**关联设计文档**: `2026-05-21-streaming-chat-design.md`

---

## 0. 文档说明

本文档是 [设计文档](./2026-05-21-streaming-chat-design.md) 的**落地实施清单**。
设计文档回答 What & Why；本文档回答 How & When，按 Task 优先级组织。

### 评审已确认的决策（2026-05-22）

| 项目 | 决策 |
|------|------|
| Mock 入口位置 | **B**：dev 模式首页浮动按钮 `🧪 Streaming Demo` |
| Mock 演示场景 | **全部覆盖**：基础流程 + 失败重试 + 中途取消 + 自由文本输入 + 多轮卡片确认 |
| 视觉风格 | 由实施者把握，遵循现有 design system（chip 配色 / 卡片间距 / 字体） |

### 实施原则

1. **先 Mock，再真实**：用纯前端 Mock 验证交互形态；视觉确认后再投入后端流式改造
2. **隔离不破坏**：Mock 与真实 SSE 实现都新增文件，不动现有 `/ai/chat` 端点和 `AIDialogScreen.tsx`
3. **逐 Task 验收**：每个 Task 完成后跑验收用例 + commit，不积攒大改动
4. **灰度切换**：旧接口保留至 Phase 3 全验证完成

---

## 1. Task 优先级矩阵

| 优先级 | Task | 价值 | 阻塞关系 |
|-------|------|------|---------|
| **P0** | T1 Mock 演示页 | 验证交互形态，避免后端白做 | 阻塞 P1 后续 |
| **P0** | T2 首页多接口并行 | 独立问题，立即解决转圈 | 无 |
| **P1** | T3 SSE 协议骨架 + Schema | 后端流式基建 | 依赖 T1 形态确认 |
| **P1** | T4 `/ai/chat` 改造为流式 | 解决 15s 超时核心问题 | 依赖 T3 |
| **P1** | T5 前端 SSE 客户端 | 替换 Mock 调度器 | 依赖 T4 |
| **P1** | T6 流式渲染组件正式化 | 复用 Mock 组件升级 | 依赖 T5 |
| **P2** | T7 Choice 事件 + 组件 | 多轮澄清交互 | 依赖 T6 |
| **P2** | T8 `pending_action` 状态机 | 跨流状态串联 | 依赖 T7 |
| **P2** | T9 卡片流式插入 | 富交互完整闭环 | 依赖 T6 |
| **P3** | T10 suggestions 三接口流式化 | 首页 AI 卡片"边流边显" | 依赖 T3 |
| **P3** | T11 plans 创建流式化 | 计划生成不再阻塞 | 依赖 T3 |
| **P4** | T12 心跳 + Idle Timeout | 智能超时机制 | 依赖 T4 |
| **P4** | T13 取消传播（防烧 token） | 客户端断开后端立停 | 依赖 T4 |
| **P4** | T14 Total Timeout 兜底 | 防 LLM 死循环 | 依赖 T4 |
| **P5** | T15 监控埋点 | 可观测性 | 依赖 P1 |

**注**：本项目为新项目，无需灰度切换和旧接口保留。直接改造现有端点为流式，删除旧实现即可。

---

## 2. P0 任务详细规格

### T1: Mock 演示页（最高优先级）

**目标**：纯前端模拟 SSE 流式交互，覆盖全部场景，让用户在不改后端的前提下视觉确认形态。

**新增文件**

| 路径 | 作用 | 复杂度 |
|------|------|-------|
| `src/features/ai/demo/streamingMock.ts` | Mock 事件定义 + 调度器 + 5 种场景脚本 | M |
| `src/features/ai/demo/types.ts` | StreamEvent / Segment / Choice 类型 | S |
| `src/features/ai/demo/StreamingDemoScreen.tsx` | demo 主页 + 场景切换器 | M |
| `src/features/ai/demo/components/StatusChip.tsx` | "正在分析..." 状态条 | S |
| `src/features/ai/demo/components/ToolCallChip.tsx` | "🔍 查找鸡胸肉..." 工具条 | S |
| `src/features/ai/demo/components/StreamingText.tsx` | 带闪烁光标的流式文本 | S |
| `src/features/ai/demo/components/ChoicePromptView.tsx` | 选项 chips + 自由输入 fallback | M |
| `src/features/ai/demo/components/StreamingCardView.tsx` | 复用 `ChatCard` 类型的卡片渲染 | S |
| `src/app/navigation/types.ts` | 增加路由 `StreamingDemo` | S |
| `src/features/home/components/DevDemoButton.tsx` | dev 浮动按钮（仅 `__DEV__`） | S |

**修改文件**

| 路径 | 改动 |
|------|------|
| `src/app/navigation/AppNavigator.tsx` | 注册 StreamingDemo 路由 |
| `src/features/home/screens/HomeScreen.tsx` | 集成 `<DevDemoButton />`（条件渲染） |

**关键签名**

```ts
// streamingMock.ts
type StreamEvent =
  | { type: 'meta'; data: { message_id: string; session_id: string } }
  | { type: 'status'; data: { label: string } }
  | { type: 'tool_call'; data: { tool: string; label: string } }
  | { type: 'tool_result'; data: { tool: string; summary: string } }
  | { type: 'text_delta'; data: { content: string } }
  | { type: 'choice'; data: ChoicePrompt }
  | { type: 'card'; data: { card: ChatCard } }
  | { type: 'done'; data: { message_id: string } }
  | { type: 'error'; data: { code: string; message: string } }
  | { type: 'heartbeat'; data: {} };

interface MockStreamHandle {
  start: () => void;
  cancel: () => void;
  on: <T extends StreamEvent['type']>(type: T, handler: (data: ...) => void) => void;
}

function createMockStream(scenario: ScenarioName): MockStreamHandle;

type ScenarioName =
  | 'happy_path'              // 基础流程：text → choice → text → card
  | 'failure_retry'           // 流中途报错，引导重试
  | 'mid_cancel'              // 用户中途点"停止"
  | 'free_text_response'      // choice 选了"自己输入"分支
  | 'multi_card_confirm'      // 连续多张卡片确认（饮食 → 运动 → 睡眠）
  | 'idle_timeout';           // 模拟 30s 无事件触发超时
```

**5 个场景的事件脚本**（详细 timing 表 → 见设计文档 §16.4，扩展场景见下）

| 场景 | 关键事件序列 | 验证点 |
|------|------------|-------|
| `happy_path` | meta → status×2 → tool×2 → text_delta×N → choice → done | 基础流式 + 选项 |
| `failure_retry` | meta → status → text_delta×3 → error → 用户点重试 → 新一轮 done | 错误展示 + 重试 |
| `mid_cancel` | meta → status → text_delta×N → 用户点停止 → cancel | 取消按钮可见可用 |
| `free_text_response` | happy_path 第一段 → 用户点"自己输入" → 输入框 → 发送 → 第二段卡片 | 自由文本 fallback |
| `multi_card_confirm` | 第 1 段：饮食卡片 → 用户确认 → 第 2 段：建议运动卡片 → 用户确认 → 第 3 段：建议睡眠卡片 | 多卡片连贯交互 |
| `idle_timeout` | meta → status → 30s 静默 → 自动触发 idle 错误 | 超时检测正确 |

**入口设计**

```tsx
// DevDemoButton.tsx
export function DevDemoButton() {
  if (!__DEV__) return null;
  const navigation = useNavigation();
  return (
    <FloatingButton
      icon="🧪"
      label="Demo"
      onPress={() => navigation.navigate('StreamingDemo')}
      position="bottom-right"
      offset={{ bottom: 100, right: 20 }}
    />
  );
}
```

**Mock 调度器实现要点**

- 每个场景定义为 `{ delay_ms, event }[]` 数组，按相对延迟串行触发
- `cancel()` 立即清空所有 pending `setTimeout`，不再 emit
- `on(type, handler)` 走 `Map<EventType, Handler[]>`，跟真实 SSE EventSource API 一致
- `idleTimer` 内置实现：每个事件触发后 reset，30s 没事件 → emit `error: IDLE_TIMEOUT`
- 暴露给 demo 页的接口与未来真实 SSE 客户端**完全同构**，方便替换

**视觉规范**（自定主张，遵循 RN Paper 风格）

- `StatusChip`：圆角胶囊，浅蓝底（`#E3F2FD`）+ 旋转 spinner
- `ToolCallChip`：圆角胶囊，浅紫底（`#F3E5F5`）+ 工具图标，完成后变灰
- `StreamingText`：标准消息字号，末尾闪烁光标 `▌`（500ms 周期）
- `ChoicePromptView`：横向 wrap 布局，chips 圆角中等填充，已选高亮主题色
- `StreamingCardView`：复用现有 `ChatCard` 视觉，区别在右上角加 `⏳ 生成中` 直到 done
- 主题色复用现有 `theme.colors.primary`，不新增配色

**验收标准**

- [ ] 6 个场景全部能在 demo 页一键切换运行
- [ ] 视觉时间线匹配设计文档 §16.5 描述
- [ ] `cancel()` 中断后剩余事件不触发
- [ ] `idle_timeout` 场景能在 30s 触发错误提示
- [ ] dev 浮动按钮仅在 `__DEV__` 模式可见，正式构建不出现
- [ ] TypeScript 0 报错，ESLint 0 警告
- [ ] 不影响 `/ai/chat` 现有功能

**风险点**

- React Native 的 `setTimeout` 在 JS 线程繁忙时漂移：用累积绝对时间避免误差累积
- StreamingText 高频更新需 `useMemo` + 避免重渲整个消息列表（用 key 隔离）

---

### T2: 首页多接口并行加载（独立问题，可立即修）

**目标**：首页 4 个接口各自独立 loading + 骨架屏，不再 `Promise.all` 全等。

**当前问题**（需先用 Grep 确认）

- 怀疑现状：`useHomeData` 之类的 hook 内部 `Promise.all([...])`，整体 loading 才停止
- 后果：suggestion 接口慢 → 整个首页转圈 → 饮食/身体卡片明明已就绪也看不到

**修改思路**

| 调整 | 内容 |
|------|------|
| 拆分查询 | 每个数据源独立 `useQuery`，独立 cacheKey |
| 骨架屏组件 | `DietCardSkeleton` / `BodyCardSkeleton` / `SuggestionCardSkeleton` / `PlanCardSkeleton` |
| 渲染层 | `isLoading ? <Skeleton /> : <Card data={data} />` 各卡片独立条件 |
| 错误隔离 | 一个接口 fail 不影响其他卡片显示，错误态在卡片内部展示 |

**新增/修改文件**

| 路径 | 改动 |
|------|------|
| `src/features/home/hooks/useDietSummary.ts` | 单独抽出（如已有则保持） |
| `src/features/home/hooks/useBodyToday.ts` | 同上 |
| `src/features/home/hooks/useDailySuggestion.ts` | 同上 |
| `src/features/home/hooks/usePlanProgress.ts` | 同上 |
| `src/features/home/components/skeletons/*.tsx` | 4 个骨架屏组件 |
| `src/features/home/screens/HomeScreen.tsx` | 改为各卡片独立 loading 渲染 |
| 删除 | 老的聚合 `useHomeData` hook（如存在） |

**关键签名**

```ts
// 各卡片渲染模式统一
{dietQuery.isLoading
  ? <DietCardSkeleton />
  : dietQuery.isError
    ? <DietCardError onRetry={() => dietQuery.refetch()} />
    : <DietCard data={dietQuery.data!} />
}
```

**验收标准**

- [ ] 网络限速到 1Mbps 时，饮食/身体卡片先于 suggestion 显示
- [ ] suggestion 接口失败不影响其他 3 个卡片
- [ ] 骨架屏视觉与最终卡片对齐（高度、间距）
- [ ] 下拉刷新各 query 并行重新获取
- [ ] TypeScript 0 报错

**风险点**

- 现有代码若有"等所有接口完成才计算汇总指标"的逻辑（如总热量），需要识别并拆出独立 derived state

---

## 3. P1 任务详细规格（核心流式能力）

### T3: SSE 协议骨架 + Schema 定义

**目标**：在后端建立 SSE 响应基础设施，定义事件 Schema（Pydantic），为后续流式化端点复用。

**新增文件**

| 路径 | 作用 |
|------|------|
| `app/streaming/__init__.py` | 模块入口 |
| `app/streaming/events.py` | `StreamEvent` Pydantic 模型 + 序列化 |
| `app/streaming/sse.py` | SSE 帧编码 + StreamingResponse helper |
| `app/streaming/translator.py` | LangGraph `astream_events` → 业务事件翻译层 |

**关键签名**

```python
# events.py
class StreamEventType(str, Enum):
    META = "meta"
    STATUS = "status"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TEXT_DELTA = "text_delta"
    CHOICE = "choice"
    CARD = "card"
    DONE = "done"
    ERROR = "error"
    HEARTBEAT = "heartbeat"

class MetaPayload(BaseModel):
    message_id: str
    session_id: UUID
    started_at: datetime

# ... 其他 payload 类型

class StreamEvent(BaseModel):
    type: StreamEventType
    data: dict[str, Any]


# sse.py
def format_sse(event: StreamEvent) -> bytes:
    """编码为 SSE 帧字节流"""

async def sse_response(
    generator: AsyncIterator[StreamEvent],
    *,
    heartbeat_interval: int = 15,
) -> StreamingResponse:
    """包装 generator 为 StreamingResponse，自动注入心跳"""


# translator.py
async def translate_langgraph_events(
    agent: Runnable,
    state: dict,
    *,
    node_labels: dict[str, str],
) -> AsyncIterator[StreamEvent]:
    """把 LangGraph astream_events v2 翻译成业务事件"""
```

**节点标签映射**（chat agent 用）

```python
CHAT_NODE_LABELS = {
    "identify_intent": "正在识别意图...",
    "recall_memories": "正在回忆相关记忆...",
    "search_knowledge": "正在查找知识库...",
    "parse_text": "正在分析饮食...",
    "enrich_nutrition": "正在计算营养...",
    "wrap_response": "正在整理回复...",
}
```

**验收标准**

- [ ] 单元测试：`format_sse` 输出符合 SSE 规范（`event: ...\ndata: ...\n\n`）
- [ ] 单元测试：translator 能把伪造的 LangGraph 事件序列翻译成正确的 StreamEvent 列表
- [ ] 心跳每 15s 触发一次，不阻塞业务事件
- [ ] 异常 → emit error 事件 + 关闭流
- [ ] TypeScript 客户端类型与后端 Pydantic schema 同步（用 schema 导出工具或手写镜像）

---

### T4: `/ai/chat` 改造为流式端点

**目标**：将现有 chat 接口改造为流式，验证 T3 基建。

**修改文件**

| 路径 | 改动 |
|------|------|
| `app/api/v1/ai.py` | 将 `POST /chat` 端点改为 SSE 流式响应 |
| `app/schemas/chat_stream.py` | 新增 `ChatStreamRequest` 输入 schema（或复用现有 schema） |
| `app/agents/base.py` | `get_chat_model(streaming=True)` 支持流式输出 |

**关键签名**

```python
@router.post("/chat")
async def chat(
    payload: ChatStreamRequest,
    user: CurrentUserDep,
    chat_agent: ChatAgentDep,
    chat_service: ChatServiceDep,
    diet_service: DietServiceDep,
    memory_service: MemoryServiceDep,
    rag_service: RagServiceDep,
):
    state = build_chat_state(payload, user, ...)
    async def gen() -> AsyncIterator[StreamEvent]:
        yield StreamEvent(type="meta", data={...})
        async for ev in translate_langgraph_events(chat_agent, state, node_labels=CHAT_NODE_LABELS):
            yield ev
        await persist_message(chat_service, ...)
        yield StreamEvent(type="done", data={...})
    return await sse_response(gen())


class ChatStreamRequest(BaseModel):
    session_id: UUID | None = None
    type: Literal["text", "card_action", "choice_response"] = "text"

    # type=text
    message: str | None = None

    # type=card_action
    card_id: str | None = None
    action_id: str | None = None
    action_payload: dict | None = None

    # type=choice_response
    prompt_id: str | None = None
    selected_value: str | None = None
    free_text: str | None = None
```

**注意点**

- 直接改造现有端点，删除旧的 JSON 响应实现
- 鉴权依赖与旧端点一致（CurrentUserDep）
- 错误处理：业务异常 → emit error 事件；客户端断开 → 让 CancelledError 自然传播

**验收标准**

- [ ] curl + `--no-buffer` 测试能看到事件实时输出
- [ ] LangGraph 节点切换时能看到 status 事件
- [ ] 浏览器 DevTools 看到响应 Content-Type 为 `text/event-stream`
- [ ] 流结束后客户端 EventSource 自动 close
- [ ] 前端现有 chat 功能正常（改造后兼容）

---

### T5: 前端 SSE 客户端（替换 Mock 调度器）

**目标**：用 `react-native-sse` 实现真实 SSE 客户端，API 与 Mock 调度器一致，前端组件零改动切换。

**依赖安装**

```
yarn add react-native-sse
```

**新增文件**

| 路径 | 作用 |
|------|------|
| `src/features/ai/services/streamingClient.ts` | 真实 SSE 客户端，与 Mock 同接口 |
| `src/features/ai/services/streamingTypes.ts` | 共用类型（提取自 demo/types.ts） |

**关键签名**

```ts
// streamingClient.ts
export function createSSEStream(
  url: string,
  body: ChatStreamRequest,
  token: string,
): MockStreamHandle {  // 与 Mock 同一接口
  const source = new EventSource(url, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
    pollingInterval: 0,
  });

  // 把 EventSource 事件转成同 Mock 的 on(type, handler) API
  ...

  return { start: () => {}, cancel: () => source.close(), on, off };
}
```

**验收标准**

- [ ] demo 页加一个开关："Mock | 真实 SSE"，切换后流式行为一致
- [ ] iOS 真机 + Android 真机均验证
- [ ] 切后台再回前台，新发起的请求正常工作（旧连接断掉是预期）
- [ ] 鉴权失败返回 401 时前端能正确显示错误

---

### T6: 流式渲染组件正式化

**目标**：把 demo 用的组件提升为生产组件，集成进 `AIDialogScreen`。

**改动思路**

- demo/components 下的组件 → 移到 `src/features/ai/components/streaming/`
- `AIDialogScreen` 增加 streaming 模式分支（feature flag 控制，T15 引入）
- 新建 hook `useStreamingChat`，对外暴露 `send / cancel / streaming` 状态

**关键签名**

```ts
// hooks/useStreamingChat.ts
export function useStreamingChat(): {
  send: (payload: ChatStreamRequest) => void;
  cancel: () => void;
  streaming: StreamingMessage | null;
};

interface StreamingMessage {
  id: string;
  segments: Segment[];   // 跨多次 SSE 连接累积
  status: string | null;
  tools: ToolCallState[];
  isStreaming: boolean;
}
```

**验收标准**

- [ ] demo 页与正式聊天页视觉一致
- [ ] 已有的 chat history 渲染不受影响
- [ ] 流式中能正常输入下一条（输入框不被禁用）
- [ ] 流式中可点击"停止"按钮取消

---

## 4. P2 任务详细规格（富交互）

### T7: Choice 事件 + 组件正式化

**目标**：选项 chips 落地真实交互，点击后发起新 SSE 请求继续对话。

**关键流程**

1. 后端 LLM 决定问澄清问题 → emit `event: choice`
2. 前端渲染 chips
3. 用户点击 chip → 前端发起 `POST /ai/chat/stream`，body 为 `{ type: 'choice_response', prompt_id, selected_value }`
4. 后端读取 `pending_action`（T8），合并状态后继续生成

**新增文件**

| 路径 | 作用 |
|------|------|
| `app/schemas/chat_stream.py` | 增加 `ChoicePrompt`, `ChoiceOption` |
| `src/features/ai/components/streaming/ChoicePrompt.tsx` | 选项渲染（含自由输入 fallback） |

**验收标准**

- [ ] 点击 chip 后该 chip 高亮成已选状态
- [ ] 选了 chip 后历史里以"用户消息"形式展示（标签文本）
- [ ] "自己输入"分支唤起键盘 + 输入框
- [ ] 5 分钟内未点击的 choice 视觉变灰（前端定时器）

---

### T8: `pending_action` 状态机（跨流状态串联）

**目标**：解决"两次独立 SSE 连接如何识别为同一轮对话"。

**实现层**

- 开发期：进程内 `dict[session_id, PendingAction]`（足够 demo 用）
- 生产：Redis 带 TTL（30 分钟）

**新增文件**

| 路径 | 作用 |
|------|------|
| `app/services/pending_action_store.py` | 抽象接口 + 内存实现 + Redis 实现（占位） |
| `app/schemas/pending_action.py` | `PendingAction` 模型 |

**关键签名**

```python
class PendingActionStore(Protocol):
    async def get(self, session_id: UUID) -> PendingAction | None: ...
    async def set(self, session_id: UUID, action: PendingAction, ttl: int) -> None: ...
    async def delete(self, session_id: UUID) -> None: ...

class PendingAction(BaseModel):
    prompt_id: str
    expected_kind: Literal['choice', 'free_text']
    options: list[ChoiceOption]
    diet_partial: dict | None    # 已识别但等用户确认餐次
    plan_partial: dict | None    # 已生成草案但等用户确认目标
    expires_at: datetime
```

**节点改造**

- chat 子图：进入 `identify_intent` 前先检查 `pending_action`，命中则跳过意图识别，走"答案合并"分支

**验收标准**

- [ ] 第 1 次请求 emit choice 后，redis/dict 中能查到 PendingAction
- [ ] 第 2 次请求带 `prompt_id` 进来，服务端能正确合并并继续生成
- [ ] PendingAction 30 分钟后自动失效，前端再点已过期 chip 收到 `expired` 错误
- [ ] 同一 session 的并发请求互斥（防止用户重复点）

---

### T9: 卡片流式插入

**目标**：节点产出卡片时即时 emit `event: card`，前端插入到当前 streaming 消息的 segments。

**改造点**

- `wrap_response` 节点保持产出 cards，但在流式上下文中改为按节点完成顺序逐个 emit
- 前端 `StreamingMessage.segments` 数组接受 card 类型 segment

**验收标准**

- [ ] 饮食确认场景：text → card 顺序正确
- [ ] 用户点卡片"确认"按钮 → 走 `card_action` 类型新请求 → 服务端识别后保存饮食记录
- [ ] 卡片提交后状态变为 `submitted`，按钮置灰

---

## 5. P3 任务详细规格（其他 AI 接口）

### T10: suggestions 三接口流式化

涉及：`/suggestions/daily`, `/suggestions/meal`, `/suggestions/insights`

**复用 T3-T6 基建**，每个接口走相同协议。差异：

- 没有用户输入，请求体最简（只带 user_id 和参数）
- 没有 choice 交互，最多 status + text_delta + card
- 缓存命中时直接返回 done + card（不走流式）

**修改文件**

| 路径 | 改动 |
|------|------|
| `app/api/v1/suggestions.py` | 将三个 GET 端点改为 SSE 流式响应 |

**前端改造**

- 首页 `SuggestionCard` 接 streaming 状态：先显示 status chip（"AI 正在为你生成..."）→ 文本流出 → 完整建议
- 不再用 React Query 取数据，改用 streaming hook

**验收标准**

- [ ] 首页打开 → suggestion 卡片立即显示 "AI 正在为你生成..."
- [ ] 流出文本可见
- [ ] 缓存命中时不走流式，直接渲染（避免无意义的"假流式"）

---

### T11: plans 创建流式化

`POST /plans`：用户输入目标 → 流式生成计划草案 → 安全校验 → 持久化。

**修改文件**

| 路径 | 改动 |
|------|------|
| `app/api/v1/plans.py` | 将 `POST /plans` 端点改为 SSE 流式响应 |

**关键事件**

- text_delta：流出"了解，我来帮你制定计划..."
- status：节点切换（草案生成 → 安全校验 → 入库）
- card：最终输出 plan 卡片

**验收标准**

- [ ] 创建计划页面用流式而非传统 loading 转圈
- [ ] 安全校验失败时能 emit 业务错误并允许用户调整目标重试

---

## 6. P4 任务详细规格（健壮性）

### T12: 心跳 + Idle Timeout

后端：T3 的 sse_response 已内置 15s heartbeat。
前端：`createSSEStream` 内部维护 idleTimer，30s 无事件触发关闭 + 错误。

**验收标准**

- [ ] 模拟后端 stall（debugger 暂停）30s → 前端报 IDLE_TIMEOUT 错误
- [ ] 流持续吐数据时不会被误判超时

---

### T13: 取消传播（防烧 token）

**目标**：客户端关闭连接 → FastAPI 触发 CancelledError → LangGraph 立即终止 LLM 调用。

**关键点**

- LangGraph 0.2+ 支持自动 cancellation 传播
- 节点内 `await` 自然响应取消
- 不要 `try/except Exception` 吞 CancelledError

**验收标准**

- [ ] 用户中途点"停止" → 后端日志显示 `cancelled` 在 1s 内
- [ ] DashScope 调用立即结束，无后续 token 消耗

---

### T14: Total Timeout 兜底

后端 `asyncio.timeout(180)` 包裹整个流，超时 emit error。

**验收标准**

- [ ] 模拟 LLM 死循环 → 180s 后服务端主动关闭
- [ ] 前端收到 error 事件并展示

---

## 7. P5 任务详细规格（监控与收尾）

### T15: 监控埋点

**核心指标**

| 指标 | 含义 | 告警阈值 |
|------|------|---------|
| `chat_stream_started` | 流式请求发起数 | / |
| `chat_stream_first_token_ms` | 首 token 延迟（用户感知速度） | p95 > 3s 告警 |
| `chat_stream_total_ms` | 单次流总时长 | p95 > 60s 告警 |
| `chat_stream_idle_timeout` | idle 超时次数 | > 1% 告警 |
| `chat_stream_error_rate` | 错误率 | > 0.5% 告警 |
| `chat_stream_cancel_rate` | 用户主动取消率 | 监控趋势 |

**实施要点**

- 后端在 SSE generator 中埋点（首事件时间、done 时间、error 类型）
- 前端在 streaming hook 中埋点（连接建立、首事件、完成、取消、超时）
- 使用现有监控基础设施（如有），或先用日志聚合

**验收标准**

- [ ] 能在监控面板看到上述 6 个指标
- [ ] p95 延迟能按天/周查看趋势
- [ ] 错误率超阈值时能收到告警

---

## 8. 实施节奏建议

### 第 1 阶段：验证（仅 P0）

- 完成 T1（Mock 演示）+ T2（首页并行）
- 用户验收 demo 视觉与交互
- 决定是否继续投入

### 第 2 阶段：核心流式（P1）

- T3 → T4 → T5 → T6 顺序推进
- 完成后 chat 接口已经流式可用（功能拉齐 ChatGPT 基础流式）

### 第 3 阶段：富交互（P2）

- T7 → T8 → T9
- 完成后多轮澄清 + 卡片确认闭环

### 第 4 阶段：扩展 + 健壮性（P3 + P4）

- T10/T11 并行（suggestions + plans 流式化）
- T12/T13/T14 健壮性兜底

### 第 5 阶段：监控收尾（P5）

- T15 监控埋点 → 生产可观测性

---

## 9. 进度跟踪

| Task | 状态 | 备注 |
|------|------|------|
| T1 Mock 演示页 | ⏸️ 待开始 | |
| T2 首页多接口并行 | ⏸️ 待开始 | |
| T3 SSE 协议骨架 | ⏸️ 待开始 | |
| T4 chat 流式改造 | ⏸️ 待开始 | |
| T5 前端 SSE 客户端 | ⏸️ 待开始 | |
| T6 流式渲染组件 | ⏸️ 待开始 | |
| T7 Choice 组件 | ⏸️ 待开始 | |
| T8 pending_action | ⏸️ 待开始 | |
| T9 卡片流式插入 | ⏸️ 待开始 | |
| T10 suggestions 流式 | ⏸️ 待开始 | |
| T11 plans 流式 | ⏸️ 待开始 | |
| T12 心跳 + Idle | ⏸️ 待开始 | |
| T13 取消传播 | ⏸️ 待开始 | |
| T14 Total Timeout | ⏸️ 待开始 | |
| T15 监控埋点 | ⏸️ 待开始 | |

状态图例：⏸️ 待开始 / 🟡 进行中 / ✅ 完成 / ❌ 阻塞

---

## 10. 修订记录

| 日期 | 修订内容 |
|------|---------|
| 2026-05-22 v1 | 初稿，基于 2026-05-21 设计文档评审决策（B + 全场景 + 自定主张）拆分 18 个任务 |
| 2026-05-22 v2 | 简化灰度切换：删除 T16/T17/T18，T4/T10/T11 改为直接改造现有端点；新项目无需保留旧接口 |



