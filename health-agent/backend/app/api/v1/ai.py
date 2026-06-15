"""AI chat API endpoints.

``POST /chat`` 是 SSE 流式端点，``Content-Type: text/event-stream``。
事件协议见 :module:`app.streaming.events`。

interrupt 暂停/恢复模型（替代旧 pending_action + card_action 快速路径）：
- 每个会话用 ``thread_id = session_id`` 绑定 checkpointer 存档。
- 新一轮输入：若会话未处于中断态 → 传完整 graph 输入跑一遍。
- 恢复输入：若会话处于中断态且本次是 choice_response / card_action →
  用 ``Command(resume=<答案>)`` 从中断点继续。
- 跑完后检查是否再次被 interrupt 暂停：是→发 paused 事件（不发 done），
  否→发 done。
"""
# ruff: noqa: RUF001,RUF002,RUF003

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any, AsyncIterator

from fastapi import APIRouter, Query
from langgraph.types import Command

from app.core.exceptions import ValidationException
from app.core.responses import paginated, success
from app.core.tracing import build_langsmith_config
from app.dependencies import (
    BodyServiceDep,
    ChatAgentDep,
    ChatServiceDep,
    CurrentUserDep,
    CurrentUserWithProfileDep,
    DietServiceDep,
    MemoryServiceDep,
    PlanServiceDep,
    RagServiceDep,
    UserServiceDep,
)
from app.schemas.auth import ProfileSnapshot
from app.schemas.chat import ChatCard, ChatRole, ChatStreamRequest
from app.streaming import (
    StreamEvent,
    StreamEventType,
    emit_interrupt_events,
    sse_response,
    translate_langgraph_events,
)
from app.streaming.translator import CHAT_NODE_LABELS, snapshot_has_pending_interrupt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


def _context_dict(payload: ChatStreamRequest) -> dict[str, Any]:
    if payload.context is None:
        return {}
    if hasattr(payload.context, "model_dump"):
        return payload.context.model_dump(exclude_none=True)  # type: ignore[union-attr]
    return dict(payload.context)


def _parse_referenced_date(context: dict[str, Any]) -> date | None:
    raw = context.get("referenced_date")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw))
    except ValueError:
        return None


def _resolve_input_message(payload: ChatStreamRequest) -> str:
    """根据 ``type`` 字段统一归一化用户输入文本（用于持久化 chat history）。

    - text             → ``payload.message``
    - choice_response  → ``free_text`` 优先，否则用 ``selected_value`` 字面量
    - card_action      → 拼出"[卡片操作] <action>"的可读文本
    """
    if payload.type == "text":
        if not payload.message:
            raise ValidationException("缺少消息内容", code="CHAT_MESSAGE_REQUIRED")
        return payload.message

    if payload.type == "choice_response":
        if payload.free_text:
            return payload.free_text
        if payload.selected_value:
            return payload.selected_value
        raise ValidationException("缺少选项回应", code="CHOICE_RESPONSE_INVALID")

    if payload.type == "card_action":
        action = payload.action_id or "card_action"
        return f"[卡片操作] {action}"

    raise ValidationException(f"不支持的请求类型: {payload.type}", code="CHAT_TYPE_INVALID")


def build_resume_payload(payload: ChatStreamRequest) -> dict[str, Any]:
    """把恢复类请求转成 ``ask_human`` 约定的答案 dict。

    - choice_response → {"prompt_id", "value"} 或 {"prompt_id", "free_text"}
    - card_action     → {"prompt_id", "action", "patch"?}

    ``action_id`` 到语义动作的映射：
    - confirm_create_diet_record / confirm_create_body_record → "confirm"
    - edit_diet_items                                          → "edit"
    - cancel_body_record / 任意 cancel_*                        → "cancel"
    - accept_plan / confirm_plan                               → "accept"
    - revise_plan                                              → "revise"
    """
    if payload.type == "choice_response":
        answer: dict[str, Any] = {"prompt_id": payload.prompt_id or ""}
        if payload.free_text:
            answer["free_text"] = payload.free_text
        if payload.selected_value:
            answer["value"] = payload.selected_value
        return answer

    # card_action
    action_id = payload.action_id or ""
    action_map = {
        "confirm_create_diet_record": "confirm",
        "confirm_create_body_record": "confirm",
        "edit_diet_items": "edit",
        "cancel_body_record": "cancel",
        "accept_plan": "accept",
        "confirm_plan": "accept",
        "revise_plan": "revise",
    }
    action = action_map.get(action_id)
    if action is None:
        action = "cancel" if action_id.startswith("cancel") else (action_id or "confirm")
    answer = {"prompt_id": payload.prompt_id or action_id, "action": action}
    if payload.action_payload:
        # 编辑/修改时附带的 patch 直接透传给节点。
        answer["patch"] = payload.action_payload
    if payload.free_text:
        answer["free_text"] = payload.free_text
    return answer


