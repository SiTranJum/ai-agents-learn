"""phase5 创建身体数据追踪表

Revision ID: 20260509_0005
Revises: 20260509_0004
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260509_0005"
down_revision = "20260509_0004"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "body_weight_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_body_weight_records_user_id", "body_weight_records", ["user_id"])
    op.create_index("ix_body_weight_records_date", "body_weight_records", ["date"])
    op.create_index("idx_body_weight_user_date", "body_weight_records", ["user_id", "date"])

    op.create_table(
        "body_measurement_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("waist", sa.Float(), nullable=True),
        sa.Column("hip", sa.Float(), nullable=True),
        sa.Column("thigh", sa.Float(), nullable=True),
        sa.Column("arm", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_body_measurement_records_user_id", "body_measurement_records", ["user_id"])
    op.create_index("ix_body_measurement_records_date", "body_measurement_records", ["date"])
    op.create_index("idx_body_measurement_user_date", "body_measurement_records", ["user_id", "date"])

    op.create_table(
        "body_sleep_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("bed_time", sa.Time(), nullable=False),
        sa.Column("wake_time", sa.Time(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("quality", sa.String(length=20), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_body_sleep_records_user_id", "body_sleep_records", ["user_id"])
    op.create_index("ix_body_sleep_records_date", "body_sleep_records", ["date"])
    op.create_index("idx_body_sleep_user_date", "body_sleep_records", ["user_id", "date"])

    op.create_table(
        "body_exercise_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("exercise_type", sa.String(length=50), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_body_exercise_records_user_id", "body_exercise_records", ["user_id"])
    op.create_index("ix_body_exercise_records_date", "body_exercise_records", ["date"])
    op.create_index("idx_body_exercise_user_date", "body_exercise_records", ["user_id", "date"])

    op.create_table(
        "body_water_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount_ml", sa.Integer(), nullable=False),
        sa.Column("target_ml", sa.Integer(), nullable=False, server_default="2000"),
        *_timestamps(),
        sa.UniqueConstraint("user_id", "date", name="uq_body_water_user_date"),
    )
    op.create_index("ix_body_water_records_user_id", "body_water_records", ["user_id"])
    op.create_index("ix_body_water_records_date", "body_water_records", ["date"])
    op.create_index("idx_body_water_user_date", "body_water_records", ["user_id", "date"])

    op.create_table(
        "body_bowel_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_body_bowel_records_user_id", "body_bowel_records", ["user_id"])
    op.create_index("ix_body_bowel_records_date", "body_bowel_records", ["date"])
    op.create_index("idx_body_bowel_user_date", "body_bowel_records", ["user_id", "date"])


def downgrade() -> None:
    op.drop_index("idx_body_bowel_user_date", table_name="body_bowel_records")
    op.drop_index("ix_body_bowel_records_date", table_name="body_bowel_records")
    op.drop_index("ix_body_bowel_records_user_id", table_name="body_bowel_records")
    op.drop_table("body_bowel_records")

    op.drop_index("idx_body_water_user_date", table_name="body_water_records")
    op.drop_index("ix_body_water_records_date", table_name="body_water_records")
    op.drop_index("ix_body_water_records_user_id", table_name="body_water_records")
    op.drop_table("body_water_records")

    op.drop_index("idx_body_exercise_user_date", table_name="body_exercise_records")
    op.drop_index("ix_body_exercise_records_date", table_name="body_exercise_records")
    op.drop_index("ix_body_exercise_records_user_id", table_name="body_exercise_records")
    op.drop_table("body_exercise_records")

    op.drop_index("idx_body_sleep_user_date", table_name="body_sleep_records")
    op.drop_index("ix_body_sleep_records_date", table_name="body_sleep_records")
    op.drop_index("ix_body_sleep_records_user_id", table_name="body_sleep_records")
    op.drop_table("body_sleep_records")

    op.drop_index("idx_body_measurement_user_date", table_name="body_measurement_records")
    op.drop_index("ix_body_measurement_records_date", table_name="body_measurement_records")
    op.drop_index("ix_body_measurement_records_user_id", table_name="body_measurement_records")
    op.drop_table("body_measurement_records")

    op.drop_index("idx_body_weight_user_date", table_name="body_weight_records")
    op.drop_index("ix_body_weight_records_date", table_name="body_weight_records")
    op.drop_index("ix_body_weight_records_user_id", table_name="body_weight_records")
    op.drop_table("body_weight_records")

