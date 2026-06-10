"""add weight body composition fields

Revision ID: 20260609_0011
Revises: 20260608_0010
Create Date: 2026-06-09 20:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260609_0011"
down_revision = "20260608_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("body_weight_records", sa.Column("body_fat_rate", sa.Float(), nullable=True))
    op.add_column("body_weight_records", sa.Column("muscle_rate", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("body_weight_records", "muscle_rate")
    op.drop_column("body_weight_records", "body_fat_rate")
