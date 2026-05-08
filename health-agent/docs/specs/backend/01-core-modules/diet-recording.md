# 饮食记录模块 (Diet Recording)

> 饮食记录是健康管家的核心模块，负责自然语言饮食解析、拍照识别、营养计算、记录管理和摄入汇总。本模块以 AI 为中心设计，LLM 负责解析用户输入，RAG 负责营养数据检索，三层数据源策略保证营养数据覆盖率。
>
> 实现依据：`docs/prd/v1/03-diet-recording.md`，`docs/specs/backend/00-architecture/overview.md`，`docs/specs/backend/00-architecture/api-design.md`

---

## 1. 模块职责

本模块承担以下核心职责：

- **自然语言饮食解析**：接收用户文本输入，通过 LLM 解析为结构化食物列表（食物名、份量、餐次）
- **拍照识别**：接收食物照片，识别食物种类和估算份量（V1 使用 mock 实现）
- **营养计算**：通过 RAG 知识库查询 + LLM 估算，获取每种食物的营养数据并计算总量
- **饮食记录 CRUD**：创建、查询、更新、删除饮食记录，支持软删除
- **每日/每周营养汇总**：按日期聚合营养摄入数据，与计划目标对比

### 1.1 模块边界

| 本模块负责 | 本模块不负责 |
|-----------|------------|
| 饮食输入解析与结构化 | 健康计划制定（plan_service） |
| 营养数据查询与计算 | 饮食建议生成（suggestion_service） |
| 饮食记录持久化 | 食物图片存储（asset_service） |
| 摄入数据汇总统计 | 用户偏好管理（memory_service） |

---

## 2. API 端点

所有端点必须遵循 `api-design.md` 的统一响应格式和错误码规范。

### 2.1 端点总览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/diet/records` | 创建饮食记录（文本/拍照输入） | 必须 |
| GET | `/api/v1/diet/records` | 查询饮食记录列表（日期范围过滤） | 必须 |
| GET | `/api/v1/diet/records/{id}` | 查询单条饮食记录详情 | 必须 |
| PUT | `/api/v1/diet/records/{id}` | 更新饮食记录 | 必须 |
| DELETE | `/api/v1/diet/records/{id}` | 删除饮食记录（软删除） | 必须 |
| POST | `/api/v1/diet/parse` | AI 解析（仅解析不保存） | 必须 |
| GET | `/api/v1/diet/daily-summary` | 每日营养摄入汇总 | 必须 |
| GET | `/api/v1/diet/weekly-summary` | 每周营养摄入汇总 | 必须 |

### 2.2 端点详细定义

#### POST /api/v1/diet/records

创建饮食记录。必须提供 `input_text` 或 `image_url` 中的至少一个。

- 请求体：`DietRecordCreate`
- 响应体：`DietRecordResponse`
- 状态码：201 Created
- 流程：接收输入 → AI 解析 → 营养查询 → 保存记录 → 触发记忆提取 → 返回

#### GET /api/v1/diet/records

查询饮食记录列表，支持日期范围过滤和分页。

- 查询参数：`start_date` (date, 必须), `end_date` (date, 可选, 默认=start_date), `meal_type` (MealType, 可选), `page` (int, 默认=1), `page_size` (int, 默认=20, 最大=50)
- 响应体：分页列表 `list[DietRecordResponse]`
- 排序：按 `date` 降序，同日按 `meal_type` 排序（breakfast → lunch → dinner → snack）

#### GET /api/v1/diet/records/{id}

查询单条饮食记录详情。

- 路径参数：`id` (UUID)
- 响应体：`DietRecordResponse`
- 错误：404 `DIET_RECORD_NOT_FOUND`

#### PUT /api/v1/diet/records/{id}

更新饮食记录。支持修改餐次、食物列表、份量等。

- 路径参数：`id` (UUID)
- 请求体：`DietRecordUpdate`
- 响应体：`DietRecordResponse`
- 约束：禁止更新已软删除的记录

#### DELETE /api/v1/diet/records/{id}

软删除饮食记录，设置 `deleted_at` 时间戳。

- 路径参数：`id` (UUID)
- 响应体：`{"data": null, "message": "删除成功"}`
- 幂等：重复删除返回 200，不报错

#### POST /api/v1/diet/parse

仅执行 AI 解析，不保存记录。用于前端预览解析结果、用户确认前的展示。

- 请求体：`DietParseRequest`（与 `DietRecordCreate` 相同结构）
- 响应体：`ParseResult`
- 说明：此端点不触发记忆提取，不写入数据库

#### GET /api/v1/diet/daily-summary

