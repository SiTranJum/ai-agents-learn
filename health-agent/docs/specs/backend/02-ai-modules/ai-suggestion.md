# AI 建议系统

> 本文档定义 AI 建议系统的完整后端规格，包括建议类型、生成逻辑、缓存策略和反馈机制。
>
> 实现依据：`docs/prd/v1/08-ai-suggestion.md`，`00-architecture/integrations.md`

---

## 1. 模块职责

**核心职责**：

- 四种建议类型的统一生成入口：`diet_advice`、`goal_advice`、`trend_advice`、`proactive_insight`
- 基于用户数据 + 长期记忆 + 知识库的个性化建议生成
- 建议缓存策略（每日 / 每周）与失效控制
- 用户反馈收集，并驱动记忆系统学习用户偏好
- 建议质量规则的强制执行（具体性、安全性、个性化）

**边界**：

| 本模块负责 | 本模块不负责 |
| --- | --- |
| 建议生成、缓存、反馈收集与质量控制 | 数据采集（由各业务模块负责）、记忆管理（由 memory_service 负责）、知识检索（由 rag_service 负责） |

## 2. API 端点

### 2.1 端点列表

对齐 `00-architecture/api-design.md` 第 7.7 节。

| Method | Path | 说明 | 认证 |
| --- | --- | --- | --- |
| GET | `/api/v1/suggestions/daily` | 获取每日建议（首页卡片） | 需要 |
| GET | `/api/v1/suggestions/meal` | 获取餐食建议（按餐次） | 需要 |
| GET | `/api/v1/suggestions/insights` | 获取健康洞察 | 需要 |
| POST | `/api/v1/suggestions/{id}/feedback` | 提交建议反馈 | 需要 |

### 2.2 请求/响应规格

- `GET /api/v1/suggestions/daily`：无请求参数，返回 `DailySuggestionResponse`。优先读取缓存。
- `GET /api/v1/suggestions/meal`：必填 query 参数 `meal_type`（`breakfast` | `lunch` | `dinner` | `snack`），返回 `MealSuggestionResponse`。实时计算，不走缓存。
- `GET /api/v1/suggestions/insights`：无请求参数，返回 `InsightResponse`。优先读取每周缓存。
- `POST /api/v1/suggestions/{id}/feedback`：路径参数 `id` 为建议 UUID，body 为 `FeedbackCreate`，返回 204 No Content。

错误码：`SUGGESTION_NOT_FOUND`、`SUGGESTION_GENERATION_FAILED`、`SUGGESTION_VALIDATION_FAILED`、`SUGGESTION_PERMISSION_DENIED`。

## 3. 数据模型

### 3.1 枚举定义

```python
from enum import Enum

class SuggestionType(str, Enum):
    diet_advice = "diet_advice"
    goal_advice = "goal_advice"
    trend_advice = "trend_advice"
    proactive_insight = "proactive_insight"

class SuggestionPriority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class FeedbackRating(str, Enum):
    helpful = "helpful"
    not_helpful = "not_helpful"
    dismissed = "dismissed"
```

### 3.2 响应模型

```python
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SuggestionItem(BaseModel):
    id: UUID
    type: SuggestionType
    title: str
    content: str
    basis: Optional[str] = Field(None, description="建议的依据，例如所引用的记忆/数据/知识")
    priority: SuggestionPriority
    expires_at: Optional[datetime] = None
    created_at: datetime


class DailySuggestionResponse(BaseModel):
    suggestions: list[SuggestionItem] = Field(..., max_length=3)
    generated_at: datetime


class NutritionSummary(BaseModel):
    calories: float
    protein: float
    fat: float
    carbs: float


class MealSuggestionResponse(BaseModel):
    meal_type: str
    consumed_today: NutritionSummary
    remaining: NutritionSummary
    suggestions: list[str] = Field(..., max_length=5, description="具体食物推荐")
    reasoning: str = Field(..., description="推荐依据说明")


class InsightItem(BaseModel):
    id: UUID
    dimension: str = Field(..., description="洞察维度，如 weight_trend, diet_pattern, plan_execution")
    finding: str = Field(..., description="发现的趋势或模式")
    suggestion: str = Field(..., description="针对该发现的建议")
    data_support: dict = Field(default_factory=dict, description="支撑数据，如 {\"weight_change\": -1.2, \"period\": \"30d\"}")
    generated_at: datetime


class InsightResponse(BaseModel):
    insights: list[InsightItem] = Field(..., max_length=3)
    period: str = Field(..., description="洞察覆盖的时间窗口，如 last_30_days")
```

### 3.3 反馈模型

```python
class FeedbackCreate(BaseModel):
    rating: FeedbackRating
```

## 4. 建议生成逻辑

### 4.1 每日建议（daily）

