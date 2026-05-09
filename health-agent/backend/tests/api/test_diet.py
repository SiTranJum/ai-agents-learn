"""Phase 4 - 饮食 API 测试（纯 CRUD）。"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient

from app.dependencies import get_current_user, get_diet_service
from app.main import app
from app.schemas.auth import CurrentUser
from app.schemas.diet import (
    DailySummary,
    DataSource,
    DietRecordResponse,
    FoodItemInput,
    FoodItemResponse,
    MealType,
    NutritionSummary,
)


def _record() -> DietRecordResponse:
    return DietRecordResponse(
        id=uuid.uuid4(),
        meal_type=MealType.lunch,
        date=date(2026, 5, 9),
        foods=[
            FoodItemResponse(
                id=uuid.uuid4(),
                name="米饭",
                amount=1,
                unit="碗",
                amount_grams=200,
                calories=232,
                protein=5.2,
                fat=0.6,
                carbs=51.8,
                data_source=DataSource.database,
            )
        ],
        nutrition_summary=NutritionSummary(
            total_calories=232,
            total_protein=5.2,
            total_fat=0.6,
            total_carbs=51.8,
        ),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class _FakeDietService:
    async def create_record(
        self,
        *,
        meal_type: MealType,
        foods: list[FoodItemInput],
        record_date: date,
    ) -> DietRecordResponse:
        return _record().model_copy(update={"meal_type": meal_type, "date": record_date})

    async def get_daily_summary(self, target_date: date) -> DailySummary:
        record = _record()
        return DailySummary(
            date=target_date,
            meals={
                MealType.breakfast: [],
                MealType.lunch: [record],
                MealType.dinner: [],
                MealType.snack: [],
            },
            total_nutrition=record.nutrition_summary,
        )

    async def get_record(self, record_id: uuid.UUID) -> DietRecordResponse:
        return _record().model_copy(update={"id": record_id})

    async def delete_record(self, record_id: uuid.UUID) -> None:
        return None


@pytest.fixture
def diet_overrides():
    async def _current_user() -> CurrentUser:
        return CurrentUser(id=uuid.uuid4(), email="user@example.com")

    async def _service() -> _FakeDietService:
        return _FakeDietService()

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_diet_service] = _service
    try:
        yield
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_diet_record_api(client: AsyncClient, diet_overrides) -> None:
    resp = await client.post(
        "/api/v1/diet/records",
        json={
            "meal_type": "lunch",
            "date": "2026-05-09",
            "foods": [{"name": "米饭", "amount": 1, "unit": "碗"}],
        },
    )

    assert resp.status_code == 201
    assert resp.json()["data"]["foods"][0]["name"] == "米饭"


@pytest.mark.asyncio
async def test_create_diet_record_rejects_empty_foods(
    client: AsyncClient, diet_overrides
) -> None:
    """POST /records 不再接受自然语言输入，foods 为空时应校验失败。"""
    resp = await client.post(
        "/api/v1/diet/records",
        json={"meal_type": "lunch", "date": "2026-05-09", "foods": []},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_parse_endpoint_removed(client: AsyncClient, diet_overrides) -> None:
    """/diet/parse 已下线，AI 解析路径统一走 /ai/chat。"""
    resp = await client.post(
        "/api/v1/diet/parse",
        json={"input_text": "一碗米饭"},
    )

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_daily_summary_api(client: AsyncClient, diet_overrides) -> None:
    resp = await client.get("/api/v1/diet/daily-summary", params={"date": "2026-05-09"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["meals"]["lunch"][0]["nutrition_summary"]["total_calories"] == 232
