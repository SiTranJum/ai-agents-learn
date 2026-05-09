"""phase3 创建知识库表

Revision ID: 20260508_0003
Revises: 20260508_0002
Create Date: 2026-05-08
"""

from __future__ import annotations

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260508_0003"
down_revision = "20260508_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # noinspection SqlNoDataSourceInspection
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    op.create_table(
        "foods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("aliases", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("calories_per_100g", sa.Float(), nullable=False),
        sa.Column("protein_per_100g", sa.Float(), nullable=False),
        sa.Column("fat_per_100g", sa.Float(), nullable=False),
        sa.Column("carbs_per_100g", sa.Float(), nullable=False),
        sa.Column("fiber_per_100g", sa.Float(), nullable=True),
        sa.Column("sodium_per_100g", sa.Float(), nullable=True),
        sa.Column("sugar_per_100g", sa.Float(), nullable=True),
        sa.Column("common_portions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("data_source", sa.String(length=50), nullable=False, server_default="manual"),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_foods_name"),
    )
    op.create_index("ix_foods_name", "foods", ["name"])
    op.create_index("ix_foods_category", "foods", ["category"])
    # noinspection SqlNoDataSourceInspection
    op.execute(
        sa.text(
            "CREATE INDEX idx_foods_embedding ON foods "
            "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"
        )
    )

    op.create_table(
        "knowledge_docs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("title", name="uq_knowledge_docs_title"),
    )
    op.create_index("ix_knowledge_docs_title", "knowledge_docs", ["title"])
    op.create_index(
        "idx_knowledge_docs_metadata",
        "knowledge_docs",
        ["metadata"],
        postgresql_using="gin",
    )
    # noinspection SqlNoDataSourceInspection
    op.execute(
        sa.text(
            "CREATE INDEX idx_knowledge_docs_embedding ON knowledge_docs "
            "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"
        )
    )


def downgrade() -> None:
    # noinspection SqlNoDataSourceInspection
    op.execute(sa.text("DROP INDEX IF EXISTS idx_knowledge_docs_embedding"))
    op.drop_index("idx_knowledge_docs_metadata", table_name="knowledge_docs")
    op.drop_index("ix_knowledge_docs_title", table_name="knowledge_docs")
    op.drop_table("knowledge_docs")

    # noinspection SqlNoDataSourceInspection
    op.execute(sa.text("DROP INDEX IF EXISTS idx_foods_embedding"))
    op.drop_index("ix_foods_category", table_name="foods")
    op.drop_index("ix_foods_name", table_name="foods")
    op.drop_table("foods")

