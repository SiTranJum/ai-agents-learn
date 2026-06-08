"""add plan phases column

Revision ID: 20260608_0010
Revises: 20260513_0009
Create Date: 2026-06-08 16:50:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260608_0010"
down_revision = "20260513_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plans",
        sa.Column("phases", JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )


def downgrade() -> None:
    op.drop_column("plans", "phases")
