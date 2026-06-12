# 计划模块设计讨论（需求4 拆分）

> 生成日期：2026-06-09
> 来源：从 `2026-06-09-weight-record-requirements.md` 需求4 拆分独立
> 状态：讨论中
> 关联模块：计划模块（`docs/prd/v1/07-plan-system.md`）、数据模块（`docs/prd/v1/04-body-tracking.md`）

## 二、计划模块的真实范围

以"减重"为例，一个完整的减重计划包含多个子计划和能力：

### 1. 运动计划
- 运动是一个大类，下面要再细分：
  - **运动种类**：跑步、力量、游泳、骑行……
  - **时间安排**：每天/每周哪些时段、时长
  - **任务拆解**：把运动目标拆成可执行的任务
  - **完成率**：每个任务、每天、每周的完成情况追踪

### 2. 每日体重目标计划
- 设定每天的目标体重（这才是上一版误以为的"计划全部"）
- 这个每日目标值会被**数据模块**消费，生成目标曲线

### 3. 计划完成情况的 AI 分析
- AI 分析用户对计划的执行情况（完成率、偏差、趋势）
- 给出反馈和建议

### 4. AI 实时调整计划
- 计划不是一次设定就固定的，**会动态变动**
- AI 需要根据实际数据（体重变化、运动完成情况等）**实时调整计划**
- 例如：用户连续没完成运动 → AI 调低强度或重新编排

---

## 三、计划模块与数据模块的关系（修正版）

```
┌─────────────────────────────────────────────┐
│              计划模块（大模块）                │
│                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ 运动计划  │ │每日体重   │ │ 其他维度计划  │   │
│  │ 种类/时间 │ │目标计划   │ │ 饮水/围度...  │   │
│  │ 任务/完成 │ │          │ │              │   │
│  └──────────┘ └────┬─────┘ └──────────────┘   │
│                    │                          │
│  ┌─────────────────┴──────────────────────┐   │
│  │  AI 能力层：完成情况分析 + 实时调整计划   │   │
│  └────────────────────────────────────────┘   │
└────────────────────┬──────────────────────────┘
                     │ 输出"每日目标值"
                     ▼
┌─────────────────────────────────────────────┐
│              数据模块                          │
│  趋势图 = 实际数据曲线  vs  计划目标曲线        │
│         （实测体重）        （来自计划模块）     │
└─────────────────────────────────────────────┘
```

**关系要点**：
- 计划模块是**生产者**，向数据模块输出每日目标值
- 数据模块是**消费者**，把目标值画成目标曲线，叠加在实际数据趋势图上做对比
- 但计划模块的价值**不止于此**——它有自己完整的运动管理、任务管理、AI 分析与动态调整能力

---

## 三、需求确认（用户回答）

### 1. 计划的数据结构
✅ **已确认**：是「主计划 + 多个子计划（运动/体重/饮水…）」的树状结构

### 2. 子计划与数据维度的对应
✅ **已确认**：每个子计划对应数据模块的一个维度

### 3. 运动任务和数据记录的关系
✅ **已确认**：运动计划里的"任务"完成后，**自动生成数据模块里的一条运动记录**

### 4. AI 调整计划的触发与边界
✅ **已确认**：
- **触发频率**：每日检查一次
- **触发条件**：如有异常（如连续未完成、偏差过大等）
- **交互方式**：提示用户调整，**需要用户确认**后才生效
- **历史留痕**：调整历史**不留痕**（不保存调整记录）

### 5. 完成率的计算口径
✅ **已确认**：由 Claude 决定（你设计单维度完成率、整体计划完成率的定义和聚合逻辑）

### 6. 现有代码梳理
✅ **已确认**：不管现有 `07-plan-system.md`，检查现有代码，整理「已有 vs 缺失 vs 需改」

---

## 四、现有代码能力梳理（基于 backend 代码）

### 已有能力（✅ 现有代码支持）

#### 1. 数据模型层（`app/db/models/plan.py`）
- ✅ **Plan 表**：主计划表，包含 `name`、`goal_description`、`plan_type`、`status`、`start_date`、`target_date`
- ✅ **tasks 字段**（JSONB）：存储任务列表，已支持树状结构中的"任务"部分
- ✅ **phases 字段**（JSONB）：存储阶段化计划（Phase 概念，一个 Phase 包含多个 Task）
- ✅ **PlanTarget 表**：存储数值目标（`daily_calories`、`protein_target`、`fat_target`、`carbs_target`、`weight_target`）
- ✅ **PlanExecution 表**：存储每日执行记录（`date`、`calories_consumed`、`calories_target`、营养三大件、`status`）
- ✅ **PlanCheckIn 表**：存储手动打卡记录（`task_id`、`date`、`completed`、`note`）

