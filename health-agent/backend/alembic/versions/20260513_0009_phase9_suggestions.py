"""phase9 创建 AI 建议表

Revision ID: 20260513_0009
Revises: 20260513_0008
Create Date: 2026-05-13
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260513_0009"
down_revision = "20260513_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("suggestion_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("basis", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("meal_type", sa.String(length=20), nullable=True),
        sa.Column("dimension", sa.String(length=50), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("data_support", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("user_feedback", sa.String(length=20), nullable=True),
        sa.Column("feedback_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_suggestions_user_id", "suggestions", ["user_id"])
    op.create_index("ix_suggestions_suggestion_type", "suggestions", ["suggestion_type"])
    op.create_index("ix_suggestions_meal_type", "suggestions", ["meal_type"])
    op.create_index("ix_suggestions_expires_at", "suggestions", ["expires_at"])
    op.create_index("idx_suggestions_user_type_expires", "suggestions", ["user_id", "suggestion_type", "expires_at"])
    op.create_index("idx_suggestions_user_created", "suggestions", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_suggestions_user_created", table_name="suggestions")
    op.drop_index("idx_suggestions_user_type_expires", table_name="suggestions")
    op.drop_index("ix_suggestions_expires_at", table_name="suggestions")
    op.drop_index("ix_suggestions_meal_type", table_name="suggestions")
    op.drop_index("ix_suggestions_suggestion_type", table_name="suggestions")
    op.drop_index("ix_suggestions_user_id", table_name="suggestions")
    op.drop_table("suggestions")

