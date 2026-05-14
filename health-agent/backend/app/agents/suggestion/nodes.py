"""Suggestion agent nodes."""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

import logging
from datetime import date
from typing import Any, cast

from app.agents.base import get_chat_model
from app.agents.prompts.suggestion_daily import build_daily_suggestion_messages
from app.agents.prompts.suggestion_insight import build_insight_suggestion_messages
from app.agents.prompts.suggestion_meal import build_meal_suggestion_messages
from app.agents.suggestion.state import SuggestionState
from app.agents.suggestion.tools import recall_memories_tool, search_knowledge_tool
from app.schemas.suggestion import (
    SuggestionAgentOutput,
    SuggestionDraft,
    SuggestionPriority,
    SuggestionType,
)
from app.services.memory_service import MemoryService
from app.services.rag_service import RagService

logger = logging.getLogger(__name__)

_FORBIDDEN_MEDICAL_WORDS = ["诊断", "治疗", "处方", "停药", "断食"]


async def collect_data(state: SuggestionState) -> dict[str, Any]:
    """Collect lightweight structured context from injected services."""
    recent_data: dict[str, Any] = {"date": date.today().isoformat(), "suggestion_type": state.get("suggestion_type")}
    profile = state.get("profile")
    if profile is not None:
        recent_data["profile"] = {
            "current_weight": getattr(profile, "current_weight", None),
            "target_weight": getattr(profile, "target_weight", None),
            "daily_calorie_target": getattr(profile, "daily_calorie_target", None),
            "goal_type": getattr(profile, "goal_type", None),
        }
    return {"recent_data": recent_data}


async def recall_memories(state: SuggestionState) -> dict[str, Any]:
    service = state.get("memory_service")
    if service is None:
        return {"memories": []}
    try:
        query = f"健康建议 {state.get('suggestion_type')} {state.get('meal_type') or ''}"
        return {"memories": await recall_memories_tool(cast(MemoryService, service), query)}
    except Exception as exc:  # pragma: no cover
        logger.warning("suggestion memory recall failed: %s", exc)
        return {"memories": []}


async def search_knowledge(state: SuggestionState) -> dict[str, Any]:
    service = state.get("rag_service")
    if service is None:
        return {"knowledge": []}
    try:
        query = "健康饮食建议" if state.get("suggestion_type") != "insight" else "健康趋势洞察"
        return {"knowledge": await search_knowledge_tool(cast(RagService, service), query)}
    except Exception as exc:  # pragma: no cover
        logger.warning("suggestion knowledge search failed: %s", exc)
        return {"knowledge": []}


def _fallback_output(state: SuggestionState) -> SuggestionAgentOutput:
    kind = state.get("suggestion_type") or "daily"
    meal_type = state.get("meal_type") or "meal"
    if kind == "meal":
        return SuggestionAgentOutput(
            suggestions=[
                SuggestionDraft(
                    type=SuggestionType.diet_advice,
                    title=f"{meal_type} 餐食建议",
                    content="鸡蛋, 豆腐, 绿叶蔬菜",
                    basis="优先补充蛋白质和蔬菜。",
                    priority=SuggestionPriority.medium,
                    meal_type=meal_type,
                )
            ],
            reasoning="根据今日摄入和计划目标，优先补充蛋白质与蔬菜。",
        )
    if kind == "insight":
        return SuggestionAgentOutput(
            suggestions=[
                SuggestionDraft(
                    type=SuggestionType.trend_advice,
                    title="记录趋势洞察",
                    content="连续记录 7 天饮食和体重后，可以更准确判断热量目标是否合适。",
                    basis="基于数据完整性规则生成。",
                    priority=SuggestionPriority.low,
                    dimension="data_completeness",
                    data_support={"period": "last_30_days"},
                )
            ],
            reasoning="基于最近数据完整性生成。",
        )
    return SuggestionAgentOutput(
        suggestions=[
            SuggestionDraft(
                type=SuggestionType.proactive_insight,
                title="今日执行提醒",
                content="今天先完成一个小目标：饮水达到 2000ml，并记录每一餐。",
                basis="基于日常健康管理目标生成。",
                priority=SuggestionPriority.medium,
            )
        ],
        reasoning="基于今日健康管理目标生成。",
    )


def _messages_for_state(state: SuggestionState) -> list[Any]:
    context = {
        "recent_data": state.get("recent_data", {}),
        "memories": state.get("memories", []),
        "knowledge": state.get("knowledge", []),
        "meal_type": state.get("meal_type"),
    }
    kind = state.get("suggestion_type")
    if kind == "meal":
        return build_meal_suggestion_messages(context)
    if kind == "insight":
        return build_insight_suggestion_messages(context)
    return build_daily_suggestion_messages(context)


async def generate_suggestions(state: SuggestionState) -> dict[str, Any]:
    """Generate raw suggestions through DashScope-compatible ChatOpenAI.

    SDK/API 说明：``with_structured_output(SuggestionAgentOutput)`` 要求模型输出
    符合 Pydantic schema 的结构，便于后续节点确定性过滤。
    """
    try:
        model = cast(Any, get_chat_model(temperature=0.7, timeout=60)).with_structured_output(SuggestionAgentOutput)
        output = await model.ainvoke(_messages_for_state(state))
    except Exception as exc:  # pragma: no cover - local fallback without API key
        logger.info("suggestion fallback used: %s", exc)
        output = _fallback_output(state)
    return {"raw_suggestions": output.suggestions, "reasoning": output.reasoning}


async def deduplicate_filter(state: SuggestionState) -> dict[str, Any]:
    """Apply deterministic quality filters and text-level deduplication."""
    seen: set[str] = set()
    filtered: list[SuggestionDraft] = []
    for draft in state.get("raw_suggestions", []) or []:
        content = draft.content.strip()
        if not content or content in seen:
            continue
        if any(word in content for word in _FORBIDDEN_MEDICAL_WORDS):
            continue
        seen.add(content)
        filtered.append(draft)
    limit = 5 if state.get("suggestion_type") == "meal" else 3
    return {"filtered_suggestions": filtered[:limit]}


__all__ = ["collect_data", "deduplicate_filter", "generate_suggestions", "recall_memories", "search_knowledge"]


