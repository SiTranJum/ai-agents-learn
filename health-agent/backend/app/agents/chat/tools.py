"""Tool wrappers used by the top-level chat agent."""

from __future__ import annotations

from typing import Any

from app.services.memory_service import MemoryService
from app.services.rag_service import RagService


async def recall_memories_tool(
    service: MemoryService,
    *,
    query: str,
    intent: str | None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Recall user memories through MemoryService and return JSON-safe dicts."""
    memories = await service.recall_memories(query, intent=intent, top_k=top_k)
    return [memory.model_dump(mode="json") for memory in memories]


async def get_long_term_profile_tool(
    service: MemoryService,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return long-term profile memory snippets for prompt personalization."""
    memories = await service.get_long_term_profile(limit=limit)
    return [memory.model_dump(mode="json") for memory in memories]


async def search_knowledge_tool(
    service: RagService,
    *,
    query: str,
    category: str | None = None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Search the health knowledge base through RagService."""
    results = await service.search_knowledge(query, category=category, top_k=top_k)
    return [result.model_dump(mode="json") for result in results]


__all__ = ["get_long_term_profile_tool", "recall_memories_tool", "search_knowledge_tool"]

