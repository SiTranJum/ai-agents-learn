# 计划系统模块 (Plan System)

> 计划系统是健康管家的 AI 驱动模块，负责通过对话式交互帮用户制定个性化健康计划，自动追踪执行情况，并基于规则检测 + LLM 建议触发计划修改。支持减重、营养调整、习惯养成三种计划类型，每个用户同时只能有一个活跃计划。
>
> 实现依据：`docs/prd/v1/07-plan-system.md`，`docs/specs/backend/00-architecture/overview.md`，`docs/specs/backend/00-architecture/api-design.md`

---

## 1. 模块职责

本模块承担以下核心职责：

- **对话式计划创建**：通过 4 步 AI 对话（目标确认 → 现状分析 → 方案制定 → 确认启动）生成个性化健康计划
- **三种计划类型**：减重计划（weight_loss）、营养调整计划（nutrition_adjustment）、习惯养成计划（habit_formation）
- **执行追踪**：自动关联每日饮食记录到活跃计划，计算营养达标率和连续达标天数
- **计划修改**：规则检测（连续未达标、热量过低、目标提前达成、计划过期）+ LLM 建议，用户确认后生效
- **计划终止与状态管理**：支持主动终止、自然完成、软删除

### 1.1 模块边界

| 本模块负责 | 本模块不负责 |
|-----------|------------|
| 计划创建（AI 对话生成） | 饮食记录管理（diet_service） |
| 执行追踪与达标计算 | 用户健康档案管理（user_service） |
| 计划修改建议与执行 | AI 记忆存取（memory_service） |
| 计划状态流转（活跃/完成/终止） | 主动建议推送（suggestion_service） |
| BMR 计算与安全校验 | 食物营养数据查询（diet_service） |

---

## 2. API 端点

所有端点必须遵循 `api-design.md` 的统一响应格式和错误码规范。

### 2.1 端点总览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/plans` | 创建计划（AI 根据用户目标生成） | 必须 |
| GET | `/api/v1/plans` | 查询计划列表 | 必须 |
| GET | `/api/v1/plans/{id}` | 查询计划详情 | 必须 |
| PUT | `/api/v1/plans/{id}` | 更新计划 | 必须 |
| DELETE | `/api/v1/plans/{id}` | 终止计划（软删除） | 必须 |
| POST | `/api/v1/plans/{id}/check-ins` | 每日打卡 | 必须 |
| GET | `/api/v1/plans/{id}/progress` | 查询进度统计 | 必须 |
| GET | `/api/v1/plans/{id}/execution` | 查询执行记录列表 | 必须 |

### 2.2 端点详细定义

#### POST /api/v1/plans

创建健康计划。AI 根据用户目标描述、健康档案和近期数据生成个性化计划。

- 请求体：`PlanCreate`
- 响应体：`PlanResponse`
- 状态码：201 Created
- 流程：接收目标 → AI 4 步对话生成 → 安全校验 → 保存计划 → 返回
- 错误：409 `PLAN_ALREADY_ACTIVE`（已有活跃计划时）

#### GET /api/v1/plans

查询计划列表，支持状态过滤和分页。

- 查询参数：`status` (PlanStatus, 可选), `page` (int, 默认=1), `page_size` (int, 默认=20, 最大=50)
- 响应体：分页列表 `list[PlanResponse]`
- 排序：按 `created_at` 降序

#### GET /api/v1/plans/{id}

查询单个计划详情，包含目标、任务列表和当前状态。

- 路径参数：`id` (UUID)
- 响应体：`PlanResponse`
- 错误：404 `PLAN_NOT_FOUND`

#### PUT /api/v1/plans/{id}

更新计划。支持修改目标值、目标日期、任务列表。必须经过安全校验。

- 路径参数：`id` (UUID)
- 请求体：`PlanUpdate`
- 响应体：`PlanResponse`
- 约束：禁止更新已终止或已完成的计划，返回 400 `PLAN_NOT_MODIFIABLE`

#### DELETE /api/v1/plans/{id}

终止计划（软删除），设置状态为 `terminated`，记录 `terminated_at` 时间戳。

