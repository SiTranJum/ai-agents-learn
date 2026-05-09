"""phase1 用户系统初始迁移

Revision ID: 20260506_0001
Revises:
Create Date: 2026-05-06

创建用户档案/偏好/健康信息/设置 4 张表。所有表通过 ``user_id`` 与
Supabase Auth 的 ``auth.users`` 关联（外键由 Supabase 托管，本迁移
仅声明列与索引）。

字段与 ``docs/specs/shared/api-contract.md`` §2-§3 保持一致：
- health_profiles 含 ``goal_type``/``daily_calorie_target``/``onboarding_completed``
- user_preferences.diet_type 可空（无默认值），枚举见契约 §2.4
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260506_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------- health_profiles ----------
    op.create_table(
        "health_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nickname", sa.String(length=20), nullable=True),
        sa.Column("gender", sa.String(length=10), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("current_weight", sa.Float(), nullable=True),
        sa.Column("target_weight", sa.Float(), nullable=True),
        sa.Column("activity_level", sa.String(length=20), nullable=True),
        # 目标字段（api-contract.md §2.3 / §3.1）
        sa.Column("goal_type", sa.String(length=20), nullable=True),
        sa.Column("daily_calorie_target", sa.Integer(), nullable=True),
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_health_profiles_user_id"),
    )
    op.create_index(
        "ix_health_profiles_user_id", "health_profiles", ["user_id"]
    )

    # ---------- user_preferences ----------
    # diet_type 可空、无默认值（api-contract.md §2.4 枚举 balanced/low_carb/...）
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("diet_type", sa.String(length=20), nullable=True),
        sa.Column(
            "allergies",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "forbidden_foods",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "disliked_foods",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
    )
    op.create_index(
        "ix_user_preferences_user_id", "user_preferences", ["user_id"]
    )

    # ---------- user_health_info ----------
    op.create_table(
        "user_health_info",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "diseases",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("medications", sa.Text(), nullable=True),
        sa.Column("medical_restrictions", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_user_health_info_user_id"),
    )
    op.create_index(
        "ix_user_health_info_user_id", "user_health_info", ["user_id"]
    )

    # ---------- user_settings ----------
    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "interaction_mode",
            sa.String(length=20),
            nullable=False,
            server_default="confirmation",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_user_settings_user_id"),
    )
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_settings_user_id", table_name="user_settings")
    op.drop_table("user_settings")
    op.drop_index("ix_user_health_info_user_id", table_name="user_health_info")
    op.drop_table("user_health_info")
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_table("user_preferences")
    op.drop_index("ix_health_profiles_user_id", table_name="health_profiles")
    op.drop_table("health_profiles")
