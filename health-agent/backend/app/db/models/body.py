"""身体数据追踪 ORM 模型。"""

from __future__ import annotations

import uuid
from datetime import date, time

from sqlalchemy import Date, Float, Index, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class WeightRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """体重记录。"""

    __tablename__ = "body_weight_records"
    __table_args__ = (Index("idx_body_weight_user_date", "user_id", "date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    body_fat_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    muscle_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class MeasurementRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """围度记录。API 对前端命名为 measurement。"""

    __tablename__ = "body_measurement_records"
    __table_args__ = (Index("idx_body_measurement_user_date", "user_id", "date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    waist: Mapped[float | None] = mapped_column(Float, nullable=True)
    hip: Mapped[float | None] = mapped_column(Float, nullable=True)
    thigh: Mapped[float | None] = mapped_column(Float, nullable=True)
    arm: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class SleepRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """睡眠记录。"""

    __tablename__ = "body_sleep_records"
    __table_args__ = (Index("idx_body_sleep_user_date", "user_id", "date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    bed_time: Mapped[time] = mapped_column(Time, nullable=False)
    wake_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    quality: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExerciseRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """运动记录。"""

    __tablename__ = "body_exercise_records"
    __table_args__ = (Index("idx_body_exercise_user_date", "user_id", "date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    calories: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 计划关联（可空）：标记该记录由哪个计划任务自动生成，便于反向追溯与幂等去重
    plan_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    sub_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    # 来源：manual（用户手动）/ plan_task（任务自动生成）
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")


class WaterRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """每日饮水记录。POST 采用按日期累加语义。"""

    __tablename__ = "body_water_records"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_body_water_user_date"),
        Index("idx_body_water_user_date", "user_id", "date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount_ml: Mapped[int] = mapped_column(Integer, nullable=False)
    target_ml: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)


class BowelRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """排便记录。"""

    __tablename__ = "body_bowel_records"
    __table_args__ = (Index("idx_body_bowel_user_date", "user_id", "date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = [
    "BowelRecord",
    "ExerciseRecord",
    "MeasurementRecord",
    "SleepRecord",
    "WaterRecord",
    "WeightRecord",
]

