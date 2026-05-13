"""AI chat API endpoints."""
# ruff: noqa: RUF001,RUF002,RUF003

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Query

from app.core.responses import paginated, success
from app.dependencies import (
    ChatAgentDep,
    ChatServiceDep,
    CurrentUserDep,
    DietServiceDep,
    MemoryServiceDep,
    RagServiceDep,
)
from app.schemas.chat import ChatCard, ChatRequest, ChatResponse, ChatResponseMessage, ChatRole

router = APIRouter(prefix="/ai", tags=["ai"])


def _context_dict(payload: ChatRequest) -> dict[str, Any]:
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


@router.post("/chat", response_model=dict)
async def send_message(
    payload: ChatRequest,
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
    chat_agent: ChatAgentDep,
    diet_service: DietServiceDep,
    memory_service: MemoryServiceDep,
    rag_service: RagServiceDep,
) -> dict[str, Any]:
    """Send one message to the global chat agent.

    流程：保存用户消息 → 调用 chat_agent → 保存助手消息 → 返回助手消息。
    LLM 调用只发生在 ``app.agents.chat`` 内部。
    """
    session_id = await chat_service.get_or_create_session(payload.session_id)
    user_message = await chat_service.save_message(
        session_id=session_id,
        role=ChatRole.user,
        content=payload.message,
    )
    history, _, _ = await chat_service.get_history(session_id=session_id, page=1, page_size=10)
    context = _context_dict(payload)
    result = await chat_agent.ainvoke(
        {
            "user_id": str(user.id),
            "session_id": session_id,
            "user_message": payload.message,
            "chat_history": [item.model_dump(mode="json") for item in history],
            "context": context,
            "diet_input_text": payload.message,
            "diet_image_url": context.get("image_url"),
            "diet_date": _parse_referenced_date(context),
            "diet_service": diet_service,
            "memory_service": memory_service,
            "rag_service": rag_service,
            "embedding_client": memory_service.embedding_client,
        }
    )
    cards = [ChatCard(**card) for card in result.get("response_cards", [])]
    assistant_message = await chat_service.save_message(
        session_id=session_id,
        role=ChatRole.assistant,
        content=result.get("ai_response") or "我已经收到你的消息。",
        cards=cards,
    )
    response = ChatResponse(
        session_id=session_id,
        intent=result.get("intent"),
        messages=[
            ChatResponseMessage(
                id=assistant_message.id,
                role=assistant_message.role,
                content=assistant_message.content,
                cards=assistant_message.cards,
                created_at=assistant_message.created_at,
            )
        ],
    )
    # 保留 user_message 变量以明确“已持久化用户消息”的流程，避免静态分析误判未使用。
    _ = user_message
    return success(response.model_dump(mode="json"))


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