- **输入**：`HealthProfile` + 最近 7 天饮食记录 + 当前活跃 plan 进度 + 长期记忆（偏好、目标、习惯）。
- **流程**：LLM 综合用户画像与近期数据，生成 2-3 条个性化建议。
- **缓存**：每日生成一次，写入 `suggestions` 表，`expires_at` 设为次日 00:00。命中缓存直接返回。
- **数量限制**：最多 3 条。

### 4.2 餐食建议（meal）

- **输入**：当日已摄入营养 + 当前 plan 的每日营养目标 + `user_preferences`（偏好、忌口）+ `allergies`。
- **流程**：计算剩余营养缺口 → LLM 结合偏好与忌口，输出具体食物推荐。
- **缓存**：不缓存（依赖实时摄入数据）。
- **数量限制**：最多 5 个食物推荐。

### 4.3 健康洞察（insights）

- **输入**：体征数据趋势（30 天）+ 饮食模式 + plan 执行情况 + 运动数据。
- **流程**：LLM 分析趋势并生成洞察，每条洞察必须附带 `data_support`。
- **缓存**：每周生成一次，`expires_at` 设为下周一 00:00。
- **数量限制**：最多 3 条。

## 5. 质量规则

所有建议必须满足以下约束，违反任一规则的建议在 `deduplicate_filter` 节点被过滤：

- **具体可执行**：禁止泛泛而谈（如"多喝水"），必须给出具体动作或数值。
- **尊重忌口**：必须读取 `user_preferences.allergies` 与 `forbidden_foods`，违反者直接丢弃。
- **避免医疗诊断**：不得提供疾病诊断或极端饮食方案（如断食、生酮极限等）。
- **结合活跃 plan**：必须参考当前 plan 的目标，不能与之冲突。
- **友好语气**：避免说教式、命令式表达。
- **健康免责声明**：响应中必须包含免责声明文本（前端展示）。
- **去重**：
  - 同一天内不重复生成相同内容；
  - 3 天内不生成与已有建议向量相似度 > 0.8 的建议。

## 6. LangGraph 流程

对齐 `00-architecture/integrations.md` 第 5.2 节，定义 `suggestion_graph`：

```python
from typing import TypedDict


class SuggestionState(TypedDict):
    user_id: str
    suggestion_type: str
    user_profile: dict
    recent_data: dict
    memories: list[dict]
    knowledge: list[dict]
    raw_suggestions: list[dict]
    filtered_suggestions: list[dict]


# 节点定义：
# collect_data       —— 调用各业务 service 收集用户画像与近期数据
# recall_memories    —— 通过 memory_service 检索相关长期记忆
# search_knowledge   —— 通过 rag_service 检索营养/健康知识
# generate_suggestions —— 调用 llm_service 生成原始建议
# deduplicate_filter —— 去重 + 质量规则过滤
#
# 边：collect_data -> recall_memories -> search_knowledge
#     -> generate_suggestions -> deduplicate_filter -> END
```

## 7. 反馈机制

- 用户可对单条建议给出 `helpful` / `not_helpful` / `dismissed` 评价。
- 反馈写入 `suggestions.user_feedback` 字段。
- 反馈触发 `memory_service.extract_memory(type="suggestion_feedback")`，将偏好（如"用户不喜欢牛油果"）沉淀为长期记忆。
- 后续建议生成时，`recall_memories` 节点会召回这些偏好，从而实现持续学习。

## 8. Service 接口

```python
from uuid import UUID


class SuggestionService:
    async def get_daily_suggestions(self, user_id: UUID) -> DailySuggestionResponse:
        """获取每日建议，优先命中缓存，缓存失效则触发 suggestion_graph。"""

    async def get_meal_suggestions(self, user_id: UUID, meal_type: MealType) -> MealSuggestionResponse:
        """实时生成餐食建议，不走缓存。"""

    async def get_insights(self, user_id: UUID) -> InsightResponse:
        """获取每周健康洞察，优先命中缓存。"""

    async def submit_feedback(self, user_id: UUID, suggestion_id: UUID, feedback: FeedbackCreate) -> None:
        """写入反馈并触发记忆提取。"""
```

## 9. 模块依赖

- **上游**（本模块调用）：`llm_service`、`memory_service`、`rag_service`、`diet_service`、`body_service`、`plan_service`、`user_service`。
- **下游**（调用本模块）：无（叶子模块，仅由 API 路由直接调用）。

## 10. 实现约束

- **每日建议**：最多 3 条，缓存命中时响应 < 5s。
- **餐食建议**：最多 5 条食物推荐，实时生成，响应 < 10s。
- **健康洞察**：最多 3 条，缓存命中时响应 < 15s。
- 所有建议响应必须包含统一的健康免责声明文本。
- 不需要软删除（建议本身具有时效性，由 `expires_at` 控制可见性）。
- 错误码统一使用 `SUGGESTION_NOT_FOUND`、`SUGGESTION_GENERATION_FAILED`。
