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


def _parse_result_to_card(
    parse_result: ParseResult,
    suggested_date: date | None,
    *,
    requires_confirmation: bool = True,
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
    )


_BODY_TYPE_LABEL = {
    "water": "饮水",
    "sleep": "睡眠",
    "exercise": "运动",
    "bowel": "排便",
}

_MEAL_LABELS = {
    "breakfast": "早餐",
    "lunch": "午餐",
    "dinner": "晚餐",
    "snack": "加餐",
}


def _body_result_to_card(
    parse_result: BodyParseResult,
    suggested_date: date | None,
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
    """把各分支输出归一化为 ``ai_response`` + ``response_cards``（终态反馈）。

    interrupt 模型下，diet/body 子图通过 ``interrupt()`` 自己完成"问餐次 / 出确认卡"
    的交互，且 **interrupt 暂停时本节点根本不会运行**（graph 在子图内就暂停了，
    卡片由 ``emit_interrupt_events`` 从 interrupt 载荷发出）。

    因此本节点只在子图**自然结束**（已落库 / 已取消）后运行，职责仅剩"给一句
    结果反馈"，绝不能再重发确认卡——否则保存成功后又弹确认卡会造成死循环。
    """
    # diet：根据落库 / 取消结果给终态反馈（不再重发确认卡——确认卡已由 interrupt
    # 发出，前端会把它从 pending 切到 submitted 作为回执；这里只补一句文本即可，
    # 再发卡会与之前的确认卡重复）。
    if state.get("intent") == "diet" and state.get("diet_parse_result") is not None:
        parse_result = cast(ParseResult, state["diet_parse_result"])
        food_count = len(parse_result.foods)

        if state.get("diet_cancelled"):
            return {"ai_response": "好的，已取消，这条记录没有保存。", "response_cards": [], "choice_prompts": []}

        if state.get("diet_saved_record") is not None:
            meal_type = parse_result.meal_type.value if parse_result.meal_type else "snack"
            meal_label = _MEAL_LABELS.get(meal_type, meal_type)
            calories = parse_result.nutrition_summary.total_calories
            response = f"已记录{meal_label}，{food_count} 项食物，共 {calories:.0f}kcal。"
            return {"ai_response": response, "response_cards": [], "choice_prompts": []}

        # 既没保存也没取消（子图理论上要么 interrupt 要么落库/取消，兜底）。
        return {"ai_response": "我已经收到你的饮食信息。", "response_cards": [], "choice_prompts": []}

    # body：同理，子图已通过 interrupt 完成确认，这里只给结果反馈。
    if state.get("intent") == "body" and state.get("body_parse_result") is not None:
        body_result = cast(BodyParseResult, state["body_parse_result"])
        if state.get("body_cancelled"):
            return {"ai_response": "好的，已取消，这条记录没有保存。", "response_cards": [], "choice_prompts": []}
        if state.get("body_saved"):
            label = _BODY_TYPE_LABEL.get(body_result.record_type.value, "数据")
            return {"ai_response": f"已记录{label}。", "response_cards": [], "choice_prompts": []}
        return {"ai_response": "我已经收到你的身体数据。", "response_cards": [], "choice_prompts": []}

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