#### 2. Schema 层（`app/schemas/plan.py`）
- ✅ **PlanType**：枚举（`weight_loss`、`nutrition_adjustment`、`habit_formation`）
- ✅ **PlanStatus**：枚举（`active`、`completed`、`terminated`）
- ✅ **ExecutionStatus**：枚举（`on_track`、`deviation`、`missed`）
- ✅ **PlanTask**：任务结构（`id`、`description`、`frequency`、`time_period`）
- ✅ **PlanPhase**：阶段结构（`id`、`title`、`goal`、`start_date`、`end_date`、`tasks`）
- ✅ **PlanProgress**：进度统计（`total_days`、`elapsed_days`、`compliance_rate`、`streak_days`、`completed_tasks`、`total_tasks`）

#### 3. API 层（`app/api/v1/plans.py`）
- ✅ **POST /plans/stream**：对话式创建计划（Agent 驱动，结合档案和记忆）
- ✅ **GET /plans**：列出计划（支持按 `status` 筛选、分页）
- ✅ **GET /plans/{plan_id}**：获取计划详情
- ✅ **PUT /plans/{plan_id}**：更新计划（目标值、截止日期、任务列表）
- ✅ **DELETE /plans/{plan_id}**：终止计划（软删除，带 `termination_reason`）
- ✅ **POST /plans/{plan_id}/check-ins**：手动打卡
- ✅ **GET /plans/{plan_id}/progress**：查询进度统计
- ✅ **GET /plans/{plan_id}/execution**：查询每日执行记录（支持日期范围、状态筛选、分页）

#### 4. 数据模块的运动记录（`app/db/models/body.py`）
- ✅ **ExerciseRecord 表**：存储运动记录（`date`、`exercise_type`、`duration_minutes`、`calories`、`note`）
- ✅ 已有表结构支持从计划任务自动生成运动记录

---

### 缺失能力（❌ 现有代码没有）

#### 1. 子计划层级结构
- ❌ **没有独立的"子计划"表**：当前 `Plan` 表是扁平的，没有"主计划 → 子计划"的层级关系
- ❌ **没有子计划与维度的映射**：当前 `PlanTarget` 只有 5 个固定字段（热量 + 营养三大件 + 体重），不支持"一个子计划对应一个数据维度"的扩展设计
- ❌ **运动子计划**：没有独立的运动计划表，运动相关的目标和任务散落在 `tasks` JSONB 中，无法结构化查询

#### 2. 运动计划的细化能力
- ❌ **运动种类管理**：没有运动种类的枚举或字典表（跑步、力量、游泳、骑行……）
- ❌ **运动任务的时间安排**：`PlanTask` 有 `frequency` 和 `time_period`，但语义模糊，不支持"每周一/三/五 18:00-19:00"这样的精细安排
- ❌ **运动任务的目标值**：没有单个任务的目标（如"跑步 5km"、"力量训练 30 分钟"），只有计划级别的目标

#### 3. 任务完成后自动生成数据记录
- ❌ **缺少任务 → 数据记录的自动转换逻辑**：当前 `PlanCheckIn` 只是打卡，不会自动生成 `ExerciseRecord`
- ❌ **缺少反向关联**：`ExerciseRecord` 没有 `plan_id` 或 `task_id` 字段，无法关联回计划任务

#### 4. 每日目标曲线的生成
- ❌ **没有"每日目标值"的存储**：`PlanTarget` 只有一个总目标（如 `weight_target`），没有按天展开的目标曲线（如"第 1 天 70kg，第 2 天 69.9kg，……"）
- ❌ **没有目标曲线的 API**：数据模块需要的"目标曲线"数据，计划模块现在没有输出接口

#### 5. AI 完成情况分析
- ❌ **没有 AI 分析的存储和 API**：当前 `PlanProgress` 只是统计数字（完成率、连续天数），没有 AI 生成的文本分析（如"本周运动完成率低，建议降低强度"）
- ❌ **没有异常检测的触发机制**：代码里没有"每日检查 → 发现异常 → 触发 AI 分析"的调度逻辑

#### 6. AI 实时调整计划
- ❌ **没有计划调整的工作流**：没有"AI 提议调整 → 用户确认 → 应用调整"的状态机
- ❌ **没有调整历史的存储**：虽然用户说"不留痕"，但至少需要一个临时表存储"待确认的调整提议"

