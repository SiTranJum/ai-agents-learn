"""Phase 7 - AI chat API tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from app.dependencies import (
    get_chat_agent,
    get_chat_service,
    get_current_user,
    get_diet_service,
    get_memory_service,
    get_rag_service,
)
from app.main import app
from app.schemas.auth import CurrentUser
from app.schemas.chat import ChatCard, ChatMessageResponse, ChatRole


class _FakeChatService:
    def __init__(self) -> None:
        self.saved: list[dict[str, Any]] = []
        self.session_id = "session-1"

    async def get_or_create_session(self, session_id: str | None = None) -> str:
        return session_id or self.session_id

    async def save_message(self, *, session_id: str, role, content: str, cards=None):
        item = {"session_id": session_id, "role": str(role.value if hasattr(role, "value") else role), "content": content, "cards": cards or []}
        self.saved.append(item)
        return ChatMessageResponse(
            id=uuid.uuid4(),
            role=ChatRole(item["role"]),
            content=content,
            cards=[card if isinstance(card, ChatCard) else ChatCard(**card) for card in (cards or [])],
            created_at=datetime.now(UTC),
        )

    async def get_history(self, *, session_id: str | None, page: int = 1, page_size: int = 20):
        messages = [
            ChatMessageResponse(
                id=uuid.uuid4(),
                role=ChatRole(item["role"]),
                content=item["content"],
                created_at=datetime.now(UTC),
            )
            for item in self.saved
        ]
        return messages, len(messages), session_id or self.session_id

    async def delete_session(self, session_id: str) -> None:
        self.saved = [item for item in self.saved if item["session_id"] != session_id]


class _FakeAgent:
    async def ainvoke(self, state):
        assert state["user_message"] == "午饭吃了一碗米饭"
        return {
            "intent": "diet",
            "ai_response": "我识别到 1 项食物。",
            "response_cards": [
                {
                    "type": "diet_parse",
                    "payload": {"foods": [], "meal_type": "lunch", "confidence": 0.9, "suggested_date": "2026-05-12"},
                    "actions": [{"kind": "confirm_create_diet_record"}],
                }
            ],
        }


class _FakeMemoryService:
    embedding_client = object()


@pytest.fixture
async def ai_overrides():
    chat_service = _FakeChatService()

    async def _current_user() -> CurrentUser:
        return CurrentUser(id=uuid.uuid4(), email="user@example.com")

    async def _chat_service() -> _FakeChatService:
        return chat_service

    async def _diet_service():
        return object()

    async def _memory_service():
        return _FakeMemoryService()

    async def _rag_service():
        return object()

    def _chat_agent():
        return _FakeAgent()

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_chat_service] = _chat_service
    app.dependency_overrides[get_diet_service] = _diet_service
    app.dependency_overrides[get_memory_service] = _memory_service
    app.dependency_overrides[get_rag_service] = _rag_service
    app.dependency_overrides[get_chat_agent] = _chat_agent
    try:
        yield chat_service
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ai_chat_endpoint_saves_user_and_assistant_messages(client: AsyncClient, ai_overrides) -> None:
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"message": "午饭吃了一碗米饭", "context": {"referenced_date": "2026-05-12"}},
    )

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["session_id"] == "session-1"
    assert body["intent"] == "diet"
    assert body["messages"][0]["cards"][0]["type"] == "diet_parse"
    assert [item["role"] for item in ai_overrides.saved] == ["user", "assistant"]


@pytest.mark.asyncio
async def test_ai_chat_history_and_delete(client: AsyncClient, ai_overrides) -> None:
    await ai_overrides.save_message(session_id="session-1", role=ChatRole.user, content="hi")

    history = await client.get("/api/v1/ai/chat/history", params={"session_id": "session-1"})
    assert history.status_code == 200
    assert history.json()["pagination"]["total"] == 1

    deleted = await client.delete("/api/v1/ai/chat/sessions/session-1")
    assert deleted.status_code == 200
    assert deleted.json()["data"] is None

