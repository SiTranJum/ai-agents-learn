"""Top-level chat agent nodes."""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date
from typing import Any, cast

from pydantic import BaseModel, Field

from app.agents._logging import llm_call, log_llm_call, log_node
from app.agents.base import get_chat_model
from app.agents.chat.state import ChatState, Intent
from app.agents.chat.tools import recall_memories_tool, search_knowledge_tool
from app.agents.memory.subgraph import build_memory_subgraph
from app.agents.prompts.chat_system import build_chat_messages, build_intent_messages
from app.core.exceptions import LLMProviderException
from app.schemas.chat import ChatCard, ChatCardAction
from app.schemas.body import BodyParseResult
from app.schemas.diet import ParseResult

logger = logging.getLogger(__name__)
_BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()


class IntentResult(BaseModel):
    """Structured output schema for the intent classifier."""

    intent: Intent = Field(description="One of diet/body/plan/memory/suggestion/general")
    confidence: float = Field(default=0.7, ge=0, le=1)


def _rule_based_intent(message: str) -> Intent:
    text = message.strip().lower()
    if re.search(r"(?:减|瘦|增)\s*\d+(?:\.\d+)?\s*(?:kg|公斤|斤)", text):
        return "plan"
    if any(keyword in text for keyword in ["计划", "目标", "减脂", "减肥", "增肌", "早睡", "作息", "习惯养成"]):
        return "plan"
    if any(phrase in text for phrase in ["改善饮食", "控制热量", "少吃外卖", "戒零食", "运动习惯"]):
        return "plan"
    if any(keyword in text for keyword in ["吃", "饭", "餐", "早餐", "午餐", "晚餐", "零食", "热量", "卡路里", "鸡胸", "米饭"]):
        return "diet"
    if any(keyword in text for keyword in ["体重", "睡眠", "喝水", "运动", "围度", "排便"]):
        return "body"
    if any(keyword in text for keyword in ["建议", "推荐", "怎么", "如何", "应该"]):
        return "suggestion"
    if any(keyword in text for keyword in ["记住", "别忘", "忘记"]):
        return "memory"
    return "general"


def _get_dependency(state: ChatState, name: str) -> Any:
    return cast(dict[str, Any], cast(object, state)).get(name)


@log_node
async def identify_intent(state: ChatState) -> dict[str, Any]:
    """Identify user intent with LLM structured output and safe rule fallback.

    SDK/API 说明：
    - ``get_chat_model`` 返回 DashScope OpenAI 兼容模型。
    - ``with_structured_output(IntentResult)`` 会让 LangChain 要求模型按
      Pydantic schema 输出，并自动解析成 ``IntentResult``。
    - 如果模型不可用，fallback 到关键词规则，保证接口在本地测试时可跑通。
    """
    message = (state.get("user_message") or state.get("diet_input_text") or "").strip()
    if not message:
        return {"intent": "general"}
    fallback = _rule_based_intent(message)
    try:
        chat_model = cast(Any, get_chat_model(temperature=0.0, timeout=20))
        model = chat_model.with_structured_output(IntentResult)
        async with llm_call("identify_intent", "qwen-plus", message=message):
            result = await model.ainvoke(build_intent_messages(message))
        return {"intent": result.intent or fallback}
    except Exception as exc:  # pragma: no cover - protects local/dev without API key
        logger.info("intent classifier fallback used: %s", exc)
        return {"intent": fallback}


@log_node
def route_after_intent(state: ChatState) -> str:
    """Route only implemented domain subgraphs; unfinished domains use general chat."""
    intent = state.get("intent")
    if intent == "diet":
        return "diet"
    if intent == "body":
        return "body"
    if intent == "plan":
        return "plan"
    return "general"


@log_node
async def recall_memories(state: ChatState) -> dict[str, Any]:
    """Recall top memories for the current message.

    失败时返回空列表，不影响主对话；这是 AI 体验降级，不是业务失败。
    """
    service = _get_dependency(state, "memory_service")
    if service is None:
        return {"recalled_memories": [], "long_term_profile": []}
    query = state.get("user_message") or ""
    try:
        recalled = await recall_memories_tool(
            service,
            query=query,
            intent=state.get("intent"),
            top_k=3,
        )
        return {"recalled_memories": recalled, "long_term_profile": []}
    except Exception as exc:  # pragma: no cover - embedding/db graceful degradation
        logger.warning("memory recall failed: %s", exc)
        return {"recalled_memories": [], "long_term_profile": [], "error": "memory_recall_failed"}


@log_node
async def search_knowledge(state: ChatState) -> dict[str, Any]:
    """Retrieve health knowledge snippets for general responses."""
    service = _get_dependency(state, "rag_service")
    if service is None:
        return {"knowledge": []}
    try:
        results = await search_knowledge_tool(
            service,
            query=state.get("user_message") or "",
            category=None,
            top_k=3,
        )
        return {"knowledge": results}
    except Exception as exc:  # pragma: no cover
        logger.warning("knowledge search failed: %s", exc)
        return {"knowledge": [], "error": "knowledge_search_failed"}


