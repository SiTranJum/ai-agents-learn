"""计划模块拆分：子计划/每日目标/AI 分析/调整提议 + 运动记录计划关联

Revision ID: 20260610_0012
Revises: 20260609_0011
Create Date: 2026-06-10
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260610_0012"
down_revision = "20260609_0011"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    # ---------- plan_sub_plans ----------
    op.create_table(
        "plan_sub_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dimension", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("goal_description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("tasks", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_plan_sub_plans_user_id", "plan_sub_plans", ["user_id"])
    op.create_index("ix_plan_sub_plans_plan_id", "plan_sub_plans", ["plan_id"])
    op.create_index("ix_plan_sub_plans_dimension", "plan_sub_plans", ["dimension"])
    op.create_index("ix_plan_sub_plans_status", "plan_sub_plans", ["status"])
    op.create_index("idx_sub_plan_plan", "plan_sub_plans", ["plan_id"])
    op.create_index("idx_sub_plan_user_dimension", "plan_sub_plans", ["user_id", "dimension"])

    # ---------- plan_daily_targets ----------
    op.create_table(
        "plan_daily_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sub_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_sub_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dimension", sa.String(length=30), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("sub_plan_id", "date", name="uq_daily_target_sub_plan_date"),
    )
    op.create_index("ix_plan_daily_targets_user_id", "plan_daily_targets", ["user_id"])
    op.create_index("ix_plan_daily_targets_plan_id", "plan_daily_targets", ["plan_id"])
    op.create_index("ix_plan_daily_targets_sub_plan_id", "plan_daily_targets", ["sub_plan_id"])
    op.create_index("ix_plan_daily_targets_date", "plan_daily_targets", ["date"])
    op.create_index(
        "idx_daily_target_user_dim_date", "plan_daily_targets", ["user_id", "dimension", "date"]
    )
    op.create_index("idx_daily_target_plan_date", "plan_daily_targets", ["plan_id", "date"])

    # ---------- plan_analyses ----------
    op.create_table(
        "plan_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("overall_compliance", sa.Float(), nullable=False),
        sa.Column(
            "dimension_compliance",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("has_anomaly", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("summary", sa.Text(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("plan_id", "analysis_date", name="uq_plan_analysis_plan_date"),
    )
    op.create_index("ix_plan_analyses_user_id", "plan_analyses", ["user_id"])
    op.create_index("ix_plan_analyses_plan_id", "plan_analyses", ["plan_id"])
    op.create_index("ix_plan_analyses_analysis_date", "plan_analyses", ["analysis_date"])
    op.create_index("idx_plan_analysis_user_date", "plan_analyses", ["user_id", "analysis_date"])

    # ---------- plan_adjustment_proposals ----------
    op.create_table(
        "plan_adjustment_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sub_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "proposed_changes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_plan_adjustment_proposals_user_id", "plan_adjustment_proposals", ["user_id"])
    op.create_index("ix_plan_adjustment_proposals_plan_id", "plan_adjustment_proposals", ["plan_id"])
    op.create_index(
        "ix_plan_adjustment_proposals_sub_plan_id", "plan_adjustment_proposals", ["sub_plan_id"]
    )
    op.create_index("ix_plan_adjustment_proposals_status", "plan_adjustment_proposals", ["status"])
    op.create_index("idx_adjust_plan_status", "plan_adjustment_proposals", ["plan_id", "status"])
    op.create_index("idx_adjust_user_status", "plan_adjustment_proposals", ["user_id", "status"])

    # ---------- body_exercise_records: 计划关联字段 ----------
    op.add_column(
        "body_exercise_records",
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "body_exercise_records",
        sa.Column("sub_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "body_exercise_records",
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "body_exercise_records",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="manual"),
    )
    op.create_index("ix_body_exercise_records_plan_id", "body_exercise_records", ["plan_id"])
    op.create_index("ix_body_exercise_records_sub_plan_id", "body_exercise_records", ["sub_plan_id"])
    op.create_index("ix_body_exercise_records_task_id", "body_exercise_records", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_body_exercise_records_task_id", table_name="body_exercise_records")
    op.drop_index("ix_body_exercise_records_sub_plan_id", table_name="body_exercise_records")
    op.drop_index("ix_body_exercise_records_plan_id", table_name="body_exercise_records")
    op.drop_column("body_exercise_records", "source")
    op.drop_column("body_exercise_records", "task_id")
    op.drop_column("body_exercise_records", "sub_plan_id")
    op.drop_column("body_exercise_records", "plan_id")

    op.drop_index("idx_adjust_user_status", table_name="plan_adjustment_proposals")
    op.drop_index("idx_adjust_plan_status", table_name="plan_adjustment_proposals")
    op.drop_index("ix_plan_adjustment_proposals_status", table_name="plan_adjustment_proposals")
    op.drop_index("ix_plan_adjustment_proposals_sub_plan_id", table_name="plan_adjustment_proposals")
    op.drop_index("ix_plan_adjustment_proposals_plan_id", table_name="plan_adjustment_proposals")
    op.drop_index("ix_plan_adjustment_proposals_user_id", table_name="plan_adjustment_proposals")
    op.drop_table("plan_adjustment_proposals")

    op.drop_index("idx_plan_analysis_user_date", table_name="plan_analyses")
    op.drop_index("ix_plan_analyses_analysis_date", table_name="plan_analyses")
    op.drop_index("ix_plan_analyses_plan_id", table_name="plan_analyses")
    op.drop_index("ix_plan_analyses_user_id", table_name="plan_analyses")
    op.drop_table("plan_analyses")

    op.drop_index("idx_daily_target_plan_date", table_name="plan_daily_targets")
    op.drop_index("idx_daily_target_user_dim_date", table_name="plan_daily_targets")
    op.drop_index("ix_plan_daily_targets_date", table_name="plan_daily_targets")
    op.drop_index("ix_plan_daily_targets_sub_plan_id", table_name="plan_daily_targets")
    op.drop_index("ix_plan_daily_targets_plan_id", table_name="plan_daily_targets")
    op.drop_index("ix_plan_daily_targets_user_id", table_name="plan_daily_targets")
    op.drop_table("plan_daily_targets")

    op.drop_index("idx_sub_plan_user_dimension", table_name="plan_sub_plans")
    op.drop_index("idx_sub_plan_plan", table_name="plan_sub_plans")
    op.drop_index("ix_plan_sub_plans_status", table_name="plan_sub_plans")
    op.drop_index("ix_plan_sub_plans_dimension", table_name="plan_sub_plans")
    op.drop_index("ix_plan_sub_plans_plan_id", table_name="plan_sub_plans")
    op.drop_index("ix_plan_sub_plans_user_id", table_name="plan_sub_plans")
    op.drop_table("plan_sub_plans")

