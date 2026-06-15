"""Plan chat subgraph for the global AI graph.

改造要点（interrupt 版）：
- 旧实现 ``run_plan_conversation`` 一次性返回 ``choice_prompts`` / 草案卡片，graph 结束，
  靠下次请求 + transcript 文本重建草案续接，脆弱且重复计算。
- 新实现把 ``run_plan_conversation`` 当作"决策引擎"：每轮跑出它要"问"的内容
  （选项澄清 / 草案确认）后，用 ``interrupt()`` 暂停等用户作答，把答案回灌为下一轮
  的用户消息，循环直到产出终态响应（已保存计划 / 进度 / 纯文本）。
- 草案存活在 checkpoint state，不再塞进 chat_history 文本。
"""

from __future__ import annotations

import logging
from typing import Any, cast

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

from app.agents.deps import get_dep
from app.agents.interrupts import HumanPrompt, ask_human, card_action, choice_answer
from app.agents.plan.conversation import run_plan_conversation
from app.schemas.plan import PlanConversationMessage, PlanDraft

logger = logging.getLogger(__name__)

# 防止异常情况下 interrupt 循环无限进行（正常 2-4 轮内收敛）。
_MAX_PLAN_TURNS = 8


def _messages_from_chat_history(history: list[dict[str, Any]]) -> list[PlanConversationMessage]:
    messages: list[PlanConversationMessage] = []
    for item in history:
        content = item.get("content")
        if content:
            messages.append(PlanConversationMessage(role=item.get("role", "user"), content=content))
    return messages


def _saved_card(saved: Any) -> dict[str, Any]:
    return {
        "type": "plan_saved",
        "payload": {"plan_id": str(saved.id), "plan": saved.model_dump(mode="json")},
        "actions": [{"kind": "view_plan_detail", "label": "查看计划"}],
    }


async def handle_plan_turn(state: dict[str, Any], config: RunnableConfig = None) -> dict[str, Any]:
    """计划对话节点：用 interrupt 驱动多轮澄清 + 草案确认。

    循环逻辑：
    1. 跑 run_plan_conversation 得到本轮响应。
    2. 若响应里有 plan_draft 卡片 → interrupt(card)：
       - accept/confirm → 保存计划，返回 plan_saved 终态；
       - revise/edit → 把用户修改诉求作为下一轮用户消息，继续循环。
    3. 若响应里有 choice_prompts → interrupt(choice)：把用户选择作为下一轮用户消息。
    4. 否则为终态（纯文本 / 进度卡片）→ 直接返回。
    """
    messages = _messages_from_chat_history(state.get("chat_history", []) or [])
    plan_service = get_dep(state, config, "plan_service")
    memory_service = get_dep(state, config, "memory_service")
    profile = state.get("profile")
    user_message = state.get("user_message")

    for _ in range(_MAX_PLAN_TURNS):
        result = await run_plan_conversation(
            user_message=user_message,
            messages=messages,
            profile=profile,
            plan_service=plan_service,
            memory_service=memory_service,
            request_type="text",
        )
        cards = result.get("response_cards") or []
        choice_prompts = result.get("choice_prompts") or []
        draft_card = next((c for c in cards if isinstance(c, dict) and c.get("type") == "plan_draft"), None)

        if draft_card is not None:
            decision = ask_human(
                HumanPrompt(
                    kind="card",
                    prompt_id="plan_draft",
                    domain="plan",
                    card=draft_card,
                )
            )
            action = card_action(decision)
            if action in ("accept", "confirm"):
                draft_payload = draft_card.get("payload", {}).get("draft", {})
                # 允许用户在确认时附带最终编辑 patch（浅覆盖草案顶层字段）。
                patch = decision.get("patch") or {}
                if patch:
                    draft_payload = {**draft_payload, **patch}
                draft = PlanDraft.model_validate(draft_payload)
                if plan_service is None:
                    return {
                        "ai_response": "计划服务暂不可用，无法保存。",
                        "response_cards": [],
                        "choice_prompts": [],
                    }
                saved = await plan_service.create_plan_from_draft(draft)
                return {
                    "ai_response": f"《{saved.name}》已保存。接下来你可以在详情页查看阶段、任务和执行进度。",
                    "response_cards": [_saved_card(saved)],
                    "choice_prompts": [],
                }
            # revise / edit：把修改诉求回灌为下一轮用户消息。
            revision = decision.get("free_text") or "我想继续调整这个计划。"
            messages.append(PlanConversationMessage(role="user", content=revision))
            user_message = revision
            continue

        if choice_prompts:
            cp = choice_prompts[0]
            answer = ask_human(
                HumanPrompt(
                    kind="choice",
                    prompt_id=str(cp.get("prompt_id", "plan_choice")),
                    domain="plan",
                    question=cp.get("question"),
                    options=cp.get("options", []),
                    allow_free_text=bool(cp.get("allow_free_text", False)),
                )
            )
            chosen = choice_answer(answer) or ""
            messages.append(PlanConversationMessage(role="user", content=chosen))
            user_message = chosen
            continue

        # 终态：纯文本 / 进度卡片，原样返回。
        return result

    logger.warning("plan conversation exceeded max turns; returning last result")
    return result


def build_plan_subgraph():
    graph = StateGraph(cast(Any, dict[str, Any]))
    graph.add_node("handle_plan_turn", cast(Any, handle_plan_turn))
    graph.set_entry_point("handle_plan_turn")
    graph.add_edge("handle_plan_turn", END)
    return graph.compile()


__all__ = ["build_plan_subgraph", "handle_plan_turn"]