@log_node
async def assemble_prompt(state: ChatState) -> dict[str, Any]:
    """Assemble deterministic prompt messages for the final LLM call."""
    prompt_messages = build_chat_messages(
        user_message=state.get("user_message") or "",
        history=state.get("chat_history", []) or [],
        memories=state.get("recalled_memories", []) or [],
        knowledge=state.get("knowledge", []) or [],
        interaction_mode=state.get("interaction_mode"),
    )
    return {"prompt_messages": prompt_messages}


@log_node
async def call_llm(state: ChatState) -> dict[str, Any]:
    """Generate final assistant text for general chat.

    SDK/API 说明：
    - ``ainvoke(messages)`` 是 LangChain chat model 的异步调用方法。
    - 返回通常是 ``AIMessage``，其 ``content`` 是模型回复文本。
    """
    try:
        # streaming=True 让 LangChain 走 SSE 模式调用 DashScope，
        # astream_events(version="v2") 才能捕获 on_chat_model_stream → text_delta。
        # with_structured_output 节点（identify_intent 等）不开 streaming，
        # 因为它们返回结构化对象，token 流没意义。
        model = cast(Any, get_chat_model(temperature=0.7, timeout=60, streaming=True))
        async with llm_call("call_llm", "qwen-plus", messages_count=len(state.get("prompt_messages", []) or [])):
            response = await model.ainvoke(state.get("prompt_messages", []))
        content = getattr(response, "content", response)
        return {"ai_response": str(content), "response_cards": []}
    except Exception as exc:
        raise LLMProviderException("AI 对话服务暂时不可用") from exc


@log_node
async def trigger_memory_extract(state: ChatState) -> dict[str, Any]:
    """Fire-and-forget memory extraction after assistant reply."""
    memory_service = _get_dependency(state, "memory_service")
    embedding_client = _get_dependency(state, "embedding_client")
    if memory_service is None or embedding_client is None:
        return {}
    context_data = {
        "session_id": state.get("session_id"),
        "user_message": state.get("user_message"),
        "assistant_message": state.get("ai_response"),
        "intent": state.get("intent"),
    }
    try:
        memory_graph = build_memory_subgraph()
        task = asyncio.create_task(
            memory_graph.ainvoke(
                {
                    "user_id": state.get("user_id"),
                    "trigger_type": "chat_message",
                    "context_data": context_data,
                    "memory_service": memory_service,
                    "embedding_client": embedding_client,
                }
            )
        )
        _BACKGROUND_TASKS.add(task)
        task.add_done_callback(_BACKGROUND_TASKS.discard)
    except Exception as exc:  # pragma: no cover
        logger.warning("failed to schedule memory extraction: %s", exc)
    return {}


def _diet_knowledge_text(parse_result: ParseResult) -> str:
    """学习模式：基于解析出的营养汇总，生成简短的营养知识讲解。"""
    s = parse_result.nutrition_summary
    return (
        f"本餐约 {s.total_calories:.0f}kcal，三大营养素：碳水 {s.total_carbs:.0f}g、"
        f"蛋白质 {s.total_protein:.0f}g、脂肪 {s.total_fat:.0f}g。"
        "碳水是主要供能来源，蛋白质有助于肌肉合成与饱腹，脂肪需适量控制。"
    )


def _parse_result_to_card(
    parse_result: ParseResult,
    suggested_date: date | None,
    *,
    requires_confirmation: bool = True,
    knowledge: str | None = None,
) -> ChatCard:
    payload = parse_result.model_dump(mode="json")
    payload["suggested_date"] = (suggested_date or date.today()).isoformat()
    # 效率模式（requires_confirmation=False）已直接落库，卡片仅作结果展示，
    # 不提供"确认保存"按钮，仅保留"修改食物"作为纠错入口。
    if requires_confirmation:
        actions = [
            ChatCardAction(kind="confirm_create_diet_record", label="确认保存"),
            ChatCardAction(kind="edit_diet_items", label="修改食物"),
        ]
    else:
        actions = [ChatCardAction(kind="edit_diet_items", label="修改食物")]
    return ChatCard(
        type="diet_parse",
        payload=payload,
        actions=actions,
        requires_confirmation=requires_confirmation,
        knowledge=knowledge,
    )


_BODY_TYPE_LABEL = {
    "water": "饮水",
    "sleep": "睡眠",
    "exercise": "运动",
    "bowel": "排便",
}


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
    suggested_date: date | None,
    *,
    knowledge: str | None = None,
) -> ChatCard:
    payload = parse_result.model_dump(mode="json")
    payload["suggested_date"] = (suggested_date or date.today()).isoformat()
    return ChatCard(
        type="body_parse",
        payload=payload,
        actions=[
            ChatCardAction(kind="confirm_create_body_record", label="确认保存"),
            ChatCardAction(kind="cancel_body_record", label="取消"),
        ],
        knowledge=knowledge,
    )


