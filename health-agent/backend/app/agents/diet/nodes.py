"""diet subgraph 节点实现。

本文件的所有节点都读写 :class:`ChatState`（而不是独立的 DietState）。
节点读写的都是 ``diet_*`` 前缀字段，与全局 Graph 保持一致。

关键约定：
- ``diet_service`` 通过 LangGraph 的 ``config["configurable"]`` 注入（不进 checkpoint，
  因为 service 持有 DB session 不可序列化）。旧单测仍可直接写入 state 里，
  ``get_dep`` 会按 config → state 顺序回退解析。
- 餐次澄清 / 保存确认通过 ``interrupt()`` 暂停 graph，等用户作答后从中断点恢复。
"""
# ruff: noqa: RUF002

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import date, datetime
from typing import Any, cast

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from app.agents._logging import llm_call, log_node
from app.agents.base import get_chat_model
from app.agents.chat.state import ChatState
from app.agents.deps import get_dep
from app.agents.diet.tools import enrich_food_tool, save_diet_record_tool
from app.agents.interrupts import HumanPrompt, ask_human, card_action, choice_answer
from app.agents.memory.subgraph import build_memory_subgraph
from app.agents.prompts.diet_narrate import build_diet_narrate_messages
from app.agents.prompts.diet_parse import build_diet_parse_messages
from app.core.exceptions import BusinessRuleException, ValidationException
from app.integrations.embedding import EmbeddingClient
from app.schemas.diet import (
    DataSource,
    DietOperation,
    FoodItemInput,
    MealType,
    NutritionSummary,
    ParsedFood,
    ParseResult,
)

logger = logging.getLogger(__name__)
_BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()

_MEAL_LABELS = {
    "breakfast": "早餐",
    "lunch": "午餐",
    "dinner": "晚餐",
    "snack": "加餐",
}


def _discard_task(task: asyncio.Task[Any]) -> None:
    _BACKGROUND_TASKS.discard(task)
    if not task.cancelled():
        with suppress(Exception):
            task.exception()


def _get_service(state: ChatState, config: RunnableConfig = None):
    """取 DietService：优先 ``config.configurable.diet_service``，回退 state。"""
    return get_dep(state, config, "diet_service")


def _parse_result_to_card(
    parse_result: ParseResult,
    suggested_date: date | None,
) -> dict[str, Any]:
    """把 ParseResult 转成 diet_parse 卡片 dict（供 interrupt 载荷使用）。"""
    payload = parse_result.model_dump(mode="json")
    payload["suggested_date"] = (suggested_date or date.today()).isoformat()
    card: dict[str, Any] = {
        "type": "diet_parse",
        "payload": payload,
        "actions": [
            {"kind": "confirm_create_diet_record", "label": "确认保存"},
            {"kind": "edit_diet_items", "label": "修改食物"},
        ],
        "requires_confirmation": True,
    }
    return card


@log_node
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


@log_node
async def parse_text(state: ChatState, config: RunnableConfig = None) -> dict[str, Any]:
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
        async with llm_call("parse_text", "qwen-plus", input_text=input_text):
            parsed = await model.ainvoke(build_diet_parse_messages(input_text))
    except Exception as exc:
        raise BusinessRuleException("饮食解析失败", code="DIET_PARSE_FAILED") from exc
    return {
        "diet_parse_result": parsed,
        "diet_parsed_foods": parsed.foods,
        "diet_confidence": parsed.confidence,
    }


@log_node
async def parse_photo_mock(state: ChatState, config: RunnableConfig = None) -> dict[str, Any]:
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


@log_node
async def standardize_units(state: ChatState, config: RunnableConfig = None) -> dict[str, Any]:
    """把所有食物的 amount 统一换算到 grams，方便后续营养计算。"""
    service = _get_service(state, config)
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


