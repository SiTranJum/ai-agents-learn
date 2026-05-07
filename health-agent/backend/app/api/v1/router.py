"""v1 API 路由聚合器。

各模块路由在此处统一注册；``app.main`` 将本路由挂载到 ``/api/v1``。

注：后端不再提供 auth 端点（注册/登录/登出/刷新由前端直接调用 Supabase Auth SDK），
详见 ``docs/specs/backend/00-architecture/auth.md`` §3。
"""

from fastapi import APIRouter

from app.api.v1 import users

api_router = APIRouter()
api_router.include_router(users.router)

# 待 Phase 2 起按阶段接入：
# from app.api.v1 import diet, body, plans, ai, suggestions, knowledge

__all__ = ["api_router"]
