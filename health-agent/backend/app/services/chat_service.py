"""Chat message service.

本 Service 只负责会话和消息 CRUD，不包含任何 LLM 调用；AI 编排在
``app.agents.chat`` 中完成。
"""
# ruff: noqa: RUF002

from __future__ import annotations

import uuid
from typing import Any

from app.db.models.chat import ChatMessage
from app.db.repositories.chat_repo import ChatRepository
from app.schemas.chat import ChatCard, ChatMessageResponse, ChatRole


class ChatService:
    """User-scoped chat session and message management."""

    def __init__(self, repo: ChatRepository) -> None:
        self.repo = repo

    async def get_or_create_session(self, session_id: str | None = None) -> str:
        if session_id and session_id.strip():
            return session_id.strip()
        return str(uuid.uuid4())

    async def get_recent_or_create_session(self) -> str:
        return await self.repo.latest_session_id() or str(uuid.uuid4())

    async def save_message(
        self,
        *,
        session_id: str,
        role: ChatRole | str,
        content: str,
        cards: list[ChatCard | dict[str, Any]] | None = None,
    ) -> ChatMessageResponse:
        normalized_cards = [
            card.model_dump(mode="json") if isinstance(card, ChatCard) else card
            for card in (cards or [])
        ]
        message = await self.repo.create_message(
            session_id=session_id,
            role=str(role.value if isinstance(role, ChatRole) else role),
            content=content,
            cards=normalized_cards,
        )
        await self.repo.session.commit()
        return self._to_response(message)

    async def get_history(
        self,
        *,
        session_id: str | None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ChatMessageResponse], int, str | None]:
        target_session_id = session_id or await self.repo.latest_session_id()
        if target_session_id is None:
            return [], 0, None
        page = max(page, 1)
        page_size = min(max(page_size, 1), 50)
        messages = await self.repo.list_messages(
            session_id=target_session_id,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        total = await self.repo.count_messages(session_id=target_session_id)
        return [self._to_response(message) for message in messages], total, target_session_id

    async def delete_session(self, session_id: str) -> None:
        await self.repo.soft_delete_session(session_id)
        await self.repo.session.commit()

    @staticmethod
    def _to_response(message: ChatMessage) -> ChatMessageResponse:
        cards = [ChatCard(**card) for card in (message.cards or [])]
        return ChatMessageResponse(
            id=message.id,
            role=ChatRole(message.role),
            content=message.content,
            cards=cards,
            created_at=message.created_at,
        )


__all__ = ["ChatService"]