- 路径参数：`id` (UUID)
- 请求体：`{"reason": "用户主动终止"}` (可选)
- 响应体：`{"data": null, "message": "计划已终止"}`
- 幂等：重复终止返回 200，不报错

#### POST /api/v1/plans/{id}/check-ins

每日打卡，用于习惯养成计划的手动打卡或任务完成确认。

- 路径参数：`id` (UUID)
- 请求体：`CheckInCreate`
- 响应体：`CheckInResponse`
- 状态码：201 Created
- 约束：同一 `date` + `task_id` 组合禁止重复打卡，返回 409 `CHECK_IN_DUPLICATE`

#### GET /api/v1/plans/{id}/progress

查询计划进度统计，包含达标率、连续达标天数、每日执行概览。

- 路径参数：`id` (UUID)
- 响应体：`PlanProgress`

#### GET /api/v1/plans/{id}/execution

查询执行记录列表，支持日期范围过滤和分页。

- 路径参数：`id` (UUID)
- 查询参数：`start_date` (date, 可选), `end_date` (date, 可选), `status` (ExecutionStatus, 可选), `page` (int, 默认=1), `page_size` (int, 默认=20, 最大=50)
- 响应体：分页列表 `list[DailyExecution]`
- 排序：按 `date` 降序

---

## 3. 数据模型

所有模型使用 Pydantic v2 定义。必须遵循 `overview.md` 的类型安全原则，禁止裸 dict 传递。

### 3.1 枚举类型

```python
from enum import Enum

class PlanType(str, Enum):
    """计划类型"""
    weight_loss = "weight_loss"                    # 减重计划
    nutrition_adjustment = "nutrition_adjustment"    # 营养调整计划
    habit_formation = "habit_formation"              # 习惯养成计划

class PlanStatus(str, Enum):
    """计划状态"""
    active = "active"            # 活跃中
    completed = "completed"      # 已完成
    terminated = "terminated"    # 已终止

class ExecutionStatus(str, Enum):
    """每日执行状态"""
    on_track = "on_track"        # 达标：偏离 ≤ 10%
    deviation = "deviation"      # 偏离：偏离 10-20%
    missed = "missed"            # 未达标：偏离 > 20% 或未记录
```

### 3.2 请求模型

```python
from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field

class PlanCreate(BaseModel):
    """创建计划的请求体。goal_description 必须提供，plan_type 可选（不传则由 AI 推断）。"""
    goal_description: str = Field(..., max_length=500, description="自然语言目标描述，如'我想减到65kg'")
    plan_type: PlanType | None = Field(None, description="计划类型，不传则由 AI 根据目标推断")

class PlanUpdate(BaseModel):
    """更新计划的请求体。只传需要修改的字段。"""
    daily_calories: int | None = Field(None, gt=0, description="每日热量目标 kcal")
    protein_target: float | None = Field(None, gt=0, description="蛋白质目标 g")
    fat_target: float | None = Field(None, gt=0, description="脂肪目标 g")
    carbs_target: float | None = Field(None, gt=0, description="碳水目标 g")
    weight_target: float | None = Field(None, gt=0, description="目标体重 kg")
    target_date: date | None = Field(None, description="目标日期")
    tasks: list["PlanTaskUpdate"] | None = Field(None, description="任务列表更新")

class PlanTaskUpdate(BaseModel):
    """更新单个计划任务"""
    id: UUID | None = Field(None, description="已有任务 ID，新增时不传")
    description: str = Field(..., max_length=200, description="任务描述")
    frequency: str = Field(..., max_length=50, description="频率，如'每天'、'每周3次'")
    time_period: str | None = Field(None, max_length=50, description="时间段，如'早餐'、'晚上'")

class CheckInCreate(BaseModel):
    """每日打卡请求体"""
    date: date = Field(default_factory=date.today, description="打卡日期，默认今天")
    task_id: UUID | None = Field(None, description="关联任务 ID，不传则为整体打卡")
    completed: bool = Field(..., description="是否完成")
    note: str | None = Field(None, max_length=500, description="打卡备注")
```

### 3.3 响应模型

