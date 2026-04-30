# 身体数据追踪模块 (Body Tracking)

> 身体数据追踪模块负责体重、围度、睡眠、运动、饮水、排便六类身体数据的记录与管理，提供趋势计算和异常值检测能力，为计划追踪和 AI 建议提供数据支撑。
>
> 实现依据：`docs/prd/v1/04-body-tracking.md`，`docs/specs/backend/00-architecture/overview.md`，`docs/specs/backend/00-architecture/api-design.md`

---

## 1. 模块职责

本模块承担以下核心职责：

- **体重记录与趋势**：记录用户体重数据，计算移动平均线，生成趋势可视化数据
- **围度追踪**：记录腰围、臀围、大腿围、上臂围，支持多维度趋势对比
- **辅助健康记录**：睡眠、运动、饮水、排便四类轻量级健康数据的追加记录
- **趋势计算**：按 7/30/90/365 天周期计算移动平均、最值、变化量等统计指标
- **异常值检测**：新记录偏离历史均值超过 2 个标准差时，返回告警信息（不阻断操作）

### 1.1 模块边界

| 本模块负责 | 本模块不负责 |
|-----------|------------|
| 六类身体数据的 CRUD | 健康计划制定（plan_service） |
| 趋势统计与移动平均计算 | AI 健康建议生成（suggestion_service） |
| 异常值检测与告警 | 用户偏好与记忆管理（memory_service） |
| 最新值聚合查询 | 食物/营养数据管理（diet_service） |

---

## 2. API 端点

所有端点必须遵循 `api-design.md` 的统一响应格式和错误码规范。

### 2.1 端点总览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/body/weight` | 创建体重记录 | 必须 |
| GET | `/api/v1/body/weight` | 查询体重记录列表 | 必须 |
| PUT | `/api/v1/body/weight/{id}` | 更新体重记录 | 必须 |
| DELETE | `/api/v1/body/weight/{id}` | 删除体重记录（软删除） | 必须 |
| POST | `/api/v1/body/circumference` | 创建围度记录 | 必须 |
| GET | `/api/v1/body/circumference` | 查询围度记录列表 | 必须 |
| PUT | `/api/v1/body/circumference/{id}` | 更新围度记录 | 必须 |
| DELETE | `/api/v1/body/circumference/{id}` | 删除围度记录（软删除） | 必须 |
| POST | `/api/v1/body/sleep` | 创建睡眠记录 | 必须 |
| GET | `/api/v1/body/sleep` | 查询睡眠记录列表 | 必须 |
| POST | `/api/v1/body/exercise` | 创建运动记录 | 必须 |
| GET | `/api/v1/body/exercise` | 查询运动记录列表 | 必须 |
| POST | `/api/v1/body/water` | 创建/累加饮水记录 | 必须 |
| GET | `/api/v1/body/water` | 查询饮水记录列表 | 必须 |
| POST | `/api/v1/body/bowel` | 创建排便记录 | 必须 |
| GET | `/api/v1/body/bowel` | 查询排便记录列表 | 必须 |
| GET | `/api/v1/body/trends` | 趋势数据查询 | 必须 |
| GET | `/api/v1/body/latest` | 各类型最新值聚合 | 必须 |

### 2.2 端点详细定义

#### POST `/api/v1/body/weight`

创建体重记录。同一日期允许覆盖（以最新一条为准）。

- 请求体：`WeightRecordCreate`
- 响应：`WeightRecordResponse`（包含异常值告警字段）

#### GET `/api/v1/body/weight`

查询体重记录列表，支持日期范围过滤。

- Query 参数：`start_date`（可选）、`end_date`（可选）、`page`（默认 1）、`page_size`（默认 20）
- 响应：分页列表，按日期降序

#### PUT `/api/v1/body/weight/{id}`

更新指定体重记录。必须校验记录归属当前用户。

#### DELETE `/api/v1/body/weight/{id}`

软删除体重记录。设置 `deleted_at` 时间戳，禁止物理删除。

#### POST `/api/v1/body/circumference`

创建围度记录。至少填写一项围度值，禁止全部为空。

- 请求体：`CircumferenceRecordCreate`
- 响应：`CircumferenceRecordResponse`

#### GET/PUT/DELETE `/api/v1/body/circumference[/{id}]`

与体重端点行为一致，支持软删除。

#### POST `/api/v1/body/sleep`

创建睡眠记录。V1 仅支持追加，禁止编辑和删除。

#### POST `/api/v1/body/exercise`

创建运动记录。V1 仅支持追加，禁止编辑和删除。

#### POST `/api/v1/body/water`

创建或累加饮水记录。同一日期使用 **upsert 逻辑**：若当日已有记录，累加 `amount_ml`；否则新建。

#### POST `/api/v1/body/bowel`

