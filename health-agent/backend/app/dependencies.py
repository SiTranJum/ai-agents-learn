"""全局 FastAPI 依赖。

模块特有的依赖（service、repository）应放在各自模块内；本文件仅承载
跨模块共享的基础设施依赖。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import CurrentUser, claims_to_current_user, decode_supabase_jwt
from app.db.session import get_db_session

# 重新导出数据库会话依赖，调用方可直接 ``from app.dependencies import DbSession``
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _extract_bearer_token(authorization: str | None) -> str:
    """从 ``Authorization`` 头中提取 Bearer Token。"""
    if not authorization:
        raise UnauthorizedException("缺少 Authorization 头", code="AUTH_TOKEN_MISSING")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedException(
            "Authorization 头格式错误", code="AUTH_TOKEN_MALFORMED"
        )
    return token


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> CurrentUser:
    """从 Bearer JWT 中解析当前登录用户。

    异常：
        UnauthorizedException: 当 token 缺失、格式错误、过期或非法时抛出。
    """
    token = _extract_bearer_token(authorization)
    claims = decode_supabase_jwt(token)
    return claims_to_current_user(claims)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