```python
from datetime import datetime

class PlanTargets(BaseModel):
    """计划目标值"""
    daily_calories: int | None = Field(None, description="每日热量目标 kcal")
    protein_target: float | None = Field(None, description="蛋白质目标 g")
    fat_target: float | None = Field(None, description="脂肪目标 g")
    carbs_target: float | None = Field(None, description="碳水目标 g")
    weight_target: float | None = Field(None, description="目标体重 kg")

class PlanTask(BaseModel):
    """计划任务项"""
    id: UUID
    description: str                               # 任务描述
    frequency: str                                 # 频率，如"每天"、"每周3次"
    time_period: str | None = None                 # 时间段，如"早餐"、"晚上"

class PlanResponse(BaseModel):
    """计划响应"""
    id: UUID
    name: str                                      # 计划名称，AI 生成
    plan_type: PlanType
    status: PlanStatus
    start_date: date
    target_date: date
    targets: PlanTargets
    tasks: list[PlanTask]
    created_at: datetime
    updated_at: datetime

class CheckInResponse(BaseModel):
    """打卡响应"""
    id: UUID
    plan_id: UUID
    task_id: UUID | None = None
    date: date
    completed: bool
    note: str | None = None
    created_at: datetime
```

### 3.4 进度与执行模型

```python
class DailyExecution(BaseModel):
    """每日执行记录"""
    date: date
    calories_consumed: float                       # 实际摄入热量 kcal
    calories_target: float                         # 目标热量 kcal
    protein: float                                 # 实际蛋白质 g
    fat: float                                     # 实际脂肪 g
    carbs: float                                   # 实际碳水 g
    status: ExecutionStatus                        # 达标状态

class PlanProgress(BaseModel):
    """计划进度统计"""
    plan_id: UUID
    total_days: int                                # 计划总天数
    elapsed_days: int                              # 已过天数
    compliance_rate: float = Field(..., ge=0, le=1, description="达标率，0-1")
    streak_days: int = Field(..., ge=0, description="连续达标天数")
    daily_records: list[DailyExecution]            # 每日执行记录列表
```

---

## 4. AI 创建流程（plan_agent）

**所有 LLM 推理通过 `plan_agent` (LangGraph) 发起**，`PlanService` 不做 LLM 编排（见 `00-architecture/agents.md`）。

### 4.1 Agent 总览

```
POST /api/v1/plans
    ↓
[API Router] 先校验活跃计划唯一性（PlanService.has_active_plan）
    ↓
[plan_agent.ainvoke] 输入 {user_id, goal_description, plan_type?}
    ↓
[Node: confirm_goal]      LLM 读取 profile + 记忆确认目标合理性
    Tool: UserService.get_full_profile / MemoryService.recall_memories
    ↓
[Node: analyze_status]    LLM 基于近 7 天饮食/身体数据生成当前状况分析
    Tool: DietService.get_weekly_summary / BodyService.get_trends
    ↓
[Node: draft_plan]        LLM 生成 PlanTargets + PlanTask 列表（structured output）
    ↓
[Node: safety_validate]   代码确定性：BMR / 减重速度 / 周期校验（Tool: PlanService.calculate_bmr / safety_check）
    ├── 校验不通过 → 回到 draft_plan 重新生成（最多 2 次）
    └── 通过 → 继续
    ↓
[Node: persist_plan]      Tool: PlanService.create_plan_from_draft(...)
    ↓
END (返回 PlanResponse)
```

### 4.2 各步骤规范

| 步骤 | 输入 | 输出 | 约束 |
|------|------|------|------|
| confirm_goal | goal_description + profile + memories | 目标合理性评估 | 必须引用用户档案数据 |
| analyze_status | 近 7 天饮食 + 身体数据 | 现状分析 + 关键问题 | 基于真实数据，禁止编造 |
| draft_plan | 前两步结果 + user_preferences | PlanTargets + PlanTask 列表 | 通过安全校验 |
| safety_validate | draft + profile | 通过/拒绝 + 拒绝原因 | BMR / 减重速度 / 周期全部通过 |
| persist_plan | 已校验的 draft | 持久化结果 | 无活跃冲突（API 层已校验） |

