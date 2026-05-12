"""diet subgraph 节点实现。

本文件的所有节点都读写 :class:`ChatState`（而不是独立的 DietState）。
节点读写的都是 ``diet_*`` 前缀字段，与全局 Graph 保持一致。

关键约定：
- ``diet_service`` 通过 LangGraph 的 ``config["configurable"]`` 注入；测试场景
  也允许直接写入 state 里（key 仍用 ``diet_service``，但它不是 ChatState 的
  正式字段，仅临时携带）。
"""
# ruff: noqa: RUF002

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from app.agents.base import get_chat_model
from app.agents.chat.state import ChatState
from app.agents.diet.tools import enrich_food_tool, save_diet_record_tool
from app.agents.prompts.diet_parse import build_diet_parse_messages
from app.core.exceptions import BusinessRuleException, ValidationException
from app.schemas.diet import (
    DataSource,
    FoodItemInput,
    MealType,
    NutritionSummary,
    ParsedFood,
    ParseResult,
)


def _get_service(state: ChatState):
    """从 state 取 DietService 实例。

    当前 Phase 4：subgraph 单元测试时直接注入到 state。Phase 6 将改为
    从 LangGraph 的 ``RunnableConfig.configurable`` 注入，避免污染 state。
    """
    return cast(Any, state).get("diet_service")


def route_input(state: ChatState) -> str:
    """根据当前 state 决定 diet 分支入口节点。

    - 已有结构化 foods（由其他路径预先塞入 state）→ 直接标准化；
    - 有 image_url → 图片解析（mock）；
    - 否则按文本解析处理。
    """
    if cast(Any, state).get("foods") or state.get("diet_parsed_foods"):
        return "standardize_units"
    if state.get("diet_image_url"):
        return "parse_photo_mock"
    return "parse_text"


async def parse_text(state: ChatState) -> dict[str, Any]:
    """LLM 解析饮食自然语言描述。

    读 ``diet_input_text``；写 ``diet_parse_result`` / ``diet_parsed_foods``
    / ``diet_confidence``。
    """
    input_text = (state.get("diet_input_text") or "").strip()
    if not input_text:
        raise ValidationException("饮食描述不能为空", code="INVALID_QUERY")
    try:
        chat_model = cast(Any, get_chat_model(temperature=0.1))
        model = chat_model.with_structured_output(ParseResult)
        parsed = await model.ainvoke(build_diet_parse_messages(input_text))
    except Exception as exc:
        raise BusinessRuleException("饮食解析失败", code="DIET_PARSE_FAILED") from exc
    return {
        "diet_parse_result": parsed,
        "diet_parsed_foods": parsed.foods,
        "diet_confidence": parsed.confidence,
    }


async def parse_photo_mock(state: ChatState) -> dict[str, Any]:
    """图片解析 mock（Phase 2 暂不接多模态）。"""
    foods = [
        ParsedFood(
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
            data_source=DataSource.llm_estimate,
        ),
        ParsedFood(
            name="未知菜品",
            amount=1,
            unit="份",
            amount_grams=150,
            calories=180,
            protein=8,
            fat=10,
            carbs=15,
            data_source=DataSource.llm_estimate,
        ),
    ]
    return {"diet_parsed_foods": foods, "diet_confidence": 0.3}


async def standardize_units(state: ChatState) -> dict[str, Any]:
    """把所有食物的 amount 统一换算到 grams，方便后续营养计算。"""
    service = _get_service(state)
    pre_structured = cast(Any, state).get("foods")  # 兼容外部注入
    if pre_structured:
        parsed = [await service.food_input_to_parsed(food) for food in pre_structured]
        return {"diet_parsed_foods": parsed, "diet_confidence": 1.0}

    parsed_foods: list[ParsedFood] = []
    for food in state.get("diet_parsed_foods", []) or []:
        amount_grams = food.amount_grams or service.estimate_amount_grams(
            food.name, food.amount, food.unit
        )
        parsed_foods.append(food.model_copy(update={"amount_grams": amount_grams}))
    return {"diet_parsed_foods": parsed_foods}


