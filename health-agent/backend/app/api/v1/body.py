"""身体数据追踪 API 路由。"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.responses import paginated, success
from app.dependencies import BodyServiceDep, CurrentUserWithProfileDep
from app.schemas.body import (
    BodyRecordType,
    BowelRecordCreate,
    BowelRecordResponse,
    BowelRecordUpdate,
    ExerciseRecordCreate,
    ExerciseRecordResponse,
    ExerciseRecordUpdate,
    MeasurementMetric,
    MeasurementRecordCreate,
    MeasurementRecordResponse,
    MeasurementRecordUpdate,
    SleepRecordCreate,
    SleepRecordResponse,
    SleepRecordUpdate,
    TimeRange,
    TodayRecords,
    TrendResponse,
    WaterRecordCreate,
    WaterRecordResponse,
    WaterRecordUpdate,
    WeightRecordCreate,
    WeightRecordResponse,
    WeightRecordUpdate,
)
from app.schemas.common import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/body", tags=["body"])

StartDateQuery = Annotated[date | None, Query()]
EndDateQuery = Annotated[date | None, Query()]
PageQuery = Annotated[int, Query(ge=1)]
PageSizeQuery = Annotated[int, Query(ge=1, le=50)]
TargetDateQuery = Annotated[date, Query(alias="date")]


@router.get("/today", response_model=ApiResponse[TodayRecords], summary="查询指定日期的身体数据聚合")
async def today_records(
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
    target_date: TargetDateQuery,
):
    data = await service.get_today_records(target_date)
    return success(data.model_dump(mode="json"))


@router.get("/latest", response_model=ApiResponse[TodayRecords], summary="查询各类型最新身体数据")
async def latest_records(user: CurrentUserWithProfileDep, service: BodyServiceDep):
    data = await service.get_latest()
    return success(data.model_dump(mode="json"))


@router.get("/trends", response_model=ApiResponse[TrendResponse], summary="查询身体数据趋势")
async def trends(
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
    record_type: Annotated[BodyRecordType, Query(alias="type")],
    period: Annotated[TimeRange, Query()] = TimeRange.thirty_days,
    metric: Annotated[MeasurementMetric | None, Query()] = None,
):
    data = await service.get_trends(record_type, period, metric)
    return success(data.model_dump(mode="json"))


@router.post(
    "/weight",
    response_model=ApiResponse[WeightRecordResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建体重记录",
)
async def create_weight(
    payload: WeightRecordCreate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.create_weight(payload)
    return success(data.model_dump(mode="json"))


@router.get("/weight", response_model=PaginatedResponse[WeightRecordResponse], summary="查询体重记录")
async def list_weight(
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
    start_date: StartDateQuery = None,
    end_date: EndDateQuery = None,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 20,
):
    items, total = await service.list_weight(
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return paginated([item.model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


@router.put("/weight/{record_id}", response_model=ApiResponse[WeightRecordResponse], summary="更新体重记录")
async def update_weight(
    record_id: uuid.UUID,
    payload: WeightRecordUpdate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.update_weight(record_id, payload)
    return success(data.model_dump(mode="json"))


@router.delete("/weight/{record_id}", response_model=ApiResponse[object], summary="删除体重记录")
async def delete_weight(record_id: uuid.UUID, user: CurrentUserWithProfileDep, service: BodyServiceDep):
    await service.delete_weight(record_id)
    return success(None, message="删除成功")


@router.post(
    "/measurement",
    response_model=ApiResponse[MeasurementRecordResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建围度记录",
)
async def create_measurement(
    payload: MeasurementRecordCreate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.create_measurement(payload)
    return success(data.model_dump(mode="json"))


@router.get("/measurement", response_model=PaginatedResponse[MeasurementRecordResponse], summary="查询围度记录")
async def list_measurement(
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
    start_date: StartDateQuery = None,
    end_date: EndDateQuery = None,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 20,
):
    items, total = await service.list_measurement(
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return paginated([item.model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


@router.put(
    "/measurement/{record_id}",
    response_model=ApiResponse[MeasurementRecordResponse],
    summary="更新围度记录",
)
async def update_measurement(
    record_id: uuid.UUID,
    payload: MeasurementRecordUpdate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.update_measurement(record_id, payload)
    return success(data.model_dump(mode="json"))


@router.delete("/measurement/{record_id}", response_model=ApiResponse[object], summary="删除围度记录")
async def delete_measurement(record_id: uuid.UUID, user: CurrentUserWithProfileDep, service: BodyServiceDep):
    await service.delete_measurement(record_id)
    return success(None, message="删除成功")


@router.post(
    "/sleep",
    response_model=ApiResponse[SleepRecordResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建睡眠记录",
)
async def create_sleep(
    payload: SleepRecordCreate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.create_sleep(payload)
    return success(data.model_dump(mode="json"))


@router.get("/sleep", response_model=PaginatedResponse[SleepRecordResponse], summary="查询睡眠记录")
async def list_sleep(
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
    start_date: StartDateQuery = None,
    end_date: EndDateQuery = None,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 20,
):
    items, total = await service.list_sleep(
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return paginated([item.model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


@router.put("/sleep/{record_id}", response_model=ApiResponse[SleepRecordResponse], summary="更新睡眠记录")
async def update_sleep(
    record_id: uuid.UUID,
    payload: SleepRecordUpdate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.update_sleep(record_id, payload)
    return success(data.model_dump(mode="json"))


@router.delete("/sleep/{record_id}", response_model=ApiResponse[object], summary="删除睡眠记录")
async def delete_sleep(record_id: uuid.UUID, user: CurrentUserWithProfileDep, service: BodyServiceDep):
    await service.delete_sleep(record_id)
    return success(None, message="删除成功")


@router.post(
    "/exercise",
    response_model=ApiResponse[ExerciseRecordResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建运动记录",
)
async def create_exercise(
    payload: ExerciseRecordCreate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.create_exercise(payload)
    return success(data.model_dump(mode="json"))


@router.get("/exercise", response_model=PaginatedResponse[ExerciseRecordResponse], summary="查询运动记录")
async def list_exercise(
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
    start_date: StartDateQuery = None,
    end_date: EndDateQuery = None,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 20,
):
    items, total = await service.list_exercise(
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return paginated([item.model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


@router.put("/exercise/{record_id}", response_model=ApiResponse[ExerciseRecordResponse], summary="更新运动记录")
async def update_exercise(
    record_id: uuid.UUID,
    payload: ExerciseRecordUpdate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.update_exercise(record_id, payload)
    return success(data.model_dump(mode="json"))


@router.delete("/exercise/{record_id}", response_model=ApiResponse[object], summary="删除运动记录")
async def delete_exercise(record_id: uuid.UUID, user: CurrentUserWithProfileDep, service: BodyServiceDep):
    await service.delete_exercise(record_id)
    return success(None, message="删除成功")


@router.post(
    "/water",
    response_model=ApiResponse[WaterRecordResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建或累加饮水记录",
)
async def create_water(
    payload: WaterRecordCreate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.create_water(payload)
    return success(data.model_dump(mode="json"))


@router.get("/water", response_model=PaginatedResponse[WaterRecordResponse], summary="查询饮水记录")
async def list_water(
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
    start_date: StartDateQuery = None,
    end_date: EndDateQuery = None,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 20,
):
    items, total = await service.list_water(
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return paginated([item.model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


@router.put("/water/{record_id}", response_model=ApiResponse[WaterRecordResponse], summary="设置饮水记录")
async def update_water(
    record_id: uuid.UUID,
    payload: WaterRecordUpdate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.update_water(record_id, payload)
    return success(data.model_dump(mode="json"))


@router.delete("/water/{record_id}", response_model=ApiResponse[object], summary="删除饮水记录")
async def delete_water(record_id: uuid.UUID, user: CurrentUserWithProfileDep, service: BodyServiceDep):
    await service.delete_water(record_id)
    return success(None, message="删除成功")


@router.post(
    "/bowel",
    response_model=ApiResponse[BowelRecordResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建排便记录",
)
async def create_bowel(
    payload: BowelRecordCreate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.create_bowel(payload)
    return success(data.model_dump(mode="json"))


@router.get("/bowel", response_model=PaginatedResponse[BowelRecordResponse], summary="查询排便记录")
async def list_bowel(
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
    start_date: StartDateQuery = None,
    end_date: EndDateQuery = None,
    page: PageQuery = 1,
    page_size: PageSizeQuery = 20,
):
    items, total = await service.list_bowel(
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return paginated([item.model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


@router.put("/bowel/{record_id}", response_model=ApiResponse[BowelRecordResponse], summary="更新排便记录")
async def update_bowel(
    record_id: uuid.UUID,
    payload: BowelRecordUpdate,
    user: CurrentUserWithProfileDep,
    service: BodyServiceDep,
):
    data = await service.update_bowel(record_id, payload)
    return success(data.model_dump(mode="json"))


@router.delete("/bowel/{record_id}", response_model=ApiResponse[object], summary="删除排便记录")
async def delete_bowel(record_id: uuid.UUID, user: CurrentUserWithProfileDep, service: BodyServiceDep):
    await service.delete_bowel(record_id)
    return success(None, message="删除成功")


__all__ = ["router"]


