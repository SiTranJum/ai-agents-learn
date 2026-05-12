"""Prompt builder for memory consolidation."""

from __future__ import annotations

from app.schemas.memory import MemoryEntry


def build_consolidate_messages(memories: list[MemoryEntry]) -> list[dict[str, str]]:
    """Build messages for summarizing similar memories into one medium-term summary."""
    return [
        {
            "role": "system",
            "content": "你是健康管家 AI 的记忆合并器。请把相似记忆压缩成准确、简洁、可用于个性化建议的摘要。",
        },
        {
            "role": "user",
            "content": f"需要合并的记忆: {[memory.model_dump(mode='json') for memory in memories]}",
        },
    ]


__all__ = ["build_consolidate_messages"]

