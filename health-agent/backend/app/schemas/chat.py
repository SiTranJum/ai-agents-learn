"""Chat API schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRole(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ChatIntent(StrEnum):
    diet = "diet"
    body = "body"
    plan = "plan"
    memory = "memory"
    suggestion = "suggestion"
    general = "general"


class ChatContext(BaseModel):
    image_url: str | None = None
    referenced_date: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=64)
    context: ChatContext | dict[str, Any] | None = None


class ChatCardAction(BaseModel):
    kind: Literal["confirm_create_diet_record", "edit_diet_items"] | str
    label: str | None = None


class ChatCard(BaseModel):
    type: Literal["diet_parse"] | str
    payload: dict[str, Any]
    actions: list[ChatCardAction] = Field(default_factory=list)


class ChatMessageResponse(BaseModel):
    id: UUID
    role: ChatRole
    content: str
    created_at: datetime
    cards: list[ChatCard] = Field(default_factory=list)


class ChatResponseMessage(BaseModel):
    id: UUID | None = None
    role: ChatRole = ChatRole.assistant
    content: str
    cards: list[ChatCard] = Field(default_factory=list)
    created_at: datetime | None = None


class ChatResponse(BaseModel):
    session_id: str
    messages: list[ChatResponseMessage]
    intent: ChatIntent | str | None = None


__all__ = [
    "ChatCard",
    "ChatCardAction",
    "ChatContext",
    "ChatIntent",
    "ChatMessageResponse",
    "ChatRequest",
    "ChatResponse",
    "ChatResponseMessage",
    "ChatRole",
]

