"""Phase 6 - MemoryService unit tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.db.models.memory import Memory
from app.schemas.memory import MemoryCreate, MemoryStatus, MemoryType
from app.services.memory_service import MemoryService


class _FakeSession:
    async def commit(self) -> None:
        return None


class _FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return [0.1, 0.2, 0.3]


class _FakeRepo:
    def __init__(self) -> None:
        self.session = _FakeSession()
        self.memories: list[Memory] = []
        self.accessed: list[Memory] = []

    async def create_memory(self, data: MemoryCreate) -> Memory:
        memory = _memory(
            memory_type=data.memory_type,
            content=data.content,
            quality_score=data.quality_score,
            status=data.status,
        )
        memory.embedding = data.embedding
        memory.metadata_ = data.metadata
        self.memories.append(memory)
        return memory

    async def prune_to_limit(self, max_active: int = 1000) -> None:
        return None

    async def search_by_embedding(self, query_embedding, *, top_k, score_threshold):
        return [(memory, 0.9 - index * 0.1) for index, memory in enumerate(self.memories[:top_k])]

    async def mark_accessed(self, memories: list[Memory]) -> None:
        self.accessed.extend(memories)
        for memory in memories:
            memory.access_count += 1

    async def list_memories(self, *, memory_status: MemoryStatus | None = None, limit: int = 100):
        result = self.memories
        if memory_status is not None:
            result = [memory for memory in result if memory.status == memory_status.value]
        return result[:limit]


def _memory(
    *,
    memory_type: MemoryType = MemoryType.food_preference,
    content: str = "用户喜欢鸡胸肉",
    quality_score: int = 90,
    status: MemoryStatus = MemoryStatus.active,
    days_old: int = 0,
    access_count: int = 0,
) -> Memory:
    now = datetime.now(UTC) - timedelta(days=days_old)
    return Memory(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        memory_type=memory_type.value,
        content=content,
        embedding=[0.1, 0.2, 0.3],
        metadata_={},
        quality_score=quality_score,
        status=status.value,
        access_count=access_count,
        created_at=now,
        updated_at=now,
    )


def test_time_decay_uses_age_and_access_bonus() -> None:
    now = datetime.now(UTC)

    assert MemoryService.calculate_time_decay(now - timedelta(days=3), 0) == 1.0
    assert MemoryService.calculate_time_decay(now - timedelta(days=10), 0) == 0.9
    assert MemoryService.calculate_time_decay(now - timedelta(days=40), 10) == 0.7


def test_recall_score_multiplies_all_factors() -> None:
    assert MemoryService.calculate_recall_score(
        vector_similarity=0.9,
        time_decay=1.0,
        type_weight=0.8,
        quality_score=90,
    ) == 0.648


@pytest.mark.asyncio
async def test_store_memory_persists_entry() -> None:
    repo = _FakeRepo()
    service = MemoryService(repo=repo, embedding_client=_FakeEmbeddingClient())  # type: ignore[arg-type]

    entry = await service.store_memory(
        MemoryCreate(
            memory_type=MemoryType.food_preference,
            content="用户喜欢鸡胸肉",
            embedding=[0.1, 0.2, 0.3],
            quality_score=88,
        )
    )

    assert entry.content == "用户喜欢鸡胸肉"
    assert entry.quality_score == 88
    assert len(repo.memories) == 1


@pytest.mark.asyncio
async def test_recall_memories_filters_low_quality_and_marks_accessed() -> None:
    repo = _FakeRepo()
    good = _memory(memory_type=MemoryType.food_preference, quality_score=90)
    low = _memory(memory_type=MemoryType.health_goal, quality_score=50)
    repo.memories = [good, low]
    embedding = _FakeEmbeddingClient()
    service = MemoryService(repo=repo, embedding_client=embedding)  # type: ignore[arg-type]

    results = await service.recall_memories("鸡胸肉", intent="record_diet", top_k=3)

    assert embedding.calls == ["鸡胸肉"]
    assert [item.id for item in results] == [good.id]
    assert repo.accessed == [good]


@pytest.mark.asyncio
async def test_on_profile_updated_creates_profile_memory() -> None:
    repo = _FakeRepo()
    embedding = _FakeEmbeddingClient()
    service = MemoryService(repo=repo, embedding_client=embedding)  # type: ignore[arg-type]

    entry = await service.on_profile_updated({"target_weight": 60, "nickname": "小明"})

    assert entry is not None
    assert entry.memory_type == MemoryType.profile
    assert "target_weight" in entry.content
    assert embedding.calls == [entry.content]


