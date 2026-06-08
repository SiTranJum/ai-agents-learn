"""Plan API endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Annotated, Any, AsyncIterator

from fastapi import APIRouter, Query, status

from app.agents.plan.conversation import run_plan_conversation
from app.core.exceptions import ConflictException, ValidationException
from app.core.responses import paginated, success
from app.dependencies import (
    CurrentUserWithProfileDep,
    MemoryServiceDep,
    PlanAgentDep,
    PlanServiceDep,
)
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.plan import (
    CheckInCreate,
    CheckInResponse,
    DailyExecution,
    ExecutionStatus,
    PlanCreate,
    PlanProgress,
    PlanResponse,
    PlanStatus,
    PlanStreamRequest,
    PlanTerminateRequest,
    PlanUpdate,
)
from app.streaming import StreamEvent, StreamEventType, sse_response

router = APIRouter(prefix="/plans", tags=["plans"])


def _resolve_stream_message(payload: PlanStreamRequest) -> str:
    if payload.type == "text":
        if not payload.message:
            raise ValidationException("Missing plan message", code="PLAN_MESSAGE_REQUIRED")
        return payload.message
    if payload.type == "choice_response":
        if payload.free_text:
            return payload.free_text
        if payload.selected_value:
            return payload.selected_value
        raise ValidationException("Missing choice response", code="PLAN_CHOICE_REQUIRED")
    if payload.type == "card_action":
        return payload.message or f"[card_action] {payload.action_id or 'action'}"
    raise ValidationException("Unsupported request type", code="PLAN_STREAM_TYPE_INVALID")


def _chunk_text(text: str, chunk_size: int = 80) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


@router.post("", response_model=ApiResponse[PlanResponse], status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreate,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    plan_agent: PlanAgentDep,
) -> dict[str, Any]:
    if await service.has_active_plan():
        raise ConflictException("Active plan already exists", code="PLAN_ALREADY_ACTIVE")
    result = await plan_agent.ainvoke(
        {
            "user_id": str(user.id),
            "goal_description": payload.goal_description,
            "plan_type": payload.plan_type,
            "profile": user.profile,
            "plan_service": service,
        }
    )
    if result.get("error"):
        raise ValidationException("Plan creation failed", code=str(result["error"]))
    data = result["result"]
    return success(data.model_dump(mode="json"))


@router.post("/stream")
async def create_plan_stream(
    payload: PlanStreamRequest,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    memory_service: MemoryServiceDep,
):
    message_id = uuid.uuid4().hex
    user_text = _resolve_stream_message(payload)

    async def gen() -> AsyncIterator[StreamEvent]:
        yield StreamEvent(
            type=StreamEventType.META,
            data={"message_id": message_id, "session_id": payload.session_id, "started_at": datetime.now(timezone.utc).isoformat()},
        )
        yield StreamEvent(type=StreamEventType.STATUS, data={"node": "handle_plan_turn", "label": "Preparing your plan..."})
        try:
            result = await run_plan_conversation(
                user_message=user_text,
                messages=payload.messages,
                profile=user.profile,
                plan_service=service,
                memory_service=memory_service,
                plan_type_hint=payload.plan_type_hint,
                request_type=payload.type,
                action_id=payload.action_id,
                action_payload=payload.action_payload,
            )
        except ValidationException as exc:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                data={"code": exc.code or "PLAN_STREAM_FAILED", "message": exc.message, "retriable": False},
            )
            return
        except Exception as exc:  # pragma: no cover
            yield StreamEvent(
                type=StreamEventType.ERROR,
                data={"code": "PLAN_STREAM_FAILED", "message": str(exc) or "Plan conversation failed", "retriable": True},
            )
            return

        text = str(result.get("ai_response") or "")
        for chunk in _chunk_text(text):
            yield StreamEvent(type=StreamEventType.TEXT_DELTA, data={"content": chunk})
        for card in result.get("response_cards", []) or []:
            yield StreamEvent(type=StreamEventType.CARD, data={"card": card})
        for prompt in result.get("choice_prompts", []) or []:
            yield StreamEvent(type=StreamEventType.CHOICE, data=prompt)
        yield StreamEvent(type=StreamEventType.DONE, data={"message_id": message_id, "session_id": payload.session_id})

    return await sse_response(gen(), endpoint="plans/stream")


@router.get("", response_model=PaginatedResponse[PlanResponse])
async def list_plans(
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    plan_status: Annotated[PlanStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> dict[str, Any]:
    _ = user
    items, total = await service.list_plans(status=plan_status, page=page, page_size=page_size)
    return paginated([item.model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


@router.get("/{plan_id}", response_model=ApiResponse[PlanResponse])
async def get_plan(plan_id: uuid.UUID, user: CurrentUserWithProfileDep, service: PlanServiceDep) -> dict[str, Any]:
    _ = user
    data = await service.get_plan(plan_id)
    return success(data.model_dump(mode="json"))


@router.put("/{plan_id}", response_model=ApiResponse[PlanResponse])
async def update_plan(
    plan_id: uuid.UUID,
    payload: PlanUpdate,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
) -> dict[str, Any]:
    _ = user
    data = await service.update_plan(plan_id, payload)
    return success(data.model_dump(mode="json"))


@router.delete("/{plan_id}", response_model=ApiResponse[object])
async def terminate_plan(
    plan_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    payload: PlanTerminateRequest | None = None,
) -> dict[str, Any]:
    _ = user
    await service.terminate_plan(plan_id, payload.reason if payload else None)
    return success(None, message="Plan terminated")


@router.post("/{plan_id}/check-ins", response_model=ApiResponse[CheckInResponse], status_code=status.HTTP_201_CREATED)
async def create_check_in(
    plan_id: uuid.UUID,
    payload: CheckInCreate,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
) -> dict[str, Any]:
    _ = user
    data = await service.create_check_in(plan_id, payload)
    return success(data.model_dump(mode="json"))


@router.get("/{plan_id}/progress", response_model=ApiResponse[PlanProgress])
async def get_progress(plan_id: uuid.UUID, user: CurrentUserWithProfileDep, service: PlanServiceDep) -> dict[str, Any]:
    _ = user
    data = await service.get_progress(plan_id)
    return success(data.model_dump(mode="json"))


@router.get("/{plan_id}/execution", response_model=PaginatedResponse[DailyExecution])
async def list_execution(
    plan_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    execution_status: Annotated[ExecutionStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> dict[str, Any]:
    _ = user
    items, total = await service.list_execution_records(
        plan_id,
        start_date=start_date,
        end_date=end_date,
        status=execution_status,
        page=page,
        page_size=page_size,
    )
    return paginated([item.model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


__all__ = ["router"]
