"""Top-level chat agent nodes."""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any, cast

from pydantic import BaseModel, Field

from app.agents.base import get_chat_model
from app.agents.chat.state import ChatState, Intent
from app.agents.chat.tools import recall_memories_tool, search_knowledge_tool
from app.agents.memory.subgraph import build_memory_subgraph
from app.agents.prompts.chat_system import build_chat_messages, build_intent_messages
from app.core.exceptions import LLMProviderException
from app.schemas.chat import ChatCard, ChatCardAction
from app.schemas.diet import ParseResult

logger = logging.getLogger(__name__)
_BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()


class IntentResult(BaseModel):
    """Structured output schema for the intent classifier."""

    intent: Intent = Field(description="One of diet/body/plan/memory/suggestion/general")
    confidence: float = Field(default=0.7, ge=0, le=1)


def _rule_based_intent(message: str) -> Intent:
    text = message.strip().lower()
    if any(keyword in text for keyword in ["吃", "饭", "餐", "早餐", "午餐", "晚餐", "零食", "热量", "卡路里", "鸡胸", "米饭"]):
        return "diet"
    if any(keyword in text for keyword in ["体重", "睡眠", "喝水", "运动", "围度", "排便"]):
        return "body"
    if any(keyword in text for keyword in ["计划", "目标", "减脂", "减肥", "增肌"]):
        return "plan"
    if any(keyword in text for keyword in ["建议", "推荐", "怎么", "如何", "应该"]):
        return "suggestion"
    if any(keyword in text for keyword in ["记住", "别忘", "忘记"]):
        return "memory"
    return "general"


def _get_dependency(state: ChatState, name: str) -> Any:
    return cast(dict[str, Any], cast(object, state)).get(name)


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
        result = await model.ainvoke(build_intent_messages(message))
        return {"intent": result.intent or fallback}
    except Exception as exc:  # pragma: no cover - protects local/dev without API key
        logger.info("intent classifier fallback used: %s", exc)
        return {"intent": fallback}


def route_after_intent(state: ChatState) -> str:
    """Route only implemented domain subgraphs; unfinished domains use general chat."""
    return "diet" if state.get("intent") == "diet" else "general"


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


async def assemble_prompt(state: ChatState) -> dict[str, Any]:
    """Assemble deterministic prompt messages for the final LLM call."""
    prompt_messages = build_chat_messages(
        user_message=state.get("user_message") or "",
        history=state.get("chat_history", []) or [],
        memories=state.get("recalled_memories", []) or [],
        knowledge=state.get("knowledge", []) or [],
    )
    return {"prompt_messages": prompt_messages}


async def call_llm(state: ChatState) -> dict[str, Any]:
    """Generate final assistant text for general chat.

    SDK/API 说明：
    - ``ainvoke(messages)`` 是 LangChain chat model 的异步调用方法。
    - 返回通常是 ``AIMessage``，其 ``content`` 是模型回复文本。
    """
    try:
        model = cast(Any, get_chat_model(temperature=0.7, timeout=60))
        response = await model.ainvoke(state.get("prompt_messages", []))
        content = getattr(response, "content", response)
        return {"ai_response": str(content), "response_cards": []}
    except Exception as exc:
        raise LLMProviderException("AI 对话服务暂时不可用") from exc


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


def _parse_result_to_card(parse_result: ParseResult, suggested_date: date | None) -> ChatCard:
    payload = parse_result.model_dump(mode="json")
    payload["suggested_date"] = (suggested_date or date.today()).isoformat()
    return ChatCard(
        type="diet_parse",
        payload=payload,
        actions=[
            ChatCardAction(kind="confirm_create_diet_record", label="确认保存"),
            ChatCardAction(kind="edit_diet_items", label="修改食物"),
        ],
    )


async def wrap_response(state: ChatState) -> dict[str, Any]:
    """Normalize branch outputs into ``ai_response`` + ``response_cards``."""
    if state.get("intent") == "diet" and state.get("diet_parse_result") is not None:
        parse_result = cast(ParseResult, state["diet_parse_result"])
        card = _parse_result_to_card(parse_result, state.get("diet_date"))
        food_count = len(parse_result.foods)
        meal_type = parse_result.meal_type.value if parse_result.meal_type else "snack"
        response = f"我识别到 {food_count} 项食物，餐次暂定为 {meal_type}。请确认后再保存到饮食记录。"
        return {"ai_response": response, "response_cards": [card.model_dump(mode="json")]}
    return {"ai_response": state.get("ai_response") or "我已经收到你的消息。", "response_cards": state.get("response_cards", []) or []}


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




