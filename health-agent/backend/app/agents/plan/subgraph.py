"""Plan chat subgraph for the global AI graph."""

from __future__ import annotations

import json
from typing import Any, cast

from langgraph.graph import END, StateGraph

from app.agents.plan.conversation import run_plan_conversation
from app.schemas.plan import PlanConversationMessage


def _messages_from_chat_history(history: list[dict[str, Any]]) -> list[PlanConversationMessage]:
    messages: list[PlanConversationMessage] = []
    for item in history:
        content = item.get("content")
        if content:
            messages.append(PlanConversationMessage(role=item.get("role", "user"), content=content))
        for card in item.get("cards") or []:
            if not isinstance(card, dict) or card.get("type") != "plan_draft":
                continue
            payload = card.get("payload") or {}
            draft = payload.get("draft")
            if draft:
                messages.append(
                    PlanConversationMessage(
                        role="system",
                        content=f"[plan_draft] {json.dumps(draft, ensure_ascii=False)}",
                    )
                )
    return messages


async def handle_plan_turn(state: dict[str, Any]) -> dict[str, Any]:
    messages = _messages_from_chat_history(state.get("chat_history", []) or [])
    pending_draft = (state.get("context") or {}).get("pending_plan_draft")
    if pending_draft:
        messages.append(
            PlanConversationMessage(
                role="system",
                content=f"[plan_draft] {json.dumps(pending_draft, ensure_ascii=False)}",
            )
        )
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
