"""Memory subgraph tool wrappers."""

from __future__ import annotations

from app.schemas.memory import MemoryCreate, MemoryEntry
from app.services.memory_service import MemoryService


async def save_memory_tool(service: MemoryService, memory: MemoryCreate) -> MemoryEntry:
    """Persist one approved memory via MemoryService."""
    return await service.store_memory(memory)


async def list_existing_memories_tool(service: MemoryService, *, limit: int = 20) -> list[str]:
    """Return existing long-term memory contents for uniqueness scoring."""
    entries = await service.get_long_term_profile(limit=limit)
    return [entry.content for entry in entries]


__all__ = ["list_existing_memories_tool", "save_memory_tool"]

