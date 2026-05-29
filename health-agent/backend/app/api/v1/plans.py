"""Plan system API endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Annotated, Any, AsyncIterator

from fastapi import APIRouter, Depends, Query, status

from app.core.exceptions import ConflictException, ValidationException
from app.core.responses import paginated, success
from app.dependencies import get_current_user_with_profile, get_plan_agent, get_plan_service
from app.schemas.auth import CurrentUser
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
    PlanTerminateRequest,
    PlanUpdate,
)
from app.services.plan_service import PlanService
from app.streaming import StreamEvent, StreamEventType, sse_response
from app.streaming.translator import PLAN_NODE_LABELS

router = APIRouter(prefix="/plans", tags=["plans"])

CurrentUserWithProfileDep = Annotated[CurrentUser, Depends(get_current_user_with_profile)]
PlanServiceDep = Annotated[PlanService, Depends(get_plan_service)]
PlanAgentDep = Annotated[Any, Depends(get_plan_agent)]


@router.post("", response_model=ApiResponse[PlanResponse], status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreate,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    plan_agent: PlanAgentDep,
) -> dict[str, Any]:
    """Create a plan through plan_agent. LLM calls happen only in agent nodes."""
    if await service.has_active_plan():
        raise ConflictException("已有活跃计划", code="PLAN_ALREADY_ACTIVE")
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
        raise ValidationException("计划创建失败", code=str(result["error"]))
    data = result["result"]
    return success(data.model_dump(mode="json"))


@router.post("/stream")
async def create_plan_stream(
    payload: PlanCreate,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    plan_agent: PlanAgentDep,
):
    """SSE 流式创建计划 (T11)。

    事件序列：
      meta → status(×N) → card(plan) + done   (成功)
      meta → status(×M) → error                (安全校验失败 / 内部错误)
    """
    message_id = uuid.uuid4().hex

    async def gen() -> AsyncIterator[StreamEvent]:
        yield StreamEvent(
            type=StreamEventType.META,
            data={"message_id": message_id, "started_at": datetime.now(timezone.utc).isoformat()},
        )

        if await service.has_active_plan():
            yield StreamEvent(
                type=StreamEventType.ERROR,
                data={"code": "PLAN_ALREADY_ACTIVE", "message": "已有活跃计划", "retriable": False},
            )
            return

        state = {
            "user_id": str(user.id),
            "goal_description": payload.goal_description,
            "plan_type": payload.plan_type,
            "profile": user.profile,
            "plan_service": service,
        }

        final_output: dict[str, Any] = {}
        async for ev in plan_agent.astream_events(state, version="v2"):
            kind = ev.get("event")
            name = ev.get("name", "")
            if kind == "on_chain_start" and name in PLAN_NODE_LABELS:
                yield StreamEvent(
                    type=StreamEventType.STATUS,
                    data={"node": name, "label": PLAN_NODE_LABELS[name]},
                )
            elif kind == "on_chain_end" and name == "persist_plan":
                final_output = (ev.get("data") or {}).get("output") or {}

        err = final_output.get("error")
        if err:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                data={"code": str(err), "message": "计划创建失败", "retriable": True},
            )
            return

        result = final_output.get("result")
        if result is None:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                data={"code": "PLAN_NO_RESULT", "message": "未生成计划，请重试", "retriable": True},
            )
            return

        yield StreamEvent(
            type=StreamEventType.CARD,
            data={"card": result.model_dump(mode="json"), "card_type": "plan"},
        )
        yield StreamEvent(type=StreamEventType.DONE, data={"message_id": message_id})

    return await sse_response(gen())


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
    return success(None, message="计划已终止")


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


