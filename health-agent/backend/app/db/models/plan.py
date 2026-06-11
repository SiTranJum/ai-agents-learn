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
    """User health plan header with compatibility task JSON and phased JSON."""

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
    phases: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
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


class SubPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """子计划：主计划下的一个维度计划（运动/体重/饮水…）。

    任务列表内嵌为 JSONB（含运动种类/时间安排/单任务目标值），沿用 ``Plan.tasks`` 的风格。
    """

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
    tasks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    # 该子计划的权重（用于整体完成率加权），默认等权
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)


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


class PlanAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI 对计划完成情况的分析结果（每日一条，保留历史）。"""

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
    overall_compliance: Mapped[float] = mapped_column(Float, nullable=False)
    # 各维度完成率快照 {"exercise": 0.6, "weight": 0.9, ...}
    dimension_compliance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    has_anomaly: Mapped[bool] = mapped_column(nullable=False, default=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)


class PlanAdjustmentProposal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI 提出的计划调整，等待用户确认。确认/拒绝后置为终态，不留历史 diff。"""

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


__all__ = [
    "DailyTarget",
    "Plan",
    "PlanAdjustmentProposal",
    "PlanAnalysis",
    "PlanCheckIn",
    "PlanExecution",
    "PlanTarget",
    "SubPlan",
]

