# AI 记忆模块 (AI Memory)

> AI 记忆系统是健康管家的核心 AI 模块，负责三层记忆架构管理（短期/中期/长期）、记忆自动提取、质量评分与验证、时间衰减召回、记忆合并摘要，以及对话消息管理。本模块让 AI 能"记住"用户的偏好、习惯和行为模式，实现个性化交互。
>
> 实现依据：`docs/prd/v1/05-ai-memory.md`，`docs/specs/backend/00-architecture/overview.md`，`docs/specs/backend/00-architecture/api-design.md`

---

## 1. 模块职责

本模块承担以下核心职责：

- **三层记忆架构管理**：短期记忆（会话上下文）、中期记忆（近期行为摘要）、长期记忆（用户画像级偏好）
- **记忆自动提取**：从对话和用户行为中异步提取有价值的记忆片段
- **质量评分与验证**：多维度评分（相关性、准确性、可操作性、非冗余性），过滤低质量记忆
- **时间衰减召回**：基于向量相似度 × 时间衰减 × 类型权重 × 质量系数的多因子召回
- **记忆合并摘要**：定期将相似记忆合并为摘要，防止记忆膨胀
- **对话消息管理**：聊天会话创建、消息存储、历史查询

### 1.1 模块边界

| 本模块负责 | 本模块不负责 |
|-----------|------------|
| 三层记忆的存储与检索 | 饮食记录解析（diet_service） |
| 记忆提取与质量评分 | 健康建议生成（suggestion_service） |
| 对话消息持久化与历史查询 | 健康计划制定（plan_service） |
| 向量 embedding 生成与 pgvector 检索 | 用户档案管理（user_service） |
| 记忆合并与归档 | RAG 知识库管理（knowledge_service） |

---

## 2. API 端点

所有端点必须遵循 `api-design.md` 的统一响应格式和错误码规范。基础路径：`/api/v1/ai/`。

### 2.1 端点总览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/ai/chat` | 发送消息（对话入口，记忆读写在此发生） | 必须 |
| GET | `/api/v1/ai/chat/history` | 查询对话历史（分页） | 必须 |
| DELETE | `/api/v1/ai/chat/sessions/{id}` | 删除对话会话 | 必须 |

### 2.2 端点详细定义

#### POST /api/v1/ai/chat

主对话入口。接收用户消息，召回相关记忆注入 prompt，返回 AI 回复，异步触发记忆提取。

- 请求体：`ChatRequest`
- 响应体：`ApiResponse[ChatResponse]`
- 状态码：200 OK
- 流程：接收消息 → 召回记忆（长期 + 中期 Top 3） → 组装 prompt → LLM 生成回复 → 返回响应 → 异步提取记忆

#### GET /api/v1/ai/chat/history

查询当前用户的对话历史，支持分页。

- 查询参数：`session_id` (str, 可选, 不传则返回最近会话), `page` (int, 默认=1), `page_size` (int, 默认=20, 最大=50)
- 响应体：`PaginatedResponse[ChatMessageResponse]`
- 排序：按 `created_at` 升序（时间线顺序）

#### DELETE /api/v1/ai/chat/sessions/{id}

删除指定对话会话及其所有消息（软删除）。

- 路径参数：`id` (str, session_id)
- 响应体：`{"data": null, "message": "删除成功"}`
- 错误：404 `CHAT_SESSION_NOT_FOUND`
- 幂等：重复删除返回 200，不报错

### 2.3 路由定义

