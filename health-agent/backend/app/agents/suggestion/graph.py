"""Suggestion agent graph assembly."""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, StateGraph

from app.agents.suggestion.nodes import (
    collect_data,
    deduplicate_filter,
    generate_suggestions,
    recall_memories,
    search_knowledge,
)
from app.agents.suggestion.state import SuggestionState


def build_suggestion_agent():
    """Build suggestion generation graph."""
    graph = StateGraph(cast(Any, SuggestionState))
    graph.add_node("collect_data", cast(Any, collect_data))
    graph.add_node("recall_memories", cast(Any, recall_memories))
    graph.add_node("search_knowledge", cast(Any, search_knowledge))
    graph.add_node("generate_suggestions", cast(Any, generate_suggestions))
    graph.add_node("deduplicate_filter", cast(Any, deduplicate_filter))
    graph.set_entry_point("collect_data")
    graph.add_edge("collect_data", "recall_memories")
    graph.add_edge("recall_memories", "search_knowledge")
    graph.add_edge("search_knowledge", "generate_suggestions")
    graph.add_edge("generate_suggestions", "deduplicate_filter")
    graph.add_edge("deduplicate_filter", END)
    return graph.compile()


__all__ = ["build_suggestion_agent"]

