"""AI suggestion API endpoints — SSE 流式版本（T10）。

三个接口均改为 SSE 流式响应：
- 缓存命中：直接 emit card + done（无 LangGraph，极快）
- 缓存未命中：走 LangGraph astream_events → status + card + done

事件序列：
  meta → [status(×N)] → card(×M) → done

注意：suggestion agent 用 with_structured_output，不产生 text_delta，
只有 status 事件（节点切换）和最终 card 事件。
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import suppress
from datetime import datetime, timezone
from typing import Annotated, Any, AsyncIterator

from fastapi import APIRouter, Depends, Query, Response, status

import app.dependencies as deps
from app.agents.memory.subgraph import build_memory_subgraph
from app.core.tracing import build_langsmith_config
from app.integrations.embedding import EmbeddingClient
from app.schemas.auth import CurrentUser
from app.schemas.suggestion import FeedbackCreate
from app.services.memory_service import MemoryService
from app.services.rag_service import RagService
from app.services.suggestion_service import SuggestionService
from app.streaming import StreamEvent, StreamEventType, sse_response
from app.streaming.translator import SUGGESTION_NODE_LABELS

router = APIRouter(prefix="/suggestions", tags=["suggestions"])

CurrentUserWithProfileDep = Annotated[CurrentUser, Depends(deps.get_current_user_with_profile)]
SuggestionServiceDep = Annotated[SuggestionService, Depends(deps.get_suggestion_service)]
SuggestionAgentDep = Annotated[Any, Depends(deps.get_suggestion_agent)]
MemoryServiceDep = Annotated[MemoryService, Depends(deps.get_memory_service)]
RagServiceDep = Annotated[RagService, Depends(deps.get_rag_service)]
_BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()


def _discard_task(task: asyncio.Task[Any]) -> None:
    _BACKGROUND_TASKS.discard(task)
    if not task.cancelled():
        with suppress(Exception):
            task.exception()


def _meta_event() -> StreamEvent:
    return StreamEvent(
        type=StreamEventType.META,
        data={"message_id": uuid.uuid4().hex, "started_at": datetime.now(timezone.utc).isoformat()},
    )


def _build_state(
    user: CurrentUser,
    suggestion_type: str,
    meal_type: str | None,
    memory_service: MemoryService,
    rag_service: RagService,
) -> dict[str, Any]:
    return {
        "user_id": str(user.id),
        "suggestion_type": suggestion_type,
        "meal_type": meal_type,
        "profile": user.profile,
        "memory_service": memory_service,
        "rag_service": rag_service,
    }


async def _stream_suggestion_agent(
    agent: Any,
    state: dict[str, Any],
    user_id: str | None = None,
    suggestion_type: str = "unknown",
) -> AsyncIterator[tuple[StreamEvent | None, dict[str, Any]]]:
    """运行 suggestion agent，yield (status_event | None, final_output)。

    - 节点开始时 yield (status_event, {})
    - deduplicate_filter 结束时 yield (None, final_output)
    - 其他事件忽略

    调用方只需要 yield 非 None 的 event，并在最后用 final_output 保存结果。
    """
    # LangSmith 追踪配置
    langsmith_config: dict[str, Any] = {}
    if user_id:
        langsmith_config = build_langsmith_config(
            user_id=user_id,
            endpoint="/api/v1/suggestions",
            extra_tags=["suggestion", suggestion_type],
            extra_metadata={"suggestion_type": suggestion_type},
        )

    final_output: dict[str, Any] = {}
    async for ev in agent.astream_events(state, version="v2", config=langsmith_config):
        kind = ev.get("event")
        name = ev.get("name", "")
        if kind == "on_chain_start" and name in SUGGESTION_NODE_LABELS:
            yield StreamEvent(
                type=StreamEventType.STATUS,
                data={"node": name, "label": SUGGESTION_NODE_LABELS[name]},
            ), {}
        elif kind == "on_chain_end" and name == "deduplicate_filter":
            final_output = (ev.get("data") or {}).get("output") or {}
    yield None, final_output  # type: ignore[misc]


@router.get("/daily")
async def get_daily_suggestions(
    user: CurrentUserWithProfileDep,
    service: SuggestionServiceDep,
    suggestion_agent: SuggestionAgentDep,
    memory_service: MemoryServiceDep,
    rag_service: RagServiceDep,
):
    """每日建议 SSE 流。缓存命中直接返回，未命中走 LangGraph。"""
    message_id = uuid.uuid4().hex

    async def gen() -> AsyncIterator[StreamEvent]:
        yield _meta_event()

        cached = await service.get_cached_daily()
        if cached is not None:
            for item in cached.suggestions:
                yield StreamEvent(
                    type=StreamEventType.CARD,
                    data={"card": item.model_dump(mode="json"), "suggestion_type": "daily"},
                )
        else:
            state = _build_state(user, "daily", None, memory_service, rag_service)
            final_output: dict[str, Any] = {}
            async for ev, output in _stream_suggestion_agent(
                suggestion_agent, state, user_id=str(user.id), suggestion_type="daily"
            ):
                if ev is not None:
                    yield ev
                else:
                    final_output = output
            data = await service.save_daily(final_output.get("filtered_suggestions", []))
            for item in data.suggestions:
                yield StreamEvent(
                    type=StreamEventType.CARD,
                    data={"card": item.model_dump(mode="json"), "suggestion_type": "daily"},
                )

        yield StreamEvent(type=StreamEventType.DONE, data={"message_id": message_id})

    return await sse_response(gen(), endpoint="suggestions/daily")


@router.get("/meal")
async def get_meal_suggestions(
    user: CurrentUserWithProfileDep,
    service: SuggestionServiceDep,
    suggestion_agent: SuggestionAgentDep,
    memory_service: MemoryServiceDep,
    rag_service: RagServiceDep,
    meal_type: Annotated[str, Query(pattern="^(breakfast|lunch|dinner|snack)$")],
):
    """餐食建议 SSE 流（无缓存，每次走 LangGraph）。"""
    message_id = uuid.uuid4().hex

    async def gen() -> AsyncIterator[StreamEvent]:
        yield _meta_event()
        state = _build_state(user, "meal", meal_type, memory_service, rag_service)
        final_output: dict[str, Any] = {}
        async for ev, output in _stream_suggestion_agent(
            suggestion_agent, state, user_id=str(user.id), suggestion_type=f"meal-{meal_type}"
        ):
            if ev is not None:
                yield ev
            else:
                final_output = output
        data = await service.save_meal(
            meal_type,
            final_output.get("filtered_suggestions", []),
            final_output.get("reasoning", ""),
        )
        for item in data.suggestions:
            yield StreamEvent(
                type=StreamEventType.CARD,
                data={"card": item.model_dump(mode="json"), "suggestion_type": "meal", "meal_type": meal_type},
            )
        yield StreamEvent(type=StreamEventType.DONE, data={"message_id": message_id})

    return await sse_response(gen(), endpoint="suggestions/meal")


@router.get("/insights")
async def get_insights(
    user: CurrentUserWithProfileDep,
    service: SuggestionServiceDep,
    suggestion_agent: SuggestionAgentDep,
    memory_service: MemoryServiceDep,
    rag_service: RagServiceDep,
):
    """洞察建议 SSE 流。缓存命中直接返回，未命中走 LangGraph。"""
    message_id = uuid.uuid4().hex

    async def gen() -> AsyncIterator[StreamEvent]:
        yield _meta_event()

        cached = await service.get_cached_insights()
        if cached is not None:
            for item in cached.insights:
                yield StreamEvent(
                    type=StreamEventType.CARD,
                    data={"card": item.model_dump(mode="json"), "suggestion_type": "insight"},
                )
        else:
            state = _build_state(user, "insight", None, memory_service, rag_service)
            final_output: dict[str, Any] = {}
            async for ev, output in _stream_suggestion_agent(
                suggestion_agent, state, user_id=str(user.id), suggestion_type="insight"
            ):
                if ev is not None:
                    yield ev
                else:
                    final_output = output
            data = await service.save_insights(final_output.get("filtered_suggestions", []))
            for item in data.insights:
                yield StreamEvent(
                    type=StreamEventType.CARD,
                    data={"card": item.model_dump(mode="json"), "suggestion_type": "insight"},
                )

        yield StreamEvent(type=StreamEventType.DONE, data={"message_id": message_id})

    return await sse_response(gen(), endpoint="suggestions/insights")


@router.post("/{suggestion_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def submit_feedback(
    suggestion_id: uuid.UUID,
    payload: FeedbackCreate,
    user: CurrentUserWithProfileDep,
    service: SuggestionServiceDep,
    memory_service: MemoryServiceDep,
) -> Response:
    item = await service.submit_feedback(suggestion_id, payload)
    try:
        graph = build_memory_subgraph()
        task = asyncio.create_task(
            graph.ainvoke(
                {
                    "user_id": str(user.id),
                    "trigger_type": "suggestion_feedback",
                    "context_data": {"suggestion": item.model_dump(mode="json"), "rating": payload.rating.value},
                    "memory_service": memory_service,
                    "embedding_client": EmbeddingClient(),
                }
            )
        )
        _BACKGROUND_TASKS.add(task)
        task.add_done_callback(_discard_task)
    except Exception:  # pragma: no cover
        pass
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
