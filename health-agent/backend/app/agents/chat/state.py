"""Shared state for the global chat graph."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal, TypedDict

try:  # pragma: no cover
    from langchain_core.messages import BaseMessage
    from langgraph.graph.message import add_messages
except ModuleNotFoundError:  # pragma: no cover
    BaseMessage = Any  # type: ignore[assignment,misc]

    def add_messages(left: Any, right: Any) -> Any:  # type: ignore[no-redef]
        raise RuntimeError("langgraph is required for ChatState.messages merging")


Intent = Literal["diet", "body", "plan", "memory", "suggestion", "general"]

# 交互模式：影响 AI 是否要求确认、是否附带知识讲解。
# 注意与 diet 子图的 ``mode`` 字段（保存开关 "create"/None）区分。
InteractionMode = Literal["efficiency", "confirmation", "learning"]


class ChatState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    session_id: str | None
    user_message: str
    chat_history: list[dict[str, Any]]
    context: dict[str, Any]
    interaction_mode: InteractionMode | None
    prompt_messages: list[Any]
    ai_response: str
    response_cards: list[dict[str, Any]]
    intent: Intent | None

    long_term_profile: list[dict[str, Any]]
    recalled_memories: list[dict[str, Any]]
    knowledge: list[dict[str, Any]]

    diet_input_text: str | None
    diet_image_url: str | None
    diet_meal_type: str | None
    diet_date: date | None
    diet_parsed_foods: list[Any]
    diet_confidence: float
    diet_parse_result: Any
    diet_saved_record: Any
    diet_cancelled: bool
    foods: list[Any]
    mode: str | None
    diet_service: Any

    body_input_text: str | None
    body_date: date | None
    body_parse_result: Any
    body_saved: bool
    body_cancelled: bool
    body_service: Any

    profile: Any
    plan_service: Any
    request_type: str | None
    card_action_id: str | None
    card_action_payload: dict[str, Any] | None

    memory_service: Any
    rag_service: Any
    embedding_client: Any

    request_id: str | None
    error: str | None
    pending_action: Any
    choice_prompts: list[dict[str, Any]]


__all__ = ["ChatState", "Intent", "InteractionMode"]
