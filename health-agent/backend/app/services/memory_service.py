"""AI memory service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.db.models.memory import Memory, MemorySummary
from app.db.repositories.memory_repo import MemoryRepository
from app.integrations.embedding import EmbeddingClient
from app.schemas.memory import (
    MemoryCreate,
    MemoryEntry,
    MemoryRecallResult,
    MemoryStatus,
    MemorySummaryCreate,
    MemorySummaryEntry,
    MemoryType,
)

TYPE_WEIGHTS: dict[str, dict[MemoryType, float]] = {
    "record_diet": {
        MemoryType.food_preference: 1.0,
        MemoryType.portion_habit: 0.9,
        MemoryType.behavior_pattern: 0.7,
        MemoryType.suggestion_feedback: 0.6,
        MemoryType.health_goal: 0.7,
        MemoryType.allergy: 1.0,
        MemoryType.exercise_habit: 0.4,
    },
    "create_plan": {
        MemoryType.behavior_pattern: 1.0,
        MemoryType.suggestion_feedback: 0.9,
        MemoryType.food_preference: 0.8,
        MemoryType.portion_habit: 0.6,
        MemoryType.health_goal: 1.0,
        MemoryType.allergy: 0.7,
        MemoryType.exercise_habit: 0.9,
    },
    "general_advice": {
        MemoryType.food_preference: 1.0,
        MemoryType.behavior_pattern: 0.9,
        MemoryType.suggestion_feedback: 0.8,
        MemoryType.portion_habit: 0.7,
        MemoryType.health_goal: 0.9,
        MemoryType.allergy: 1.0,
        MemoryType.exercise_habit: 0.8,
    },
}

DEFAULT_TYPE_WEIGHT = 0.7


class MemoryService:
    """Memory CRUD, recall scoring, and profile synchronization.

    This service intentionally contains no LLM calls. LLM extraction, scoring, and
    consolidation belong to memory subgraph nodes.
    """

    def __init__(self, repo: MemoryRepository, embedding_client: EmbeddingClient) -> None:
        self.repo = repo
        self.embedding_client = embedding_client

    async def store_memory(self, data: MemoryCreate) -> MemoryEntry:
        memory = await self.repo.create_memory(data)
        await self.repo.prune_to_limit(max_active=1000)
        await self.repo.session.commit()
        return self._memory_to_entry(memory)

    async def recall_memories(
        self,
        query: str,
        *,
        intent: str | None = None,
        top_k: int = 3,
        candidate_k: int = 10,
    ) -> list[MemoryRecallResult]:
        normalized = query.strip()
        if not normalized:
            return []
        query_embedding = await self.embedding_client.embed(normalized)
        candidates = await self.repo.search_by_embedding(
            query_embedding,
            top_k=max(candidate_k, top_k),
            score_threshold=0.5,
        )
        scored: list[MemoryRecallResult] = []
        accessed: list[Memory] = []
        for memory, vector_similarity in candidates:
            if memory.quality_score < 60:
                continue
            time_decay = self.calculate_time_decay(memory.created_at, memory.access_count)
            memory_type = MemoryType(memory.memory_type)
            recall_score = self.calculate_recall_score(
                vector_similarity=vector_similarity,
                time_decay=time_decay,
                type_weight=self.type_weight(memory_type, intent),
                quality_score=memory.quality_score,
            )
            scored.append(
                self._memory_to_recall_result(
                    memory,
                    vector_similarity=vector_similarity,
                    recall_score=recall_score,
                    time_decay_factor=time_decay,
                )
            )
            accessed.append(memory)
        scored.sort(key=lambda item: item.recall_score, reverse=True)
        selected = scored[:top_k]
        selected_ids = {item.id for item in selected}
        await self.repo.mark_accessed([memory for memory in accessed if memory.id in selected_ids])
        await self.repo.session.commit()
        return selected

    async def get_long_term_profile(self, *, limit: int = 100) -> list[MemoryEntry]:
        memories = await self.repo.list_memories(memory_status=MemoryStatus.active, limit=limit)
        return [self._memory_to_entry(memory) for memory in memories]

    async def create_summary(self, data: MemorySummaryCreate) -> MemorySummaryEntry:
        summary = await self.repo.create_summary(data)
        await self.repo.session.commit()
        return self._summary_to_entry(summary)

    async def on_profile_updated(self, updated_data: dict[str, object]) -> MemoryEntry | None:
        facts = [f"{key}: {value}" for key, value in updated_data.items() if value not in (None, "", [])]
        if not facts:
            return None
        content = "用户健康档案更新: " + "; ".join(facts)[:450]
        embedding = await self.embedding_client.embed(content)
        return await self.store_memory(
            MemoryCreate(
                memory_type=MemoryType.profile,
                content=content,
                embedding=embedding,
                metadata={"source_fields": list(updated_data.keys())},
                quality_score=90,
                status=MemoryStatus.active,
                source="profile",
                trigger_type="profile_updated",
            )
        )

    async def archive_memories(self, memory_ids: list[uuid.UUID]) -> None:
        await self.repo.archive_memories(memory_ids)
        await self.repo.session.commit()

    @staticmethod
    def calculate_time_decay(created_at: datetime, access_count: int) -> float:
        now = datetime.now(UTC)
        normalized_created = created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC)
        days = (now - normalized_created).days
        if days <= 7:
            base = 1.0
        elif days <= 14:
            base = 0.9
        elif days <= 21:
            base = 0.8
        elif days <= 30:
            base = 0.7
        else:
            base = 0.5
        if access_count >= 10:
            base += 0.2
        elif access_count >= 5:
            base += 0.1
        return min(base, 1.2)

    @staticmethod
    def calculate_recall_score(
        *,
        vector_similarity: float,
        time_decay: float,
        type_weight: float,
        quality_score: int,
    ) -> float:
        return round(vector_similarity * time_decay * type_weight * (quality_score / 100), 4)

    @staticmethod
    def type_weight(memory_type: MemoryType, intent: str | None) -> float:
        if not intent:
            return DEFAULT_TYPE_WEIGHT
        return TYPE_WEIGHTS.get(intent, {}).get(memory_type, DEFAULT_TYPE_WEIGHT)

    def _memory_to_entry(self, memory: Memory) -> MemoryEntry:
        return MemoryEntry(
            id=memory.id,
            user_id=memory.user_id,
            memory_type=MemoryType(memory.memory_type),
            content=memory.content,
            metadata=memory.metadata_,
            quality_score=memory.quality_score,
            status=MemoryStatus(memory.status),
            source=memory.source,
            trigger_type=memory.trigger_type,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
            last_accessed_at=memory.last_accessed_at,
            access_count=memory.access_count,
            time_decay_factor=self.calculate_time_decay(memory.created_at, memory.access_count),
        )

    def _memory_to_recall_result(
        self,
        memory: Memory,
        *,
        vector_similarity: float,
        recall_score: float,
        time_decay_factor: float,
    ) -> MemoryRecallResult:
        base = self._memory_to_entry(memory).model_dump()
        base.update(
            {
                "vector_similarity": round(vector_similarity, 4),
                "recall_score": recall_score,
                "time_decay_factor": time_decay_factor,
            }
        )
        return MemoryRecallResult(**base)

    @staticmethod
    def _summary_to_entry(summary: MemorySummary) -> MemorySummaryEntry:
        return MemorySummaryEntry(
            id=summary.id,
            user_id=summary.user_id,
            period_start=summary.period_start,
            period_end=summary.period_end,
            summary_content=summary.summary_content,
            key_facts=summary.key_facts,
            source_memory_ids=summary.source_memory_ids,
            quality_score=summary.quality_score,
            status=MemoryStatus(summary.status),
            created_at=summary.created_at,
            updated_at=summary.updated_at,
        )


__all__ = ["DEFAULT_TYPE_WEIGHT", "TYPE_WEIGHTS", "MemoryService"]


