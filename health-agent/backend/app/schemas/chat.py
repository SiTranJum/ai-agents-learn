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


class ChatStreamRequest(BaseModel):
    """流式 chat 端点的统一输入。

    通过 ``type`` 字段区分三种入口：

    - ``text`` 普通文本消息（兼容旧 ``ChatRequest.message``）
    - ``card_action`` 用户点击卡片按钮（如"确认保存饮食"）
    - ``choice_response`` 用户回应了 AI 的选项澄清（chip 选择 / 自由输入）

    设计参考 docs/plans/2026-05-21-streaming-chat-design.md §4.4
    """

    session_id: str | None = Field(default=None, max_length=64)
    type: Literal["text", "card_action", "choice_response"] = "text"

    # type=text
    message: str | None = Field(default=None, max_length=2000)
    context: ChatContext | dict[str, Any] | None = None

    # type=card_action
    card_id: str | None = None
    action_id: str | None = None
    action_payload: dict[str, Any] | None = None

    # type=choice_response
    prompt_id: str | None = None
    selected_value: str | None = None
    free_text: str | None = Field(default=None, max_length=2000)


class ChatCardAction(BaseModel):
    kind: Literal["confirm_create_diet_record", "edit_diet_items"] | str
    label: str | None = None


class ChatCard(BaseModel):
    type: Literal["diet_parse"] | str
    payload: dict[str, Any]
    actions: list[ChatCardAction] = Field(default_factory=list)
    # 交互模式协议字段：
    # requires_confirmation=False 表示后端已直接执行（效率模式），卡片仅作结果展示，
    # 前端用 Toast 风格呈现，不显示确认按钮。学习模式的讲解走 text_delta 流式输出，
    # 不再以卡内字段携带，因此卡片只剩 requires_confirmation 一个交互模式协议字段。
    requires_confirmation: bool = True


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
    "ChatStreamRequest",
]

