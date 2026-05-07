"""用户系统 Repository。

封装 ``health_profiles`` / ``user_preferences`` / ``user_health_info``
/ ``user_settings`` 四张表的访问；所有方法强制以 ``user_id`` 过滤。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.db.models.user import (
    HealthProfile,
    UserHealthInfo,
    UserPreference,
    UserSetting,
)
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """用户档案/偏好/健康信息/设置 的统一仓储。"""

    # ---------- 通用工具 ----------

    @staticmethod
    def _apply_updates(instance: Any, fields: dict[str, Any]) -> None:
        """仅更新非 ``None`` 字段，符合 PUT 的语义（spec §4）。"""
        for key, value in fields.items():
            if value is None:
                continue
            setattr(instance, key, value)

    # ---------- HealthProfile ----------

    async def get_profile(self) -> HealthProfile | None:
        stmt = select(HealthProfile).where(HealthProfile.user_id == self.user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_empty_profile(self) -> HealthProfile:
        instance = HealthProfile(user_id=self.user_id)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update_profile(self, fields: dict[str, Any]) -> HealthProfile | None:
        profile = await self.get_profile()
        if profile is None:
            return None
        self._apply_updates(profile, fields)
        await self.session.flush()
        return profile

    # ---------- UserPreference ----------

    async def get_preferences(self) -> UserPreference | None:
        stmt = select(UserPreference).where(UserPreference.user_id == self.user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_or_create_preferences(self) -> UserPreference:
        instance = await self.get_preferences()
        if instance is not None:
            return instance
        instance = UserPreference(user_id=self.user_id)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update_preferences(self, fields: dict[str, Any]) -> UserPreference:
        instance = await self.get_or_create_preferences()
        self._apply_updates(instance, fields)
        await self.session.flush()
        return instance

    # ---------- UserHealthInfo ----------

    async def get_health_info(self) -> UserHealthInfo | None:
        stmt = select(UserHealthInfo).where(UserHealthInfo.user_id == self.user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_or_create_health_info(self) -> UserHealthInfo:
        instance = await self.get_health_info()
        if instance is not None:
            return instance
        instance = UserHealthInfo(user_id=self.user_id)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update_health_info(self, fields: dict[str, Any]) -> UserHealthInfo:
        instance = await self.get_or_create_health_info()
        self._apply_updates(instance, fields)
        await self.session.flush()
        return instance

    # ---------- UserSetting ----------

    async def get_settings(self) -> UserSetting | None:
        stmt = select(UserSetting).where(UserSetting.user_id == self.user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_or_create_settings(self) -> UserSetting:
        instance = await self.get_settings()
        if instance is not None:
            return instance
        instance = UserSetting(user_id=self.user_id)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update_settings(self, fields: dict[str, Any]) -> UserSetting:
        instance = await self.get_or_create_settings()
        self._apply_updates(instance, fields)
        await self.session.flush()
        return instance

    # ---------- 注册时初始化全部空记录 ----------

    async def initialize_for_user(self) -> HealthProfile:
        """注册成功后在四张表各创建一条空记录。"""
        profile = await self.get_profile()
        if profile is None:
            profile = await self.create_empty_profile()
        await self.get_or_create_preferences()
        await self.get_or_create_health_info()
        await self.get_or_create_settings()
        return profile


__all__ = ["UserRepository"]