async def enrich_nutrition(state: ChatState) -> dict[str, Any]:
    """补全食物营养并产出整餐 ParseResult。"""
    service = _get_service(state)
    enriched: list[ParsedFood] = []
    for food in state.get("diet_parsed_foods", []) or []:
        if food.data_source != DataSource.llm_estimate and food.calories > 0:
            enriched.append(food)
            continue
        try:
            enriched.append(
                await enrich_food_tool(
                    service,
                    FoodItemInput(
                        name=food.name,
                        amount=food.amount,
                        unit=food.unit,
                        amount_grams=food.amount_grams,
                        cooking_method=food.cooking_method,
                    ),
                )
            )
        except Exception:
            enriched.append(food.model_copy(update={"data_source": DataSource.llm_estimate}))
    summary = _summary(enriched)
    meal_type_raw = state.get("diet_meal_type")
    meal_type = MealType(meal_type_raw) if isinstance(meal_type_raw, str) else meal_type_raw
    return {
        "diet_parsed_foods": enriched,
        "diet_parse_result": ParseResult(
            foods=enriched,
            meal_type=meal_type,
            confidence=state.get("diet_confidence", 0.7),
            nutrition_summary=summary,
        ),
    }


async def infer_meal_type(state: ChatState) -> dict[str, Any]:
    """推断或确认餐次类型。"""
    meal_type_raw = state.get("diet_meal_type")
    if isinstance(meal_type_raw, str):
        meal_type: MealType | None = MealType(meal_type_raw)
    else:
        meal_type = meal_type_raw
    if meal_type is None:
        hour = datetime.now().hour
        if 6 <= hour <= 9:
            meal_type = MealType.breakfast
        elif 11 <= hour <= 14:
            meal_type = MealType.lunch
        elif 17 <= hour <= 20:
            meal_type = MealType.dinner
        else:
            meal_type = MealType.snack
    parse_result = state.get("diet_parse_result")
    if parse_result is not None:
        parse_result = parse_result.model_copy(update={"meal_type": meal_type})
    return {"diet_meal_type": meal_type.value, "diet_parse_result": parse_result}


def save_or_end(state: ChatState) -> str:
    """决定是否进入保存节点。

    diet subgraph 的保存由全局 Graph 决定（通常 AI 对话确认后由 Tool 触发）；
    在 subgraph 内部默认直接结束，返回解析结果给上游。
    """
    mode = cast(Any, state).get("mode")
    return "save_record" if mode == "create" else "__end__"


async def save_record(state: ChatState) -> dict[str, Any]:
    """保存 parse 结果到数据库（仅当显式传入 mode == 'create' 时走）。"""
    service = _get_service(state)
    meal_type_raw = state.get("diet_meal_type")
    meal_type = (
        MealType(meal_type_raw) if isinstance(meal_type_raw, str) else meal_type_raw
    ) or MealType.snack
    record = await save_diet_record_tool(
        service,
        meal_type=meal_type,
        foods=state.get("diet_parsed_foods", []) or [],
        record_date=state.get("diet_date") or datetime.now().date(),
    )
    return {"diet_saved_record": record}


async def trigger_memory(state: ChatState) -> dict[str, Any]:
    """预留记忆触发节点（Phase 6 集成 memory_agent）。"""
    return {}


def _summary(foods: list[ParsedFood]) -> NutritionSummary:
    fiber_values = [food.fiber for food in foods if food.fiber is not None]
    sodium_values = [food.sodium for food in foods if food.sodium is not None]
    return NutritionSummary(
        total_calories=round(sum(food.calories for food in foods), 1),
        total_protein=round(sum(food.protein for food in foods), 1),
        total_fat=round(sum(food.fat for food in foods), 1),
        total_carbs=round(sum(food.carbs for food in foods), 1),
        total_fiber=round(sum(fiber_values), 1) if fiber_values else None,
        total_sodium=round(sum(sodium_values), 1) if sodium_values else None,
    )


__all__ = [
    "enrich_nutrition",
    "infer_meal_type",
    "parse_photo_mock",
    "parse_text",
    "route_input",
    "save_or_end",
    "save_record",
    "standardize_units",
    "trigger_memory",
]