查询指定日期的营养摄入汇总。

- 查询参数：`date` (date, 必须)
- 响应体：`DailySummary`

#### GET /api/v1/diet/weekly-summary

查询指定周的营养摄入汇总。

- 查询参数：`start_date` (date, 必须, 必须是周一)
- 响应体：`WeeklySummary`

---

## 3. 数据模型

所有模型使用 Pydantic v2 定义。必须遵循 `overview.md` 的类型安全原则，禁止裸 dict 传递。

### 3.1 枚举类型

```python
from enum import Enum

class MealType(str, Enum):
    """餐次类型"""
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"

class DataSource(str, Enum):
    """营养数据来源"""
    database = "database"      # 本地知识库命中
    api = "api"                # 第三方 API（V2）
    llm_estimate = "llm_estimate"  # LLM 估算
```

### 3.2 请求模型

```python
from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field

class DietRecordCreate(BaseModel):
    """创建饮食记录的请求体。input_text 和 image_url 至少提供一个。"""
    input_text: str | None = Field(None, max_length=500, description="自然语言饮食描述")
    image_url: str | None = Field(None, description="食物照片 URL")
    meal_type: MealType | None = Field(None, description="餐次，不传则由 AI 根据时间推断")
    date: date = Field(default_factory=date.today, description="记录日期，默认今天")

    @model_validator(mode="after")
    def check_input(self) -> "DietRecordCreate":
        if not self.input_text and not self.image_url:
            raise ValueError("input_text 和 image_url 至少提供一个")
        return self

class DietRecordUpdate(BaseModel):
    """更新饮食记录的请求体。只传需要修改的字段。"""
    meal_type: MealType | None = None
    date: date | None = None
    foods: list["FoodItemUpdate"] | None = None

class FoodItemUpdate(BaseModel):
    """更新单个食物项"""
    id: UUID | None = Field(None, description="已有食物项 ID，新增时不传")
    name: str = Field(..., max_length=100)
    amount: float = Field(..., gt=0)
    unit: str = Field(..., max_length=20)
    cooking_method: str | None = Field(None, max_length=50)
```

### 3.3 响应模型

```python
from datetime import datetime

class FoodItemResponse(BaseModel):
    """单个食物项的响应"""
    id: UUID
    name: str
    amount: float                          # 标准化后的克数
    unit: str                              # 标准化单位（g/ml）
    cooking_method: str | None = None      # 烹饪方式
    calories: float                        # 热量 kcal
    protein: float                         # 蛋白质 g
    fat: float                             # 脂肪 g
    carbs: float                           # 碳水化合物 g
    fiber: float | None = None             # 膳食纤维 g
    sodium: float | None = None            # 钠 mg
    data_source: DataSource                # 营养数据来源

class NutritionSummary(BaseModel):
    """营养汇总"""
    total_calories: float                  # 总热量 kcal
    total_protein: float                   # 总蛋白质 g
    total_fat: float                       # 总脂肪 g
    total_carbs: float                     # 总碳水 g
    total_fiber: float | None = None       # 总膳食纤维 g

class DietRecordResponse(BaseModel):
    """饮食记录响应"""
    id: UUID
    meal_type: MealType
    date: date
    input_text: str | None = None
    foods: list[FoodItemResponse]
    nutrition_summary: NutritionSummary
    created_at: datetime
    updated_at: datetime
```

### 3.4 AI 解析模型

```python
class ParsedFood(BaseModel):
    """LLM 解析出的单个食物"""
    name: str                              # 食物名称
    amount: float                          # 份量数值
    unit: str                              # 原始单位（碗、个、份等）
    amount_grams: float                    # 标准化克数
    cooking_method: str | None = None      # 烹饪方式
    calories: float                        # 热量 kcal
    protein: float                         # 蛋白质 g
    fat: float                             # 脂肪 g
    carbs: float                           # 碳水 g
    fiber: float | None = None
    sodium: float | None = None
    data_source: DataSource                # 营养数据来源

class ParseResult(BaseModel):
    """AI 解析结果"""
    foods: list[ParsedFood]
    meal_type: MealType | None = None      # AI 推断的餐次，可能为 None
    confidence: float = Field(..., ge=0, le=1)  # 整体解析置信度

class DailySummary(BaseModel):
    """每日营养汇总"""
    date: date
    meals: dict[MealType, list[DietRecordResponse]]
    total_nutrition: NutritionSummary
    target_nutrition: NutritionSummary | None = None  # 来自健康计划
    completion_rate: dict[str, float]      # {"calories": 0.85, "protein": 0.72, ...}

class WeeklySummary(BaseModel):
    """每周营养汇总"""
    start_date: date
    end_date: date
    daily_summaries: list[DailySummary]
    avg_nutrition: NutritionSummary        # 日均摄入
    total_nutrition: NutritionSummary      # 周总摄入
```

