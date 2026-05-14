"""Tool wrappers for suggestion agent."""

from __future__ import annotations

from typing import Any

from app.services.memory_service import MemoryService
from app.services.rag_service import RagService


async def recall_memories_tool(service: MemoryService, query: str, top_k: int = 3) -> list[dict[str, Any]]:
    memories = await service.recall_memories(query, intent="suggestion", top_k=top_k)
    return [memory.model_dump(mode="json") for memory in memories]


async def search_knowledge_tool(service: RagService, query: str, top_k: int = 3) -> list[dict[str, Any]]:
    results = await service.search_knowledge(query, category=None, top_k=top_k)
    return [result.model_dump(mode="json") for result in results]


__all__ = ["recall_memories_tool", "search_knowledge_tool"]

