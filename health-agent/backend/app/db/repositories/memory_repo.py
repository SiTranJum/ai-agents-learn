"""AI memory repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.memory import Memory, MemorySummary
from app.integrations.vector import PgVectorClient
from app.schemas.memory import MemoryCreate, MemoryStatus, MemorySummaryCreate


class MemoryRepository:
    """User-scoped memory repository."""

    def __init__(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        self.session = session
        self.user_id = user_id
        self.vector_client = PgVectorClient(session)

    def _active_stmt(self) -> Select[tuple[Memory]]:
        return select(Memory).where(
            Memory.user_id == self.user_id,
            Memory.status.in_([MemoryStatus.active.value, MemoryStatus.pending.value]),
        )

    async def create_memory(self, data: MemoryCreate) -> Memory:
        memory = Memory(
            user_id=self.user_id,
            memory_type=data.memory_type.value,
            content=data.content,
            embedding=data.embedding,
            metadata_=data.metadata,
            quality_score=data.quality_score,
            status=data.status.value,
            source=data.source,
            trigger_type=data.trigger_type,
        )
        self.session.add(memory)
        await self.session.flush()
        return memory

    async def get_memory(self, memory_id: uuid.UUID) -> Memory | None:
        stmt = select(Memory).where(Memory.user_id == self.user_id, Memory.id == memory_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_memories(
        self,
        *,
        memory_status: MemoryStatus | None = None,
        limit: int = 100,
    ) -> list[Memory]:
        stmt = select(Memory).where(Memory.user_id == self.user_id)
        if memory_status is not None:
            stmt = stmt.where(Memory.status == memory_status.value)
        stmt = stmt.order_by(Memory.created_at.desc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def count_active_memories(self) -> int:
        stmt = select(func.count()).select_from(Memory).where(
            Memory.user_id == self.user_id,
            Memory.status.in_([MemoryStatus.active.value, MemoryStatus.pending.value]),
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def search_by_embedding(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 10,
        score_threshold: float = 0.5,
    ) -> list[tuple[Memory, float]]:
        results = await self.vector_client.similarity_search(
            Memory,
            query_embedding,
            top_k=top_k,
            filters={"user_id": self.user_id, "status": [MemoryStatus.active.value, MemoryStatus.pending.value]},
            score_threshold=score_threshold,
        )
        return [(result.item, result.score) for result in results]

    async def mark_accessed(self, memories: list[Memory]) -> None:
        now = datetime.now(UTC)
        for memory in memories:
            memory.last_accessed_at = now
            memory.access_count += 1
        await self.session.flush()

    async def archive_memories(self, memory_ids: list[uuid.UUID]) -> None:
        if not memory_ids:
            return
        stmt = select(Memory).where(Memory.user_id == self.user_id, Memory.id.in_(memory_ids))
        memories = list((await self.session.execute(stmt)).scalars().all())
        for memory in memories:
            memory.status = MemoryStatus.archived.value
        await self.session.flush()

    async def prune_to_limit(self, max_active: int = 1000) -> None:
        total = await self.count_active_memories()
        overflow = total - max_active
        if overflow <= 0:
            return
        stmt = (
            self._active_stmt()
            .order_by(Memory.quality_score.asc(), Memory.created_at.asc())
            .limit(overflow)
        )
        memories = list((await self.session.execute(stmt)).scalars().all())
        for memory in memories:
            memory.status = MemoryStatus.archived.value
        await self.session.flush()

    async def create_summary(self, data: MemorySummaryCreate) -> MemorySummary:
        summary = MemorySummary(
            user_id=self.user_id,
            period_start=data.period_start,
            period_end=data.period_end,
            summary_content=data.summary_content,
            key_facts=data.key_facts,
            source_memory_ids=data.source_memory_ids,
            quality_score=data.quality_score,
            status=data.status.value,
        )
        self.session.add(summary)
        await self.session.flush()
        return summary

    async def list_summaries(
        self,
        *,
        status: MemoryStatus = MemoryStatus.active,
        limit: int = 20,
    ) -> list[MemorySummary]:
        stmt = (
            select(MemorySummary)
            .where(MemorySummary.user_id == self.user_id, MemorySummary.status == status.value)
            .order_by(MemorySummary.period_end.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())


__all__ = ["MemoryRepository"]



