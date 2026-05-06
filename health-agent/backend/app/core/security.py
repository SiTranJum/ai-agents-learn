"""安全相关工具。

Phase 0 仅提供 JWT 解码助手和 ``CurrentUser`` 领域对象的占位实现。
完整的 Supabase Auth 集成（含 audience / issuer 校验、刷新流程）将
在 Phase 1 落地。

参见 ``docs/specs/backend/00-architecture/auth.md``。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jose import JWTError, jwt

from app.config import settings
from app.core.exceptions import UnauthorizedException


@dataclass(slots=True, frozen=True)
class CurrentUser:
    """从 JWT 中解析出的当前登录用户身份。"""

    id: str
    email: str | None = None
    role: str = "authenticated"
    raw_claims: dict[str, Any] | None = None


def decode_supabase_jwt(token: str) -> dict[str, Any]:
    """校验 Supabase 签发的 JWT 并返回 claims。

    异常：
        UnauthorizedException: 当 token 缺失、格式错误、过期或非法时抛出。
    """
    if not token:
        raise UnauthorizedException("缺少认证令牌", code="AUTH_TOKEN_MISSING")
    if not settings.supabase_jwt_secret:
        # 安全策略：未配置 secret 一律拒绝，避免无签名 token 通过校验
        raise UnauthorizedException(
            "服务端未配置 JWT secret", code="AUTH_NOT_CONFIGURED"
        )
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[settings.supabase_jwt_algorithm],
            audience=settings.supabase_jwt_audience or None,
            options={"verify_aud": bool(settings.supabase_jwt_audience)},
        )
    except JWTError as exc:
        raise UnauthorizedException(
            "认证令牌无效或已过期", code="AUTH_TOKEN_INVALID"
        ) from exc


def claims_to_current_user(claims: dict[str, Any]) -> CurrentUser:
    """将 JWT claims 映射为 :class:`CurrentUser`。"""
    user_id = claims.get("sub")
    if not user_id:
        raise UnauthorizedException("令牌缺少 sub 字段", code="AUTH_TOKEN_INVALID")
    return CurrentUser(
        id=str(user_id),
        email=claims.get("email"),
        role=str(claims.get("role", "authenticated")),
        raw_claims=claims,
    )
