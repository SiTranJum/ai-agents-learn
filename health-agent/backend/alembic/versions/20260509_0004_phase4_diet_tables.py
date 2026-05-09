"""phase4 创建饮食记录表

Revision ID: 20260509_0004
Revises: 20260508_0003
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260509_0004"
down_revision = "20260508_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diet_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("meal_type", sa.String(length=10), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_diet_records_user_id", "diet_records", ["user_id"])
    op.create_index("ix_diet_records_meal_type", "diet_records", ["meal_type"])
    op.create_index("ix_diet_records_date", "diet_records", ["date"])
    op.create_index("idx_diet_records_user_date", "diet_records", ["user_id", "date"])
    op.create_index("idx_diet_records_user_meal", "diet_records", ["user_id", "date", "meal_type"])

    op.create_table(
        "diet_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("food_name", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("amount_grams", sa.Float(), nullable=False),
        sa.Column("cooking_method", sa.String(length=50), nullable=True),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("protein", sa.Float(), nullable=False),
        sa.Column("fat", sa.Float(), nullable=False),
        sa.Column("carbs", sa.Float(), nullable=False),
        sa.Column("fiber", sa.Float(), nullable=True),
        sa.Column("sodium", sa.Float(), nullable=True),
        sa.Column("data_source", sa.String(length=20), nullable=False),
        sa.Column("food_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["record_id"], ["diet_records.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_diet_items_record_id", "diet_items", ["record_id"])


def downgrade() -> None:
    op.drop_index("ix_diet_items_record_id", table_name="diet_items")
    op.drop_table("diet_items")
    op.drop_index("idx_diet_records_user_meal", table_name="diet_records")
    op.drop_index("idx_diet_records_user_date", table_name="diet_records")
    op.drop_index("ix_diet_records_date", table_name="diet_records")
    op.drop_index("ix_diet_records_meal_type", table_name="diet_records")
    op.drop_index("ix_diet_records_user_id", table_name="diet_records")
    op.drop_table("diet_records")
