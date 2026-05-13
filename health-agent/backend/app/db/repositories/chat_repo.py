"""Chat message repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat import ChatMessage


class ChatRepository:
    """User-scoped repository for chat messages and sessions."""

    def __init__(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def latest_session_id(self) -> str | None:
        stmt = (
            select(ChatMessage.session_id)
            .where(ChatMessage.user_id == self.user_id, ChatMessage.deleted_at.is_(None))
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        cards: list[dict[str, Any]] | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            user_id=self.user_id,
            session_id=session_id,
            role=role,
            content=content,
            cards=cards or [],
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def list_messages(
        self,
        *,
        session_id: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(
                ChatMessage.user_id == self.user_id,
                ChatMessage.session_id == session_id,
                ChatMessage.deleted_at.is_(None),
            )
            .order_by(ChatMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def count_messages(self, *, session_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ChatMessage)
            .where(
                ChatMessage.user_id == self.user_id,
                ChatMessage.session_id == session_id,
                ChatMessage.deleted_at.is_(None),
            )
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def session_exists(self, session_id: str) -> bool:
        stmt = (
            select(ChatMessage.id)
            .where(ChatMessage.user_id == self.user_id, ChatMessage.session_id == session_id)
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    async def soft_delete_session(self, session_id: str) -> int:
        stmt = select(ChatMessage).where(
            ChatMessage.user_id == self.user_id,
            ChatMessage.session_id == session_id,
            ChatMessage.deleted_at.is_(None),
        )
        messages = list((await self.session.execute(stmt)).scalars().all())
        now = datetime.now(UTC)
        for message in messages:
            message.deleted_at = now
        await self.session.flush()
        return len(messages)


__all__ = ["ChatRepository"]

