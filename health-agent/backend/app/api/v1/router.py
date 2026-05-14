"""v1 API 路由聚合器。

各模块路由在此处统一注册; ``app.main`` 将本路由挂载到 ``/api/v1``。

注: 后端不再提供 auth 端点(注册/登录/登出/刷新由前端直接调用 Supabase Auth SDK),
详见 ``docs/specs/backend/00-architecture/auth.md`` §3。
"""

from fastapi import APIRouter

from app.api.v1 import ai, body, diet, knowledge, plans, suggestions, users

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(knowledge.router)
api_router.include_router(diet.router)
api_router.include_router(body.router)
api_router.include_router(ai.router)
api_router.include_router(plans.router)
api_router.include_router(suggestions.router)

# 待后续阶段接入:

__all__ = ["api_router"]
