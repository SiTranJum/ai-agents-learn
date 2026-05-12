"""Memory extraction state."""

from __future__ import annotations

from typing import Any, TypedDict

from app.schemas.memory import MemoryCreate, MemoryEntry, MemoryQualityScore, MemorySummaryEntry


class MemoryExtractionState(TypedDict, total=False):
    """State used by memory subgraph."""

    user_id: str
    trigger_type: str
    context_data: dict[str, Any]
    existing_memories: list[str]
    extracted: list[Any]
    scored: list[MemoryQualityScore]
    approved: list[MemoryCreate]
    stored: list[MemoryEntry]
    consolidate_memories: list[MemoryEntry]
    summary: MemorySummaryEntry
    memory_service: Any
    embedding_client: Any
    error: str | None


__all__ = ["MemoryExtractionState"]