---

## 4. AI 解析流程（diet_agent）

### 4.0 架构约定

**所有 LLM 推理必须通过 `diet_agent` (LangGraph) 发起**，禁止在 `DietService` 内直接调用 LLM。Service 层只负责 DB CRUD 和营养计算，作为 Agent 的 Tool 被调用。详见 `00-architecture/agents.md`。

### 4.1 文本解析流程（diet_agent 文本分支）

```
用户输入 (input_text, image_url, meal_type, date)
    ↓
[API Router] 调用 diet_agent.ainvoke(input)
    ↓
[Graph 入口节点] route_input
    - input_text 非空 → 走 parse_text
    - image_url 非空 → 走 parse_photo_mock
    ↓
[Node: parse_text]  LLM 结构化解析（qwen-plus + with_structured_output(ParseResult)）
    ↓
[Node: standardize_units]  模糊单位标准化（参照 4.3 换算表，代码确定性逻辑）
    ↓
[Node: enrich_nutrition]  三层营养查询
    ├── Tool: search_food (RagService, 精确 + 别名 + 语义)
    ├── 命中率 < 100% 的食物 → LLM 估算兜底节点
    └── 聚合为 ParsedFood[]
    ↓
[Node: infer_meal_type]   （若 meal_type 为 None）按时间推断
    ↓
[Conditional: save_or_parse_only]
    - mode == "parse" → END（返回 ParseResult）
    - mode == "create" → 继续
    ↓
[Node: save_record]  Tool: DietService.create_record_from_parsed(...)
    ↓
[Node: trigger_memory]  异步触发 memory_agent.ainvoke(trigger="diet_record", ...)
    ↓
END (返回 DietRecordResponse 或 ParseResult)
```

### 4.2 拍照识别分支（V1 Mock）

Mock 也在 `diet_agent` 的节点中实现，不在 service 里。接口一致，V2 切换到多模态 LLM 时只改节点内部：

```
parse_photo_mock 节点
    ↓
返回固定 ParseResult：米饭 200g + 未知菜品 150g，confidence=0.3
    ↓
进入 enrich_nutrition（与文本分支同一路径）
```

### 4.3 模糊单位换算表

必须内置以下常见换算规则，standardize_units 节点中代码确定性应用，同时作为 `parse_text` 节点的 prompt 参考：

| 食物类别 | 单位 | 标准克数 |
|---------|------|---------|
| 米饭 | 一碗 | 200g |
| 面条/粉 | 一碗 | 300g |
| 鸡蛋 | 一个 | 50g |
| 苹果/梨 | 一个 | 200g |
| 牛奶 | 一杯 | 250ml |
| 通用菜品 | 一份 | 150g |
| 通用菜品 | 一盘 | 300g |
| 通用菜品 | 半份 | 75g |
| 饮料 | 一杯 | 300ml |
| 面包 | 一片 | 40g |

### 4.4 LLM 解析节点设计要点

- 使用 `ChatOpenAI().with_structured_output(ParseResult)`，禁止自由文本输出
- Prompt（`app/agents/prompts/diet_parse.py`）包含模糊单位换算表和 few-shot 示例
- 必须输出 `confidence` 字段（0-1）
- 餐次推断规则：未明确指定时，按当前时间推断（6-9 点早餐，11-14 点午餐，17-20 点晚餐，其余为加餐）
- 复合食物必须拆分：如 "兰州拉面加个蛋" → ["兰州拉面", "鸡蛋"]

---

## 5. 营养计算逻辑

### 5.1 食物匹配策略

从知识库中匹配食物的优先级：

1. **精确名称匹配**：食物名完全一致
2. **别名匹配**：通过别名表匹配（如 "牛肉面" → "兰州拉面"）
3. **Embedding 语义相似度匹配**：使用 text-embedding-v3 计算相似度，阈值 ≥ 0.85
4. **LLM 估算兜底**：以上均未命中时，由 LLM 直接估算营养数据，`data_source` 标记为 `llm_estimate`

### 5.2 单项营养计算

