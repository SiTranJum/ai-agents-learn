"""Phase 7 - AI chat API tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from app.dependencies import (
    get_body_service,
    get_chat_agent,
    get_chat_service,
    get_current_user,
    get_current_user_with_profile,
    get_diet_service,
    get_memory_service,
    get_plan_service,
    get_rag_service,
    get_user_service,
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
    """模拟 LangGraph compiled agent 的流式 + 状态接口。

    - astream_events：吐一个 wrap_response 结束事件，带 diet_parse 卡片；
    - aget_state：返回 next=() 表示未中断（本测试不验证 interrupt 暂停）。
    """

    async def astream_events(self, state, *, version=None, config=None):
        assert state["user_message"] == "午饭吃了一碗米饭"
        yield {
            "event": "on_chain_end",
            "name": "wrap_response",
            "data": {
                "output": {
                    "intent": "diet",
                    "ai_response": "我识别到 1 项食物。",
                    "response_cards": [
                        {
                            "type": "diet_parse",
                            "payload": {
                                "foods": [],
                                "meal_type": "lunch",
                                "confidence": 0.9,
                                "suggested_date": "2026-05-12",
                            },
                            "actions": [{"kind": "confirm_create_diet_record"}],
                        }
                    ],
                }
            },
            "metadata": {},
        }

    async def aget_state(self, config):
        class _Snap:
            next = ()
            tasks = ()

        return _Snap()


class _FakeMemoryService:
    embedding_client = object()


class _FakeUserService:
    async def get_interaction_mode(self) -> str:
        return "confirmation"


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

    async def _body_service():
        return object()

    async def _plan_service():
        return object()

    async def _user_service():
        return _FakeUserService()

    def _chat_agent():
        return _FakeAgent()

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_current_user_with_profile] = _current_user
    app.dependency_overrides[get_chat_service] = _chat_service
    app.dependency_overrides[get_diet_service] = _diet_service
    app.dependency_overrides[get_memory_service] = _memory_service
    app.dependency_overrides[get_rag_service] = _rag_service
    app.dependency_overrides[get_body_service] = _body_service
    app.dependency_overrides[get_plan_service] = _plan_service
    app.dependency_overrides[get_user_service] = _user_service
    app.dependency_overrides[get_chat_agent] = _chat_agent
    try:
        yield chat_service
    finally:
        app.dependency_overrides.clear()


def _parse_sse(text: str) -> list[dict[str, Any]]:
    """把 SSE 原始响应体解析成事件列表 [{event, data}, ...]。"""
    import json

    events: list[dict[str, Any]] = []
    event_name: str | None = None
    for line in text.splitlines():
        if line.startswith("event:"):
            event_name = line[len("event:"):].strip()
        elif line.startswith("data:"):
            raw = line[len("data:"):].strip()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = raw
            events.append({"event": event_name, "data": data})
            event_name = None
    return events


@pytest.mark.asyncio
async def test_ai_chat_endpoint_saves_user_and_assistant_messages(client: AsyncClient, ai_overrides) -> None:
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"message": "午饭吃了一碗米饭", "context": {"referenced_date": "2026-05-12"}},
    )

    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types = [e["event"] for e in events]
    assert "meta" in types
    assert "card" in types
    assert "done" in types
    card_ev = next(e for e in events if e["event"] == "card")
    assert card_ev["data"]["card"]["type"] == "diet_parse"
    # user 先存，assistant 流结束后存
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