---

### 需要修改的部分（🔧 现有设计需调整）

#### 1. Plan 表的 `tasks` 和 `phases` 字段
- 🔧 **当前**：`tasks` 是 JSONB，扁平存储，无法表达"运动子计划 → 跑步任务 + 力量任务"的层级
- 🔧 **需要**：要么拆成独立的 `SubPlan` 表，要么在 JSONB 里嵌套"子计划"概念并规范 schema

#### 2. PlanTarget 表的扩展性
- 🔧 **当前**：只有 5 个固定字段（热量、营养、体重），不支持其他维度（如饮水目标、睡眠目标）
- 🔧 **需要**：改为 KV 存储（如新增 `target_type` + `target_value` 字段），或拆成多个子计划表各自带目标

#### 3. ExerciseRecord 的关联字段
- 🔧 **当前**：只有 `user_id`、`date`、`exercise_type`，无法关联回计划任务
- 🔧 **需要**：新增 `plan_id` 和 `task_id` 字段（可选，用于标记"这条记录是哪个任务自动生成的"）

#### 4. PlanProgress 的完成率计算
- 🔧 **当前**：只有 `completed_tasks` / `total_tasks`，语义是"任务级完成率"
- 🔧 **需要**：扩展为"单维度完成率"（运动完成率、饮食完成率）+ "整体计划完成率"（加权聚合）

---

## 五、架构方案（已确认决策）

> 用户决策：
> 1. 子计划 → **新增 `SubPlan` 表**
> 2. 每日目标值 → **新增 `DailyTarget` 表**
> 3. 任务 → 数据记录自动化 → **后台任务**
> 4. AI 分析/调整存储 → 由 Claude 定义
> 5. 完成率口径 → 由 Claude 定义

### 5.1 整体表关系总览

```
plans (主计划，已存在)
  │ 1:N
  ├── plan_sub_plans (子计划，新增) ────────┐
  │      │ 1:N                              │
  │      ├── tasks(JSONB 内嵌任务)           │ sub_plan_id
  │      │                                  │
  │      └── 1:N plan_daily_targets (新增)   │
  │              dimension/date/value        │
  │                                          │
  ├── plan_targets (总目标，保留兼容)         │
  ├── plan_executions (每日执行，保留)        │
  ├── plan_check_ins (打卡，保留)             │
  ├── plan_analyses (AI 分析，新增)           │
  └── plan_adjustment_proposals (待确认调整，新增)
                                             │
body_exercise_records (运动记录，需改) ◄──────┘
  + plan_id / sub_plan_id / task_id (新增可空外键)
```

### 5.2 新增表 1：`SubPlan`（子计划）

一个主计划下挂多个子计划，每个子计划对应数据模块的**一个维度**（运动/体重/饮水/睡眠…）。任务仍用 JSONB 内嵌（沿用现有 `Plan.tasks` 的风格，避免过度拆表）。

```python
class SubPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """子计划：主计划下的一个维度计划（运动/体重/饮水…）。"""

    __tablename__ = "plan_sub_plans"
    __table_args__ = (
        Index("idx_sub_plan_plan", "plan_id"),
        Index("idx_sub_plan_user_dimension", "user_id", "dimension"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 对应数据模块维度：exercise / weight / water / sleep / measurement / nutrition
    dimension: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    goal_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    # 任务列表内嵌（含运动种类/时间安排/单任务目标值），schema 见 5.6
    tasks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    # 该子计划的权重（用于整体完成率加权），默认等权
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
```

**`dimension` 枚举**（与数据模块表一一对应）：

| dimension | 对应数据表 | 说明 |
|-----------|-----------|------|
| `exercise` | `body_exercise_records` | 运动计划 |
| `weight` | `body_weight_records` | 每日体重目标 |
| `water` | `body_water_records` | 饮水计划 |
| `sleep` | `body_sleep_records` | 睡眠计划 |
| `measurement` | `body_measurement_records` | 围度计划 |
| `nutrition` | `plan_executions` | 饮食营养（沿用现有执行表） |

### 5.3 新增表 2：`DailyTarget`（每日目标值）

把"总目标"按天展开成**目标曲线**，供数据模块叠加在实际趋势图上。这是计划模块作为"生产者"输出给数据模块的核心数据。

