"""Phase 9 - suggestion_agent tests."""

from __future__ import annotations

import uuid

import pytest

from app.agents.suggestion.graph import build_suggestion_agent
from app.schemas.suggestion import SuggestionAgentOutput, SuggestionDraft, SuggestionType


@pytest.mark.asyncio
async def test_suggestion_agent_daily_fallback(monkeypatch) -> None:
    class _BrokenModel:
        def with_structured_output(self, schema):
            raise RuntimeError("no llm")

    monkeypatch.setattr("app.agents.suggestion.nodes.get_chat_model", lambda *args, **kwargs: _BrokenModel())
    graph = build_suggestion_agent()

    state = await graph.ainvoke({"user_id": str(uuid.uuid4()), "suggestion_type": "daily"})

    assert state["filtered_suggestions"]
    assert state["filtered_suggestions"][0].type == SuggestionType.proactive_insight


@pytest.mark.asyncio
async def test_suggestion_agent_filters_medical_words(monkeypatch) -> None:
    class _FakeModel:
        def with_structured_output(self, schema):
            class _Structured:
                async def ainvoke(self, messages):
                    _ = messages
                    return SuggestionAgentOutput(
                        suggestions=[
                            SuggestionDraft(title="危险", content="建议停药治疗", type=SuggestionType.proactive_insight),
                            SuggestionDraft(title="可执行", content="晚餐增加一份蔬菜", type=SuggestionType.proactive_insight),
                        ]
                    )

            return _Structured()

    monkeypatch.setattr("app.agents.suggestion.nodes.get_chat_model", lambda *args, **kwargs: _FakeModel())
    graph = build_suggestion_agent()

    state = await graph.ainvoke({"suggestion_type": "daily"})

    assert [item.title for item in state["filtered_suggestions"]] == ["可执行"]

