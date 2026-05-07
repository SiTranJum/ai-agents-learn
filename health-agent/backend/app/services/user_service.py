"""用户系统 Service 层。

封装健康档案、饮食偏好、健康信息、用户设置的业务逻辑。
依赖 :class:`UserRepository` 进行持久化；档案完整度计算和
对外脱敏的 ``get_profile_for_ai`` 也在此实现。

注：本 Service 不直接依赖 ``memory_service``。在 Phase 6 引入记忆模块
后，可在 ``update_*`` 方法中通过事件或显式调用触发记忆同步
（参见 spec §4.3）。
"""

from __future__ import annotations

import uuid
from typing import Any

from app.core.exceptions import NotFoundException
from app.db.models.user import (
    HealthProfile,
    UserHealthInfo,
    UserPreference,
    UserSetting,
)
from app.db.repositories.user_repo import UserRepository
from app.schemas.user import (
    InteractionMode,
    UserFullResponse,
    UserHealthInfoResponse,
    UserHealthInfoUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserProfileResponse,
    UserProfileUpdate,
    UserSettingsResponse,
    UserSettingsUpdate,
)

# 档案完整度参与字段（spec §4.2）
PROFILE_REQUIRED_FIELDS: tuple[str, ...] = (
    "nickname",
    "gender",
    "birth_date",
    "height",
    "current_weight",
    "target_weight",
    "activity_level",
)


class UserService:
    """用户系统业务服务。"""

    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    # ---------- 内部装配 ----------

    @staticmethod
    def _calculate_completeness(profile: HealthProfile) -> float:
        filled = sum(
            1
            for field in PROFILE_REQUIRED_FIELDS
            if getattr(profile, field, None) not in (None, "")
        )
        return round(filled / len(PROFILE_REQUIRED_FIELDS), 4)

    def _profile_to_response(self, profile: HealthProfile) -> UserProfileResponse:
        return UserProfileResponse(
            nickname=profile.nickname,
            gender=profile.gender,  # type: ignore[arg-type]
            birth_date=profile.birth_date,
            height=profile.height,
            current_weight=profile.current_weight,
            target_weight=profile.target_weight,
            activity_level=profile.activity_level,  # type: ignore[arg-type]
            profile_completeness=self._calculate_completeness(profile),
        )

    @staticmethod
    def _preferences_to_response(p: UserPreference) -> UserPreferencesResponse:
        return UserPreferencesResponse(
            diet_type=p.diet_type,  # type: ignore[arg-type]
            allergies=list(p.allergies or []),
            forbidden_foods=list(p.forbidden_foods or []),
            disliked_foods=list(p.disliked_foods or []),
        )

    @staticmethod
    def _health_info_to_response(h: UserHealthInfo) -> UserHealthInfoResponse:
        return UserHealthInfoResponse(
            diseases=list(h.diseases or []),
            medications=h.medications,
            medical_restrictions=h.medical_restrictions,
        )

    @staticmethod
    def _settings_to_response(s: UserSetting) -> UserSettingsResponse:
        return UserSettingsResponse(
            interaction_mode=InteractionMode(s.interaction_mode),
        )


    # ---------- 查询 ----------

    async def get_full_profile(self, user_id: uuid.UUID, *, email: str) -> UserFullResponse:
        profile = await self.repo.get_profile()
        if profile is None:
            raise NotFoundException("用户档案不存在", code="USER_NOT_FOUND")
        preferences = await self.repo.get_or_create_preferences()
        health_info = await self.repo.get_or_create_health_info()
        settings_row = await self.repo.get_or_create_settings()
        await self.repo.session.commit()
        return UserFullResponse(
            id=user_id,
            email=email,
            profile=self._profile_to_response(profile),
            preferences=self._preferences_to_response(preferences),
            health_info=self._health_info_to_response(health_info),
            settings=self._settings_to_response(settings_row),
        )

    async def get_profile_completeness(self, user_id: uuid.UUID) -> float:
        profile = await self.repo.get_profile()
        if profile is None:
            return 0.0
        return self._calculate_completeness(profile)

    async def get_profile_for_ai(self, user_id: uuid.UUID) -> dict[str, Any]:
        """供 AI 模块使用的脱敏档案（不含 user_id / email）。"""
        profile = await self.repo.get_profile()
        preferences = await self.repo.get_preferences()
        health_info = await self.repo.get_health_info()
        return {
            "profile": {
                "nickname": getattr(profile, "nickname", None),
                "gender": getattr(profile, "gender", None),
                "birth_date": getattr(profile, "birth_date", None),
                "height": getattr(profile, "height", None),
                "current_weight": getattr(profile, "current_weight", None),
                "target_weight": getattr(profile, "target_weight", None),
                "activity_level": getattr(profile, "activity_level", None),
                "completeness": (
                    self._calculate_completeness(profile) if profile else 0.0
                ),
            },
            "preferences": {
                "diet_type": getattr(preferences, "diet_type", None),
                "allergies": list(getattr(preferences, "allergies", []) or []),
                "forbidden_foods": list(
                    getattr(preferences, "forbidden_foods", []) or []
                ),
                "disliked_foods": list(
                    getattr(preferences, "disliked_foods", []) or []
                ),
            },
            "health_info": {
                "diseases": list(getattr(health_info, "diseases", []) or []),
                "medications": getattr(health_info, "medications", None),
                "medical_restrictions": getattr(
                    health_info, "medical_restrictions", None
                ),
            },
        }

    # ---------- 更新 ----------

    async def update_profile(
        self, user_id: uuid.UUID, data: UserProfileUpdate
    ) -> UserProfileResponse:
        fields = data.model_dump(exclude_unset=True)
        profile = await self.repo.update_profile(fields)
        if profile is None:
            raise NotFoundException("用户档案不存在", code="USER_NOT_FOUND")
        await self.repo.session.commit()
        # TODO(Phase 6): memory_service.on_profile_updated(user_id, data)
        return self._profile_to_response(profile)

    async def update_preferences(
        self, user_id: uuid.UUID, data: UserPreferencesUpdate
    ) -> UserPreferencesResponse:
        fields = data.model_dump(exclude_unset=True)
        instance = await self.repo.update_preferences(fields)
        await self.repo.session.commit()
        # TODO(Phase 6): memory_service.on_profile_updated(user_id, data)
        return self._preferences_to_response(instance)

    async def update_health_info(
        self, user_id: uuid.UUID, data: UserHealthInfoUpdate
    ) -> UserHealthInfoResponse:
        fields = data.model_dump(exclude_unset=True)
        instance = await self.repo.update_health_info(fields)
        await self.repo.session.commit()
        # TODO(Phase 6): memory_service.on_profile_updated(user_id, data)
        return self._health_info_to_response(instance)

    async def update_settings(
        self, user_id: uuid.UUID, data: UserSettingsUpdate
    ) -> UserSettingsResponse:
        fields = data.model_dump(exclude_unset=True)
        instance = await self.repo.update_settings(fields)
        await self.repo.session.commit()
        return self._settings_to_response(instance)


__all__ = ["UserService", "PROFILE_REQUIRED_FIELDS"]
