"""Plan system schemas."""

from __future__ import annotations

from datetime import date as dt_date
from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanType(StrEnum):
    weight_loss = "weight_loss"
    nutrition_adjustment = "nutrition_adjustment"
    habit_formation = "habit_formation"


class PlanStatus(StrEnum):
    active = "active"
    completed = "completed"
    terminated = "terminated"


class ExecutionStatus(StrEnum):
    on_track = "on_track"
    deviation = "deviation"
    missed = "missed"


class PlanTask(BaseModel):
    id: UUID
    description: str
    frequency: str = "daily"
    time_period: str | None = None


class PlanTaskUpdate(BaseModel):
    id: UUID | None = None
    description: str = Field(min_length=1, max_length=200)
    frequency: str = Field(default="daily", max_length=50)
    time_period: str | None = Field(default=None, max_length=50)


class PlanPhase(BaseModel):
    id: UUID
    title: str = Field(min_length=1, max_length=100)
    goal: str = Field(min_length=1, max_length=300)
    start_date: dt_date
    end_date: dt_date
    tasks: list[PlanTask] = Field(default_factory=list)


class PlanPhaseDraft(BaseModel):
    id: UUID | None = None
    title: str = Field(min_length=1, max_length=100)
    goal: str = Field(min_length=1, max_length=300)
    start_date: dt_date
    end_date: dt_date
    tasks: list[PlanTaskUpdate] = Field(default_factory=list)


class WeightAnchor(BaseModel):
    """方案 C：LLM 为减重计划给出少量关键锚点，后端在锚点间线性插值成逐日曲线。

    - day_offset：相对于 start_date 的第几天（0 起算）
    - target_weight：该锚点的目标体重 (kg)

    LLM 只需给 3-5 个锚点（含首尾），大幅降低 token 与生成时间；
    后端分段线性插值后再做单调性/速率校验，失败则退回整段线性。
    """

    day_offset: int = Field(ge=0, le=200, description="相对于 start_date 的第几天，0=第一天")
    target_weight: float = Field(gt=0, le=300, description="该锚点的目标体重 kg")


