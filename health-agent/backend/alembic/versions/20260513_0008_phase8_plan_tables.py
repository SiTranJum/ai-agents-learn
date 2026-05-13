"""phase8 创建计划系统表

Revision ID: 20260513_0008
Revises: 20260512_0007
Create Date: 2026-05-13
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260513_0008"
down_revision = "20260512_0007"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("goal_description", sa.Text(), nullable=False),
        sa.Column("plan_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("tasks", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("terminated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("termination_reason", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_plans_user_id", "plans", ["user_id"])
    op.create_index("ix_plans_plan_type", "plans", ["plan_type"])
    op.create_index("ix_plans_status", "plans", ["status"])
    op.create_index("idx_plans_user_status", "plans", ["user_id", "status"])
    op.create_index("idx_plans_user_created", "plans", ["user_id", "created_at"])
    op.create_index(
        "uq_plans_one_active_per_user",
        "plans",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND deleted_at IS NULL"),
    )

    op.create_table(
        "plan_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("daily_calories", sa.Integer(), nullable=True),
        sa.Column("protein_target", sa.Float(), nullable=True),
        sa.Column("fat_target", sa.Float(), nullable=True),
        sa.Column("carbs_target", sa.Float(), nullable=True),
        sa.Column("weight_target", sa.Float(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("plan_id", name="uq_plan_targets_plan_id"),
    )
    op.create_index("ix_plan_targets_user_id", "plan_targets", ["user_id"])
    op.create_index("ix_plan_targets_plan_id", "plan_targets", ["plan_id"])

    op.create_table(
        "plan_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("calories_consumed", sa.Float(), nullable=False),
        sa.Column("calories_target", sa.Float(), nullable=False),
        sa.Column("protein", sa.Float(), nullable=False),
        sa.Column("fat", sa.Float(), nullable=False),
        sa.Column("carbs", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("plan_id", "date", name="uq_plan_execution_plan_date"),
    )
    op.create_index("ix_plan_executions_user_id", "plan_executions", ["user_id"])
    op.create_index("ix_plan_executions_plan_id", "plan_executions", ["plan_id"])
    op.create_index("ix_plan_executions_date", "plan_executions", ["date"])
    op.create_index("ix_plan_executions_status", "plan_executions", ["status"])
    op.create_index("idx_plan_execution_user_date", "plan_executions", ["user_id", "date"])
    op.create_index("idx_plan_execution_plan_status", "plan_executions", ["plan_id", "status"])

    op.create_table(
        "plan_check_ins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("plan_id", "task_id", "date", name="uq_plan_check_in_plan_task_date"),
    )
    op.create_index("ix_plan_check_ins_user_id", "plan_check_ins", ["user_id"])
    op.create_index("ix_plan_check_ins_plan_id", "plan_check_ins", ["plan_id"])
    op.create_index("ix_plan_check_ins_date", "plan_check_ins", ["date"])
    op.create_index("idx_plan_check_in_user_date", "plan_check_ins", ["user_id", "date"])


def downgrade() -> None:
    op.drop_index("idx_plan_check_in_user_date", table_name="plan_check_ins")
    op.drop_index("ix_plan_check_ins_date", table_name="plan_check_ins")
    op.drop_index("ix_plan_check_ins_plan_id", table_name="plan_check_ins")
    op.drop_index("ix_plan_check_ins_user_id", table_name="plan_check_ins")
    op.drop_table("plan_check_ins")
    op.drop_index("idx_plan_execution_plan_status", table_name="plan_executions")
    op.drop_index("idx_plan_execution_user_date", table_name="plan_executions")
    op.drop_index("ix_plan_executions_status", table_name="plan_executions")
    op.drop_index("ix_plan_executions_date", table_name="plan_executions")
    op.drop_index("ix_plan_executions_plan_id", table_name="plan_executions")
    op.drop_index("ix_plan_executions_user_id", table_name="plan_executions")
    op.drop_table("plan_executions")
    op.drop_index("ix_plan_targets_plan_id", table_name="plan_targets")
    op.drop_index("ix_plan_targets_user_id", table_name="plan_targets")
    op.drop_table("plan_targets")
    op.drop_index("uq_plans_one_active_per_user", table_name="plans")
    op.drop_index("idx_plans_user_created", table_name="plans")
    op.drop_index("idx_plans_user_status", table_name="plans")
    op.drop_index("ix_plans_status", table_name="plans")
    op.drop_index("ix_plans_plan_type", table_name="plans")
    op.drop_index("ix_plans_user_id", table_name="plans")
    op.drop_table("plans")

