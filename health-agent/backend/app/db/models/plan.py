"""Plan system ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Plan(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """User health plan header and task JSON."""

    __tablename__ = "plans"
    __table_args__ = (
        Index("idx_plans_user_status", "user_id", "status"),
        Index("idx_plans_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    goal_description: Mapped[str] = mapped_column(Text, nullable=False)
    plan_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    tasks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    terminated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    termination_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class PlanTarget(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Numeric targets attached to a plan."""

    __tablename__ = "plan_targets"
    __table_args__ = (UniqueConstraint("plan_id", name="uq_plan_targets_plan_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    daily_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_target: Mapped[float | None] = mapped_column(Float, nullable=True)


class PlanExecution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Daily execution record generated from diet/body data."""

    __tablename__ = "plan_executions"
    __table_args__ = (
        UniqueConstraint("plan_id", "date", name="uq_plan_execution_plan_date"),
        Index("idx_plan_execution_user_date", "user_id", "date"),
        Index("idx_plan_execution_plan_status", "plan_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    calories_consumed: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    calories_target: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    protein: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    fat: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    carbs: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)


class PlanCheckIn(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Manual check-in for a plan or task."""

    __tablename__ = "plan_check_ins"
    __table_args__ = (
        UniqueConstraint("plan_id", "task_id", "date", name="uq_plan_check_in_plan_task_date"),
        Index("idx_plan_check_in_user_date", "user_id", "date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    completed: Mapped[bool] = mapped_column(nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = ["Plan", "PlanCheckIn", "PlanExecution", "PlanTarget"]