class PlanTargets(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    daily_calories: int | None = Field(default=None, gt=0)
    protein_target: float | None = Field(default=None, gt=0)
    fat_target: float | None = Field(default=None, gt=0)
    carbs_target: float | None = Field(default=None, gt=0)
    weight_target: float | None = Field(default=None, gt=0)
    # 方案 C：减重计划专用，LLM 给 3-5 个关键锚点，后端插值成逐日曲线
    weight_anchors: list[WeightAnchor] | None = Field(
        default=None,
        description=(
            "减重计划专用。给 3-5 个关键锚点（含 day_offset=0 起点和最后一天终点），"
            "体现阶段速率；后端会在锚点间线性插值。校验失败将被丢弃，退回整段线性。"
        ),
    )


class PlanCreate(BaseModel):
    goal_description: str = Field(min_length=1, max_length=500)
    plan_type: PlanType | None = None


class PlanUpdate(BaseModel):
    daily_calories: int | None = Field(default=None, gt=0)
    protein_target: float | None = Field(default=None, gt=0)
    fat_target: float | None = Field(default=None, gt=0)
    carbs_target: float | None = Field(default=None, gt=0)
    weight_target: float | None = Field(default=None, gt=0)
    target_date: dt_date | None = None
    tasks: list[PlanTaskUpdate] | None = None


class PlanTerminateRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class CheckInCreate(BaseModel):
    date: dt_date = Field(default_factory=dt_date.today)
    task_id: UUID | None = None
    completed: bool
    note: str | None = Field(default=None, max_length=500)


class CheckInResponse(BaseModel):
    id: UUID
    plan_id: UUID
    task_id: UUID | None = None
    date: dt_date
    completed: bool
    note: str | None = None
    created_at: datetime


class DailyExecution(BaseModel):
    id: UUID | None = None
    date: dt_date
    calories_consumed: float
    calories_target: float
    protein: float
    fat: float
    carbs: float
    status: ExecutionStatus


class PlanProgress(BaseModel):
    plan_id: UUID
    total_days: int
    elapsed_days: int
    compliance_rate: float = Field(ge=0, le=1)
    streak_days: int = Field(ge=0)
    completed_tasks: int = Field(default=0, ge=0)
    total_tasks: int = Field(default=0, ge=0)
    completed_task_ids: list[UUID] = Field(default_factory=list)
    daily_records: list[DailyExecution] = Field(default_factory=list)


class PlanDraft(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    goal_description: str = Field(min_length=1, max_length=500)
    plan_type: PlanType
    start_date: dt_date
    target_date: dt_date
    targets: PlanTargets
    tasks: list[PlanTaskUpdate] = Field(default_factory=list)
    phases: list[PlanPhaseDraft] = Field(default_factory=list)


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    goal_description: str
    plan_type: PlanType
    status: PlanStatus
    start_date: dt_date
    target_date: dt_date
    targets: PlanTargets
    tasks: list[PlanTask] = Field(default_factory=list)
    phases: list[PlanPhase] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PlanConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str = Field(min_length=1, max_length=16000)


class PlanStreamRequest(BaseModel):
    session_id: str | None = Field(default=None, max_length=64)
    type: Literal["text", "card_action", "choice_response"] = "text"
    message: str | None = Field(default=None, max_length=2000)
    messages: list[PlanConversationMessage] = Field(default_factory=list)
    plan_type_hint: PlanType | None = None
    card_id: str | None = None
    action_id: str | None = None
    action_payload: dict[str, object] | None = None
    prompt_id: str | None = None
    selected_value: str | None = None
    free_text: str | None = Field(default=None, max_length=2000)


# ---------- 子计划 / 维度 ----------


class PlanDimension(StrEnum):
    """子计划对应的数据模块维度。"""

    exercise = "exercise"
    weight = "weight"
    water = "water"
    sleep = "sleep"
    measurement = "measurement"
    nutrition = "nutrition"


class TargetCurveStrategy(StrEnum):
    """每日目标曲线生成策略。"""

    linear = "linear"
    constant = "constant"
    phased = "phased"


class ProposalStatus(StrEnum):
    """AI 调整提议的终态机状态。"""

    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


class ExerciseSchedule(BaseModel):
    """运动任务的精细时间安排。"""

    weekdays: list[int] = Field(default_factory=list, description="ISO 周几 1-7（周一=1）")
    start_time: str | None = Field(default=None, description="HH:MM")
    end_time: str | None = Field(default=None, description="HH:MM")


class ExerciseTarget(BaseModel):
    """单个运动任务的目标值。"""

    duration_minutes: int | None = Field(default=None, ge=0)
    distance_km: float | None = Field(default=None, ge=0)
    calories: int | None = Field(default=None, ge=0)


class SubPlanTask(BaseModel):
    """子计划任务（运动维度时携带 exercise_type/schedule/target）。"""

    id: UUID
    description: str = Field(min_length=1, max_length=200)
    frequency: str = Field(default="daily", max_length=50)
    exercise_type: str | None = Field(default=None, max_length=50)
    schedule: ExerciseSchedule | None = None
    target: ExerciseTarget | None = None


class SubPlanTaskDraft(BaseModel):
    id: UUID | None = None
    description: str = Field(min_length=1, max_length=200)
    frequency: str = Field(default="daily", max_length=50)
    exercise_type: str | None = Field(default=None, max_length=50)
    schedule: ExerciseSchedule | None = None
    target: ExerciseTarget | None = None


class SubPlanCreate(BaseModel):
    dimension: PlanDimension
    name: str = Field(min_length=1, max_length=100)
    goal_description: str = Field(min_length=1, max_length=500)
    weight: float = Field(default=1.0, gt=0)
    tasks: list[SubPlanTaskDraft] = Field(default_factory=list)
    curve_strategy: TargetCurveStrategy = TargetCurveStrategy.linear
    start_value: float | None = Field(default=None, description="起点值（线性曲线必填）")
    end_value: float | None = Field(default=None, description="终点值（线性曲线必填）")
    constant_value: float | None = Field(default=None, description="恒定值（恒定曲线必填）")
    unit: str = Field(min_length=1, max_length=20)


class SubPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    goal_description: str | None = Field(default=None, min_length=1, max_length=500)
    status: PlanStatus | None = None
    weight: float | None = Field(default=None, gt=0)
    tasks: list[SubPlanTaskDraft] | None = None


class SubPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    dimension: PlanDimension
    name: str
    goal_description: str
    status: PlanStatus
    weight: float
    tasks: list[SubPlanTask] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# ---------- 每日目标曲线 ----------


class DailyTargetPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: dt_date
    target_value: float
    unit: str
    dimension: PlanDimension


class DailyTargetCurve(BaseModel):
    plan_id: UUID
    sub_plan_id: UUID | None = None
    dimension: PlanDimension
    unit: str
    points: list[DailyTargetPoint] = Field(default_factory=list)


# ---------- 完成率 ----------


class DimensionCompliance(BaseModel):
    dimension: PlanDimension
    sub_plan_id: UUID
    compliance_rate: float = Field(ge=0, le=1)
    expected_count: int = Field(default=0, ge=0)
    actual_count: int = Field(default=0, ge=0)
    average_attainment: float | None = Field(default=None)


class OverallCompliance(BaseModel):
    plan_id: UUID
    overall_compliance: float = Field(ge=0, le=1)
    dimensions: list[DimensionCompliance] = Field(default_factory=list)


# ---------- AI 分析 / 调整提议 ----------


class PlanAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    analysis_date: dt_date
    overall_compliance: float
    dimension_compliance: dict[str, float] = Field(default_factory=dict)
    has_anomaly: bool
    summary: str
    created_at: datetime


class AdjustmentProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    sub_plan_id: UUID | None = None
    reason: str
    proposed_changes: dict[str, object] = Field(default_factory=dict)
    status: ProposalStatus
    created_at: datetime
    resolved_at: datetime | None = None


__all__ = [
    "AdjustmentProposalResponse",
    "CheckInCreate",
    "CheckInResponse",
    "DailyExecution",
    "DailyTargetCurve",
    "DailyTargetPoint",
    "DimensionCompliance",
    "ExecutionStatus",
    "ExerciseSchedule",
    "ExerciseTarget",
    "OverallCompliance",
    "PlanAnalysisResponse",
    "PlanConversationMessage",
    "PlanCreate",
    "PlanDimension",
    "PlanDraft",
    "PlanPhase",
    "PlanPhaseDraft",
    "PlanProgress",
    "PlanResponse",
    "PlanStatus",
    "PlanStreamRequest",
    "PlanTargets",
    "PlanTask",
    "PlanTaskUpdate",
    "PlanTerminateRequest",
    "PlanType",
    "PlanUpdate",
    "ProposalStatus",
    "SubPlanCreate",
    "SubPlanResponse",
    "SubPlanTask",
    "SubPlanTaskDraft",
    "SubPlanUpdate",
    "TargetCurveStrategy",
    "WeightAnchor",
]