创建排便记录。V1 仅支持追加，禁止编辑和删除。

#### GET `/api/v1/body/trends`

趋势数据查询。

- Query 参数：`type`（必须，枚举：weight/circumference/sleep/exercise/water/bowel）、`period`（必须，枚举：7d/30d/90d/365d）、`sub_type`（可选，围度子类型：waist/hip/thigh/arm）
- 响应：`TrendResponse`

#### GET `/api/v1/body/latest`

返回每种数据类型的最新一条记录。

- 响应：`LatestValuesResponse`

---

## 3. 数据模型

所有模型必须使用 Pydantic v2，遵循 `overview.md` 的类型安全原则。

### 3.1 枚举定义

```python
from enum import Enum

class SleepQuality(str, Enum):
    """睡眠质量枚举"""
    GOOD = "good"      # 好
    FAIR = "fair"      # 一般
    POOR = "poor"      # 差

class ExerciseType(str, Enum):
    """运动类型枚举"""
    WALKING = "walking"    # 走路
    RUNNING = "running"    # 跑步
    CYCLING = "cycling"    # 骑行
    SWIMMING = "swimming"  # 游泳
    GYM = "gym"            # 力量训练
    YOGA = "yoga"          # 瑜伽
    OTHER = "other"        # 其他

class BowelStatus(str, Enum):
    """排便状态枚举"""
    NORMAL = "normal"      # 正常
    HARD = "hard"          # 偏硬
    SOFT = "soft"          # 偏软
    DIARRHEA = "diarrhea"  # 腹泻
```

### 3.2 请求模型

```python
from pydantic import BaseModel, Field
from datetime import date, datetime

class WeightRecordCreate(BaseModel):
    """体重记录创建请求"""
    weight: float = Field(..., ge=30.0, le=300.0, description="体重，单位 kg，精确到 0.1")
    date: date = Field(..., description="记录日期，禁止未来日期")
    note: str | None = Field(None, max_length=200, description="备注，如'空腹称重'")

class CircumferenceRecordCreate(BaseModel):
    """围度记录创建请求。至少填写一项围度值，禁止全部为 None"""
    waist: float | None = Field(None, ge=30.0, le=200.0, description="腰围 cm")
    hip: float | None = Field(None, ge=30.0, le=200.0, description="臀围 cm")
    thigh: float | None = Field(None, ge=10.0, le=100.0, description="大腿围 cm")
    arm: float | None = Field(None, ge=10.0, le=80.0, description="上臂围 cm")
    date: date = Field(..., description="记录日期，禁止未来日期")

class SleepRecordCreate(BaseModel):
    """睡眠记录创建请求"""
    sleep_time: datetime = Field(..., description="入睡时间")
    wake_time: datetime = Field(..., description="起床时间，必须晚于 sleep_time")
    quality: SleepQuality = Field(..., description="睡眠质量")
    date: date = Field(..., description="记录日期，禁止未来日期")

class ExerciseRecordCreate(BaseModel):
    """运动记录创建请求"""
    exercise_type: ExerciseType = Field(..., description="运动类型")
    duration_minutes: int = Field(..., ge=1, le=600, description="运动时长，单位分钟")
    note: str | None = Field(None, max_length=200, description="备注")
    date: date = Field(..., description="记录日期，禁止未来日期")

class WaterRecordCreate(BaseModel):
    """饮水记录创建请求。同一日期使用 upsert 逻辑，amount_ml 为本次新增量"""
    amount_ml: int = Field(..., ge=1, le=5000, description="本次饮水量 ml")
    date: date = Field(..., description="记录日期，禁止未来日期")

class BowelRecordCreate(BaseModel):
    """排便记录创建请求"""
    time: datetime = Field(..., description="排便时间")
    status: BowelStatus = Field(..., description="排便状态")
    date: date = Field(..., description="记录日期，禁止未来日期")
```

### 3.3 响应模型

```python
from pydantic import BaseModel
from datetime import date, datetime
from uuid import UUID

class WeightRecordResponse(BaseModel):
    """体重记录响应"""
    id: UUID
    weight: float
    date: date
    note: str | None
    anomaly_warning: str | None = Field(None, description="异常值告警信息，如'体重变化较大，请确认'")
    created_at: datetime
    updated_at: datetime

class CircumferenceRecordResponse(BaseModel):
    """围度记录响应"""
    id: UUID
    waist: float | None
    hip: float | None
    thigh: float | None
    arm: float | None
    date: date
    created_at: datetime
    updated_at: datetime

class SleepRecordResponse(BaseModel):
    """睡眠记录响应"""
    id: UUID
    sleep_time: datetime
    wake_time: datetime
    duration_hours: float = Field(..., description="睡眠时长（小时），由 service 层计算")
    quality: SleepQuality
    date: date
    created_at: datetime

class ExerciseRecordResponse(BaseModel):
    """运动记录响应"""
    id: UUID
    exercise_type: ExerciseType
    duration_minutes: int
    note: str | None
    date: date
    created_at: datetime

class WaterRecordResponse(BaseModel):
    """饮水记录响应"""
    id: UUID
    amount_ml: int = Field(..., description="当日累计饮水量 ml")
    date: date
    updated_at: datetime

class BowelRecordResponse(BaseModel):
    """排便记录响应"""
    id: UUID
    time: datetime
    status: BowelStatus
    date: date
    created_at: datetime
```