```python
# app/api/v1/ai_chat.py
from fastapi import APIRouter, Depends, Query
from app.schemas.ai_memory import (
    ChatRequest, ChatResponse, ChatMessageResponse,
)
from app.schemas.common import ApiResponse, PaginatedResponse
from app.services.ai_chat_service import AiChatService
from app.dependencies import get_current_user, get_ai_chat_service
from app.schemas.auth import CurrentUser

router = APIRouter()

@router.post("/chat", response_model=ApiResponse[ChatResponse])
async def send_message(
    data: ChatRequest,
    user: CurrentUser = Depends(get_current_user),
    service: AiChatService = Depends(get_ai_chat_service),
):
    """发送消息，AI 回复。记忆召回和提取在内部自动完成。"""
    return await service.chat(user.id, data)

@router.get("/chat/history", response_model=PaginatedResponse[ChatMessageResponse])
async def get_chat_history(
    session_id: str | None = Query(None, description="会话 ID，不传返回最近会话"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: CurrentUser = Depends(get_current_user),
    service: AiChatService = Depends(get_ai_chat_service),
):
    """查询对话历史"""
    return await service.get_history(user.id, session_id, page, page_size)

@router.delete("/chat/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: CurrentUser = Depends(get_current_user),
    service: AiChatService = Depends(get_ai_chat_service),
):
    """删除对话会话"""
    return await service.delete_session(user.id, session_id)
```

---

## 3. 三层记忆架构

### 3.1 架构总览

| 层级 | 范围 | 内容 | 存储方式 | 生命周期 |
|------|------|------|---------|---------|
| 短期记忆 | 单次会话 | 当前对话上下文、当前意图、提取的实体 | 内存（LangGraph State） | 会话结束即清空 |
| 中期记忆 | 7-30 天 | 近期行为摘要、偏好变化 | PostgreSQL `memory_summaries` 表 | 时间衰减，30 天后归档 |
| 长期记忆 | 永久 | 稳定偏好、习惯、目标、过敏信息 | PostgreSQL + pgvector `memories` 表 | 永久保存，质量淘汰 |

### 3.2 短期记忆（Session Memory）

- 存储当前会话的最近消息（最多 10 轮）、当前意图、临时提取的实体
- 由 LangGraph State 管理，禁止持久化到数据库
- 会话超时（30 分钟无活动）或用户主动结束时清空
- 示例：用户说"还有一碗米饭"，短期记忆中保留了上文的"鸡胸肉"，AI 知道是同一餐

### 3.3 中期记忆（Behavioral Memory）

- 由 LLM 从短期数据中定期提取，记录近 7 天的行为模式
- 存储在 `memory_summaries` 表（PostgreSQL）
- 示例："最近一周午餐偏好面食"、"连续 3 天没有运动记录"
- 30 天后自动归档，不再参与召回

### 3.4 长期记忆（Profile Memory）

- 从中期记忆中蒸馏出的用户画像级信息
- 存储在 `memories` 表，包含 pgvector embedding（1024 维）用于语义检索
- 示例："不喜欢吃香菜"、"目标是减重到 65kg"、"每天早上跑步的习惯"
- 永久保存，每用户最多 1000 条，超出时淘汰最旧的低质量记忆

---

## 4. 数据模型

所有模型使用 Pydantic v2 定义。必须遵循 `overview.md` 的类型安全原则，禁止裸 dict 传递。

### 4.1 枚举类型

```python
# app/schemas/ai_memory.py
from enum import Enum

class MemoryType(str, Enum):
    """记忆类型枚举"""
    food_preference = "food_preference"          # 食物偏好（喜欢/不喜欢某食物）
    portion_habit = "portion_habit"              # 份量习惯（一碗米饭约 150g）
    behavior_pattern = "behavior_pattern"        # 行为模式（午餐时间、运动频率）
    suggestion_feedback = "suggestion_feedback"  # 建议反馈（采纳/拒绝某类建议）
    health_goal = "health_goal"                  # 健康目标（减重、增肌等）
    allergy = "allergy"                          # 过敏信息
    exercise_habit = "exercise_habit"            # 运动习惯
```

### 4.2 请求模型

```python
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """对话请求体"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息内容")
    session_id: str | None = Field(None, description="会话 ID，不传则自动创建新会话")
```

### 4.3 响应模型

```python
from datetime import datetime
from uuid import UUID

class ChatResponse(BaseModel):
    """对话响应体"""
    message: str = Field(..., description="AI 回复内容")
    session_id: str = Field(..., description="会话 ID")
    intent: str | None = Field(None, description="识别到的用户意图，如 record_diet / ask_advice")

class ChatMessageResponse(BaseModel):
    """单条对话消息响应"""
    id: UUID
    role: str = Field(..., description="消息角色：user / assistant")
    content: str = Field(..., description="消息内容")
    created_at: datetime
```

