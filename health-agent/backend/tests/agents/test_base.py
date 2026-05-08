"""Phase 2 - Agent 基础设施测试。"""

from __future__ import annotations

from app.agents import BaseAgentState, get_chat_model


def test_base_agent_state_accepts_common_fields() -> None:
    state: BaseAgentState = {
        "user_id": "user-1",
        "request_id": "req-1",
        "error": None,
    }

    assert state["user_id"] == "user-1"
    assert state["request_id"] == "req-1"
    assert state["error"] is None


def test_get_chat_model_uses_dashscope_settings(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("app.agents.base.ChatOpenAI", FakeChatOpenAI)

    model = get_chat_model(temperature=0.7, timeout=90, max_retries=5)

    assert isinstance(model, FakeChatOpenAI)
    assert captured["model"] == "qwen-plus"
    assert captured["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert captured["temperature"] == 0.7
    assert captured["timeout"] == 90
    assert captured["max_retries"] == 5