### 3.4 趋势与聚合模型

```python
class DataPoint(BaseModel):
    """趋势数据点"""
    date: date
    value: float

class TrendStatistics(BaseModel):
    """趋势统计指标"""
    min: float = Field(..., description="周期内最小值")
    max: float = Field(..., description="周期内最大值")
    average: float = Field(..., description="周期内平均值，保留 1 位小数")
    latest: float = Field(..., description="最新值")
    change: float = Field(..., description="变化量 = 最新值 - 周期起始值，正数为增加")

class TrendResponse(BaseModel):
    """趋势查询响应"""
    type: str = Field(..., description="数据类型，如 weight/waist/sleep 等")
    period: str = Field(..., description="查询周期，如 7d/30d/90d/365d")
    data_points: list[DataPoint] = Field(..., description="趋势数据点列表，按日期升序")
    statistics: TrendStatistics
    target: float | None = Field(None, description="目标值，来自 health_profiles.target_weight")

class LatestValuesResponse(BaseModel):
    """各类型最新值聚合响应"""
    weight: WeightRecordResponse | None = None
    circumference: CircumferenceRecordResponse | None = None
    sleep: SleepRecordResponse | None = None
    exercise: ExerciseRecordResponse | None = None
    water: WaterRecordResponse | None = None
    bowel: BowelRecordResponse | None = None
```

---

## 4. 趋势计算逻辑

### 4.1 移动平均计算

趋势接口必须按以下规则计算数据点：

- **7d / 30d / 90d**：返回每日原始数据点，缺失日期不补零、不插值
- **365d**：返回每周平均值（按自然周聚合），避免数据点过于密集
- 数据点列表必须按日期升序排列

### 4.2 统计指标计算

```python
# 伪代码：趋势统计计算逻辑
def calculate_statistics(records: list, period: str) -> TrendStatistics:
    values = [r.value for r in records]
    return TrendStatistics(
        min=min(values),
        max=max(values),
        average=round(sum(values) / len(values), 1),
        latest=values[-1],                    # 最新值
        change=round(values[-1] - values[0], 1)  # 变化量 = 最新 - 最早
    )
```

### 4.3 目标线

- 体重趋势的 `target` 字段从 `health_profiles.target_weight` 读取
- 其他类型的 `target` 在 V1 固定返回 `None`

---

## 5. 异常值检测

### 5.1 检测规则

当用户创建体重或围度记录时，必须执行异常值检测：

```python
import statistics

def detect_anomaly(new_value: float, history: list[float]) -> str | None:
    """
    异常值检测。
    history: 最近 30 天的历史记录值列表。
    返回告警文本或 None。
    """
    if len(history) < 5:
        return None  # 历史数据不足，跳过检测

    mean = statistics.mean(history)
    stdev = statistics.stdev(history)

    if stdev == 0:
        return None  # 数据无波动，跳过

    deviation = abs(new_value - mean)
    if deviation > 2 * stdev:
        return f"本次记录 {new_value} 偏离近 30 天均值 {mean:.1f} 较大，请确认是否正确"

    return None
```

### 5.2 检测行为

| 规则 | 说明 |
|------|------|
| 触发时机 | POST（创建）和 PUT（更新）体重、围度记录时 |
| 历史窗口 | 最近 30 天同类型记录 |
| 阈值 | 偏离均值 > 2 个标准差 |
| 最少样本 | 历史记录 < 5 条时跳过检测 |
| 行为 | 仅告警，禁止阻断保存操作 |
| 返回方式 | 响应体中 `anomaly_warning` 字段携带告警文本 |

---

