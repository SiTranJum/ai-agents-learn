"""Phase 5 - 身体数据 API 测试。"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient

from app.dependencies import get_body_service, get_current_user_with_profile, get_memory_service
from app.main import app
from app.schemas.auth import CurrentUser
from app.schemas.body import (
    BodyRecordType,
    TimeRange,
    TodayRecords,
    TrendPoint,
    TrendResponse,
    TrendStatistics,
    WaterRecordResponse,
    WeightRecordResponse,
)


def _weight() -> WeightRecordResponse:
    return WeightRecordResponse(
        id=uuid.uuid4(),
        date=date(2026, 5, 9),
        weight=66.0,
        bmi=22.8,
        change=-0.2,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _water() -> WaterRecordResponse:
    return WaterRecordResponse(
        id=uuid.uuid4(),
        date=date(2026, 5, 9),
        amount=1800,
        target=2000,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class _FakeBodyService:
    async def create_weight(self, payload):
        return _weight().model_copy(update={"weight": payload.weight, "date": payload.date})

    async def list_weight(self, **kwargs):
        return [_weight()], 1

    async def create_water(self, payload):
        return _water().model_copy(update={"amount": payload.amount, "target": payload.target})

    async def get_today_records(self, target_date: date) -> TodayRecords:
        return TodayRecords(
            weight=_weight().model_copy(update={"date": target_date}),
            water=_water().model_copy(update={"date": target_date}),
        )

    async def get_trends(self, record_type, period, metric):
        return TrendResponse(
            type=record_type,
            period=period,
            metric="weight",
            data_points=[TrendPoint(date=date(2026, 5, 8), value=66.2), TrendPoint(date=date(2026, 5, 9), value=66.0)],
            statistics=TrendStatistics(min=66.0, max=66.2, average=66.1, latest=66.0, change=-0.2),
            target=60,
        )


class _FakeMemoryService:
    pass


@pytest.fixture
async def body_overrides():
    async def _current_user() -> CurrentUser:
        return CurrentUser(id=uuid.uuid4(), email="user@example.com", profile=object())

    async def _service() -> _FakeBodyService:
        return _FakeBodyService()

    async def _memory_service() -> _FakeMemoryService:
        return _FakeMemoryService()

    app.dependency_overrides[get_current_user_with_profile] = _current_user
    app.dependency_overrides[get_body_service] = _service
    app.dependency_overrides[get_memory_service] = _memory_service
    try:
        yield
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_weight_api(client: AsyncClient, body_overrides) -> None:
    resp = await client.post(
        "/api/v1/body/weight",
        json={"date": "2026-05-09", "weight": 66.0, "note": "空腹"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["weight"] == 66.0
    assert body["data"]["bmi"] == 22.8


@pytest.mark.asyncio
async def test_list_weight_api(client: AsyncClient, body_overrides) -> None:
    resp = await client.get("/api/v1/body/weight", params={"page": 1, "page_size": 20})

    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_water_post_uses_frontend_amount_target_fields(client: AsyncClient, body_overrides) -> None:
    resp = await client.post(
        "/api/v1/body/water",
        json={"date": "2026-05-09", "amount": 500, "target": 2200},
    )

    assert resp.status_code == 201
    assert resp.json()["data"]["amount"] == 500
    assert resp.json()["data"]["target"] == 2200


@pytest.mark.asyncio
async def test_today_records_api(client: AsyncClient, body_overrides) -> None:
    resp = await client.get("/api/v1/body/today", params={"date": "2026-05-09"})

    assert resp.status_code == 200
    assert resp.json()["data"]["weight"]["date"] == "2026-05-09"
    assert resp.json()["data"]["water"]["amount"] == 1800


@pytest.mark.asyncio
async def test_trends_api(client: AsyncClient, body_overrides) -> None:
    resp = await client.get(
        "/api/v1/body/trends",
        params={"type": BodyRecordType.weight.value, "period": TimeRange.thirty_days.value},
    )

    assert resp.status_code == 200
    assert resp.json()["data"]["statistics"]["change"] == -0.2

