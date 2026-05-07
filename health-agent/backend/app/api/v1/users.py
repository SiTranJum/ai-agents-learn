"""用户系统 API 路由。

参见 ``docs/specs/backend/01-core-modules/user-system.md`` §2。
所有端点均要求 JWT 认证（通过 ``UserServiceDep`` 间接依赖 :func:`get_current_user`）。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.responses import success
from app.dependencies import (
    CurrentUserDep,
    CurrentUserWithProfileDep,
    UserServiceDep,
)
from app.schemas.common import ApiResponse
from app.schemas.user import (
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

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ApiResponse[UserFullResponse], summary="获取当前用户")
async def get_me(user: CurrentUserWithProfileDep, service: UserServiceDep):
    """获取当前用户完整信息（档案 + 偏好 + 健康信息 + 设置）。

    若该用户首次访问后端，依赖 :func:`get_current_user_with_profile`
    会自动为其创建空档案。
    """
    data = await service.get_full_profile(user.id, email=user.email or "")
    return success(data.model_dump(mode="json"))


@router.put(
    "/me/profile",
    response_model=ApiResponse[UserProfileResponse],
    summary="更新健康档案",
)
async def update_profile(
    payload: UserProfileUpdate,
    user: CurrentUserDep,
    service: UserServiceDep,
):
    data = await service.update_profile(user.id, payload)
    return success(data.model_dump(mode="json"))


@router.put(
    "/me/preferences",
    response_model=ApiResponse[UserPreferencesResponse],
    summary="更新饮食偏好",
)
async def update_preferences(
    payload: UserPreferencesUpdate,
    user: CurrentUserDep,
    service: UserServiceDep,
):
    data = await service.update_preferences(user.id, payload)
    return success(data.model_dump(mode="json"))


@router.put(
    "/me/health-info",
    response_model=ApiResponse[UserHealthInfoResponse],
    summary="更新健康信息",
)
async def update_health_info(
    payload: UserHealthInfoUpdate,
    user: CurrentUserDep,
    service: UserServiceDep,
):
    data = await service.update_health_info(user.id, payload)
    return success(data.model_dump(mode="json"))


@router.put(
    "/me/settings",
    response_model=ApiResponse[UserSettingsResponse],
    summary="更新用户设置",
)
async def update_settings(
    payload: UserSettingsUpdate,
    user: CurrentUserDep,
    service: UserServiceDep,
):
    data = await service.update_settings(user.id, payload)
    return success(data.model_dump(mode="json"))


__all__ = ["router"]
