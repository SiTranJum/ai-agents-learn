"""Prompt builder for memory extraction."""

from __future__ import annotations

from typing import Any


def build_memory_extract_messages(trigger_type: str, context_data: dict[str, Any]) -> list[dict[str, str]]:
    """Build messages for extracting durable health-management memories."""
    return [
        {
            "role": "system",
            "content": (
                "你是健康管家 AI 的记忆提取器。只提取对长期个性化健康管理有价值的事实。"
                "不要提取一次性的闲聊、无依据猜测或隐私无关内容。"
                "每条记忆必须简洁、可验证、可用于之后的建议或对话。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"触发类型: {trigger_type}\n"
                f"上下文数据: {context_data}\n\n"
                "请提取 0-10 条记忆。记忆类型只能使用 schema 中的枚举值。"
            ),
        },
    ]


__all__ = ["build_memory_extract_messages"]

