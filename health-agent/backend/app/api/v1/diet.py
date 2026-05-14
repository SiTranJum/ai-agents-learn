"""饮食记录 API 路由（纯 CRUD）。

所有端点均为 ``API → DietService → Repository`` 直连，不经过 Agent。
自然语言解析路径由 ``/ai/chat`` + diet subgraph 承担（见 ``docs/specs/shared/api-contract.md`` §5）。
"""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.responses import paginated, success
from app.dependencies import CurrentUserDep, DietServiceDep, PlanServiceDep
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.diet import (
    DailySummary,
    DietRecordCreate,
    DietRecordResponse,
    DietRecordUpdate,
    MealType,
    WeeklySummary,
)

router = APIRouter(prefix="/diet", tags=["diet"])

StartDateQuery = Annotated[date, Query()]
EndDateQuery = Annotated[date | None, Query()]
MealTypeQuery = Annotated[MealType | None, Query()]
PageQuery = Annotated[int, Query(ge=1)]
PageSizeQuery = Annotated[int, Query(ge=1, le=50)]
TargetDateQuery = Annotated[date, Query(alias="date")]


@router.post(
    "/records",
    response_model=ApiResponse[DietRecordResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建饮食记录（结构化输入）",
)
async def create_record(
    payload: DietRecordCreate,
    user: CurrentUserDep,
    service: DietServiceDep,
    plan_service: PlanServiceDep,
):
    data = await service.create_record(
        meal_type=payload.meal_type,
        foods=payload.foods,
        record_date=payload.date,
    )
    daily = await service.get_daily_summary(payload.date)
    await plan_service.on_diet_record_created(payload.date, daily.total_nutrition)
    return success(data.model_dump(mode="json"))


@router.get(
    "/records",
    response_model=PaginatedResponse[DietRecordResponse],
    summary="查询饮食记录列表",
)
async def list_records(
    user: CurrentUserDep,
    service: DietServiceDep,
    start_date: StartDateQuery,
    end_date: EndDateQuery = None,
    meal_type: MealTypeQuery = None,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 20,
):
    items, total = await service.list_records(
        start_date=start_date,
        end_date=end_date,
        meal_type=meal_type,
        page=page,
        page_size=page_size,
    )
    return paginated(
        [item.model_dump(mode="json") for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/records/{record_id}",
    response_model=ApiResponse[DietRecordResponse],
    summary="获取饮食记录详情",
)
async def get_record(record_id: uuid.UUID, user: CurrentUserDep, service: DietServiceDep):
    data = await service.get_record(record_id)
    return success(data.model_dump(mode="json"))


@router.put(
    "/records/{record_id}",
    response_model=ApiResponse[DietRecordResponse],
    summary="更新饮食记录",
)
async def update_record(
    record_id: uuid.UUID,
    payload: DietRecordUpdate,
    user: CurrentUserDep,
    service: DietServiceDep,
):
    data = await service.update_record(record_id, payload)
    return success(data.model_dump(mode="json"))


@router.delete("/records/{record_id}", response_model=ApiResponse[object], summary="删除饮食记录")
async def delete_record(record_id: uuid.UUID, user: CurrentUserDep, service: DietServiceDep):
    await service.delete_record(record_id)
    return success(None, message="删除成功")


@router.get(
    "/daily-summary",
    response_model=ApiResponse[DailySummary],
    summary="每日营养汇总",
)
async def daily_summary(
    user: CurrentUserDep,
    service: DietServiceDep,
    target_date: TargetDateQuery,
):
    data = await service.get_daily_summary(target_date)
    return success(data.model_dump(mode="json"))


@router.get(
    "/weekly-summary",
    response_model=ApiResponse[WeeklySummary],
    summary="每周营养汇总",
)
async def weekly_summary(
    user: CurrentUserDep,
    service: DietServiceDep,
    start_date: StartDateQuery,
):
    data = await service.get_weekly_summary(start_date)
    return success(data.model_dump(mode="json"))


__all__ = ["router"]
