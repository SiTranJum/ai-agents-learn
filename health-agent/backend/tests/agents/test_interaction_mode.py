"""交互模式（效率 / 确认 / 学习）对 AI 行为差异的单测。

验证同一输入在不同 ``interaction_mode`` 下，``wrap_response`` 产出不同的响应结构：
- efficiency：diet 子图自动落库，卡片 ``requires_confirmation=False`` 且无"确认保存"按钮。
- confirmation / learning：出确认卡片（``requires_confirmation=True``），不自动落库；
  学习讲解由独立的 ``narrate_learning`` 节点流式输出，不再以卡内字段携带（详见
  ``test_diet_agent.py::test_diet_subgraph_learning_mode_routes_through_narrate_node``）。
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
async def test_wrap_response_receipt_after_save() -> None:
    """落库后（确认模式）：wrap_response 只发文本反馈，不再发卡——
    确认卡已由子图 interrupt 发出，前端把它从 pending 切到 submitted 即是回执，
    再发一张相同卡会重复显示。"""
    result = await wrap_response(
        {
            "intent": "diet",
            "interaction_mode": "confirmation",
            "diet_parse_result": _parse_result(),
            "diet_saved_record": object(),
            "diet_date": date(2026, 6, 12),
        }
    )
    assert result["response_cards"] == []
    assert "已记录" in result["ai_response"]


@pytest.mark.asyncio
async def test_wrap_response_cancel_text() -> None:
    """取消后：wrap_response 给取消文案，无卡片（避免取消后又弹卡造成循环）。"""
    result = await wrap_response(
        {
            "intent": "diet",
            "interaction_mode": "confirmation",
            "diet_parse_result": _parse_result(),
            "diet_cancelled": True,
        }
    )
    assert result["response_cards"] == []
    assert "取消" in result["ai_response"]


@pytest.mark.asyncio
async def test_efficiency_mode_no_confirm_card() -> None:
    """效率模式（已落库）：wrap_response 给纯文本'已记录'反馈，不发卡。"""
    result = await wrap_response(
        {
            "intent": "diet",
            "interaction_mode": "efficiency",
            "diet_parse_result": _parse_result(),
            "diet_saved_record": object(),
            "diet_date": date(2026, 6, 12),
        }
    )
    assert result["response_cards"] == []
    assert "已记录" in result["ai_response"]


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
    """效率模式跑完整 graph：diet 子图应自动落库（create_record_from_parsed 被调用），
    wrap_response 给纯文本'已记录'反馈，不发回执卡（确认卡场景才有交互卡）。"""
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
    assert state["response_cards"] == []
    assert "已记录" in state["ai_response"]