@log_node
async def enrich_nutrition(state: ChatState, config: RunnableConfig = None) -> dict[str, Any]:
    """补全食物营养并产出整餐 ParseResult。"""
    service = _get_service(state, config)
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
    # 保留 parse_text 阶段 LLM 判断出的 operation（append/replace）
    prev_result = state.get("diet_parse_result")
    operation = prev_result.operation if prev_result is not None else DietOperation.replace
    return {
        "diet_parsed_foods": enriched,
        "diet_parse_result": ParseResult(
            foods=enriched,
            meal_type=meal_type,
            operation=operation,
            confidence=state.get("diet_confidence", 0.7),
            nutrition_summary=summary,
        ),
    }


@log_node
async def infer_meal_type(state: ChatState, config: RunnableConfig = None) -> dict[str, Any]:
    """效率模式下按时间自动推断餐次；其它模式保留缺失态留给 confirm_or_clarify 询问。

    - efficiency：缺餐次时按当前时间猜一个，保证无需用户介入即可落库。
    - confirmation/learning：若 meal_type 缺失，保持 None，让 confirm_or_clarify
      通过 interrupt 询问用户。
    """
    meal_type_raw = state.get("diet_meal_type")
    if isinstance(meal_type_raw, str):
        meal_type: MealType | None = MealType(meal_type_raw)
    else:
        meal_type = meal_type_raw

    interaction_mode = state.get("interaction_mode")
    if meal_type is None and interaction_mode == "efficiency":
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
    if parse_result is not None and meal_type is not None:
        parse_result = parse_result.model_copy(update={"meal_type": meal_type})
    return {
        "diet_meal_type": meal_type.value if meal_type is not None else None,
        "diet_parse_result": parse_result,
    }


@log_node
async def confirm_or_clarify(state: ChatState, config: RunnableConfig = None) -> Command:
    """交互式确认节点：餐次澄清 + 路由到下一阶段。

    流程：
    1. 效率模式：infer_meal_type 已补全餐次 → 直接 goto save_record。
    2. 非效率模式且餐次缺失 → interrupt(choice) 询问餐次。
    3. 学习模式：goto narrate_learning（流式讲解 → 再出确认卡）。
    4. 确认模式：goto confirm_save（直接出确认卡）。

    注意：本节点 interrupt 之前无副作用（不落库），满足"恢复时整段重跑"的幂等要求。
    """
    interaction_mode = state.get("interaction_mode") or "confirmation"
    parse_result = state.get("diet_parse_result")
    if parse_result is None:
        return Command(goto="__end__")

    # 效率模式：infer_meal_type 已补全餐次，直接落库。
    if interaction_mode == "efficiency":
        return Command(goto="save_record")

    # 餐次缺失 → 询问用户。
    if parse_result.meal_type is None:
        answer = ask_human(
            HumanPrompt(
                kind="choice",
                prompt_id="diet_meal_type",
                domain="diet",
                question="请问是哪一餐？",
                options=[
                    {"value": "breakfast", "label": "早餐"},
                    {"value": "lunch", "label": "午餐"},
                    {"value": "dinner", "label": "晚餐"},
                    {"value": "snack", "label": "加餐"},
                ],
                allow_free_text=True,
            )
        )
        chosen = choice_answer(answer) or "snack"
        try:
            meal = MealType(chosen)
        except ValueError:
            meal = MealType.snack
        parse_result = parse_result.model_copy(update={"meal_type": meal})

    next_node = "narrate_learning" if interaction_mode == "learning" else "confirm_save"
    return Command(
        goto=next_node,
        update={
            "diet_parse_result": parse_result,
            "diet_meal_type": parse_result.meal_type.value if parse_result.meal_type else "snack",
        },
    )