## 6. Service 接口
```python
from datetime import date

class BodyService:
    """
    身体数据追踪 Service。
    遵循模块自治原则，所有外部模块必须通过此接口访问身体数据。
    """

    # ── 体重 ──
    async def create_weight(self, user_id: str, data: WeightRecordCreate) -> WeightRecordResponse:
        """创建体重记录，执行异常值检测，触发 memory_service 更新"""
        ...

    async def list_weight(self, user_id: str, start_date: date | None, end_date: date | None, page: int, page_size: int) -> PaginatedResponse[WeightRecordResponse]:
        """查询体重记录列表"""
        ...

    async def update_weight(self, user_id: str, record_id: str, data: WeightRecordCreate) -> WeightRecordResponse:
        """更新体重记录，执行异常值检测"""
        ...

    async def delete_weight(self, user_id: str, record_id: str) -> None:
        """软删除体重记录"""
        ...

    # ── 围度 ──
    async def create_circumference(self, user_id: str, data: CircumferenceRecordCreate) -> CircumferenceRecordResponse:
        """创建围度记录，校验至少一项非空"""
        ...

    async def list_circumference(self, user_id: str, start_date: date | None, end_date: date | None, page: int, page_size: int) -> PaginatedResponse[CircumferenceRecordResponse]:
        ...

    async def update_circumference(self, user_id: str, record_id: str, data: CircumferenceRecordCreate) -> CircumferenceRecordResponse:
        ...

    async def delete_circumference(self, user_id: str, record_id: str) -> None:
        ...

    # ── 辅助记录（仅追加） ──
    async def create_sleep(self, user_id: str, data: SleepRecordCreate) -> SleepRecordResponse:
        """创建睡眠记录，自动计算 duration_hours"""
        ...

    async def list_sleep(self, user_id: str, start_date: date | None, end_date: date | None, page: int, page_size: int) -> PaginatedResponse[SleepRecordResponse]:
        ...

    async def create_exercise(self, user_id: str, data: ExerciseRecordCreate) -> ExerciseRecordResponse:
        ...

    async def list_exercise(self, user_id: str, start_date: date | None, end_date: date | None, page: int, page_size: int) -> PaginatedResponse[ExerciseRecordResponse]:
        ...

    async def create_water(self, user_id: str, data: WaterRecordCreate) -> WaterRecordResponse:
        """创建或累加饮水记录（upsert），返回当日累计量"""
        ...

    async def list_water(self, user_id: str, start_date: date | None, end_date: date | None, page: int, page_size: int) -> PaginatedResponse[WaterRecordResponse]:
        ...

    async def create_bowel(self, user_id: str, data: BowelRecordCreate) -> BowelRecordResponse:
        ...

    async def list_bowel(self, user_id: str, start_date: date | None, end_date: date | None, page: int, page_size: int) -> PaginatedResponse[BowelRecordResponse]:
        ...

    # ── 趋势与聚合 ──
    async def get_trends(self, user_id: str, type: str, period: str, sub_type: str | None = None) -> TrendResponse:
        """趋势数据查询，包含统计指标和目标线"""
        ...

    async def get_latest(self, user_id: str) -> LatestValuesResponse:
        """返回每种数据类型的最新一条记录"""
        ...
```

---

## 7. 模块依赖

### 7.1 依赖关系

```
body_service
    ├── 依赖 → memory_service    （体重/围度变化触发记忆更新）
    ├── 被依赖 ← suggestion_service （趋势分析数据供建议生成使用）
    └── 被依赖 ← plan_service       （体重追踪数据供计划进度使用）
```

### 7.2 依赖说明

| 方向 | 模块 | 交互方式 | 说明 |
|------|------|---------|------|
| 依赖 | memory_service | 创建/更新体重或围度后调用 | 将身体数据变化写入用户记忆，供 AI 对话引用 |
| 被依赖 | suggestion_service | 通过 `get_trends()` 读取 | 基于趋势数据生成健康建议 |
| 被依赖 | plan_service | 通过 `get_latest()` / `list_weight()` 读取 | 追踪体重目标完成进度 |

---

## 8. 实现约束

### 8.1 数据精度

| 数据类型 | 精度 | 说明 |
|---------|------|------|
| 体重 | 0.1 kg | 数据库字段 `DECIMAL(5,1)` |
| 围度 | 0.1 cm | 数据库字段 `DECIMAL(5,1)` |
| 睡眠时长 | 0.1 小时 | service 层计算，非用户输入 |

### 8.2 业务规则

| 规则 | 说明 |
|------|------|
| 日期校验 | 所有记录的 `date` 字段禁止未来日期，必须 `<= today` |
| 饮水 upsert | 同一用户同一日期只保留一条饮水记录，POST 时累加 `amount_ml` |
| 软删除 | 体重和围度记录使用软删除（`deleted_at` 字段），查询时必须过滤已删除记录 |
| 辅助记录不可编辑 | 睡眠、运动、饮水、排便在 V1 仅支持追加，禁止提供 PUT/DELETE 端点 |
| 围度非空校验 | 围度记录的 waist/hip/thigh/arm 至少一项非 None，否则返回 422 |
| 睡眠时间校验 | `wake_time` 必须晚于 `sleep_time`，否则返回 422 |
| 记录归属校验 | PUT/DELETE 操作必须校验记录属于当前认证用户，否则返回 403 |
