"""安全相关工具。

支持 Supabase 双算法 JWT 验证：
- ES256 / RS256（非对称）：从 JWKS 端点动态获取公钥
- HS256（对称，向后兼容）：使用 SUPABASE_JWT_SECRET

参见 ``docs/specs/backend/00-architecture/auth.md``。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt as pyjwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from app.config import settings
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)

_ASYMMETRIC_ALGORITHMS = {"ES256", "RS256", "ES384", "RS384", "ES512", "RS512"}


@dataclass(slots=True, frozen=True)
class CurrentUser:
    """从 JWT 中解析出的当前登录用户身份。"""

    id: str
    email: str | None = None
    role: str = "authenticated"
    raw_claims: dict[str, Any] | None = None


@lru_cache(maxsize=1)
def _get_jwks_client() -> PyJWKClient:
    """返回缓存的 JWKS 客户端（进程内单例）。

    PyJWKClient 内部已缓存公钥，避免每次验证都拉取 JWKS 端点。
    """
    jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    logger.info("初始化 JWKS 客户端: url=%s", jwks_url)
    return PyJWKClient(jwks_url, cache_keys=True)


def _decode_with_asymmetric(token: str) -> dict[str, Any]:
    """使用 JWKS 公钥验证非对称签名 JWT。"""
    if not settings.supabase_url:
        raise UnauthorizedException(
            "服务端未配置 SUPABASE_URL", code="AUTH_NOT_CONFIGURED"
        )
    client = _get_jwks_client()
    signing_key = client.get_signing_key_from_jwt(token)
    return pyjwt.decode(
        token,
        signing_key.key,
        algorithms=[settings.supabase_jwt_algorithm],
        audience=settings.supabase_jwt_audience or None,
        options={"verify_aud": bool(settings.supabase_jwt_audience)},
    )


def _decode_with_symmetric(token: str) -> dict[str, Any]:
    """使用 JWT Secret 验证对称签名 JWT（HS256 等）。"""
    if not settings.supabase_jwt_secret:
        raise UnauthorizedException(
            "服务端未配置 JWT secret", code="AUTH_NOT_CONFIGURED"
        )
    return pyjwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=[settings.supabase_jwt_algorithm],
        audience=settings.supabase_jwt_audience or None,
        options={"verify_aud": bool(settings.supabase_jwt_audience)},
    )


def decode_supabase_jwt(token: str) -> dict[str, Any]:
    """校验 Supabase 签发的 JWT 并返回 claims。

    根据 ``settings.supabase_jwt_algorithm`` 自动选择验证方式：
    - ES256/RS256/...：通过 JWKS 公钥（推荐，新 Supabase 项目默认）
    - HS256：通过对称 JWT Secret（旧项目兼容）

    异常：
        UnauthorizedException: 当 token 缺失、格式错误、过期或非法时抛出。
    """
    if not token:
        raise UnauthorizedException("缺少认证令牌", code="AUTH_TOKEN_MISSING")

    # 调试：解码 token header 查看实际算法
    try:
        import base64
        import json
        header_b64 = token.split('.')[0]
        header_b64 += '=' * (4 - len(header_b64) % 4)
        header_json = base64.urlsafe_b64decode(header_b64)
        actual_header = json.loads(header_json)
        logger.info(f"Token header: {actual_header}")
        logger.info(f"配置的算法: {settings.supabase_jwt_algorithm}")
    except Exception as e:
        logger.warning(f"无法解码 token header: {e}")

    algorithm = settings.supabase_jwt_algorithm
    try:
        if algorithm in _ASYMMETRIC_ALGORITHMS:
            return _decode_with_asymmetric(token)
        return _decode_with_symmetric(token)
    except UnauthorizedException:
        raise
    except InvalidTokenError as exc:
        logger.warning("JWT 验证失败: %s", exc)
        raise UnauthorizedException(
            "认证令牌无效或已过期", code="AUTH_TOKEN_INVALID"
        ) from exc
    except Exception as exc:  # noqa: BLE001 - 防御性兜底（如 JWKS 网络错误）
        logger.error("JWT 验证发生未知错误: %s", exc, exc_info=True)
        raise UnauthorizedException(
            "认证令牌验证失败", code="AUTH_TOKEN_INVALID"
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