```python
class DailyTarget(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """每日目标值：按天展开的目标曲线，供数据模块消费。"""

    __tablename__ = "plan_daily_targets"
    __table_args__ = (
        UniqueConstraint("sub_plan_id", "date", name="uq_daily_target_sub_plan_date"),
        Index("idx_daily_target_user_dim_date", "user_id", "dimension", "date"),
        Index("idx_daily_target_plan_date", "plan_id", "date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sub_plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_sub_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dimension: Mapped[str] = mapped_column(String(30), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    # 目标数值（体重 kg / 饮水 ml / 运动分钟 / 热量 kcal…），单位由 dimension 决定
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
```

**目标曲线生成策略**（创建/调整计划时由后台批量写入）：
- **线性插值**：起点值 → 终点值，按天均匀过渡（默认，适合体重）。例：70kg → 65kg，30 天，每天 -0.167kg。
- **恒定值**：每天目标相同（适合饮水 2000ml、运动 30min）。
- **阶段化**：按 `phases` 分段，每段内部再线性/恒定（适合进阶式训练）。

### 5.4 修改表：`ExerciseRecord` 增加计划关联

让"任务完成 → 自动生成运动记录"可反向追溯，并避免重复生成。

```python
class ExerciseRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    # ...existing fields...
    # 新增三个可空外键：标记该记录由哪个计划/子计划/任务自动生成
    plan_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    sub_plan_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    task_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    # 来源：manual（用户手动）/ plan_task（任务自动生成）
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
```

> 手动记录 `source="manual"`，三个外键为空；任务自动生成 `source="plan_task"`，三个外键填充。

### 5.5 任务 → 数据记录自动化（后台任务）

**触发链路**：

```
用户对运动任务打卡 (POST /plans/{id}/check-ins, completed=true)
        │  仅写 plan_check_ins，立即返回（不阻塞接口）
        ▼
投递后台任务 enqueue(generate_exercise_record, check_in_id)
        │  沿用项目现有 asyncio.create_task 后台模式
        ▼ 后台执行
1. 读取 check_in → 找到 task_id → 读 SubPlan.tasks 里的任务定义
2. 幂等校验：按 (task_id, date) 查 body_exercise_records 是否已存在
   - 已存在 → 跳过（防重复）
3. 用任务的 target（exercise_type/duration/calories）生成 ExerciseRecord
   source="plan_task"，回填 plan_id/sub_plan_id/task_id
4. 写入成功 → 该日该任务的"实际完成"即被数据模块感知
```

**为什么用后台任务**（与项目现状一致）：
- 打卡接口保持快速响应，不被记录生成阻塞。
- 沿用 `diet/nodes.py` 里 `_BACKGROUND_TASKS` + `asyncio.create_task` 的既有范式，无需引入 Celery。
- 幂等键 `(task_id, date)` 保证重试安全。

### 5.6 子计划内嵌任务的 JSONB Schema（运动细化）

解决"运动种类 / 时间安排 / 单任务目标值"缺失：

```jsonc
// SubPlan.tasks 单个元素
{
  "id": "uuid",
  "exercise_type": "running",        // 运动种类：running/strength/swimming/cycling
  "schedule": {                       // 精细时间安排
    "weekdays": [1, 3, 5],            // 周一/三/五（1-7）
    "start_time": "18:00",
    "end_time": "19:00"
  },
  "target": {                         // 单任务目标值
    "duration_minutes": 30,
    "distance_km": 5,
    "calories": 300
  },
  "frequency": "weekly"               // 兼容旧字段
}
```

### 5.7 新增表 3：`PlanAnalysis`（AI 完成情况分析）

> Claude 定义：每日检查触发一次，存储 AI 生成的文本分析 + 结构化指标。**保留分析历史**（与"调整不留痕"不同，分析是观测记录，留痕有价值）。

```python
class PlanAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI 对计划完成情况的分析结果（每日一条）。"""

    __tablename__ = "plan_analyses"
    __table_args__ = (
        UniqueConstraint("plan_id", "analysis_date", name="uq_plan_analysis_plan_date"),
        Index("idx_plan_analysis_user_date", "user_id", "analysis_date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    # 整体完成率快照（见 5.9 口径）
    overall_compliance: Mapped[float] = mapped_column(Float, nullable=False)
    # 各维度完成率快照 {"exercise": 0.6, "weight": 0.9, ...}
    dimension_compliance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    # 是否检测到异常（触发调整提议的依据）
    has_anomaly: Mapped[bool] = mapped_column(nullable=False, default=False)
    # AI 生成的自然语言分析与建议
    summary: Mapped[str] = mapped_column(Text, nullable=False)
```

