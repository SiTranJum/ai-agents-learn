"""Daily suggestion prompt."""
# ruff: noqa: RUF001

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

SYSTEM = """你是健康管家 AI Agent 的建议专家。请生成 2-3 条日常健康建议。
要求：具体可执行、温和、结合用户目标，不做医疗诊断。"""


def build_daily_suggestion_messages(context: dict[str, Any]) -> list[Any]:
    return [SystemMessage(content=SYSTEM), HumanMessage(content=f"上下文：{context}\n请输出 SuggestionAgentOutput。")]


__all__ = ["build_daily_suggestion_messages"]

