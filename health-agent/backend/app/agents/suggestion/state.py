"""Suggestion agent state."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from app.schemas.suggestion import SuggestionDraft

SuggestionKind = Literal["daily", "meal", "insight"]


class SuggestionState(TypedDict, total=False):
    user_id: str
    suggestion_type: SuggestionKind
    meal_type: str | None
    profile: Any
    diet_service: Any
    body_service: Any
    plan_service: Any
    memory_service: Any
    rag_service: Any
    recent_data: dict[str, Any]
    memories: list[dict[str, Any]]
    knowledge: list[dict[str, Any]]
    raw_suggestions: list[SuggestionDraft]
    filtered_suggestions: list[SuggestionDraft]
    reasoning: str
    error: str | None


__all__ = ["SuggestionKind", "SuggestionState"]

