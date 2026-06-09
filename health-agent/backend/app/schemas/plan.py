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


class PlanTargets(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    daily_calories: int | None = Field(default=None, gt=0)
    protein_target: float | None = Field(default=None, gt=0)
    fat_target: float | None = Field(default=None, gt=0)
    carbs_target: float | None = Field(default=None, gt=0)
    weight_target: float | None = Field(default=None, gt=0)


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
    content: str = Field(min_length=1, max_length=4000)


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


__all__ = [
    "CheckInCreate",
    "CheckInResponse",
    "DailyExecution",
    "ExecutionStatus",
    "PlanConversationMessage",
    "PlanCreate",
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
]
