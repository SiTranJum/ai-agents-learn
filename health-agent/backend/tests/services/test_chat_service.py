"""Phase 7 - ChatService unit tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from app.db.models.chat import ChatMessage
from app.schemas.chat import ChatRole
from app.services.chat_service import ChatService


class _FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class _FakeRepo:
    def __init__(self) -> None:
        self.session = _FakeSession()
        self.messages: list[ChatMessage] = []

    async def latest_session_id(self) -> str | None:
        active = [message for message in self.messages if message.deleted_at is None]
        return active[-1].session_id if active else None

    async def create_message(self, *, session_id: str, role: str, content: str, cards: list[dict[str, Any]] | None = None) -> ChatMessage:
        now = datetime.now(UTC)
        message = ChatMessage(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            cards=cards or [],
            created_at=now,
            updated_at=now,
        )
        self.messages.append(message)
        return message

    async def list_messages(self, *, session_id: str, offset: int = 0, limit: int = 20) -> list[ChatMessage]:
        return [message for message in self.messages if message.session_id == session_id and message.deleted_at is None][offset : offset + limit]

    async def count_messages(self, *, session_id: str) -> int:
        return len([message for message in self.messages if message.session_id == session_id and message.deleted_at is None])

    async def soft_delete_session(self, session_id: str) -> int:
        count = 0
        for message in self.messages:
            if message.session_id == session_id and message.deleted_at is None:
                message.deleted_at = datetime.now(UTC)
                count += 1
        return count


@pytest.mark.asyncio
async def test_chat_service_creates_session_and_saves_message() -> None:
    repo = _FakeRepo()
    service = ChatService(repo=repo)  # type: ignore[arg-type]

    session_id = await service.get_or_create_session(None)
    message = await service.save_message(
        session_id=session_id,
        role=ChatRole.user,
        content="午饭吃了一碗米饭",
    )

    assert uuid.UUID(session_id)
    assert message.role == ChatRole.user
    assert repo.session.commits == 1


@pytest.mark.asyncio
async def test_chat_service_history_and_idempotent_delete() -> None:
    repo = _FakeRepo()
    service = ChatService(repo=repo)  # type: ignore[arg-type]
    session_id = "s1"
    await service.save_message(session_id=session_id, role=ChatRole.user, content="hi")
    await service.save_message(session_id=session_id, role=ChatRole.assistant, content="hello")

    messages, total, resolved_session_id = await service.get_history(session_id=None)

    assert total == 2
    assert resolved_session_id == session_id
    assert [message.content for message in messages] == ["hi", "hello"]

    await service.delete_session(session_id)
    await service.delete_session(session_id)
    messages, total, _ = await service.get_history(session_id=session_id)
    assert messages == []
    assert total == 0

