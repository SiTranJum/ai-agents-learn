"""Phase 3 - 知识库 API 测试。"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from httpx import AsyncClient

from app.core.exceptions import NotFoundException
from app.dependencies import get_current_user, get_rag_service
from app.main import app
from app.schemas.auth import CurrentUser
from app.schemas.knowledge import (
    FoodCategory,
    FoodDetailResponse,
    FoodSearchResponse,
    NutritionInfo,
)


class _FakeRagService:
    def __init__(self) -> None:
        self.food_id = uuid.uuid4()

    async def search_foods(self, query: str, limit: int = 10) -> list[FoodSearchResponse]:
        return [
            FoodSearchResponse(
                id=self.food_id,
                name=query,
                aliases=["白米饭"],
                category=FoodCategory.grains,
                calories_per_100g=116,
                match_score=1.0,
            )
        ][:limit]

    async def get_food_detail(self, food_id: uuid.UUID) -> FoodDetailResponse:
        if food_id != self.food_id:
            raise NotFoundException("食物不存在", code="FOOD_NOT_FOUND")
        return FoodDetailResponse(
            id=food_id,
            name="米饭",
            aliases=["白米饭"],
            category=FoodCategory.grains,
            nutrition_per_100g=NutritionInfo(
                calories=116,
                protein=2.6,
                fat=0.3,
                carbs=25.9,
                fiber=0.3,
                sodium=2,
                sugar=0.1,
            ),
            common_portions=[],
            data_source="test",
        )


@pytest.fixture
def fake_rag_service() -> Iterator[_FakeRagService]:
    service = _FakeRagService()

    async def _current_user() -> CurrentUser:
        return CurrentUser(id=uuid.uuid4(), email="user@example.com")

    async def _rag_service() -> _FakeRagService:
        return service

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_rag_service] = _rag_service
    try:
        yield service
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_foods_api(client: AsyncClient, fake_rag_service: _FakeRagService) -> None:
    resp = await client.get("/api/v1/knowledge/foods/search", params={"q": "米饭", "limit": 5})

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"][0]["name"] == "米饭"
    assert body["data"][0]["match_score"] == 1.0


@pytest.mark.asyncio
async def test_get_food_detail_api(client: AsyncClient, fake_rag_service: _FakeRagService) -> None:
    resp = await client.get(f"/api/v1/knowledge/foods/{fake_rag_service.food_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["name"] == "米饭"
    assert body["data"]["nutrition_per_100g"]["calories"] == 116


@pytest.mark.asyncio
async def test_get_food_detail_api_not_found(
    client: AsyncClient, fake_rag_service: _FakeRagService
) -> None:
    resp = await client.get(f"/api/v1/knowledge/foods/{uuid.uuid4()}")

    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "FOOD_NOT_FOUND"

