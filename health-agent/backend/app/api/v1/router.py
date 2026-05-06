"""v1 API 路由聚合器。

各模块路由在此处统一注册；``app.main`` 将本路由挂载到 ``/api/v1``。
随着各阶段实现，对应模块的 router 会逐步接入。
"""

from fastapi import APIRouter

api_router = APIRouter()

# 待 Phase 1 起按阶段接入：
# from app.api.v1 import auth, users, diet, body, plans, ai, suggestions, knowledge
# api_router.include_router(auth.router)
# api_router.include_router(users.router)
# ...

__all__ = ["api_router"]
