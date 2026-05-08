"""用户系统 Pydantic 模型。

定义参见 ``docs/specs/shared/api-contract.md`` §3、
``docs/specs/backend/01-core-modules/user-system.md`` §3。
所有 PUT 字段均为 Optional，未传字段保持原值不变。
"""

from __future__ import annotations

from datetime import date, datetime
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


class GoalType(str, Enum):
    lose_fat = "lose_fat"
    gain_muscle = "gain_muscle"
    maintain = "maintain"
    healthy_diet = "healthy_diet"


class DietType(str, Enum):
    balanced = "balanced"
    low_carb = "low_carb"
    high_protein = "high_protein"
    vegetarian = "vegetarian"
    vegan = "vegan"
    keto = "keto"
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
    goal_type: Optional[GoalType] = None
    daily_calorie_target: Optional[int] = Field(
        None, ge=500, le=6000, description="每日热量目标 kcal"
    )


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


class OnboardingPayload(BaseModel):
    """POST /users/me/onboarding 的一次性提交请求体。

    聚合 profile / preferences / health_info 三段，语义同各分片 PUT：
    - 字段全部 Optional；
    - 未传字段不改原值；
    - 成功后将 ``onboarding_completed`` 置 True；
    - 幂等：对已完成 onboarding 的用户再次调用，仍执行聚合更新。
    """

    profile: Optional[UserProfileUpdate] = None
    preferences: Optional[UserPreferencesUpdate] = None
    health_info: Optional[UserHealthInfoUpdate] = None


# ---------- 响应模型 ----------


class UserProfileResponse(BaseModel):
    """健康档案响应（含完整度 + 目标字段）。"""

    model_config = ConfigDict(from_attributes=True)

    nickname: Optional[str] = None
    gender: Optional[Gender] = None
    birth_date: Optional[date] = None
    height: Optional[float] = None
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    goal_type: Optional[GoalType] = None
    daily_calorie_target: Optional[int] = None
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
    """``GET /users/me`` / ``POST /users/me/onboarding`` 的聚合响应。"""

    id: UUID
    email: str
    onboarding_completed: bool = False
    profile: UserProfileResponse
    preferences: UserPreferencesResponse
    health_info: UserHealthInfoResponse
    settings: UserSettingsResponse
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


__all__ = [
    "Gender",
    "ActivityLevel",
    "GoalType",
    "DietType",
    "InteractionMode",
    "UserProfileUpdate",
    "UserPreferencesUpdate",
    "UserHealthInfoUpdate",
    "UserSettingsUpdate",
    "OnboardingPayload",
    "UserProfileResponse",
    "UserPreferencesResponse",
    "UserHealthInfoResponse",
    "UserSettingsResponse",
    "UserFullResponse",
]
