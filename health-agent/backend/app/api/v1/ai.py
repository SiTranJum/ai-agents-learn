"""AI chat API endpoints.

设计参考: docs/plans/2026-05-21-streaming-chat-design.md
任务规格: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T4

``POST /chat`` 是 SSE 流式端点，``Content-Type: text/event-stream``。
事件协议见 :module:`app.streaming.events`。
"""
# ruff: noqa: RUF001,RUF002,RUF003

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any, AsyncIterator

from fastapi import APIRouter, Query

from app.core.exceptions import ValidationException
from app.core.responses import paginated, success
from app.dependencies import (
    ChatAgentDep,
    ChatServiceDep,
    CurrentUserDep,
    DietServiceDep,
    MemoryServiceDep,
    RagServiceDep,
)
from app.schemas.chat import ChatCard, ChatRole, ChatStreamRequest
from app.streaming import (
    StreamEvent,
    StreamEventType,
    sse_response,
    translate_langgraph_events,
)
from app.streaming.translator import CHAT_NODE_LABELS

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
    """根据 ``type`` 字段统一归一化用户输入文本。

    - text             → ``payload.message``
    - choice_response  → ``free_text`` 优先，否则用 ``selected_value`` 字面量
    - card_action      → 由后端拼出"用户点击 <action> 按钮"的可读文本

    保持文本形式才能让 chat history 阅读连贯（参考 §15.4 设计）。
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


@router.post("/chat")
async def send_message(
    payload: ChatStreamRequest,
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
    chat_agent: ChatAgentDep,
    diet_service: DietServiceDep,
    memory_service: MemoryServiceDep,
    rag_service: RagServiceDep,
):
    """流式 chat 端点（SSE）。

    流程：
    1. 接收用户消息（text / card_action / choice_response 三种）
    2. 持久化用户消息
    3. 用 LangGraph ``astream_events(version="v2")`` 跑 chat agent
    4. 通过 ``translator`` 把节点事件翻译为业务事件
    5. 流结束时持久化助手消息 + emit done

    错误：
    - 客户端断开 → ``CancelledError`` 自然向上传播，sse_response 会清理 producer
    - 业务异常 → sse_response 包装为 ``error`` 事件再关闭
    """
    user_text = _resolve_input_message(payload)
    session_id = await chat_service.get_or_create_session(payload.session_id)
    await chat_service.save_message(
        session_id=session_id,
        role=ChatRole.user,
        content=user_text,
    )
    history, _, _ = await chat_service.get_history(
        session_id=session_id, page=1, page_size=10
    )
    context = _context_dict(payload)

    state: dict[str, Any] = {
        "user_id": str(user.id),
        "session_id": session_id,
        "user_message": user_text,
        "chat_history": [item.model_dump(mode="json") for item in history],
        "context": context,
        "diet_input_text": user_text,
        "diet_image_url": context.get("image_url"),
        "diet_date": _parse_referenced_date(context),
        "diet_service": diet_service,
        "memory_service": memory_service,
        "rag_service": rag_service,
        "embedding_client": memory_service.embedding_client,
    }

    message_id = uuid.uuid4().hex
    # 边吐边累积，流结束时一次性持久化
    pending: dict[str, Any] = {"text_parts": [], "cards": []}

    async def gen() -> AsyncIterator[StreamEvent]:
        # 1. meta：告知客户端会话标识
        yield StreamEvent(
            type=StreamEventType.META,
            data={
                "message_id": message_id,
                "session_id": session_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        # 2. 翻译 LangGraph 事件
        async for ev in translate_langgraph_events(
            chat_agent, state, node_labels=CHAT_NODE_LABELS
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

        # 3. 持久化助手消息
        full_text = "".join(pending["text_parts"]) or "我已经收到你的消息。"
        cards: list[ChatCard] = [ChatCard(**c) for c in pending["cards"]]
        try:
            await chat_service.save_message(
                session_id=session_id,
                role=ChatRole.assistant,
                content=full_text,
                cards=cards,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("failed to persist assistant message: %s", exc)

        # 4. done
        yield StreamEvent(
            type=StreamEventType.DONE,
            data={"message_id": message_id, "session_id": session_id},
        )

    return await sse_response(gen())


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


__all__ = ["router"]