### 4.4 内部模型（不暴露给 API）

```python
from datetime import date

class MemoryEntry(BaseModel):
    """长期记忆条目（内部使用，不暴露给 API）"""
    id: UUID
    user_id: UUID
    memory_type: MemoryType                                    # 记忆类型
    content: str = Field(..., max_length=500)                  # 自然语言描述
    embedding: list[float] = Field(..., description="1024 维向量")  # pgvector 存储
    metadata: dict = Field(default_factory=dict, description="结构化元数据，如 food/frequency/date_range")
    quality_score: int = Field(..., ge=0, le=100)              # 质量评分
    created_at: datetime
    last_accessed: datetime                                    # 最近一次被召回的时间
    access_count: int = Field(default=0, ge=0)                 # 被召回次数
    time_decay_factor: float = Field(default=1.0, ge=0, le=1.2)  # 时间衰减系数

class MemorySummary(BaseModel):
    """中期记忆摘要（内部使用，不暴露给 API）"""
    id: UUID
    user_id: UUID
    period_start: date                                         # 摘要覆盖的起始日期
    period_end: date                                           # 摘要覆盖的结束日期
    summary_content: str = Field(..., max_length=1000)         # 摘要内容
    key_facts: list[str] = Field(default_factory=list)         # 关键事实列表
    created_at: datetime
```

---

## 5. 记忆写入流程

### 5.1 触发点

记忆提取必须异步执行，禁止阻塞主流程响应。

| 触发点 | 触发时机 | 提取内容 | 示例 |
|--------|---------|---------|------|
| 饮食记录创建 | `diet_service` 创建记录后 | 食物偏好、份量习惯 | 连续 3 天吃鸡胸肉 → "喜欢鸡胸肉" |
| 用户纠正 | 用户编辑 AI 解析结果 | 偏好反馈 | AI 说 200g，用户改 150g → "一碗米饭约 150g" |
| 建议反馈 | 用户对建议标记有用/无用 | 建议有效性 | 用户采纳"晚餐吃鱼" → "接受鱼类建议" |
| 计划执行数据 | 计划打卡/进度更新 | 行为模式 | 连续 3 天未完成 → "计划目标可能过高" |

### 5.2 写入流程

```
1. 触发事件发生（饮食记录/用户纠正/建议反馈/计划执行）
   ↓
2. 异步任务：LLM 分析上下文，提取关键信息
   ↓
3. 质量评分：relevance(30%) + accuracy(40%) + actionability(20%) + uniqueness(10%)
   ↓
4. 评分处理：
   - score ≥ 80 → 直接存储
   - score 60-79 → 标记为 "pending"，存储但降低召回权重
   - score < 60 → 拒绝存储，记录日志
   ↓
5. 生成 embedding（DashScope text-embedding-v3，1024 维）
   ↓
6. 存入 memories 表（长期记忆）
```

### 5.3 质量评分 Prompt

```python
QUALITY_CHECK_PROMPT = """
评估以下记忆片段的质量：

记忆内容：{memory_content}
用户档案：{user_profile}
已有记忆：{existing_memories}

请从以下维度评分（0-100）：
1. 相关性（relevance）：是否与用户的健康管理目标相关？
2. 准确性（accuracy）：是否基于明确的事实和数据？
3. 可操作性（actionability）：是否能用于生成个性化建议？
4. 非冗余性（uniqueness）：是否与已有记忆重复？

必须输出 JSON 格式：
{
  "relevance": 85,
  "accuracy": 90,
  "actionability": 80,
  "uniqueness": 75,
  "overall_score": 83,
  "reason": "基于用户连续 5 天的饮食记录，准确反映了食物偏好"
}
"""
```

---

## 6. 记忆召回流程

### 6.1 召回流程

