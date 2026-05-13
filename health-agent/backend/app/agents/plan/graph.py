"""Plan agent graph assembly."""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, StateGraph

from app.agents.plan.nodes import (
    analyze_deviation,
    analyze_status,
    confirm_goal,
    draft_plan,
    persist_plan,
    safety_validate,
    suggest_modification,
)
from app.agents.plan.state import PlanState


def build_plan_agent():
    """Build plan creation graph."""
    graph = StateGraph(cast(Any, PlanState))
    graph.add_node("confirm_goal", cast(Any, confirm_goal))
    graph.add_node("analyze_status", cast(Any, analyze_status))
    graph.add_node("draft_plan", cast(Any, draft_plan))
    graph.add_node("safety_validate", cast(Any, safety_validate))
    graph.add_node("persist_plan", cast(Any, persist_plan))
    graph.set_entry_point("confirm_goal")
    graph.add_edge("confirm_goal", "analyze_status")
    graph.add_edge("analyze_status", "draft_plan")
    graph.add_edge("draft_plan", "safety_validate")
    graph.add_edge("safety_validate", "persist_plan")
    graph.add_edge("persist_plan", END)
    return graph.compile()


def build_modification_subgraph():
    """Build a minimal plan modification suggestion subgraph."""
    graph = StateGraph(cast(Any, PlanState))
    graph.add_node("analyze_deviation", cast(Any, analyze_deviation))
    graph.add_node("suggest_modification", cast(Any, suggest_modification))
    graph.set_entry_point("analyze_deviation")
    graph.add_edge("analyze_deviation", "suggest_modification")
    graph.add_edge("suggest_modification", END)
    return graph.compile()


__all__ = ["build_modification_subgraph", "build_plan_agent"]


