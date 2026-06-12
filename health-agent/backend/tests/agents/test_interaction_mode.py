"""交互模式（效率 / 确认 / 学习）对 AI 行为差异的单测。

验证同一输入在不同 ``interaction_mode`` 下，``wrap_response`` 产出不同的响应结构：
- efficiency：diet 子图自动落库，卡片 ``requires_confirmation=False`` 且无"确认保存"按钮。
- confirmation：出确认卡片（``requires_confirmation=True``），不自动落库。
- learning：在确认卡片基础上附带 ``knowledge`` 知识讲解。
"""
# ruff: noqa: RUF001

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.agents.chat.graph import build_chat_agent
from app.agents.chat.nodes import wrap_response
from app.agents.prompts.chat_system import build_chat_messages
from app.schemas.diet import (
    DataSource,
    FoodItemInput,
    MealType,
    NutritionSummary,
    ParsedFood,
    ParseResult,
)


class _FakeDietService:
    """diet 子图依赖的最小假实现，记录是否被要求落库。"""

    def __init__(self) -> None:
        self.saved = False

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

    async def create_record_from_parsed(self, *, meal_type, foods, record_date):
        self.saved = True

        class _Record:
            id = uuid.uuid4()

        return _Record()


def _parse_result() -> ParseResult:
    return ParseResult(
        foods=[
            ParsedFood(
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
        meal_type=MealType.lunch,
        confidence=0.9,
        nutrition_summary=NutritionSummary(
            total_calories=232, total_protein=5.2, total_fat=0.6, total_carbs=51.8
        ),
    )


@pytest.mark.asyncio
async def test_confirmation_mode_emits_confirm_card() -> None:
    """确认模式：出带'确认保存'按钮的卡片，requires_confirmation=True，无知识讲解。"""
    result = await wrap_response(
        {
            "intent": "diet",
            "interaction_mode": "confirmation",
            "diet_parse_result": _parse_result(),
            "diet_date": date(2026, 6, 12),
        }
    )
    card = result["response_cards"][0]
    assert card["requires_confirmation"] is True
    assert card["knowledge"] is None
    kinds = {a["kind"] for a in card["actions"]}
    assert "confirm_create_diet_record" in kinds


@pytest.mark.asyncio
async def test_efficiency_mode_no_confirm_card() -> None:
    """效率模式：卡片 requires_confirmation=False，不含'确认保存'按钮，文案为'已记录'。"""
    result = await wrap_response(
        {
            "intent": "diet",
            "interaction_mode": "efficiency",
            "diet_parse_result": _parse_result(),
            "diet_date": date(2026, 6, 12),
        }
    )
    card = result["response_cards"][0]
    assert card["requires_confirmation"] is False
    kinds = {a["kind"] for a in card["actions"]}
    assert "confirm_create_diet_record" not in kinds
    assert "已记录" in result["ai_response"]


@pytest.mark.asyncio
async def test_learning_mode_attaches_knowledge() -> None:
    """学习模式：确认卡片 + 非空 knowledge 知识讲解字段。"""
    result = await wrap_response(
        {
            "intent": "diet",
            "interaction_mode": "learning",
            "diet_parse_result": _parse_result(),
            "diet_date": date(2026, 6, 12),
        }
    )
    card = result["response_cards"][0]
    assert card["requires_confirmation"] is True
    assert card["knowledge"]
    assert "kcal" in card["knowledge"]


def test_build_chat_messages_mode_changes_system_prompt() -> None:
    """同一输入，三种模式的 system prompt 追加指令应不同。"""
    kwargs = {"user_message": "你好", "history": [], "memories": [], "knowledge": []}
    eff = build_chat_messages(interaction_mode="efficiency", **kwargs)[0].content
    conf = build_chat_messages(interaction_mode="confirmation", **kwargs)[0].content
    learn = build_chat_messages(interaction_mode="learning", **kwargs)[0].content
    assert eff != conf != learn
    assert "效率模式" in eff
    assert "学习模式" in learn


@pytest.mark.asyncio
async def test_efficiency_mode_auto_saves_via_graph() -> None:
    """效率模式跑完整 graph：diet 子图应自动落库（create_record_from_parsed 被调用）。"""
    service = _FakeDietService()
    graph = build_chat_agent()
    state = await graph.ainvoke(
        {
            "user_id": str(uuid.uuid4()),
            "session_id": "s1",
            "user_message": "午饭吃了一碗米饭",
            "diet_input_text": "午饭吃了一碗米饭",
            "diet_date": date(2026, 6, 12),
            "interaction_mode": "efficiency",
            "foods": [FoodItemInput(name="米饭", amount=1, unit="碗", amount_grams=200)],
            "diet_service": service,
        }
    )
    assert state["intent"] == "diet"
    assert service.saved is True
    assert state["response_cards"][0]["requires_confirmation"] is False
