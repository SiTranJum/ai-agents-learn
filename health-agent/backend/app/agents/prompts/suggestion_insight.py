"""Insight suggestion prompt."""
# ruff: noqa: RUF001

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

SYSTEM = """你是健康管家 AI Agent 的健康洞察专家。请生成最多 3 条趋势洞察。
每条洞察必须包含发现、建议和 data_support，不做医疗诊断。"""


def build_insight_suggestion_messages(context: dict[str, Any]) -> list[Any]:
    return [SystemMessage(content=SYSTEM), HumanMessage(content=f"上下文：{context}\n请输出 SuggestionAgentOutput。")]


__all__ = ["build_insight_suggestion_messages"]

