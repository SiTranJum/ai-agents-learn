"""Prompt builder for memory quality scoring."""

from __future__ import annotations

from app.schemas.memory import ExtractedMemory


def build_memory_score_messages(memories: list[ExtractedMemory], existing_memories: list[str]) -> list[dict[str, str]]:
    """Build messages for scoring extracted memories."""
    return [
        {
            "role": "system",
            "content": (
                "你是健康管家 AI 的记忆质量评估器。"
                "请按 relevance, accuracy, actionability, uniqueness 四个维度打分, 并给出 overall_score。"
                "overall_score >= 80 表示可直接长期保存, 60-79 表示待观察, <60 表示应丢弃。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"待评分记忆: {[memory.model_dump(mode='json') for memory in memories]}\n"
                f"已有记忆摘要: {existing_memories}\n"
                "请为每条待评分记忆返回评分。"
            ),
        },
    ]


__all__ = ["build_memory_score_messages"]

