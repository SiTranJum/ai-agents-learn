"""diet_agent LangGraph 组装。"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.diet.nodes import (
    enrich_nutrition,
    infer_meal_type,
    parse_photo_mock,
    parse_text,
    route_input,
    save_or_end,
    save_record,
    standardize_units,
    trigger_memory,
)
from app.agents.diet.state import DietState


def build_diet_agent():
    """构建饮食解析/创建 Agent。"""
    graph = StateGraph(DietState)
    graph.add_node("parse_text", parse_text)
    graph.add_node("parse_photo_mock", parse_photo_mock)
    graph.add_node("standardize_units", standardize_units)
    graph.add_node("enrich_nutrition", enrich_nutrition)
    graph.add_node("infer_meal_type", infer_meal_type)
    graph.add_node("save_record", save_record)
    graph.add_node("trigger_memory", trigger_memory)

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
    graph.add_conditional_edges(
        "infer_meal_type",
        save_or_end,
        {"save_record": "save_record", "__end__": END},
    )
    graph.add_edge("save_record", "trigger_memory")
    graph.add_edge("trigger_memory", END)
    return graph.compile()


__all__ = ["build_diet_agent"]