```python
# 计算公式：每 100g 营养值 × 实际克数 / 100
def calculate_nutrition(per_100g: NutritionPer100g, amount_grams: float) -> dict:
    """
    per_100g: 知识库中存储的每 100g 营养数据
    amount_grams: 标准化后的实际克数
    """
    ratio = amount_grams / 100.0
    return {
        "calories": round(per_100g.calories * ratio, 1),
        "protein": round(per_100g.protein * ratio, 1),
        "fat": round(per_100g.fat * ratio, 1),
        "carbs": round(per_100g.carbs * ratio, 1),
        "fiber": round(per_100g.fiber * ratio, 1) if per_100g.fiber else None,
        "sodium": round(per_100g.sodium * ratio, 1) if per_100g.sodium else None,
    }
```

### 5.3 汇总计算

```python
def calculate_summary(foods: list[FoodItemResponse]) -> NutritionSummary:
    """汇总所有食物的营养数据"""
    return NutritionSummary(
        total_calories=round(sum(f.calories for f in foods), 1),
        total_protein=round(sum(f.protein for f in foods), 1),
        total_fat=round(sum(f.fat for f in foods), 1),
        total_carbs=round(sum(f.carbs for f in foods), 1),
        total_fiber=round(sum(f.fiber for f in foods if f.fiber), 1) or None,
    )
```

### 5.4 目标对比

当用户存在活跃的健康计划时，`DailySummary.completion_rate` 按以下方式计算：

```python
completion_rate = {
    "calories": round(actual.total_calories / target.total_calories, 2),
    "protein": round(actual.total_protein / target.total_protein, 2),
    "fat": round(actual.total_fat / target.total_fat, 2),
    "carbs": round(actual.total_carbs / target.total_carbs, 2),
}
# 值域 0.0 ~ 无上限（可能超标），前端负责展示逻辑
```

无活跃计划时，`target_nutrition` 为 `None`，`completion_rate` 为空 dict。

---

## 6. Agent 与 Service 接口

### 6.0 分层

- **`diet_agent`（`app/agents/diet/graph.py`）**：承载所有 AI 解析流程（文本/图片解析、营养补全、餐次推断）。API 层 `POST /diet/records`、`POST /diet/parse` 直接调用 Agent。
- **`DietService`（`app/services/diet_service.py`）**：纯 DB CRUD + 纯算法（营养汇总、完成率），作为 Agent 的 Tool 和非 AI 路径（查询、汇总）的直接依赖。

### 6.1 DietAgent State & Tool 定义

```python
# app/agents/diet/state.py
from typing import TypedDict, Literal

class DietState(TypedDict, total=False):
    # 输入
    user_id: str
    mode: Literal["parse", "create"]        # parse 只解析不保存；create 解析后保存
    input_text: str | None
    image_url: str | None
    meal_type: str | None                    # 可选，不传由 AI 推断
    date: str                                # ISO date

    # 中间态
    raw_parsed: dict | None                  # LLM 原始输出
    parsed_foods: list[dict]                 # standardize + enrich 后
    confidence: float

    # 输出
    final_parse_result: dict | None          # ParseResult.model_dump()
    final_record: dict | None                # DietRecordResponse.model_dump()
```

```python
# app/agents/diet/tools.py（节选）
@tool
async def search_food_tool(name: str) -> list[dict]:
    """按名称在食物知识库中搜索，返回 Top 5 营养候选。"""

@tool
async def save_diet_record_tool(meal_type: str, foods: list[dict], date: str) -> dict:
    """将解析结果持久化为饮食记录。返回记录 id 和营养汇总。"""
```

### 6.2 DietService（纯 CRUD + 算法）

```python
class DietService:
    """饮食记录 CRUD + 营养计算。不包含 LLM 调用。"""

    def __init__(self, diet_repo: DietRepository, rag_service: RagService, plan_service: PlanService):
        ...

    async def create_record_from_parsed(
        self, user_id: UUID, meal_type: MealType, foods: list[ParsedFood], record_date: date
    ) -> DietRecordResponse:
        """由 diet_agent 的 save_record 节点调用，接收已完成营养补全的食物列表。"""
        ...

    async def get_record(self, user_id: UUID, record_id: UUID) -> DietRecordResponse: ...

    async def list_records(
        self, user_id: UUID, start_date: date, end_date: date | None = None,
        meal_type: MealType | None = None, page: int = 1, page_size: int = 20,
    ) -> tuple[list[DietRecordResponse], int]: ...

    async def update_record(
        self, user_id: UUID, record_id: UUID, data: DietRecordUpdate
    ) -> DietRecordResponse:
        """更新食物时重新计算 nutrition_summary；若 food.name 有变动，通过 RagService 重查营养。"""

    async def delete_record(self, user_id: UUID, record_id: UUID) -> None:
        """软删除，设置 deleted_at = now()"""

    async def get_daily_summary(self, user_id: UUID, target_date: date) -> DailySummary: ...
    async def get_weekly_summary(self, user_id: UUID, start_date: date) -> WeeklySummary: ...

    # 内部辅助（纯算法）
    async def _lookup_nutrition(
        self, food_name: str, amount_grams: float
    ) -> tuple[dict, DataSource]:
        """RAG 优先，未命中返回 (None, llm_estimate) — LLM 估算由 agent 节点处理。"""

    def _calculate_summary(self, foods: list[FoodItemResponse]) -> NutritionSummary: ...
```