def _build_graph_input(
    payload: ChatStreamRequest,
    *,
    user_id: str,
    session_id: str,
    user_text: str,
    history: list[Any],
    context: dict[str, Any],
    interaction_mode: str,
    profile: Any,
) -> dict[str, Any]:
    """新一轮请求的完整 graph 输入（不含 service，service 走 config.configurable）。"""
    return {
        "user_id": user_id,
        "session_id": session_id,
        "user_message": user_text,
        "chat_history": [item.model_dump(mode="json") for item in history],
        "context": context,
        "interaction_mode": interaction_mode,
        "profile": profile,
        "request_type": payload.type,
        "diet_input_text": user_text,
        "diet_image_url": context.get("image_url"),
        "diet_date": _parse_referenced_date(context),
        "body_input_text": user_text,
        "body_date": _parse_referenced_date(context),
    }


def _build_configurable(
    *,
    diet_service: Any,
    body_service: Any,
    memory_service: Any,
    plan_service: Any,
    rag_service: Any,
) -> dict[str, Any]:
    """运行时依赖通道：service 放这里，不进 checkpoint（不可序列化）。"""
    return {
        "diet_service": diet_service,
        "body_service": body_service,
        "memory_service": memory_service,
        "plan_service": plan_service,
        "rag_service": rag_service,
        "embedding_client": memory_service.embedding_client,
    }


