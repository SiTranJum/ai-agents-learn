"""用户系统 Pydantic 模型。

定义参见 ``docs/specs/backend/01-core-modules/user-system.md`` §3。
所有 PUT 字段均为 Optional，未传字段保持原值不变。
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------- 枚举 ----------


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    heavy = "heavy"


class DietType(str, Enum):
    normal = "normal"
    vegetarian = "vegetarian"
    vegan = "vegan"
    keto = "keto"
    low_carb = "low_carb"
    low_fat = "low_fat"
    mediterranean = "mediterranean"


class InteractionMode(str, Enum):
    efficiency = "efficiency"
    confirmation = "confirmation"
    learning = "learning"


# ---------- 请求模型 ----------


class UserProfileUpdate(BaseModel):
    """健康档案更新请求。"""

    nickname: Optional[str] = Field(None, min_length=2, max_length=20)
    gender: Optional[Gender] = None
    birth_date: Optional[date] = None
    height: Optional[float] = Field(None, ge=100, le=250, description="身高 cm")
    current_weight: Optional[float] = Field(None, ge=30, le=300, description="当前体重 kg")
    target_weight: Optional[float] = Field(None, ge=30, le=300, description="目标体重 kg")
    activity_level: Optional[ActivityLevel] = None


class UserPreferencesUpdate(BaseModel):
    """饮食偏好更新请求。"""

    diet_type: Optional[DietType] = None
    allergies: Optional[list[str]] = Field(None, max_length=20)
    forbidden_foods: Optional[list[str]] = Field(None, max_length=50)
    disliked_foods: Optional[list[str]] = Field(None, max_length=50)


class UserHealthInfoUpdate(BaseModel):
    """健康信息更新请求。"""

    diseases: Optional[list[str]] = Field(None, max_length=20)
    medications: Optional[str] = Field(None, max_length=500)
    medical_restrictions: Optional[str] = Field(None, max_length=500)


class UserSettingsUpdate(BaseModel):
    """用户设置更新请求。"""

    interaction_mode: Optional[InteractionMode] = None


# ---------- 响应模型 ----------


class UserProfileResponse(BaseModel):
    """健康档案响应（含完整度）。"""

    model_config = ConfigDict(from_attributes=True)

    nickname: Optional[str] = None
    gender: Optional[Gender] = None
    birth_date: Optional[date] = None
    height: Optional[float] = None
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    profile_completeness: float = Field(default=0.0, ge=0.0, le=1.0)


class UserPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    diet_type: Optional[DietType] = None
    allergies: list[str] = []
    forbidden_foods: list[str] = []
    disliked_foods: list[str] = []


class UserHealthInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    diseases: list[str] = []
    medications: Optional[str] = None
    medical_restrictions: Optional[str] = None


class UserSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interaction_mode: InteractionMode = InteractionMode.confirmation


class UserFullResponse(BaseModel):
    """``GET /users/me`` 的聚合响应。"""

    id: UUID
    email: str
    profile: UserProfileResponse
    preferences: UserPreferencesResponse
    health_info: UserHealthInfoResponse
    settings: UserSettingsResponse


__all__ = [
    "Gender",
    "ActivityLevel",
    "DietType",
    "InteractionMode",
    "UserProfileUpdate",
    "UserPreferencesUpdate",
    "UserHealthInfoUpdate",
    "UserSettingsUpdate",
    "UserProfileResponse",
    "UserPreferencesResponse",
    "UserHealthInfoResponse",
    "UserSettingsResponse",
    "UserFullResponse",
]
