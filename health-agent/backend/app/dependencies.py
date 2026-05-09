"""全局 FastAPI 依赖。

模块特有的依赖(service、repository)应放在各自模块内; 本文件仅承载
跨模块共享的基础设施依赖。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import claims_to_current_user, decode_supabase_jwt
from app.db.repositories.diet_repo import DietRepository
from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.db.repositories.user_repo import UserRepository
from app.db.session import get_db_session
from app.integrations.embedding import EmbeddingClient
from app.schemas.auth import CurrentUser
from app.services.diet_service import DietService
from app.services.rag_service import RagService
from app.services.user_service import UserService

# 重新导出数据库会话依赖, 调用方可直接 ``from app.dependencies import DbSession``
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


async def get_access_token(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    """提取并返回原始 access_token。"""
    return _extract_bearer_token(authorization)


async def get_current_user(
    token: Annotated[str, Depends(get_access_token)],
) -> CurrentUser:
    """从 Bearer JWT 中解析当前登录用户(不查询数据库)。

    异常:
        UnauthorizedException: 当 token 缺失、格式错误、过期或非法时抛出。
    """
    claims = decode_supabase_jwt(token)
    parsed = claims_to_current_user(claims)
    try:
        user_uuid = uuid.UUID(parsed.id)
    except (ValueError, AttributeError) as exc:
        raise UnauthorizedException(
            "令牌中的用户标识无效", code="AUTH_TOKEN_INVALID"
        ) from exc
    return CurrentUser(id=user_uuid, email=parsed.email, role=parsed.role)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
AccessTokenDep = Annotated[str, Depends(get_access_token)]


async def get_current_user_with_profile(
    user: CurrentUserDep,
    session: DbSession,
) -> CurrentUser:
    """获取当前用户, 并确保其健康档案存在。

    首次访问后端 API 时(JWT 校验通过但 ``health_profiles`` 中没有对应行),
    自动创建一条空档案以及偏好/健康信息/设置的初始记录。

    详见 ``docs/specs/backend/00-architecture/auth.md`` §6。
    """
    repo = UserRepository(session=session, user_id=user.id)
    profile = await repo.get_profile()
    if profile is None:
        # 首次访问: 创建空档案及关联记录
        profile = await repo.initialize_for_user()
        await session.commit()
    user.profile = profile
    return user


CurrentUserWithProfileDep = Annotated[
    CurrentUser, Depends(get_current_user_with_profile)
]


# ---------- Service 工厂 ----------


async def get_user_service(
    session: DbSession,
    user: CurrentUserDep,
) -> UserService:
    """构造按当前用户隔离的 :class:`UserService`。"""
    repo = UserRepository(session=session, user_id=user.id)
    return UserService(repo=repo)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_rag_service(session: DbSession) -> RagService:
    """构造全局知识库检索服务。"""
    return RagService(
        repo=KnowledgeRepository(session=session),
        embedding_client=EmbeddingClient(),
    )


RagServiceDep = Annotated[RagService, Depends(get_rag_service)]


async def get_diet_service(
    session: DbSession,
    user: CurrentUserDep,
    rag_service: RagServiceDep,
) -> DietService:
    """构造按当前用户隔离的饮食服务。"""
    return DietService(
        repo=DietRepository(session=session, user_id=user.id),
        rag_service=rag_service,
    )


DietServiceDep = Annotated[DietService, Depends(get_diet_service)]