### 5.8 新增表 4：`PlanAdjustmentProposal`（待确认的调整提议）

> Claude 定义：AI 调整**需用户确认**，调整本身**不留痕**——因此本表是"待确认队列"，用户确认/拒绝后即终态，不保存历史版本 diff。

```python
class PlanAdjustmentProposal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI 提出的计划调整，等待用户确认。确认/拒绝后置为终态。"""

    __tablename__ = "plan_adjustment_proposals"
    __table_args__ = (
        Index("idx_adjust_plan_status", "plan_id", "status"),
        Index("idx_adjust_user_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sub_plan_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    # 触发原因（如 "连续3天未完成运动"）
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    # 调整内容（结构化 patch：要改哪些任务/目标/曲线）
    proposed_changes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    # pending / accepted / rejected / expired
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**调整状态机**：

```
每日检查发现异常
      │
      ▼
生成 proposal (status=pending) ──► 推送提示给用户
      │                                    │
      │ 用户接受                            │ 用户忽略（次日新提议生成时）
      ▼                                    ▼
应用 proposed_changes 到            旧 proposal 置 expired
SubPlan/DailyTarget                （不留痕，仅终态标记）
status=accepted
      │
      ▼
重新生成 DailyTarget 目标曲线
```

### 5.9 完成率计算口径（Claude 定义）

#### 单维度完成率

按维度类型分两类计算：

**A. 任务型维度**（运动）—— 基于任务打卡：

```
单维度完成率 = 已完成任务次数 / 应完成任务次数（截至今日）
```
- "应完成次数"由 `schedule.weekdays` 在 `[start_date, today]` 区间内推算。
- 例：每周一/三/五，已过 2 周 = 应完成 6 次，实际打卡 4 次 → 4/6 ≈ 0.67。

**B. 数值型维度**（体重/饮水/睡眠）—— 基于目标达成度：

```
单日达成度 = 1 - min(1, |实际值 - 目标值| / 容差带)
单维度完成率 = 平均(各有记录日的单日达成度)
```
- 容差带（tolerance）按维度设默认：体重 ±0.5kg、饮水按目标的 20%。
- 无记录的日子不计入分母（避免惩罚未记录，但会在分析中提示）。

#### 整体计划完成率（加权聚合）

```
整体完成率 = Σ(子计划完成率 × 子计划权重) / Σ(子计划权重)
```
- 权重取 `SubPlan.weight`，默认全部为 1.0（等权）。
- 用户可调权重（如更看重运动）→ 运动权重设 2.0。

#### 示例

| 子计划 | 维度 | 完成率 | 权重 |
|--------|------|--------|------|
| 运动计划 | exercise | 0.67 | 2.0 |
| 体重目标 | weight | 0.90 | 1.0 |
| 饮水计划 | water | 0.80 | 1.0 |

```
整体 = (0.67×2 + 0.90×1 + 0.80×1) / (2+1+1)
     = (1.34 + 0.90 + 0.80) / 4
     = 3.04 / 4 = 0.76
```

### 5.10 配套 API（新增/调整）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/plans/{id}/sub-plans` | 列出子计划 |
| `POST` | `/plans/{id}/sub-plans` | 新增子计划 |
| `PUT` | `/plans/{id}/sub-plans/{sub_id}` | 改子计划（任务/权重） |
| `GET` | `/plans/{id}/daily-targets` | 取目标曲线（数据模块消费，支持 `dimension`、日期范围） |
| `GET` | `/plans/{id}/analyses` | 取 AI 分析历史 |
| `GET` | `/plans/{id}/proposals?status=pending` | 取待确认调整 |
| `POST` | `/plans/{id}/proposals/{pid}/accept` | 接受调整 → 应用并重算曲线 |
| `POST` | `/plans/{id}/proposals/{pid}/reject` | 拒绝调整 |

## 六、下一步行动

> 进度更新：2026-06-10 已完成第 1–6、8 项的基础实现；第 7 项（每日检查调度 + AI 分析/调整工作流）尚未实现，且第 8 项中 `accept_proposal` 的"应用 proposed_changes 并重算曲线"为占位简化版，待补。

1. ✅ 架构方向已确认（SubPlan / DailyTarget / 后台任务 / AI 分析与调整 / 完成率口径）
2. ✅ **写 Alembic 迁移**：新增 4 张表 + `body_exercise_records` 加 4 个字段
   - `alembic/versions/20260610_0012_plan_sub_plans.py`
