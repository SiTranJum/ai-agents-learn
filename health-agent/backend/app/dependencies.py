"""全局 FastAPI 依赖。

模块特有的依赖(service、repository)应放在各自模块内; 本文件仅承载
跨模块共享的基础设施依赖。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.chat.graph import build_chat_agent
from app.agents.plan.graph import build_plan_agent
from app.agents.suggestion.graph import build_suggestion_agent
from app.core.exceptions import UnauthorizedException
from app.core.security import claims_to_current_user, decode_supabase_jwt
from app.db.repositories.body_repo import BodyRepository
from app.db.repositories.chat_repo import ChatRepository
from app.db.repositories.diet_repo import DietRepository
from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.db.repositories.memory_repo import MemoryRepository
from app.db.repositories.plan_repo import PlanRepository
from app.db.repositories.suggestion_repo import SuggestionRepository
from app.db.repositories.user_repo import UserRepository
from app.db.session import get_db_session
from app.integrations.embedding import EmbeddingClient
from app.schemas.auth import CurrentUser
from app.services.body_service import BodyService
from app.services.chat_service import ChatService
from app.services.diet_service import DietService
from app.services.memory_service import MemoryService
from app.services.plan_service import PlanService
from app.services.rag_service import RagService
from app.services.suggestion_service import SuggestionService
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
    memory_service = MemoryService(
        repo=MemoryRepository(session=session, user_id=user.id),
        embedding_client=EmbeddingClient(),
    )
    return UserService(repo=repo, memory_service=memory_service)


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


async def get_body_service(
    session: DbSession,
    user: CurrentUserWithProfileDep,
) -> BodyService:
    """构造按当前用户隔离的身体数据服务。"""
    profile = user.profile
    return BodyService(
        repo=BodyRepository(session=session, user_id=user.id),
        height_cm=getattr(profile, "height", None),
        target_weight=getattr(profile, "target_weight", None),
    )


BodyServiceDep = Annotated[BodyService, Depends(get_body_service)]


async def get_memory_service(
    session: DbSession,
    user: CurrentUserDep,
) -> MemoryService:
    """构造按当前用户隔离的记忆服务。"""
    return MemoryService(
        repo=MemoryRepository(session=session, user_id=user.id),
        embedding_client=EmbeddingClient(),
    )


MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]


async def get_chat_service(
    session: DbSession,
    user: CurrentUserDep,
) -> ChatService:
    """构造按当前用户隔离的聊天消息服务。"""
    return ChatService(repo=ChatRepository(session=session, user_id=user.id))


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]


async def get_plan_service(
    session: DbSession,
    user: CurrentUserWithProfileDep,
) -> PlanService:
    """构造按当前用户隔离的计划服务。"""
    return PlanService(
        repo=PlanRepository(session=session, user_id=user.id),
        profile=user.profile,
    )


PlanServiceDep = Annotated[PlanService, Depends(get_plan_service)]


async def get_suggestion_service(
    session: DbSession,
    user: CurrentUserDep,
) -> SuggestionService:
    """构造按当前用户隔离的建议服务。"""
    return SuggestionService(repo=SuggestionRepository(session=session, user_id=user.id))


SuggestionServiceDep = Annotated[SuggestionService, Depends(get_suggestion_service)]


_chat_agent_singleton = None
_plan_agent_singleton = None
_suggestion_agent_singleton = None


def get_chat_agent():
    """构造并复用全局 chat_agent 编译产物。"""
    global _chat_agent_singleton
    if _chat_agent_singleton is None:
        _chat_agent_singleton = build_chat_agent()
    return _chat_agent_singleton


ChatAgentDep = Annotated[object, Depends(get_chat_agent)]


def get_plan_agent():
    """构造并复用 plan_agent 编译产物。"""
    global _plan_agent_singleton
    if _plan_agent_singleton is None:
        _plan_agent_singleton = build_plan_agent()
    return _plan_agent_singleton


PlanAgentDep = Annotated[object, Depends(get_plan_agent)]


def get_suggestion_agent():
    """构造并复用 suggestion_agent 编译产物。"""
    global _suggestion_agent_singleton
    if _suggestion_agent_singleton is None:
        _suggestion_agent_singleton = build_suggestion_agent()
    return _suggestion_agent_singleton


SuggestionAgentDep = Annotated[object, Depends(get_suggestion_agent)]


