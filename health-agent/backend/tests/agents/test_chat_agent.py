"""Phase 7 - chat_agent graph tests."""
# ruff: noqa: RUF001

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.agents.chat.graph import build_chat_agent
from app.schemas.diet import DataSource, FoodItemInput, ParsedFood


class _FakeDietService:
    async def food_input_to_parsed(self, food: FoodItemInput) -> ParsedFood:
        return ParsedFood(
            name=food.name,
            amount=food.amount,
            unit=food.unit,
            amount_grams=food.amount_grams or 200,
            calories=232,
            protein=5.2,
            fat=0.6,
            carbs=51.8,
            data_source=DataSource.database,
        )

    @staticmethod
    def estimate_amount_grams(name: str, amount: float, unit: str) -> float:
        return 200 if name == "米饭" else amount


@pytest.mark.asyncio
async def test_chat_agent_routes_diet_to_parse_card_without_saving() -> None:
    graph = build_chat_agent()

    state = await graph.ainvoke(
        {
            "user_id": str(uuid.uuid4()),
            "session_id": "s1",
            "user_message": "午饭吃了一碗米饭",
            "diet_input_text": "午饭吃了一碗米饭",
            "diet_date": date(2026, 5, 12),
            "foods": [FoodItemInput(name="米饭", amount=1, unit="碗", amount_grams=200)],
            "diet_service": _FakeDietService(),
        }
    )

    assert state["intent"] == "diet"
    assert state["response_cards"][0]["type"] == "diet_parse"
    assert state["response_cards"][0]["payload"]["foods"][0]["name"] == "米饭"
    assert state.get("diet_saved_record") is None


@pytest.mark.asyncio
async def test_chat_agent_general_fallback_returns_text(monkeypatch) -> None:
    class _FakeModel:
        def with_structured_output(self, schema):
            class _Structured:
                async def ainvoke(self, messages):
                    return schema(intent="general", confidence=0.9)

            return _Structured()

        async def ainvoke(self, messages):
            class _Response:
                content = "你好，我可以帮你记录饮食和管理健康。"

            return _Response()

    monkeypatch.setattr("app.agents.chat.nodes.get_chat_model", lambda *args, **kwargs: _FakeModel())
    graph = build_chat_agent()

    state = await graph.ainvoke(
        {
            "user_id": str(uuid.uuid4()),
            "session_id": "s1",
            "user_message": "你好",
            "chat_history": [],
        }
    )

    assert state["intent"] == "general"
    assert "记录饮食" in state["ai_response"]


