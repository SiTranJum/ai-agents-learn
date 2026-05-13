"""Chat conversation ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ChatMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """One persisted chat message in a user-scoped session."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_chat_messages_user_session_time", "user_id", "session_id", "created_at"),
        Index("idx_chat_messages_user_time", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    cards: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    deleted_at: Mapped[datetime | None]


__all__ = ["ChatMessage"]


