"""Phase 5 - BodyService 单元测试。"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest

from app.db.models.body import WaterRecord, WeightRecord
from app.schemas.body import BodyRecordType, TimeRange, WaterRecordCreate, WeightRecordCreate
from app.services.body_service import BodyService


class _FakeSession:
    async def commit(self) -> None:
        return None


class _FakeRepo:
    def __init__(self) -> None:
        self.session = _FakeSession()
        self.weight_records: list[WeightRecord] = []
        self.water: WaterRecord | None = None

    async def create_weight(self, record: WeightRecord) -> WeightRecord:
        record.id = uuid.uuid4()
        record.user_id = uuid.uuid4()
        record.created_at = datetime.now(UTC)
        record.updated_at = datetime.now(UTC)
        self.weight_records.append(record)
        return record

    async def list_weight(self, **kwargs) -> list[WeightRecord]:
        start_date: date | None = kwargs.get("start_date")
        end_date: date | None = kwargs.get("end_date")
        records = self.weight_records
        if start_date is not None:
            records = [record for record in records if record.date >= start_date]
        if end_date is not None:
            records = [record for record in records if record.date <= end_date]
        return sorted(records, key=lambda record: record.date)

    async def count_weight(self, **kwargs) -> int:
        return len(await self.list_weight(**kwargs))

    async def get_water_by_date(self, target_date: date) -> WaterRecord | None:
        if self.water is not None and self.water.date == target_date:
            return self.water
        return None

    async def create_water(self, record: WaterRecord) -> WaterRecord:
        record.id = uuid.uuid4()
        record.user_id = uuid.uuid4()
        record.created_at = datetime.now(UTC)
        record.updated_at = datetime.now(UTC)
        self.water = record
        return record


@pytest.mark.asyncio
async def test_create_weight_calculates_bmi_and_trend_statistics() -> None:
    repo = _FakeRepo()
    service = BodyService(repo=repo, height_cm=170, target_weight=60)  # type: ignore[arg-type]

    for index, weight in enumerate([70.0, 69.5, 69.0]):
        await service.create_weight(
            WeightRecordCreate(date=date(2026, 5, 1 + index), weight=weight)
        )

    latest = await service.create_weight(WeightRecordCreate(date=date(2026, 5, 4), weight=68.5))
    trend = await service.get_trends(BodyRecordType.weight, TimeRange.thirty_days)

    assert latest.bmi == 23.7
    assert trend.statistics.latest == 68.5
    assert trend.statistics.change == -1.5
    assert trend.target == 60


@pytest.mark.asyncio
async def test_create_water_upserts_same_day_amount() -> None:
    repo = _FakeRepo()
    service = BodyService(repo=repo)  # type: ignore[arg-type]

    first = await service.create_water(
        WaterRecordCreate(date=date(2026, 5, 9), amount=300, target=2000)
    )
    second = await service.create_water(
        WaterRecordCreate(date=date(2026, 5, 9), amount=500, target=2200)
    )

    assert first.amount == 300
    assert second.id == first.id
    assert second.amount == 800
    assert second.target == 2200


def test_sleep_duration_supports_cross_day() -> None:
    assert BodyService.calculate_sleep_duration("23:30", "07:00") == 450
    assert BodyService.calculate_sleep_duration("01:00", "02:30") == 90


def test_detect_anomaly_requires_enough_history() -> None:
    assert BodyService._detect_anomaly(90, [70, 70.1, 69.9, 70.0]) is None
    assert BodyService._detect_anomaly(90, [70, 70.1, 69.9, 70.0, 70.2]) is not None