3. ✅ **实现 ORM 模型与 Pydantic schema**：对应 5.2–5.8
   - ORM：`SubPlan` / `DailyTarget` / `PlanAnalysis` / `PlanAdjustmentProposal`（`app/db/models/plan.py`）
   - Schema：`SubPlanCreate/Update/Response`、`SubPlanTask/TaskDraft`、`ExerciseSchedule/Target`、`DailyTargetPoint/Curve`、`TargetCurveStrategy`、`DimensionCompliance`、`OverallCompliance`、`PlanAnalysisResponse`、`AdjustmentProposalResponse`、`ProposalStatus`、`PlanDimension`（`app/schemas/plan.py`）
4. ✅ **实现目标曲线生成器**：线性/恒定/阶段化三种策略（5.3）
   - `app/services/plan_curve_service.py::generate_curve`（纯函数；线性 70→65、恒定 2000ml 已 sanity 测过）
5. ✅ **实现后台任务**：任务打卡 → 自动生成运动记录（5.5，含幂等）
   - `app/services/plan_check_in_task.py::generate_exercise_record_from_check_in`（独立 session、`(task_id, date)` 幂等键）
   - 触发点：`app/api/v1/plans.py::create_check_in`，`asyncio.create_task` 投递
6. ✅ **实现完成率服务**：单维度 + 整体加权（5.9）
   - `app/services/plan_compliance_service.py::PlanComplianceService`
   - 任务型（运动）：按 `schedule.weekdays` 推算应完成次数 vs 实际打卡数
   - 数值型（体重/饮水/睡眠/围度/营养）：容差带 + 单日达成度均值
   - 整体：`Σ(子计划完成率 × 权重) / Σ权重`
7. ⏳ **实现每日检查调度 + AI 分析/调整工作流**（5.7/5.8）—— 未开始
   - 缺：每日触发器（cron / 后台 loop）
   - 缺：异常检测规则 → 生成 `PlanAdjustmentProposal`
   - 缺：LLM 生成 `PlanAnalysis.summary`
   - 已就绪：存储层（`upsert_analysis` / `create_proposal` / `expire_pending_proposals`）+ 接受/拒绝 API
8. ✅ **补 API 路由**（5.10）
   - `GET/POST /plans/{id}/sub-plans`、`PUT /plans/{id}/sub-plans/{sub_id}`
   - `GET /plans/{id}/daily-targets`（数据模块消费入口）
   - `GET /plans/{id}/compliance`（额外补的，非 5.10 列表中）
   - `GET /plans/{id}/analyses`
   - `GET /plans/{id}/proposals`、`POST /plans/{id}/proposals/{pid}/accept|reject`
   - ⚠️ `accept_proposal` 当前是占位实现：仅置 `status=accepted`，未真正应用 `proposed_changes` patch 也未重新生成曲线

### 验证情况
- 所有模块可导入，FastAPI app 启动成功（74 路由）
- 计划相关测试全绿（25 项）：`test_plan_service.py` 6、`test_plan_curve_and_compliance.py` 7、`test_plans.py` 2、`test_plan_agent.py` 2、`test_plan_conversation.py` 8
- 已端到端在 app 验证：体重趋势图叠加"实际 vs 计划目标"两条线

### 9. AI 创建计划自动派生体重子计划（2026-06-11 补）
✅ `create_plan_from_draft` 创建减重计划后，自动派生"每日体重目标"子计划 + 线性曲线：
- 起点 = 档案 `current_weight`，终点 = `weight_target`，线性插值
- 缺当前体重或目标体重时跳过派生，不影响主计划创建
- 这样 AI 对话生成减重计划后，数据模块体重 Tab 自动出现目标线，无需手动造数据
- 测试：`test_create_weight_loss_plan_derives_weight_sub_plan`、`test_create_plan_without_current_weight_skips_derivation`

### 仍待补的细节
- 第 7 项工作流整体未实现（每日检查调度器 + AI 分析/调整提议生成）
- `accept_proposal` 应用 `proposed_changes` 并 `replace_daily_targets` 重算曲线
- `_actual_values` 中 `measurement` 维度暂以腰围为代表值，需按子计划具体度量细化
- 派生逻辑目前仅 weight 维度；运动/饮水等其他维度的自动派生待补
- check-in task 的单元测试

## 关联文档

- 计划系统 PRD：`docs/prd/v1/07-plan-system.md`
- 身体数据 PRD：`docs/prd/v1/04-body-tracking.md`
- 体重记录需求：`2026-06-09-weight-record-requirements.md`
