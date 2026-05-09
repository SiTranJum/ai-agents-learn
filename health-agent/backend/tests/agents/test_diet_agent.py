"""Phase 4 - diet subgraph 单元测试。

本测试不再验证"Agent 作为独立入口"，而是验证 diet subgraph 的节点/分支图装配
在 ChatState 签名下可以跑通（Phase 6 全局 chat_graph 会复用它）。
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest

from app.agents.diet import build_diet_subgraph
from app.schemas.diet import (
    DataSource,
    DietRecordResponse,
    FoodItemInput,
    FoodItemResponse,
    MealType,
    NutritionSummary,
    ParsedFood,
)


class _FakeDietService:
    async def food_input_to_parsed(self, food: FoodItemInput) -> ParsedFood:
        return ParsedFood(
            name=food.name,
            amount=food.amount,
            unit=food.unit,
            amount_grams=food.amount_grams or 200,
            calories=food.calories or 232,
            protein=food.protein or 5.2,
            fat=food.fat or 0.6,
            carbs=food.carbs or 51.8,
            fiber=food.fiber,
            sodium=food.sodium,
            data_source=food.data_source or DataSource.database,
        )

    @staticmethod
    def estimate_amount_grams(name: str, amount: float, unit: str) -> float:
        return 200 if name == "米饭" and unit == "碗" else amount

    async def create_record_from_parsed(
        self, *, meal_type: MealType, foods: list[ParsedFood], record_date: date
    ) -> DietRecordResponse:
        return DietRecordResponse(
            id=uuid.uuid4(),
            meal_type=meal_type,
            date=record_date,
            foods=[
                FoodItemResponse(
                    id=uuid.uuid4(),
                    name=foods[0].name,
                    amount=foods[0].amount,
                    unit=foods[0].unit,
                    amount_grams=foods[0].amount_grams,
                    calories=foods[0].calories,
                    protein=foods[0].protein,
                    fat=foods[0].fat,
                    carbs=foods[0].carbs,
                    data_source=foods[0].data_source,
                )
            ],
            nutrition_summary=NutritionSummary(
                total_calories=foods[0].calories,
                total_protein=foods[0].protein,
                total_fat=foods[0].fat,
                total_carbs=foods[0].carbs,
            ),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


@pytest.mark.asyncio
async def test_diet_subgraph_create_from_foods_without_llm() -> None:
    subgraph = build_diet_subgraph()

    state = await subgraph.ainvoke(
        {
            "user_id": str(uuid.uuid4()),
            "mode": "create",
            "diet_meal_type": MealType.lunch.value,
            "diet_date": date(2026, 5, 9),
            "foods": [FoodItemInput(name="米饭", amount=1, unit="碗", amount_grams=200)],
            "diet_service": _FakeDietService(),
        }
    )

    record: DietRecordResponse = state["diet_saved_record"]
    assert record.meal_type == MealType.lunch
    assert record.foods[0].name == "米饭"
    assert record.nutrition_summary.total_calories == 232