### 4.3 计划修改建议（plan_agent 的子图）

`plan_agent` 额外暴露 `modification_subgraph`，由 `PlanService.run_modification_rules` 触发：

```
规则命中（连续未达标 / 热量过低 / 目标提前达成 / 计划过期）
    ↓
[Node: analyze_deviation]  LLM 分析当前执行 + 历史数据
    ↓
[Node: suggest_modification]  LLM 生成具体修改建议（structured output）
    ↓
返回 建议列表（不自动修改，由用户确认后调 PUT /plans/{id}）
```

---

## 5. 执行追踪逻辑

### 5.1 自动关联机制

用户记录饮食后，系统必须自动将当日营养数据关联到活跃计划：

1. 用户通过 `diet_service` 创建饮食记录
2. `diet_service` 触发事件通知 `plan_service`
3. `plan_service` 查询当日所有饮食记录，汇总营养数据
4. 与计划目标对比，生成或更新当日 `DailyExecution` 记录

### 5.2 达标判定规则

必须按以下规则判定每日执行状态：

| 状态 | 条件 | 说明 |
|------|------|------|
| `on_track` | 热量偏离 ≤ 10%，营养素比例合理 | 达标 |
| `deviation` | 热量偏离 10-20%，或某项营养素偏离较大 | 偏离 |
| `missed` | 热量偏离 > 20%，或当日未记录饮食 | 未达标 |

```python
def calculate_execution_status(
    consumed: float, target: float
) -> ExecutionStatus:
    """
    根据实际摄入与目标的偏离程度判定执行状态。
    consumed: 实际摄入热量 kcal
    target: 目标热量 kcal
    """
    if target == 0:
        return ExecutionStatus.missed

    deviation_rate = abs(consumed - target) / target

    if deviation_rate <= 0.10:
        return ExecutionStatus.on_track
    elif deviation_rate <= 0.20:
        return ExecutionStatus.deviation
    else:
        return ExecutionStatus.missed
```

### 5.3 连续达标天数计算

`streak_days` 从最近一天向前回溯，遇到非 `on_track` 状态即中断。未记录饮食的日期视为 `missed`，中断连续计数。

---

## 6. 计划修改触发规则

### 6.1 规则检测

系统必须在每日执行记录更新时运行以下规则检测，命中时生成修改建议（不自动修改，必须用户确认）：

| 规则 | 触发条件 | 建议动作 |
|------|---------|---------|
| 连续未达标 | 连续 5 天 `missed` | 建议降低目标或调整计划 |
| 热量过低 | 连续 3 天实际摄入 < BMR | 健康风险警告，建议提高热量目标 |
| 目标提前达成 | 当前体重 ≤ 目标体重（减重计划） | 建议设定新目标或完成计划 |
| 计划过期 | 当前日期 > target_date | 提示续期或终止 |

### 6.2 修改流程

```
规则检测命中 / 用户主动请求修改
    │
    ▼
AI 分析当前执行情况 + 历史数据
    │
    ▼
AI 生成修改建议（具体数值调整）
    │
    ▼
用户确认 / 调整 / 拒绝
    │
    ▼
确认后更新计划（调用 PUT /api/v1/plans/{id}）
```

### 6.3 BMR 计算

必须使用 Mifflin-St Jeor 公式计算基础代谢率：

```python
def calculate_bmr(
    weight_kg: float, height_cm: float, age: int, gender: str
) -> float:
    """
    Mifflin-St Jeor 公式计算 BMR。
    gender: "male" 或 "female"
    返回值：BMR (kcal/day)
    """
    if gender == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
```

---

## 7. Service 接口（纯 CRUD + 算法）

`PlanService` **不做 LLM 编排**，职责限定为 DB CRUD、执行追踪、BMR 等算法。LLM 创建/修改流程由 `plan_agent` 承担。