def _body_response_text(parse_result: BodyParseResult) -> str:
    """根据解析出的身体数据类型生成确认引导文案。"""
    rt = parse_result.record_type.value
    label = _BODY_TYPE_LABEL.get(rt, "数据")
    if rt == "water" and parse_result.water_amount:
        return f"我识别到饮水 {parse_result.water_amount}ml。请确认后保存。"
    if rt == "sleep":
        parts = []
        if parse_result.sleep_bed_time and parse_result.sleep_wake_time:
            parts.append(f"{parse_result.sleep_bed_time}–{parse_result.sleep_wake_time}")
        return f"我识别到睡眠记录{('（' + '，'.join(parts) + '）') if parts else ''}。请确认后保存。"
    if rt == "exercise":
        seg = parse_result.exercise_type or "运动"
        dur = f" {parse_result.exercise_duration} 分钟" if parse_result.exercise_duration else ""
        return f"我识别到{seg}{dur}。请确认后保存。"
    if rt == "bowel":
        return "我识别到排便记录。请确认后保存。"
    return f"我识别到{label}记录。请确认后保存。"


@log_node
async def wrap_response(state: ChatState) -> dict[str, Any]:
    """Normalize branch outputs into ``ai_response`` + ``response_cards``.

    按交互模式区分响应结构：
    - efficiency：diet 子图已自动落库，返回 Toast 风格结果卡片（无需确认）。
    - confirmation：返回需用户点击确认的结果卡片（默认行为）。
    - learning：在确认卡片基础上追加 ``knowledge`` 知识讲解字段。

    P2 逻辑：当饮食意图识别到食物但 meal_type 缺失时，
    产出 choice_prompts 让前端弹选项 chips（仅非效率模式触发，
    效率模式经 infer_meal_type 已补全餐次）。
    """
    interaction_mode = state.get("interaction_mode") or "confirmation"
    is_efficiency = interaction_mode == "efficiency"
    is_learning = interaction_mode == "learning"

    if state.get("intent") == "diet" and state.get("diet_parse_result") is not None:
        parse_result = cast(ParseResult, state["diet_parse_result"])
        food_count = len(parse_result.foods)

        # 非效率模式且 meal_type 缺失且无 pending_action → 先澄清餐次
        if (
            not is_efficiency
            and parse_result.meal_type is None
            and state.get("pending_action") is None
        ):
            import uuid
            prompt_id = f"meal_type_{uuid.uuid4().hex[:8]}"
            choice_prompt = {
                "prompt_id": prompt_id,
                "question": "请选择餐次",
                "options": [
                    {"value": "breakfast", "label": "早餐"},
                    {"value": "lunch", "label": "午餐"},
                    {"value": "dinner", "label": "晚餐"},
                    {"value": "snack", "label": "加餐"},
                ],
                "allow_free_text": True,
            }
            response = f"我识别到 {food_count} 项食物。请问是哪一餐？"
            return {
                "ai_response": response,
                "response_cards": [],
                "choice_prompts": [choice_prompt],
                # 把部分解析结果存到 state，供 API 层写入 pending_action
                "diet_parse_result": parse_result,
            }

        meal_type = parse_result.meal_type.value if parse_result.meal_type else "snack"
        knowledge = _diet_knowledge_text(parse_result) if is_learning else None

        if is_efficiency:
            # 效率模式：diet 子图已落库，给 Toast 风格的"已记录"反馈，卡片不需确认。
            card = _parse_result_to_card(
                parse_result, state.get("diet_date"), requires_confirmation=False
            )
            calories = parse_result.nutrition_summary.total_calories
            response = f"已记录 {meal_type}，{food_count} 项食物，共 {calories:.0f}kcal。"
        else:
            # 确认 / 学习模式：出确认卡片，学习模式附带知识讲解。
            card = _parse_result_to_card(
                parse_result,
                state.get("diet_date"),
                requires_confirmation=True,
                knowledge=knowledge,
            )
            response = f"我识别到 {food_count} 项食物，餐次为 {meal_type}。请确认后再保存到饮食记录。"

        return {
            "ai_response": response,
            "response_cards": [card.model_dump(mode="json")],
            "choice_prompts": [],
        }

    # 身体数据意图：把 body_parse_result 转成 body_parse 卡片
    # 注：V1 body 子图尚无自动落库能力，效率模式仍走确认卡片（已在文档中标注为限制）。
    if state.get("intent") == "body" and state.get("body_parse_result") is not None:
        body_result = cast(BodyParseResult, state["body_parse_result"])
        knowledge = _body_knowledge_text(body_result) if is_learning else None
        card = _body_result_to_card(body_result, state.get("body_date"), knowledge=knowledge)
        response = _body_response_text(body_result)
        return {
            "ai_response": response,
            "response_cards": [card.model_dump(mode="json")],
            "choice_prompts": [],
        }

    return {
        "ai_response": state.get("ai_response") or "我已经收到你的消息。",
        "response_cards": state.get("response_cards", []) or [],
        "choice_prompts": state.get("choice_prompts", []) or [],
    }


__all__ = [
    "assemble_prompt",
    "call_llm",
    "identify_intent",
    "recall_memories",
    "route_after_intent",
    "search_knowledge",
    "trigger_memory_extract",
    "wrap_response",
]