**关键变更**：

- 删除 `parse_input` / `_parse_text` / `_parse_photo_mock` 方法。这些流程全部迁移到 `diet_agent`。
- 删除 `LLMService` 的注入，Service 不再依赖 LLM。
- 新增 `create_record_from_parsed`，接收 Agent 已处理好的结构化数据。

---

## 7. 模块依赖

### 7.1 本模块依赖

| 依赖对象 | 用途 | 调用方式 |
|---------|------|---------|
| `diet_agent` | 文本/图片解析、营养补全、餐次推断 | API Router 直接 `agent.ainvoke(...)` |
| `rag_service` | 食物营养知识库检索 | Agent Tool / Service 共用 |
| `memory_agent` | 饮食记录后异步提取饮食偏好 | Agent 末尾节点通过 `asyncio.create_task` 触发 |
| `plan_service` | 查询活跃计划的营养目标，用于完成率计算 | Service 层注入 |

**不再直接依赖 `llm_service` / `LLMClient`**，全部 LLM 调用在 `diet_agent` 内通过 `get_chat_model()` 发起。

### 7.2 被其他模块依赖

| 依赖方 | 用途 |
|--------|------|
| `plan_service` | 查询饮食记录，跟踪计划执行情况 |
| `suggestion_service` | 分析饮食数据，生成个性化建议 |
| `chat_service` | 对话中引用饮食记录（"我今天吃了什么"） |

---

## 8. Mock 策略

V1 阶段以下功能使用 mock 实现，API 接口必须与未来真实实现保持一致，切换时只改 service 层。

| 功能 | V1 实现 | V2 计划 |
|------|---------|---------|
| 拍照识别 | `_parse_photo_mock` 返回固定 ParseResult，confidence=0.3 | 接入多模态 LLM（qwen-vl） |
| 外部食物 API | 跳过，直接走 LLM 估算兜底 | 接入 FatSecret / Open Food Facts |

### 8.1 Mock 实现要求

- Mock 节点（`diet_agent` 的 `parse_photo_mock`）必须产生与真实节点一致的 `DietState` 字段
- Mock 返回的数据结构必须符合 Pydantic 模型校验
- Mock 数据必须标记 `data_source = DataSource.llm_estimate`
- 禁止在 router 层或 service 层判断是否 mock，mock 逻辑只存在于 Agent 节点内部

---

## 9. 实现约束

### 9.1 数据约束

| 约束 | 规则 | 校验位置 |
|------|------|---------|
| 单条记录食物上限 | 最多 20 个食物项 | Pydantic validator |
| 营养值非负 | calories/protein/fat/carbs 必须 ≥ 0 | Pydantic Field(ge=0) |
| 日期不能是未来 | `date <= today` | Pydantic validator |
| 软删除 | 删除操作设置 `deleted_at` 时间戳，禁止物理删除 | Repository 层 |
| 用户隔离 | 所有查询必须带 `user_id` 过滤，禁止跨用户访问 | Service 层 |

### 9.2 性能约束

- 文本解析响应时间：≤ 3 秒（含 LLM 调用 + RAG 检索）
- 记录列表查询：≤ 200ms
- 每日汇总查询：≤ 500ms

### 9.3 校验规则示例

```python
from pydantic import field_validator

class DietRecordCreate(BaseModel):
    # ... 字段定义同 3.2 ...

    @field_validator("date")
    @classmethod
    def date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("日期不能是未来日期")
        return v

class FoodItemUpdate(BaseModel):
    # ... 字段定义同 3.2 ...

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("份量必须大于 0")
        return v
```

### 9.4 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `DIET_RECORD_NOT_FOUND` | 404 | 饮食记录不存在或已删除 |
| `DIET_PARSE_FAILED` | 422 | AI 解析失败（LLM 返回无法解析的结果） |
| `DIET_RECORD_LIMIT_EXCEEDED` | 422 | 单条记录食物项超过 20 个 |
| `DIET_INVALID_DATE` | 422 | 日期为未来日期 |
| `DIET_RECORD_DELETED` | 409 | 尝试更新已软删除的记录 |
