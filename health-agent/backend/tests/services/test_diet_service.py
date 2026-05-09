"""Phase 4 - DietService 单元测试。"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest

from app.db.models.diet import DietRecord
from app.schemas.diet import DataSource, MealType, ParsedFood
from app.services.diet_service import DietService


class _FakeRepo:
    def __init__(self) -> None:
        self.session = self
        self.created_record: DietRecord | None = None

    async def commit(self) -> None:
        return None

    async def create_record(self, *, meal_type, record_date, items):
        record = DietRecord(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            meal_type=meal_type,
            date=record_date,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        record.items = items
        for item in items:
            item.id = uuid.uuid4()
        self.created_record = record
        return record


class _FakeRagService:
    pass


def _service() -> DietService:
    return DietService(repo=_FakeRepo(), rag_service=_FakeRagService())  # type: ignore[arg-type]


def test_estimate_amount_grams_matches_frontend_mock_units() -> None:
    assert DietService.estimate_amount_grams("米饭", 1, "碗") == 200
    assert DietService.estimate_amount_grams("鸡蛋", 1, "个") == 50
    assert DietService.estimate_amount_grams("苹果", 1, "个") == 200
    assert DietService.estimate_amount_grams("鸡胸肉", 100, "g") == 100


@pytest.mark.asyncio
async def test_create_record_from_parsed_calculates_summary() -> None:
    service = _service()
    food = ParsedFood(
        name="米饭",
        amount=1,
        unit="碗",
        amount_grams=200,
        calories=232,
        protein=5.2,
        fat=0.6,
        carbs=51.8,
        fiber=0.6,
        sodium=4,
        data_source=DataSource.database,
    )

    record = await service.create_record_from_parsed(
        meal_type=MealType.lunch,
        foods=[food],
        record_date=date(2026, 5, 9),
    )

    assert record.meal_type == MealType.lunch
    assert record.foods[0].amount_grams == 200
    assert record.nutrition_summary.total_calories == 232
    assert record.nutrition_summary.total_carbs == 51.8
