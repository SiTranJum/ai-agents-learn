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
from app.services.pending_action_store import (
    create_pending_action,
    get_pending_action_store,
)
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


# ============ T9: card_action 处理 ============


def _coerce_meal_type(value: Any) -> str:
    """把 enum / 字符串 / None 统一为字符串。"""
    if value is None:
        return "snack"
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


async def _handle_confirm_create_diet_record(
    payload: ChatStreamRequest,
    diet_service: Any,
) -> tuple[str, list[dict[str, Any]]]:
    """处理饮食卡片"确认保存"按钮。

    返回 ``(ai_response_text, response_cards)``，由调用方写入 SSE 流。

    action_payload 期望结构（由前端从原卡片 payload 复制过来）::

        {
            "foods": [{"name": ..., "amount": ..., "unit": ..., ...}, ...],
            "meal_type": "lunch",
            "date": "2026-05-26"   # 可选，缺失用今天
        }
    """
    from datetime import date as date_cls

    from app.schemas.diet import FoodItemInput, MealType

    ap = payload.action_payload or {}
    raw_foods = ap.get("foods") or []
    if not raw_foods:
        raise ValidationException(
            "卡片操作缺少食物数据", code="CARD_ACTION_PAYLOAD_INVALID"
        )

    meal_type_raw = _coerce_meal_type(ap.get("meal_type"))
    try:
        meal_type = MealType(meal_type_raw)
    except ValueError:
        meal_type = MealType.snack

    date_raw = ap.get("date")
    record_date = (
        date_cls.fromisoformat(str(date_raw)) if date_raw else date_cls.today()
    )

    foods = [FoodItemInput.model_validate(f) for f in raw_foods]
    record = await diet_service.create_record(
        meal_type=meal_type,
        foods=foods,
        record_date=record_date,
    )
    text = f"已保存到{meal_type.value}记录，共 {len(foods)} 项食物。"
    # 回一张"已确认"状态的卡片让前端把原卡片标记为 submitted
    confirmed_card = {
        "type": "diet_saved",
        "payload": {
            "record_id": str(record.id) if hasattr(record, "id") else None,
            "meal_type": meal_type.value,
            "date": record_date.isoformat(),
        },
        "actions": [],
    }
    return text, [confirmed_card]


