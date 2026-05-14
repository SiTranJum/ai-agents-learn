"""Meal suggestion prompt."""
# ruff: noqa: RUF001

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

SYSTEM = """你是健康管家 AI Agent 的餐食建议专家。请给出最多 5 个具体食物推荐。
要求：尊重忌口和过敏信息，不做极端饮食建议。"""


def build_meal_suggestion_messages(context: dict[str, Any]) -> list[Any]:
    return [SystemMessage(content=SYSTEM), HumanMessage(content=f"上下文：{context}\n请输出 SuggestionAgentOutput。")]


__all__ = ["build_meal_suggestion_messages"]

