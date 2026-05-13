"""Plan system API endpoints."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Any

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