async def _stream_card_action(
    payload: ChatStreamRequest,
    session_id: str,
    chat_service: Any,
    diet_service: Any,
):
    """把 card_action 结果包装成最小 SSE 流（meta → text → card → done）。

    不走 LangGraph，避免无意义的 LLM 调用浪费 token。
    """
    message_id = uuid.uuid4().hex
    action_id = payload.action_id or ""

    async def gen() -> AsyncIterator[StreamEvent]:
        yield StreamEvent(
            type=StreamEventType.META,
            data={
                "message_id": message_id,
                "session_id": session_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        try:
            if action_id == "confirm_create_diet_record":
                text, cards = await _handle_confirm_create_diet_record(
                    payload, diet_service
                )
            elif action_id == "edit_diet_items":
                # 编辑动作纯前端跳转，后端只回一个 ack
                text = "好的，去编辑食物。"
                cards = []
            else:
                # 未识别的 action，回一条提示
                text = f"暂不支持的操作：{action_id}"
                cards = []
        except ValidationException as exc:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                data={
                    "code": exc.code or "CARD_ACTION_FAILED",
                    "message": exc.message,
                    "retriable": False,
                },
            )
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception("card_action failed: %s", exc)
            yield StreamEvent(
                type=StreamEventType.ERROR,
                data={
                    "code": "CARD_ACTION_FAILED",
                    "message": "卡片操作失败，请稍后重试",
                    "retriable": True,
                },
            )
            return

        # 一次性 yield 完整文本（短文本不需要逐 token，保持一致协议即可）
        if text:
            yield StreamEvent(
                type=StreamEventType.TEXT_DELTA,
                data={"content": text},
            )

        for card in cards:
            yield StreamEvent(
                type=StreamEventType.CARD,
                data={"card": card},
            )

        # 持久化助手消息
        try:
            await chat_service.save_message(
                session_id=session_id,
                role=ChatRole.assistant,
                content=text,
                cards=[ChatCard(**c) for c in cards],
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("failed to persist card_action response: %s", exc)

        yield StreamEvent(
            type=StreamEventType.DONE,
            data={"message_id": message_id, "session_id": session_id},
        )

    return await sse_response(gen(), endpoint="ai/chat:card_action")


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

    # ============ T9: card_action 快速路径 ============
    # 卡片确认/取消等明确操作不需要走 LangGraph，
    # 直接调对应 service，把结果包装成最小流式响应。
    if payload.type == "card_action":
        return await _stream_card_action(
            payload=payload,
            session_id=session_id,
            chat_service=chat_service,
            diet_service=diet_service,
        )

    history, _, _ = await chat_service.get_history(
        session_id=session_id, page=1, page_size=10
    )
    context = _context_dict(payload)

    # P2: 读取 pending_action（如果是 choice_response 类型）
    pa_store = get_pending_action_store()
    existing_pa = await pa_store.get(session_id) if payload.type == "choice_response" else None

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
        # P2: 注入 pending_action 供节点使用
        "pending_action": existing_pa,
    }

    # P2: 如果是 choice_response 且有 pending_action 带 diet_partial，
    # 把用户选择的 meal_type 合并进去，让 agent 跳过重新解析直接出卡片
    if existing_pa and existing_pa.diet_partial and payload.type == "choice_response":
        meal_value = payload.selected_value or payload.free_text or "snack"
        state["intent"] = "diet"
        state["diet_parse_result"] = existing_pa.diet_partial
        # 把 meal_type 注入到 parse_result 里
        if hasattr(existing_pa.diet_partial, "meal_type"):
            existing_pa.diet_partial.meal_type = meal_value
        elif isinstance(existing_pa.diet_partial, dict):
            existing_pa.diet_partial["meal_type"] = meal_value
        # 删除 pending_action（已消费）
        await pa_store.delete(session_id)

    message_id = uuid.uuid4().hex
    # 边吐边累积，流结束时一次性持久化
    pending: dict[str, Any] = {"text_parts": [], "cards": [], "choice_prompts": []}

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

        # 2. 翻译 LangGraph 事件，注入 LangSmith 追踪配置
        langsmith_config = {
            "tags": [f"user-{user.id}", "chat", payload.type],
            "metadata": {
                "session_id": session_id,
                "message_id": message_id,
                "user_id": str(user.id),
                "endpoint": "/api/v1/chat/stream",
            },
        }
        async for ev in translate_langgraph_events(
            chat_agent, state, node_labels=CHAT_NODE_LABELS, config=langsmith_config
        ):
            if ev.type == StreamEventType.TEXT_DELTA:
                content = ev.data.get("content", "")
                if content:
                    pending["text_parts"].append(content)
            elif ev.type == StreamEventType.CARD:
                card = ev.data.get("card")
                if card:
                    pending["cards"].append(card)
            elif ev.type == StreamEventType.CHOICE:
                pending["choice_prompts"].append(ev.data)
            yield ev

        # 3. P2: 如果有 choice_prompts，存 pending_action 供下次请求使用
        if pending["choice_prompts"]:
            for cp in pending["choice_prompts"]:
                pa = create_pending_action(
                    prompt_id=cp.get("prompt_id", ""),
                    options=cp.get("options", []),
                    diet_partial=state.get("diet_parse_result"),
                )
                await pa_store.set(session_id, pa)

        # 4. 持久化助手消息
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

        # 5. done
        yield StreamEvent(
            type=StreamEventType.DONE,
            data={"message_id": message_id, "session_id": session_id},
        )

    return await sse_response(gen(), endpoint="ai/chat")


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