```
1. 用户发送新消息
   ↓
2. 生成 query embedding（DashScope text-embedding-v3）
   ↓
3. pgvector 相似度检索 memories 表（Top 10 候选）
   ↓
4. 多因子评分：vector_similarity × time_decay × type_weight × quality_coefficient
   ↓
5. 过滤 quality_score < 60 的记忆
   ↓
6. 取 Top 3 结果
   ↓
7. 注入 prompt context
```

### 6.2 时间衰减公式

基础系数根据记忆创建时间计算：

| 时间范围 | 基础系数 |
|---------|---------|
| 0-7 天 | 1.0 |
| 7-14 天 | 0.9 |
| 14-21 天 | 0.8 |
| 21-30 天 | 0.7 |
| 30+ 天 | 0.5 |

访问频率加成：

| 访问次数 | 加成 |
|---------|------|
| ≥ 5 次 | +0.1 |
| ≥ 10 次 | +0.2 |

```python
def calculate_time_decay(created_at: datetime, access_count: int) -> float:
    """计算时间衰减系数"""
    days = (datetime.utcnow() - created_at).days

    # 基础系数
    if days <= 7:
        base = 1.0
    elif days <= 14:
        base = 0.9
    elif days <= 21:
        base = 0.8
    elif days <= 30:
        base = 0.7
    else:
        base = 0.5

    # 访问频率加成
    bonus = 0.0
    if access_count >= 10:
        bonus = 0.2
    elif access_count >= 5:
        bonus = 0.1

    return min(base + bonus, 1.2)  # 上限 1.2
```

### 6.3 多因子召回评分

```python
def calculate_recall_score(
    vector_similarity: float,   # 0-1，pgvector 检索结果
    time_decay: float,          # 0.5-1.2，时间衰减系数
    type_weight: float,         # 0.6-1.0，根据当前意图
    quality_score: int,         # 0-100，记忆质量分
) -> float:
    """计算最终召回评分"""
    quality_coefficient = quality_score / 100
    return vector_similarity * time_decay * type_weight * quality_coefficient
```

### 6.4 类型权重配置

根据当前识别的用户意图，不同记忆类型的权重不同：

```python
TYPE_WEIGHTS: dict[str, dict[str, float]] = {
    "record_diet": {
        "food_preference": 1.0,
        "portion_habit": 0.9,
        "behavior_pattern": 0.7,
        "suggestion_feedback": 0.6,
        "health_goal": 0.7,
        "allergy": 1.0,
        "exercise_habit": 0.4,
    },
    "create_plan": {
        "behavior_pattern": 1.0,
        "suggestion_feedback": 0.9,
        "food_preference": 0.8,
        "portion_habit": 0.6,
        "health_goal": 1.0,
        "allergy": 0.7,
        "exercise_habit": 0.9,
    },
    "general_advice": {
        "food_preference": 1.0,
        "behavior_pattern": 0.9,
        "suggestion_feedback": 0.8,
        "portion_habit": 0.7,
        "health_goal": 0.9,
        "allergy": 1.0,
        "exercise_habit": 0.8,
    },
}
```

---

## 7. 记忆合并（Consolidation）

### 7.1 触发条件

- 每周一次自动检查（定时任务）
- 或累积 20 条新记忆时触发

### 7.2 合并流程

```
1. 检测相似记忆（向量相似度 > 0.85 的记忆组）
   ↓
2. LLM 将相似记忆合并成摘要 → 创建 MemorySummary
   ↓
3. 原始记忆标记为 "archived"，保留但不参与召回
   ↓
4. 摘要记忆参与后续召回
```

### 7.3 合并目的

- 防止记忆膨胀（每用户最多 1000 条长期记忆）
- 提高召回质量（摘要比碎片化记忆更有价值）
- 维持记忆相关性

---

## 8. Agent 层流程

**所有 LLM 推理统一走 LangGraph Agent**（见 `00-architecture/agents.md`）。记忆模块包含两个 Agent：

- **`chat_agent`**：承载 `POST /api/v1/ai/chat` 完整对话流程
- **`memory_agent`**：承载记忆提取与评分流程，异步触发

