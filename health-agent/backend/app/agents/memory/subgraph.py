"""Memory subgraph assembly."""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, StateGraph

from app.agents.memory.nodes import consolidate, embed_and_store, extract, filter_memories, score
from app.agents.memory.state import MemoryExtractionState


def build_memory_subgraph():
    """Build the memory extraction subgraph."""
    graph = StateGraph(cast(Any, MemoryExtractionState))
    graph.add_node("extract", cast(Any, extract))
    graph.add_node("score", cast(Any, score))
    graph.add_node("filter", cast(Any, filter_memories))
    graph.add_node("embed_and_store", cast(Any, embed_and_store))

    graph.set_entry_point("extract")
    graph.add_edge("extract", "score")
    graph.add_edge("score", "filter")
    graph.add_edge("filter", "embed_and_store")
    graph.add_edge("embed_and_store", END)
    return graph.compile()


def build_consolidate_subgraph():
    """Build the memory consolidation subgraph."""
    graph = StateGraph(cast(Any, MemoryExtractionState))
    graph.add_node("consolidate", cast(Any, consolidate))
    graph.set_entry_point("consolidate")
    graph.add_edge("consolidate", END)
    return graph.compile()


__all__ = ["build_consolidate_subgraph", "build_memory_subgraph"]