@log_node
async def narrate_learning(state: ChatState, config: RunnableConfig = None) -> dict[str, Any]:
    """学习模式：用流式 LLM 像营养老师一样自然讲解这一餐。

    输出会被 ``translator`` 通过 ``on_chat_model_stream`` 转成 ``text_delta`` 事件，
    在前端对话区与普通 AI 回复一样呈现，营造"陪伴式"学习体验。
    讲解结束后由 graph 路由到 ``confirm_save`` 节点出确认卡。
    """
    parse_result = state.get("diet_parse_result")
    if parse_result is None:
        return {}
    summary = parse_result.nutrition_summary
    foods_dump = [f.model_dump(mode="json") for f in parse_result.foods]
    summary_dump = summary.model_dump(mode="json") if summary is not None else None
    meal_type = parse_result.meal_type.value if parse_result.meal_type else None
    try:
        # streaming=True 让 astream_events(version="v2") 能捕获 token 流，
        # translator 会把本节点 token 透传成 text_delta（见 translator.text_visible_nodes）。
        model = cast(Any, get_chat_model(temperature=0.7, timeout=60, streaming=True))
        async with llm_call("narrate_learning", "qwen-plus", foods=len(foods_dump)):
            await model.ainvoke(
                build_diet_narrate_messages(
                    foods=foods_dump,
                    meal_type=meal_type,
                    nutrition_summary=summary_dump,
                )
            )
    except Exception as exc:  # 讲解失败不影响保存流程，降级跳过
        logger.warning("narrate_learning failed, skip narration: %s", exc)
    return {}


@log_node
async def confirm_save(state: ChatState, config: RunnableConfig = None) -> Command:
    """出确认卡 interrupt，等待用户 confirm/edit/cancel。

    从 ``confirm_or_clarify`` 拆分出来：让学习模式可以在 interrupt 前
    插入 ``narrate_learning`` 流式讲解节点；其它模式直接进入此节点。
    """
    parse_result = state.get("diet_parse_result")
    if parse_result is None:
        return Command(goto="__end__")
    decision = ask_human(
        HumanPrompt(
            kind="card",
            prompt_id="diet_confirm",
            domain="diet",
            card=_parse_result_to_card(parse_result, state.get("diet_date")),
        )
    )
    action = card_action(decision)
    if action == "cancel":
        return Command(
            goto="__end__",
            update={"diet_cancelled": True, "diet_parse_result": parse_result},
        )
    if action == "edit":
        patch = decision.get("patch") or {}
        update_fields: dict[str, Any] = {}
        if patch.get("meal_type"):
            with suppress(ValueError):
                update_fields["meal_type"] = MealType(str(patch["meal_type"]))
        if patch.get("foods"):
            update_fields["foods"] = [
                f if isinstance(f, ParsedFood) else ParsedFood.model_validate(f)
                for f in patch["foods"]
            ]
        if update_fields:
            parse_result = parse_result.model_copy(update=update_fields)

    meal_value = parse_result.meal_type.value if parse_result.meal_type else "snack"
    return Command(
        goto="save_record",
        update={
            "diet_parse_result": parse_result,
            "diet_meal_type": meal_value,
            "diet_parsed_foods": parse_result.foods,
        },
    )


@log_node
async def save_record(state: ChatState, config: RunnableConfig = None) -> dict[str, Any]:
    """保存 parse 结果到数据库。"""
    service = _get_service(state, config)
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


@log_node
async def trigger_memory(state: ChatState, config: RunnableConfig = None) -> dict[str, Any]:
    """保存饮食记录后异步触发 memory_agent。"""
    record = state.get("diet_saved_record")
    memory_service = get_dep(state, config, "memory_service")
    if record is None or memory_service is None:
        return {}
    try:
        graph = build_memory_subgraph()
        task = asyncio.create_task(
            graph.ainvoke(
                {
                    "user_id": state.get("user_id", ""),
                    "trigger_type": "record_diet",
                    "context_data": record.model_dump(mode="json") if hasattr(record, "model_dump") else record,
                    "memory_service": memory_service,
                    "embedding_client": EmbeddingClient(),
                }
            )
        )
        _BACKGROUND_TASKS.add(task)
        task.add_done_callback(_discard_task)
    except Exception as exc:  # pragma: no cover
        logger.warning("diet memory trigger failed: %s", exc)
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
    "confirm_or_clarify",
    "confirm_save",
    "enrich_nutrition",
    "infer_meal_type",
    "narrate_learning",
    "parse_photo_mock",
    "parse_text",
    "route_input",
    "save_record",
    "standardize_units",
    "trigger_memory",
]
