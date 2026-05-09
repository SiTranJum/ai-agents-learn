"""知识库 API 路由。"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.responses import success
from app.dependencies import CurrentUserDep, RagServiceDep
from app.schemas.common import ApiResponse
from app.schemas.knowledge import FoodDetailResponse, FoodSearchResponse

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get(
    "/foods/search",
    response_model=ApiResponse[list[FoodSearchResponse]],
    summary="搜索食物营养数据",
)
async def search_foods(
    user: CurrentUserDep,
    service: RagServiceDep,
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
):
    data = await service.search_foods(q, limit=limit)
    return success([item.model_dump(mode="json") for item in data])


@router.get(
    "/foods/{food_id}",
    response_model=ApiResponse[FoodDetailResponse],
    summary="获取食物详情",
)
async def get_food_detail(
    food_id: uuid.UUID,
    user: CurrentUserDep,
    service: RagServiceDep,
):
    data = await service.get_food_detail(food_id)
    return success(data.model_dump(mode="json"))


__all__ = ["router"]