### 8.1 对话 Agent（chat_agent）

```python
# app/agents/chat/state.py
from typing import TypedDict

class ChatState(TypedDict, total=False):
    user_id: str
    session_id: str
    user_message: str
    chat_history: list[dict]              # 短期记忆：最近对话（最多 10 轮）
    long_term_profile: list[dict]         # 长期记忆：用户画像
    recalled_memories: list[dict]         # 召回的记忆（Top 3）
    knowledge: list[dict]                 # RAG 检索片段
    intent: str | None
    prompt_messages: list[dict]
    ai_response: str
```

节点：

| 节点 | 实现要点 |
|------|---------|
| `identify_intent` | LLM 识别意图：record_diet / ask_advice / general_chat 等。Prompt 在 `agents/prompts/chat_system.py` |
| `recall_memories` | Tool: `MemoryService.recall_memories(user_id, query, intent)`，返回 Top 3 |
| `search_knowledge` | Tool: `RagService.search_knowledge(query, category)` |
| `assemble_prompt` | 组装 system + 长期记忆 + 召回记忆 + 知识 + 对话历史 |
| `call_llm` | `get_chat_model(temperature=0.7)` 生成回复 |
| `trigger_memory_extract` | `asyncio.create_task(memory_agent.ainvoke(...))` 异步触发，不阻塞响应 |

边：`identify_intent → recall_memories → search_knowledge → assemble_prompt → call_llm → trigger_memory_extract → END`

### 8.2 记忆 Agent（memory_agent）

```python
# app/agents/memory/state.py
class MemoryExtractionState(TypedDict, total=False):
    user_id: str
    trigger_type: str       # diet_record / user_correction / suggestion_feedback / plan_execution
    context_data: dict
    extracted: list[dict]
    scored: list[dict]
    approved: list[dict]
```

节点：

| 节点 | 实现要点 |
|------|---------|
| `extract` | LLM 从 context_data 提取记忆片段（structured output） |
| `score` | LLM 给每条记忆多维度打分（relevance/accuracy/actionability/uniqueness） |
| `filter` | 代码确定性过滤：≥80 直接存，60-79 标记 pending，<60 丢弃 |
| `embed_and_store` | Tool: `MemoryService.store_memory(entry_with_embedding)`（节点内调用 `EmbeddingClient.embed` 生成向量） |

边：`extract → score → filter → embed_and_store → END`

### 8.3 触发方式

| 触发点 | 触发方式 |
|--------|---------|
| 饮食记录创建后 | `diet_agent` 末节点 `asyncio.create_task(memory_agent.ainvoke(...))` |
| 用户纠正 | API 直接触发 `memory_agent.ainvoke(...)` |
| 建议反馈 | `SuggestionService.submit_feedback` 触发 |
| 计划执行 | `PlanService.on_diet_record_created` 触发 |
| 对话结束 | `chat_agent` 的 `trigger_memory_extract` 节点 |

禁止在 `services/memory_service.py` 或其他 service 内直接实例化 ChatOpenAI 做记忆提取。

---

## 9. Service 接口

### 9.0 分层

- **`MemoryService`**：纯 CRUD + 召回/衰减算法。**不含 LLM 调用**，作为 `memory_agent` / `chat_agent` 的 Tool 被调用。
- **`ChatService`**：对话消息持久化、会话管理。AI 对话编排在 `chat_agent` 内完成，Service 只管数据。

### 9.1 MemoryService（纯 CRUD + 算法）

