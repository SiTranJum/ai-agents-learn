"""Phase 6 - memory subgraph tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from app.agents.memory import build_consolidate_subgraph, build_memory_agent
from app.schemas.memory import (
    ConsolidatedMemorySummary,
    ExtractedMemory,
    MemoryEntry,
    MemoryExtractionResult,
    MemoryQualityScore,
    MemoryScoreResult,
    MemoryStatus,
    MemorySummaryEntry,
    MemoryType,
)


class _FakeStructuredModel:
    def __init__(self, schema: type[Any]) -> None:
        self.schema = schema

    async def ainvoke(self, messages):
        if self.schema is MemoryExtractionResult:
            return MemoryExtractionResult(
                memories=[
                    ExtractedMemory(
                        memory_type=MemoryType.food_preference,
                        content="用户喜欢鸡胸肉",
                        metadata={"food": "鸡胸肉"},
                        source="diet_record",
                    )
                ]
            )
        if self.schema is MemoryScoreResult:
            return MemoryScoreResult(
                scored_memories=[
                    MemoryQualityScore(
                        memory_type=MemoryType.food_preference,
                        content="用户喜欢鸡胸肉",
                        metadata={"food": "鸡胸肉"},
                        source="diet_record",
                        relevance=90,
                        accuracy=90,
                        actionability=85,
                        uniqueness=90,
                        overall_score=89,
                        reason="clear repeated diet preference",
                    )
                ]
            )
        if self.schema is ConsolidatedMemorySummary:
            return ConsolidatedMemorySummary(
                summary_content="用户稳定偏好高蛋白食物",
                key_facts=["喜欢鸡胸肉"],
                quality_score=88,
            )
        raise AssertionError(f"unexpected schema: {self.schema}")


class _FakeChatModel:
    def with_structured_output(self, schema: type[Any]) -> _FakeStructuredModel:
        return _FakeStructuredModel(schema)


class _FakeEmbeddingClient:
    async def embed(self, text: str) -> list[float]:
        assert text == "用户喜欢鸡胸肉"
        return [0.1, 0.2, 0.3]


class _FakeMemoryService:
    def __init__(self) -> None:
        self.saved = []
        self.archived = []

    async def get_long_term_profile(self, *, limit: int = 20):
        return []

    async def store_memory(self, memory):
        self.saved.append(memory)
        now = datetime.now(UTC)
        return MemoryEntry(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            memory_type=memory.memory_type,
            content=memory.content,
            metadata=memory.metadata,
            quality_score=memory.quality_score,
            status=memory.status,
            source=memory.source,
            trigger_type=memory.trigger_type,
            created_at=now,
            updated_at=now,
            access_count=0,
        )

    async def create_summary(self, summary):
        now = datetime.now(UTC)
        return MemorySummaryEntry(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            period_start=summary.period_start,
            period_end=summary.period_end,
            summary_content=summary.summary_content,
            key_facts=summary.key_facts,
            source_memory_ids=summary.source_memory_ids,
            quality_score=summary.quality_score,
            status=summary.status,
            created_at=now,
            updated_at=now,
        )

    async def archive_memories(self, memory_ids):
        self.archived.extend(memory_ids)


@pytest.mark.asyncio
async def test_memory_agent_extracts_scores_embeds_and_stores(monkeypatch) -> None:
    monkeypatch.setattr("app.agents.memory.nodes.get_chat_model", lambda **kwargs: _FakeChatModel())
    service = _FakeMemoryService()
    graph = build_memory_agent()

    state = await graph.ainvoke(
        {
            "user_id": str(uuid.uuid4()),
            "trigger_type": "diet_record",
            "context_data": {"foods": [{"name": "鸡胸肉"}]},
            "memory_service": service,
            "embedding_client": _FakeEmbeddingClient(),
        }
    )

    assert len(state["stored"]) == 1
    assert state["stored"][0].content == "用户喜欢鸡胸肉"
    assert service.saved[0].status == MemoryStatus.active
    assert service.saved[0].embedding == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_memory_agent_handles_empty_extraction(monkeypatch) -> None:
    class EmptyStructuredModel(_FakeStructuredModel):
        async def ainvoke(self, messages):
            if self.schema is MemoryExtractionResult:
                return MemoryExtractionResult(memories=[])
            return MemoryScoreResult(scored_memories=[])

    class EmptyChatModel:
        def with_structured_output(self, schema: type[Any]) -> EmptyStructuredModel:
            return EmptyStructuredModel(schema)

    monkeypatch.setattr("app.agents.memory.nodes.get_chat_model", lambda **kwargs: EmptyChatModel())
    state = await build_memory_agent().ainvoke(
        {
            "user_id": str(uuid.uuid4()),
            "trigger_type": "chat",
            "context_data": {"message": "你好"},
            "memory_service": _FakeMemoryService(),
            "embedding_client": _FakeEmbeddingClient(),
        }
    )

    assert state["stored"] == []


@pytest.mark.asyncio
async def test_consolidate_subgraph_summarizes_and_archives(monkeypatch) -> None:
    monkeypatch.setattr("app.agents.memory.nodes.get_chat_model", lambda **kwargs: _FakeChatModel())
    service = _FakeMemoryService()
    now = datetime.now(UTC)
    memory = MemoryEntry(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        memory_type=MemoryType.food_preference,
        content="用户喜欢鸡胸肉",
        metadata={},
        quality_score=90,
        status=MemoryStatus.active,
        created_at=now,
        updated_at=now,
    )

    state = await build_consolidate_subgraph().ainvoke(
        {"consolidate_memories": [memory], "memory_service": service}
    )

    assert state["summary"].summary_content == "用户稳定偏好高蛋白食物"
    assert service.archived == [memory.id]


