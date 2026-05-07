"""认证模块 Pydantic 模型。

后端不再处理注册/登录/登出/刷新（前端直接调用 Supabase Auth SDK），
本文件仅保留 JWT 解析后的 :class:`CurrentUser` 领域模型。

详见 ``docs/specs/backend/00-architecture/auth.md``。
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CurrentUser(BaseModel):
    """从 JWT 中解析出的当前登录用户。

    ``profile`` 仅在使用 :func:`get_current_user_with_profile` 依赖时才会被填充，
    由依赖在「首次访问自动创建档案」流程中注入。
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID
    email: str | None = None
    role: str = "authenticated"
    # 实际类型为 ``HealthProfile | None``；此处用 ``Any`` 是为避免循环导入
    profile: Any | None = None


__all__ = ["CurrentUser"]
