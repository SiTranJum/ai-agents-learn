"""Compatibility export for memory subgraph."""

from __future__ import annotations

from app.agents.memory.subgraph import build_consolidate_subgraph, build_memory_subgraph


def build_memory_agent():
    """Build memory subgraph using the Phase 6 plan name."""
    return build_memory_subgraph()


__all__ = ["build_consolidate_subgraph", "build_memory_agent", "build_memory_subgraph"]


