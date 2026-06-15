"""body subgraph 节点实现。

与 diet subgraph 对称：节点读写共享 :class:`ChatState`，字段带 ``body_`` 前缀。
解析自然语言为结构化身体数据后，通过 ``interrupt()`` 出确认卡片，用户确认后
节点内直接调 ``body_service`` 落库（不再依赖前端 card_action 快速路径）。
"""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

import logging
from datetime import date as date_cls
from typing import Any, cast

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from app.agents._logging import llm_call, log_node
from app.agents.base import get_chat_model
from app.agents.chat.state import ChatState
from app.agents.deps import get_dep
from app.agents.interrupts import HumanPrompt, ask_human, card_action
from app.agents.prompts.body_parse import build_body_parse_messages
from app.core.exceptions import BusinessRuleException, ValidationException
from app.schemas.body import BodyParseResult

logger = logging.getLogger(__name__)


def _body_knowledge_text(parse_result: BodyParseResult) -> str:
    """学习模式：针对身体数据类型给出简短健康知识讲解。"""
    rt = parse_result.record_type.value
    if rt == "water":
        return "成人每日建议饮水约 1500–1700ml，少量多次比一次大量更利于吸收。"
    if rt == "sleep":
        return "规律作息和 7–9 小时睡眠有助于代谢和食欲激素平衡，长期睡眠不足易增加进食量。"
    if rt == "exercise":
        return "有氧运动帮助消耗热量，力量训练提升基础代谢，两者结合减脂效果更好。"
    if rt == "bowel":
        return "排便规律可反映膳食纤维和水分摄入是否充足，布里斯托 3–4 型为理想形态。"
    return "持续记录身体数据有助于发现趋势，让健康管理更有依据。"


def _body_result_to_card(
    parse_result: BodyParseResult,
    suggested_date: date_cls | None,
    *,
    knowledge: str | None = None,
) -> dict[str, Any]:
    """把 BodyParseResult 转成 body_parse 卡片 dict（供 interrupt 载荷使用）。"""
    payload = parse_result.model_dump(mode="json")
    payload["suggested_date"] = (suggested_date or date_cls.today()).isoformat()
    card: dict[str, Any] = {
        "type": "body_parse",
        "payload": payload,
        "actions": [
            {"kind": "confirm_create_body_record", "label": "确认保存"},
            {"kind": "cancel_body_record", "label": "取消"},
        ],
        "requires_confirmation": True,
    }
    if knowledge is not None:
        card["knowledge"] = knowledge
    return card


async def _save_body_record(
    service: Any, parse_result: BodyParseResult, record_date: date_cls
) -> None:
    """根据 record_type 调用对应的 body_service 写入方法。"""
    from app.schemas.body import (
        BowelRecordCreate,
        BowelStatus,
        ExerciseRecordCreate,
        SleepQuality,
        SleepRecordCreate,
        WaterRecordCreate,
    )

    rt = parse_result.record_type.value
    if rt == "water":
        amount = parse_result.water_amount
        if not amount:
            raise ValidationException("缺少饮水量", code="BODY_SAVE_INVALID")
        await service.create_water(
            WaterRecordCreate(date=record_date, amount=int(amount), operation="append")
        )
    elif rt == "sleep":
        bed = parse_result.sleep_bed_time
        wake = parse_result.sleep_wake_time
        if not bed or not wake:
            raise ValidationException("缺少睡眠起止时间", code="BODY_SAVE_INVALID")
        try:
            quality = SleepQuality(parse_result.sleep_quality or "good")
        except ValueError:
            quality = SleepQuality.good
        await service.create_sleep(
            SleepRecordCreate(date=record_date, bed_time=str(bed), wake_time=str(wake), quality=quality)
        )
    elif rt == "exercise":
        duration = parse_result.exercise_duration
        if not duration:
            raise ValidationException("缺少运动时长", code="BODY_SAVE_INVALID")
        await service.create_exercise(
            ExerciseRecordCreate(
                date=record_date,
                type=str(parse_result.exercise_type or "运动"),
                duration=int(duration),
            )
        )
    elif rt == "bowel":
        try:
            status = BowelStatus(parse_result.bowel_status or "normal")
        except ValueError:
            status = BowelStatus.normal
        await service.create_bowel(
            BowelRecordCreate(
                date=record_date,
                time=str(parse_result.bowel_time or "08:00"),
                status=status,
            )
        )
    else:
        raise ValidationException(f"不支持的身体数据类型: {rt}", code="BODY_SAVE_INVALID")


@log_node
async def parse_body_text(state: ChatState, config: RunnableConfig = None) -> dict[str, Any]:
    """LLM 解析身体数据自然语言描述。

    读 ``body_input_text``；写 ``body_parse_result``。
    """
    input_text = (state.get("body_input_text") or state.get("user_message") or "").strip()
    if not input_text:
        raise ValidationException("身体数据描述不能为空", code="INVALID_QUERY")
    try:
        chat_model = cast(Any, get_chat_model(temperature=0.1))
        model = chat_model.with_structured_output(BodyParseResult)
        async with llm_call("parse_body_text", "qwen-plus", input_text=input_text):
            parsed = await model.ainvoke(build_body_parse_messages(input_text))
    except Exception as exc:
        raise BusinessRuleException("身体数据解析失败", code="BODY_PARSE_FAILED") from exc
    return {"body_parse_result": parsed}


@log_node
async def confirm_body_record(state: ChatState, config: RunnableConfig = None) -> Command:
    """身体数据确认节点：interrupt 出卡片，用户确认后落库。

    - confirm → 调 body_service 写入，标记 body_saved；
    - cancel → 不落库，标记 body_cancelled。

    interrupt 之前无副作用，满足"恢复时整段重跑"的幂等要求。
    """
    parse_result = state.get("body_parse_result")
    if parse_result is None:
        return Command(goto="__end__")

    interaction_mode = state.get("interaction_mode") or "confirmation"
    knowledge = _body_knowledge_text(parse_result) if interaction_mode == "learning" else None
    decision = ask_human(
        HumanPrompt(
            kind="card",
            prompt_id="body_confirm",
            domain="body",
            card=_body_result_to_card(parse_result, state.get("body_date"), knowledge=knowledge),
        )
    )
    if card_action(decision) == "cancel":
        return Command(goto="__end__", update={"body_cancelled": True})

    service = get_dep(state, config, "body_service")
    if service is None:
        logger.warning("body_service missing; cannot persist body record")
        return Command(goto="__end__", update={"body_saved": False})
    record_date = state.get("body_date") or date_cls.today()
    await _save_body_record(service, parse_result, record_date)
    return Command(goto="__end__", update={"body_saved": True})


__all__ = ["confirm_body_record", "parse_body_text"]
