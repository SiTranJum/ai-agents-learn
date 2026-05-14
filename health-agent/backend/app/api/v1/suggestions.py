"""AI suggestion API endpoints."""

from __future__ import annotations

import asyncio
import uuid
from contextlib import suppress
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response, status

import app.dependencies as deps
from app.agents.memory.subgraph import build_memory_subgraph
from app.integrations.embedding import EmbeddingClient
from app.schemas.auth import CurrentUser
from app.schemas.common import ApiResponse
from app.schemas.suggestion import (
    DailySuggestionResponse,
    FeedbackCreate,
    InsightResponse,
    MealSuggestionResponse,
)
from app.services.memory_service import MemoryService
from app.services.rag_service import RagService
from app.services.suggestion_service import SuggestionService

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


async def _run_agent(
    *,
    agent: Any,
    user: CurrentUser,
    suggestion_type: str,
    meal_type: str | None,
    memory_service: MemoryService,
    rag_service: RagService,
) -> dict[str, Any]:
    return await agent.ainvoke(
        {
            "user_id": str(user.id),
            "suggestion_type": suggestion_type,
            "meal_type": meal_type,
            "profile": user.profile,
            "memory_service": memory_service,
            "rag_service": rag_service,
        }
    )


@router.get("/daily", response_model=ApiResponse[DailySuggestionResponse])
async def get_daily_suggestions(
    user: CurrentUserWithProfileDep,
    service: SuggestionServiceDep,
    suggestion_agent: SuggestionAgentDep,
    memory_service: MemoryServiceDep,
    rag_service: RagServiceDep,
) -> dict[str, Any]:
    cached = await service.get_cached_daily()
    if cached is not None:
        return {"data": cached.model_dump(mode="json"), "message": "ok"}
    state = await _run_agent(
        agent=suggestion_agent,
        user=user,
        suggestion_type="daily",
        meal_type=None,
        memory_service=memory_service,
        rag_service=rag_service,
    )
    data = await service.save_daily(state.get("filtered_suggestions", []))
    return {"data": data.model_dump(mode="json"), "message": "ok"}


@router.get("/meal", response_model=ApiResponse[MealSuggestionResponse])
async def get_meal_suggestions(
    user: CurrentUserWithProfileDep,
    service: SuggestionServiceDep,
    suggestion_agent: SuggestionAgentDep,
    memory_service: MemoryServiceDep,
    rag_service: RagServiceDep,
    meal_type: Annotated[str, Query(pattern="^(breakfast|lunch|dinner|snack)$")],
) -> dict[str, Any]:
    state = await _run_agent(
        agent=suggestion_agent,
        user=user,
        suggestion_type="meal",
        meal_type=meal_type,
        memory_service=memory_service,
        rag_service=rag_service,
    )
    data = await service.save_meal(meal_type, state.get("filtered_suggestions", []), state.get("reasoning", ""))
    return {"data": data.model_dump(mode="json"), "message": "ok"}


@router.get("/insights", response_model=ApiResponse[InsightResponse])
async def get_insights(
    user: CurrentUserWithProfileDep,
    service: SuggestionServiceDep,
    suggestion_agent: SuggestionAgentDep,
    memory_service: MemoryServiceDep,
    rag_service: RagServiceDep,
) -> dict[str, Any]:
    cached = await service.get_cached_insights()
    if cached is not None:
        return {"data": cached.model_dump(mode="json"), "message": "ok"}
    state = await _run_agent(
        agent=suggestion_agent,
        user=user,
        suggestion_type="insight",
        meal_type=None,
        memory_service=memory_service,
        rag_service=rag_service,
    )
    data = await service.save_insights(state.get("filtered_suggestions", []))
    return {"data": data.model_dump(mode="json"), "message": "ok"}


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
    except Exception:  # pragma: no cover - feedback persistence already succeeded
        pass
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]




