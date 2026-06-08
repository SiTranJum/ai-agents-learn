"""Plan chat subgraph for the global AI graph."""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, StateGraph

from app.agents.plan.conversation import run_plan_conversation
from app.schemas.plan import PlanConversationMessage


async def handle_plan_turn(state: dict[str, Any]) -> dict[str, Any]:
    messages = [
        PlanConversationMessage(role=item.get("role", "user"), content=item.get("content", ""))
        for item in state.get("chat_history", [])
        if item.get("content")
    ]
    result = await run_plan_conversation(
        user_message=state.get("user_message"),
        messages=messages,
        profile=state.get("profile"),
        plan_service=state.get("plan_service"),
        memory_service=state.get("memory_service"),
        request_type=state.get("request_type", "text"),
        action_id=state.get("card_action_id"),
        action_payload=state.get("card_action_payload"),
    )
    return result


def build_plan_subgraph():
    graph = StateGraph(cast(Any, dict[str, Any]))
    graph.add_node("handle_plan_turn", cast(Any, handle_plan_turn))
    graph.set_entry_point("handle_plan_turn")
    graph.add_edge("handle_plan_turn", END)
    return graph.compile()


__all__ = ["build_plan_subgraph", "handle_plan_turn"]
