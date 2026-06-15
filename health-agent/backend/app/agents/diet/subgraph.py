"""diet subgraph 装配。

**这不是独立 Agent**。本 subgraph 作为全局 ``chat_graph`` 的一个节点（见
``app/agents/chat/graph.py``，Phase 6 实现），由路由节点在 ``intent == "diet"``
时派发到此处。

对外暴露 :func:`build_diet_subgraph`，返回 compiled graph；调用方是
全局 ``chat_graph`` 的 ``add_node("diet", compiled_diet_subgraph)``。

设计原则：
- **状态签名**：节点读写的是共享 :class:`ChatState`，字段名全部带 ``diet_`` 前缀。
- **无独立入口**：不提供 ``ainvoke``/HTTP 暴露；只接受经由全局 Graph 的派发。
- **工具访问 Service**：节点内的 ``diet_service`` 通过 LangGraph 的 config 传入
  （Phase 6 集成），当前测试场景仍允许从 state 注入以便单元测试。
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, StateGraph

from app.agents.chat.state import ChatState
from app.agents.diet.nodes import (
    confirm_or_clarify,
    confirm_save,
    enrich_nutrition,
    infer_meal_type,
    narrate_learning,
    parse_photo_mock,
    parse_text,
    route_input,
    save_record,
    standardize_units,
    trigger_memory,
)


def build_diet_subgraph():
    """构建 diet subgraph。

    返回值是 compiled ``StateGraph``，供 ``chat_graph`` 作为子节点挂载。

    交互流：解析 → 标准化 → 营养 → 推断餐次 → confirm_or_clarify
    （可能 interrupt 暂停问餐次）→
      ├ efficiency: → save_record
      ├ confirmation: → confirm_save（interrupt 出确认卡）→ save_record
      └ learning: → narrate_learning（流式讲解）→ confirm_save → save_record
    """
    graph = StateGraph(cast(Any, ChatState))
    graph.add_node("parse_text", cast(Any, parse_text))
    graph.add_node("parse_photo_mock", cast(Any, parse_photo_mock))
    graph.add_node("standardize_units", cast(Any, standardize_units))
    graph.add_node("enrich_nutrition", cast(Any, enrich_nutrition))
    graph.add_node("infer_meal_type", cast(Any, infer_meal_type))
    graph.add_node("confirm_or_clarify", cast(Any, confirm_or_clarify))
    graph.add_node("narrate_learning", cast(Any, narrate_learning))
    graph.add_node("confirm_save", cast(Any, confirm_save))
    graph.add_node("save_record", cast(Any, save_record))
    graph.add_node("trigger_memory", cast(Any, trigger_memory))

    graph.set_conditional_entry_point(
        route_input,
        {
            "parse_text": "parse_text",
            "parse_photo_mock": "parse_photo_mock",
            "standardize_units": "standardize_units",
        },
    )
    graph.add_edge("parse_text", "standardize_units")
    graph.add_edge("parse_photo_mock", "standardize_units")
    graph.add_edge("standardize_units", "enrich_nutrition")
    graph.add_edge("enrich_nutrition", "infer_meal_type")
    graph.add_edge("infer_meal_type", "confirm_or_clarify")
    # confirm_or_clarify 返回 Command(goto="save_record" | "narrate_learning" |
    # "confirm_save" | "__end__")，目标节点都需在图中可达：上面均已声明。
    graph.add_edge("narrate_learning", "confirm_save")
    # confirm_save 通过 Command 走 save_record / __end__。
    graph.add_edge("save_record", "trigger_memory")
    graph.add_edge("trigger_memory", END)
    return graph.compile()


__all__ = ["build_diet_subgraph"]