@router.post("/chat")
async def send_message(
    payload: ChatStreamRequest,
    user: CurrentUserWithProfileDep,
    chat_service: ChatServiceDep,
    chat_agent: ChatAgentDep,
    diet_service: DietServiceDep,
    body_service: BodyServiceDep,
    memory_service: MemoryServiceDep,
    plan_service: PlanServiceDep,
    rag_service: RagServiceDep,
    user_service: UserServiceDep,
):
    """流式 chat 端点（SSE），支持 interrupt 暂停/恢复。"""
    user_text = _resolve_input_message(payload)
    session_id = await chat_service.get_or_create_session(payload.session_id)
    await chat_service.save_message(
        session_id=session_id,
        role=ChatRole.user,
        content=user_text,
    )

    context = _context_dict(payload)
    interaction_mode = await user_service.get_interaction_mode()

    langsmith_config = build_langsmith_config(
        user_id=str(user.id),
        endpoint="/api/v1/chat/stream",
        extra_tags=["chat", payload.type],
        extra_metadata={"session_id": session_id},
    )
    # thread_id 绑定会话，checkpointer 据此读写存档；service 走 configurable 不进 checkpoint。
    run_config: dict[str, Any] = {
        **langsmith_config,
        "configurable": {
            **langsmith_config.get("configurable", {}),
            "thread_id": session_id,
            **_build_configurable(
                diet_service=diet_service,
                body_service=body_service,
                memory_service=memory_service,
                plan_service=plan_service,
                rag_service=rag_service,
            ),
        },
    }

    # 判断会话是否处于中断态，决定走"恢复"还是"新一轮"。
    # 用 snapshot_has_pending_interrupt 同时检查 snapshot.next 与 tasks.interrupts，
    # 避免 LangGraph 跨版本下 next 为空 tuple 时误判为"未暂停"导致从头重跑。
    snapshot = await chat_agent.aget_state(run_config)
    is_paused = snapshot_has_pending_interrupt(snapshot)
    is_resume_request = payload.type in ("choice_response", "card_action")

    # 路由诊断（debug 级，生产默认不输出）：定位暂停/恢复问题时打开。
    # 关注 session_id 是否一致、is_paused 是否为 True、resume 请求是否带 prompt_id/action_id。
    logger.debug(
        "chat routing: type=%s req_session=%s resolved_session=%s is_paused=%s "
        "is_resume=%s prompt_id=%s action_id=%s next=%s",
        payload.type,
        payload.session_id,
        session_id,
        is_paused,
        is_resume_request,
        payload.prompt_id,
        payload.action_id,
        getattr(snapshot, "next", None),
    )

    graph_input: Any
    if is_paused and is_resume_request:
        graph_input = Command(resume=build_resume_payload(payload))
    else:
        if is_paused:
            logger.info("session %s was paused but got new text; restarting turn", session_id)
        history, _, _ = await chat_service.get_history(
            session_id=session_id, page=1, page_size=10
        )
        graph_input = _build_graph_input(
            payload,
            user_id=str(user.id),
            session_id=session_id,
            user_text=user_text,
            history=history,
            context=context,
            interaction_mode=interaction_mode,
            # 转换 ORM profile 为可序列化快照（checkpointer msgpack 兼容）
            profile=ProfileSnapshot.from_orm(user.profile),
        )

    message_id = uuid.uuid4().hex
    pending: dict[str, Any] = {"text_parts": [], "cards": []}

    async def gen() -> AsyncIterator[StreamEvent]:
        yield StreamEvent(
            type=StreamEventType.META,
            data={
                "message_id": message_id,
                "session_id": session_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        async for ev in translate_langgraph_events(
            chat_agent, graph_input, node_labels=CHAT_NODE_LABELS, config=run_config
        ):
            if ev.type == StreamEventType.TEXT_DELTA:
                content = ev.data.get("content", "")
                if content:
                    pending["text_parts"].append(content)
            elif ev.type == StreamEventType.CARD:
                card = ev.data.get("card")
                if card:
                    pending["cards"].append(card)
            yield ev

        # 检查是否被 interrupt 暂停（发 choice/card + paused 事件）。
        paused = False
        async for ev in emit_interrupt_events(chat_agent, run_config):
            paused = True
            if ev.type == StreamEventType.CARD:
                card = ev.data.get("card")
                if card:
                    pending["cards"].append(card)
            yield ev

        # 持久化助手消息（暂停态也存，便于历史回看卡片）。
        full_text = "".join(pending["text_parts"]) or ("" if paused else "我已经收到你的消息。")
        cards: list[ChatCard] = [ChatCard(**c) for c in pending["cards"]]
        if full_text or cards:
            try:
                await chat_service.save_message(
                    session_id=session_id,
                    role=ChatRole.assistant,
                    content=full_text,
                    cards=cards,
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("failed to persist assistant message: %s", exc)

        # 暂停态不发 done：前端据 paused 进入 WAITING_INPUT。
        if not paused:
            yield StreamEvent(
                type=StreamEventType.DONE,
                data={"message_id": message_id, "session_id": session_id},
            )

    return await sse_response(gen(), endpoint="ai/chat")


@router.get("/chat/sessions/{session_id}/state", response_model=dict)
async def get_session_state(
    session_id: str,
    user: CurrentUserDep,
    chat_agent: ChatAgentDep,
) -> dict[str, Any]:
    """返回会话当前是否处于中断态及挂起的 prompt（前端重连/刷新后恢复 UI 用）。"""
    _ = user
    config = {"configurable": {"thread_id": session_id}}
    snapshot = await chat_agent.aget_state(config)
    paused = bool(getattr(snapshot, "next", None))
    prompts: list[dict[str, Any]] = []
    if paused:
        for task in getattr(snapshot, "tasks", None) or []:
            for intr in getattr(task, "interrupts", None) or []:
                val = getattr(intr, "value", None)
                if isinstance(val, dict):
                    prompts.append(val)
    return success(
        {
            "session_id": session_id,
            "status": "paused" if paused else "idle",
            "prompts": prompts,
        }
    )


@router.get("/chat/history", response_model=dict)
async def get_chat_history(
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
    session_id: str | None = Query(default=None, description="会话 ID，不传返回最近会话"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
) -> dict[str, Any]:
    """Return message history in timeline order."""
    _ = user
    messages, total, _session_id = await chat_service.get_history(
        session_id=session_id,
        page=page,
        page_size=page_size,
    )
    return paginated(
        [message.model_dump(mode="json") for message in messages],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/chat/sessions/{session_id}", response_model=dict)
async def delete_chat_session(
    session_id: str,
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
) -> dict[str, Any]:
    """Soft-delete all messages in a chat session; idempotent by design."""
    _ = user
    await chat_service.delete_session(session_id)
    return success(None, message="删除成功")


__all__ = ["build_resume_payload", "router"]
