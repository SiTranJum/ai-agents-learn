"""Top-level chat agent graph assembly."""
# ruff: noqa: RUF002

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, StateGraph

from app.agents.chat.nodes import (
    assemble_prompt,
    call_llm,
    identify_intent,
    recall_memories,
    route_after_intent,
    search_knowledge,
    trigger_memory_extract,
    wrap_response,
)
from app.agents.chat.state import ChatState
from app.agents.diet.subgraph import build_diet_subgraph


def build_chat_agent():
    """Build the only externally exposed AI graph.

    ``StateGraph(ChatState)`` 类似把多个可测试节点串成一个工作流：
    - 节点函数只返回要更新的 state 字段；
    - 条件边根据 ``intent`` 决定进入 diet subgraph 还是 general chat；
    - 编译后的 graph 可被 FastAPI 依赖以单例方式复用。
    """
    graph = StateGraph(cast(Any, ChatState))
    graph.add_node("identify_intent", cast(Any, identify_intent))
    graph.add_node("diet", build_diet_subgraph())
    graph.add_node("recall_memories", cast(Any, recall_memories))
    graph.add_node("search_knowledge", cast(Any, search_knowledge))
    graph.add_node("assemble_prompt", cast(Any, assemble_prompt))
    graph.add_node("call_llm", cast(Any, call_llm))
    graph.add_node("trigger_memory_extract", cast(Any, trigger_memory_extract))
    graph.add_node("wrap_response", cast(Any, wrap_response))

    graph.set_entry_point("identify_intent")
    graph.add_conditional_edges(
        "identify_intent",
        route_after_intent,
        {"diet": "diet", "general": "recall_memories"},
    )
    graph.add_edge("diet", "wrap_response")
    graph.add_edge("recall_memories", "search_knowledge")
    graph.add_edge("search_knowledge", "assemble_prompt")
    graph.add_edge("assemble_prompt", "call_llm")
    graph.add_edge("call_llm", "trigger_memory_extract")
    graph.add_edge("trigger_memory_extract", "wrap_response")
    graph.add_edge("wrap_response", END)
    return graph.compile()


__all__ = ["build_chat_agent"]


