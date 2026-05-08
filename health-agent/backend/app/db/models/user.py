"""用户系统数据库模型。

定义参见 ``docs/specs/backend/01-core-modules/user-system.md``。
所有表通过 ``user_id`` 与 ``auth.users`` 关联（Supabase Auth 托管，
本服务不直接维护该表）。
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class HealthProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """健康档案 — 基础身体信息。"""

    __tablename__ = "health_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    nickname: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    goal_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    daily_calorie_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )


class UserPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """饮食偏好。"""

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    diet_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    allergies: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    forbidden_foods: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    disliked_foods: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )


class UserHealthInfo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """健康信息（疾病、用药、医嘱）。"""

    __tablename__ = "user_health_info"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    diseases: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    medications: Mapped[str | None] = mapped_column(Text, nullable=True)
    medical_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserSetting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """用户设置（交互模式等）。"""

    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    interaction_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="confirmation"
    )


__all__ = ["HealthProfile", "UserPreference", "UserHealthInfo", "UserSetting"]