```python
class MemoryService:
    """记忆存储/召回/衰减。不做 LLM 编排。"""

    def __init__(
        self, memory_repo: MemoryRepository,
        embedding_client: EmbeddingClient,
        pgvector_client: PgVectorClient,
    ): ...

    async def store_memory(self, user_id: UUID, entry: MemoryEntry) -> MemoryEntry:
        """由 memory_agent 的 embed_and_store 节点调用，写入 memories 表。"""

    async def recall_memories(
        self, user_id: UUID, query: str, intent: str | None = None, top_k: int = 3
    ) -> list[MemoryEntry]:
        """召回：query embedding → pgvector top-10 候选 → 多因子评分 → Top K。"""

    async def get_long_term_profile(self, user_id: UUID) -> list[MemoryEntry]:
        """获取长期记忆全量（用于 System Prompt）。"""

    async def consolidate_memories(self, user_id: UUID) -> None:
        """记忆合并协调：找相似组 → 触发 memory_agent 的合并子图 → 归档原始。
        本方法本身不做 LLM 调用。"""

    async def on_profile_updated(self, user_id: UUID, updated_data: dict) -> None:
        """用户档案更新时同步长期记忆（由 user_service 调用）。"""
```

### 9.2 ChatService（会话与消息 CRUD）

```python
class ChatService:
    """对话会话与消息管理。不含 AI 编排。"""

    async def get_or_create_session(self, user_id: UUID, session_id: str | None) -> str: ...
    async def save_message(self, user_id: UUID, session_id: str, role: str, content: str) -> None: ...
    async def get_history(
        self, user_id: UUID, session_id: str | None, page: int, page_size: int
    ) -> PaginatedResponse[ChatMessageResponse]: ...
    async def delete_session(self, user_id: UUID, session_id: str) -> None: ...
```

### 9.3 `POST /ai/chat` 的协作关系

```
API Router (ai.py)
    ↓
1. ChatService.get_or_create_session(...)
2. chat_agent.ainvoke({user_id, session_id, user_message, ...})
      ↳ 内部 identify_intent → recall_memories → search_knowledge
      ↳   → assemble_prompt → call_llm → trigger_memory_extract (asyncio.create_task)
3. ChatService.save_message(role="user", ...)
4. ChatService.save_message(role="assistant", content=result["ai_response"])
5. 返回 ChatResponse
```

原 spec 中的 `AiChatService.chat()` 不再存在，对话编排由 `chat_agent` 承担。

---

## 10. 模块依赖

### 10.1 本模块依赖

| 依赖对象 | 用途 |
|---------|------|
| `get_chat_model()` (langchain-openai, DashScope qwen-plus) | 记忆提取/评分/合并/对话回复（仅在 Agent 节点中调用） |
| `EmbeddingClient` (text-embedding-v3) | 向量生成（1024 维） |
| `PgVectorClient` | 向量存储与相似度检索 |
| `user_service` | 获取用户档案（长期记忆的一部分） |

### 10.2 被其他模块依赖

| 调用方 | 调用接口 | 场景 |
|--------|---------|------|
| `chat_agent` (本模块) | `MemoryService.recall_memories()` | 对话召回 |
| `diet_agent` | `memory_agent.ainvoke(trigger="diet_record", ...)` | 饮食记录后异步提取 |
| `suggestion_agent` | `MemoryService.recall_memories()` | 建议生成时召回偏好 |
| `plan_agent` | `memory_agent.ainvoke(trigger="plan_execution", ...)` | 计划执行触发提取 |
| `user_service` | `MemoryService.on_profile_updated()` | 档案更新同步 |

---

## 11. 实现约束

- **异步提取**：记忆提取必须异步执行（`asyncio.create_task` 或后台任务），禁止阻塞对话响应
- **记忆上限**：每用户最多 1000 条长期记忆，超出时淘汰最旧的低质量记忆（quality_score 最低 + created_at 最早）
- **对话历史保留**：聊天消息保留 90 天，过期数据由定时任务清理
- **会话超时**：30 分钟无活动视为会话结束，短期记忆清空
- **Embedding 维度**：必须使用 1024 维（DashScope text-embedding-v3 默认维度）
- **向量检索**：pgvector 使用余弦相似度（cosine distance），禁止使用欧氏距离
- **错误处理**：LLM 调用失败时，记忆提取静默失败（记录日志），禁止影响主流程；对话生成失败时返回 503 `LLM_SERVICE_UNAVAILABLE`
- **数据隔离**：所有查询必须包含 `user_id` 过滤条件，禁止跨用户访问记忆
