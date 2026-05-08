"""phase2 启用 pgvector 扩展

Revision ID: 20260508_0002
Revises: 20260506_0001
Create Date: 2026-05-08

为后续 RAG、Memory 等模块的 Vector(1024) 列与 IVFFlat 索引准备数据库扩展。
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260508_0002"
down_revision = "20260506_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))


def downgrade() -> None:
    op.execute(sa.text("DROP EXTENSION IF EXISTS vector"))

