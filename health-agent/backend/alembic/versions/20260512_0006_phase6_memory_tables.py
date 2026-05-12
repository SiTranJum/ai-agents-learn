"""phase6 创建 AI 记忆表

Revision ID: 20260512_0006
Revises: 20260509_0005
Create Date: 2026-05-12
"""

from __future__ import annotations

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260512_0006"
down_revision = "20260509_0005"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.create_table(
        "memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("memory_type", sa.String(length=40), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("quality_score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("trigger_type", sa.String(length=50), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_index("ix_memories_user_id", "memories", ["user_id"])
    op.create_index("ix_memories_memory_type", "memories", ["memory_type"])
    op.create_index("ix_memories_status", "memories", ["status"])
    op.create_index("idx_memories_user_status", "memories", ["user_id", "status"])
    op.create_index("idx_memories_user_type", "memories", ["user_id", "memory_type"])
    op.execute(
        sa.text(
            "CREATE INDEX idx_memories_embedding ON memories "
            "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
        )
    )

    op.create_table(
        "memory_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("summary_content", sa.Text(), nullable=False),
        sa.Column("key_facts", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False),
        sa.Column("source_memory_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default="{}", nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_memory_summaries_user_id", "memory_summaries", ["user_id"])
    op.create_index("ix_memory_summaries_status", "memory_summaries", ["status"])
    op.create_index(
        "idx_memory_summaries_user_period",
        "memory_summaries",
        ["user_id", "period_start", "period_end"],
    )


def downgrade() -> None:
    op.drop_index("idx_memory_summaries_user_period", table_name="memory_summaries")
    op.drop_index("ix_memory_summaries_status", table_name="memory_summaries")
    op.drop_index("ix_memory_summaries_user_id", table_name="memory_summaries")
    op.drop_table("memory_summaries")

    op.drop_index("idx_memories_embedding", table_name="memories")
    op.drop_index("idx_memories_user_type", table_name="memories")
    op.drop_index("idx_memories_user_status", table_name="memories")
    op.drop_index("ix_memories_status", table_name="memories")
    op.drop_index("ix_memories_memory_type", table_name="memories")
    op.drop_index("ix_memories_user_id", table_name="memories")
    op.drop_table("memories")


