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
    """效率模式：解析后直接落库，无需 interrupt 确认。"""
    subgraph = build_diet_subgraph()

    state = await subgraph.ainvoke(
        {
            "user_id": str(uuid.uuid4()),
            "interaction_mode": "efficiency",
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


@pytest.mark.asyncio
async def test_diet_subgraph_confirmation_mode_interrupts_then_saves() -> None:
    """确认模式：先 interrupt 出确认卡片，resume confirm 后落库。"""
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command

    # 子图需挂 checkpointer 才能 interrupt 暂停/恢复。
    from app.agents.chat.state import ChatState
    from app.agents.diet.nodes import (
        confirm_or_clarify,
        confirm_save,
        enrich_nutrition,
        infer_meal_type,
        route_input,
        save_record,
        standardize_units,
    )
    from langgraph.graph import END, StateGraph
    from typing import Any, cast

    graph = StateGraph(cast(Any, ChatState))
    graph.add_node("standardize_units", cast(Any, standardize_units))
    graph.add_node("enrich_nutrition", cast(Any, enrich_nutrition))
    graph.add_node("infer_meal_type", cast(Any, infer_meal_type))
    graph.add_node("confirm_or_clarify", cast(Any, confirm_or_clarify))
    graph.add_node("confirm_save", cast(Any, confirm_save))
    graph.add_node("save_record", cast(Any, save_record))
    graph.set_entry_point("standardize_units")
    graph.add_edge("standardize_units", "enrich_nutrition")
    graph.add_edge("enrich_nutrition", "infer_meal_type")
    graph.add_edge("infer_meal_type", "confirm_or_clarify")
    graph.add_edge("save_record", END)
    subgraph = graph.compile(checkpointer=MemorySaver())

    config = {"configurable": {"thread_id": "diet-confirm-1", "diet_service": _FakeDietService()}}
    first = await subgraph.ainvoke(
        {
            "user_id": str(uuid.uuid4()),
            "interaction_mode": "confirmation",
            "diet_meal_type": MealType.lunch.value,
            "diet_date": date(2026, 5, 9),
            "foods": [FoodItemInput(name="米饭", amount=1, unit="碗", amount_grams=200)],
        },
        config=config,
    )
    # 第一轮应暂停在确认卡片
    interrupts = first.get("__interrupt__")
    assert interrupts, "expected a confirm interrupt"
    assert interrupts[0].value["prompt_id"] == "diet_confirm"
    assert "diet_saved_record" not in first

    # resume confirm → 落库
    final = await subgraph.ainvoke(
        Command(resume={"prompt_id": "diet_confirm", "action": "confirm"}),
        config=config,
    )
    record: DietRecordResponse = final["diet_saved_record"]
    assert record.meal_type == MealType.lunch
    assert record.foods[0].name == "米饭"


@pytest.mark.asyncio
async def test_diet_subgraph_learning_mode_routes_through_narrate_node(monkeypatch) -> None:
    """学习模式 + 餐次缺失：先 interrupt 问餐次，回流后应经过 narrate_learning
    节点（流式讲解）再到 confirm_save 出确认卡。

    讲解走 LLM token 流（与普通 AI 对话一致）而非卡内字段，前端通过 text_delta
    呈现亲和力陪伴效果。本测试 mock LLM，避免依赖真实 API key。
    """
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command

    from app.agents.chat.state import ChatState
    from app.agents.diet.nodes import (
        confirm_or_clarify,
        confirm_save,
        enrich_nutrition,
        infer_meal_type,
        narrate_learning,
        save_record,
        standardize_units,
    )
    from langgraph.graph import END, StateGraph
    from typing import Any, cast

    # mock 出讲解 LLM，断言被调用即视为节点执行
    narrate_called = {"count": 0}

    class _FakeModel:
        async def ainvoke(self, messages):
            narrate_called["count"] += 1

            class _Resp:
                content = "你这一餐挺不错的，鸡蛋是优质蛋白来源..."

            return _Resp()

    monkeypatch.setattr(
        "app.agents.diet.nodes.get_chat_model",
        lambda *args, **kwargs: _FakeModel(),
    )

    graph = StateGraph(cast(Any, ChatState))
    graph.add_node("standardize_units", cast(Any, standardize_units))
    graph.add_node("enrich_nutrition", cast(Any, enrich_nutrition))
    graph.add_node("infer_meal_type", cast(Any, infer_meal_type))
    graph.add_node("confirm_or_clarify", cast(Any, confirm_or_clarify))
    graph.add_node("narrate_learning", cast(Any, narrate_learning))
    graph.add_node("confirm_save", cast(Any, confirm_save))
    graph.add_node("save_record", cast(Any, save_record))
    graph.set_entry_point("standardize_units")
    graph.add_edge("standardize_units", "enrich_nutrition")
    graph.add_edge("enrich_nutrition", "infer_meal_type")
    graph.add_edge("infer_meal_type", "confirm_or_clarify")
    graph.add_edge("narrate_learning", "confirm_save")
    graph.add_edge("save_record", END)
    subgraph = graph.compile(checkpointer=MemorySaver())

    config = {"configurable": {"thread_id": "diet-learning-1", "diet_service": _FakeDietService()}}
    # 第一轮：学习模式 + 餐次缺失（"两个鸡蛋"）→ 应 interrupt 问餐次
    first = await subgraph.ainvoke(
        {
            "user_id": str(uuid.uuid4()),
            "interaction_mode": "learning",
            "diet_date": date(2026, 6, 13),
            "foods": [FoodItemInput(name="鸡蛋", amount=2, unit="个", amount_grams=100)],
        },
        config=config,
    )
    interrupts = first.get("__interrupt__")
    assert interrupts and interrupts[0].value["prompt_id"] == "diet_meal_type"
    assert narrate_called["count"] == 0, "餐次澄清前不应触发讲解"

    # 第二轮：用户选 lunch → 应经过 narrate_learning 后到 confirm 卡
    second = await subgraph.ainvoke(
        Command(resume={"prompt_id": "diet_meal_type", "value": "lunch"}),
        config=config,
    )
    interrupts2 = second.get("__interrupt__")
    assert interrupts2 and interrupts2[0].value["prompt_id"] == "diet_confirm"
    card = interrupts2[0].value["card"]
    # 卡片只剩 requires_confirmation 协议字段，knowledge 已下线（讲解走 text_delta）
    assert card["requires_confirmation"] is True
    assert "knowledge" not in card, "学习讲解不再以卡内字段携带"
    assert narrate_called["count"] == 1, "学习模式应经过 narrate_learning 节点"