```python
from uuid import UUID
from datetime import date

class PlanService:
    """计划 CRUD + BMR + 执行追踪。不含 LLM 调用。"""

    def __init__(
        self, plan_repo: PlanRepository,
        user_service: UserService,
        diet_service: DietService,
    ): ...

    async def has_active_plan(self, user_id: UUID) -> bool:
        """API 层在创建前检查。"""

    async def create_plan_from_draft(
        self, user_id: UUID, draft: PlanDraft
    ) -> PlanResponse:
        """由 plan_agent 的 persist_plan 节点调用，接收已完成安全校验的草案。"""

    async def get_plan(self, user_id: UUID, plan_id: UUID) -> PlanResponse: ...

    async def list_plans(
        self, user_id: UUID, status: PlanStatus | None = None,
        page: int = 1, page_size: int = 20
    ) -> list[PlanResponse]: ...

    async def update_plan(
        self, user_id: UUID, plan_id: UUID, data: PlanUpdate
    ) -> PlanResponse:
        """直接 CRUD 更新。更新后重新跑 safety_check()。"""

    async def terminate_plan(
        self, user_id: UUID, plan_id: UUID, reason: str | None = None
    ) -> None: ...

    async def create_check_in(
        self, user_id: UUID, plan_id: UUID, data: CheckInCreate
    ) -> CheckInResponse: ...

    async def get_progress(self, user_id: UUID, plan_id: UUID) -> PlanProgress: ...

    async def list_execution_records(
        self, user_id: UUID, plan_id: UUID,
        start_date: date | None = None, end_date: date | None = None,
        status: ExecutionStatus | None = None,
        page: int = 1, page_size: int = 20
    ) -> list[DailyExecution]: ...

    async def on_diet_record_created(self, user_id: UUID, record_date: date) -> None:
        """饮食记录创建后更新 DailyExecution，若规则命中则调用 plan_agent 的 modification_subgraph。"""

    async def run_modification_rules(self, user_id: UUID, plan_id: UUID) -> list[str]:
        """运行修改触发规则，命中时通过 plan_agent 获取建议列表。"""

    # 纯算法
    def calculate_bmr(self, weight_kg: float, height_cm: float, age: int, gender: str) -> float: ...
    def calculate_execution_status(self, consumed: float, target: float) -> ExecutionStatus: ...
    def safety_check(self, draft: PlanDraft, profile: HealthProfile) -> list[str]:
        """返回违规原因列表，空列表代表通过。plan_agent 的 safety_validate 节点也调用本方法。"""
```

## 8. 模块依赖

### 8.1 本模块依赖

| 依赖对象 | 用途 |
|---------|------|
| `plan_agent` | 4 步创建、修改建议生成（API 层 / service 层触发） |
| `user_service` | 读取用户健康档案用于 BMR 计算 |
| `diet_service` | 查询每日营养摄入数据 |
| `memory_service` | 召回用户饮食偏好（在 plan_agent 内作为 Tool） |

### 8.2 被依赖

| 下游模块 | 用途 |
|---------|------|
| `suggestion_service` | 读取计划进度数据，生成主动建议 |


---

## 9. 实现约束

### 9.1 业务规则

| 规则 | 约束 | 违反时错误码 |
|------|------|------------|
| 活跃计划唯一 | 每个用户同时最多 1 个 active 计划 | 409 `PLAN_ALREADY_ACTIVE` |
| 计划周期 | 最短 1 周，最长 24 周 | 400 `PLAN_DURATION_INVALID` |
| 减重速度 | ≤ 1 kg/周 | 400 `WEIGHT_LOSS_TOO_FAST` |
| 最低热量 | 每日热量目标 ≥ BMR | 400 `CALORIES_BELOW_BMR` |
| 软删除 | 终止的计划必须软删除，禁止物理删除 | — |
| 不可修改状态 | 禁止更新 completed 或 terminated 计划 | 400 `PLAN_NOT_MODIFIABLE` |

### 9.2 安全校验流程

计划创建和更新时，必须按以下顺序执行安全校验：

```
1. 计算用户 BMR（Mifflin-St Jeor 公式）
2. 校验每日热量目标 ≥ BMR → 否则拒绝
3. 校验减重速度 ≤ 1 kg/周 → 否则拒绝
4. 校验计划周期 1-24 周 → 否则拒绝
5. 校验用户无其他 active 计划 → 否则拒绝（仅创建时）
```
