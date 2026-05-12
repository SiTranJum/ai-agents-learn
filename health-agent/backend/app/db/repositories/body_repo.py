"""身体数据追踪 Repository。"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.body import (
    BowelRecord,
    ExerciseRecord,
    MeasurementRecord,
    SleepRecord,
    WaterRecord,
    WeightRecord,
)


class BodyRepository:
    """按 ``user_id`` 隔离的身体数据仓储。"""

    def __init__(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        self.session = session
        self.user_id = user_id

    def _weight_stmt(self) -> Select[tuple[WeightRecord]]:
        return select(WeightRecord).where(
            WeightRecord.user_id == self.user_id,
            WeightRecord.deleted_at.is_(None),
        )

    def _measurement_stmt(self) -> Select[tuple[MeasurementRecord]]:
        return select(MeasurementRecord).where(
            MeasurementRecord.user_id == self.user_id,
            MeasurementRecord.deleted_at.is_(None),
        )

    def _sleep_stmt(self) -> Select[tuple[SleepRecord]]:
        return select(SleepRecord).where(
            SleepRecord.user_id == self.user_id,
            SleepRecord.deleted_at.is_(None),
        )

    def _exercise_stmt(self) -> Select[tuple[ExerciseRecord]]:
        return select(ExerciseRecord).where(
            ExerciseRecord.user_id == self.user_id,
            ExerciseRecord.deleted_at.is_(None),
        )

    def _water_stmt(self) -> Select[tuple[WaterRecord]]:
        return select(WaterRecord).where(
            WaterRecord.user_id == self.user_id,
            WaterRecord.deleted_at.is_(None),
        )

    def _bowel_stmt(self) -> Select[tuple[BowelRecord]]:
        return select(BowelRecord).where(
            BowelRecord.user_id == self.user_id,
            BowelRecord.deleted_at.is_(None),
        )

    async def create_weight(self, record: WeightRecord) -> WeightRecord:
        record.user_id = self.user_id
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_weight(self, record_id: uuid.UUID) -> WeightRecord | None:
        return (
            await self.session.execute(self._weight_stmt().where(WeightRecord.id == record_id))
        ).scalar_one_or_none()

    async def list_weight(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 20,
        ascending: bool = False,
    ) -> list[WeightRecord]:
        stmt = self._apply_date_range(self._weight_stmt(), WeightRecord.date, start_date, end_date)
        stmt = stmt.order_by(WeightRecord.date.asc() if ascending else WeightRecord.date.desc(), WeightRecord.created_at.desc())
        return list((await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all())

    async def count_weight(self, *, start_date: date | None = None, end_date: date | None = None) -> int:
        stmt = select(func.count()).select_from(WeightRecord).where(
            WeightRecord.user_id == self.user_id,
            WeightRecord.deleted_at.is_(None),
        )
        stmt = self._apply_date_range(stmt, WeightRecord.date, start_date, end_date)
        return int((await self.session.execute(stmt)).scalar_one())

    async def latest_weight(self, target_date: date | None = None) -> WeightRecord | None:
        stmt = self._weight_stmt()
        if target_date is not None:
            stmt = stmt.where(WeightRecord.date == target_date)
        stmt = stmt.order_by(WeightRecord.date.desc(), WeightRecord.created_at.desc()).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_measurement(self, record: MeasurementRecord) -> MeasurementRecord:
        record.user_id = self.user_id
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_measurement(self, record_id: uuid.UUID) -> MeasurementRecord | None:
        return (
            await self.session.execute(self._measurement_stmt().where(MeasurementRecord.id == record_id))
        ).scalar_one_or_none()

    async def list_measurement(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 20,
        ascending: bool = False,
    ) -> list[MeasurementRecord]:
        stmt = self._apply_date_range(self._measurement_stmt(), MeasurementRecord.date, start_date, end_date)
        stmt = stmt.order_by(MeasurementRecord.date.asc() if ascending else MeasurementRecord.date.desc(), MeasurementRecord.created_at.desc())
        return list((await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all())

    async def count_measurement(self, *, start_date: date | None = None, end_date: date | None = None) -> int:
        stmt = select(func.count()).select_from(MeasurementRecord).where(
            MeasurementRecord.user_id == self.user_id,
            MeasurementRecord.deleted_at.is_(None),
        )
        stmt = self._apply_date_range(stmt, MeasurementRecord.date, start_date, end_date)
        return int((await self.session.execute(stmt)).scalar_one())

    async def latest_measurement(self, target_date: date | None = None) -> MeasurementRecord | None:
        stmt = self._measurement_stmt()
        if target_date is not None:
            stmt = stmt.where(MeasurementRecord.date == target_date)
        stmt = stmt.order_by(MeasurementRecord.date.desc(), MeasurementRecord.created_at.desc()).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_sleep(self, record: SleepRecord) -> SleepRecord:
        record.user_id = self.user_id
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_sleep(self, record_id: uuid.UUID) -> SleepRecord | None:
        return (
            await self.session.execute(self._sleep_stmt().where(SleepRecord.id == record_id))
        ).scalar_one_or_none()

    async def list_sleep(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 20,
        ascending: bool = False,
    ) -> list[SleepRecord]:
        stmt = self._apply_date_range(self._sleep_stmt(), SleepRecord.date, start_date, end_date)
        stmt = stmt.order_by(SleepRecord.date.asc() if ascending else SleepRecord.date.desc(), SleepRecord.created_at.desc())
        return list((await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all())

    async def count_sleep(self, *, start_date: date | None = None, end_date: date | None = None) -> int:
        stmt = select(func.count()).select_from(SleepRecord).where(
            SleepRecord.user_id == self.user_id,
            SleepRecord.deleted_at.is_(None),
        )
        stmt = self._apply_date_range(stmt, SleepRecord.date, start_date, end_date)
        return int((await self.session.execute(stmt)).scalar_one())

    async def latest_sleep(self, target_date: date | None = None) -> SleepRecord | None:
        stmt = self._sleep_stmt()
        if target_date is not None:
            stmt = stmt.where(SleepRecord.date == target_date)
        stmt = stmt.order_by(SleepRecord.date.desc(), SleepRecord.created_at.desc()).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_exercise(self, record: ExerciseRecord) -> ExerciseRecord:
        record.user_id = self.user_id
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_exercise(self, record_id: uuid.UUID) -> ExerciseRecord | None:
        return (
            await self.session.execute(self._exercise_stmt().where(ExerciseRecord.id == record_id))
        ).scalar_one_or_none()

    async def list_exercise(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 20,
        ascending: bool = False,
    ) -> list[ExerciseRecord]:
        stmt = self._apply_date_range(self._exercise_stmt(), ExerciseRecord.date, start_date, end_date)
        stmt = stmt.order_by(ExerciseRecord.date.asc() if ascending else ExerciseRecord.date.desc(), ExerciseRecord.created_at.desc())
        return list((await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all())

    async def count_exercise(self, *, start_date: date | None = None, end_date: date | None = None) -> int:
        stmt = select(func.count()).select_from(ExerciseRecord).where(
            ExerciseRecord.user_id == self.user_id,
            ExerciseRecord.deleted_at.is_(None),
        )
        stmt = self._apply_date_range(stmt, ExerciseRecord.date, start_date, end_date)
        return int((await self.session.execute(stmt)).scalar_one())

    async def latest_exercise(self, target_date: date | None = None) -> ExerciseRecord | None:
        stmt = self._exercise_stmt()
        if target_date is not None:
            stmt = stmt.where(ExerciseRecord.date == target_date)
        stmt = stmt.order_by(ExerciseRecord.date.desc(), ExerciseRecord.created_at.desc()).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_water_by_date(self, target_date: date) -> WaterRecord | None:
        return (
            await self.session.execute(self._water_stmt().where(WaterRecord.date == target_date))
        ).scalar_one_or_none()

    async def create_water(self, record: WaterRecord) -> WaterRecord:
        record.user_id = self.user_id
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_water(self, record_id: uuid.UUID) -> WaterRecord | None:
        return (
            await self.session.execute(self._water_stmt().where(WaterRecord.id == record_id))
        ).scalar_one_or_none()

    async def list_water(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 20,
        ascending: bool = False,
    ) -> list[WaterRecord]:
        stmt = self._apply_date_range(self._water_stmt(), WaterRecord.date, start_date, end_date)
        stmt = stmt.order_by(WaterRecord.date.asc() if ascending else WaterRecord.date.desc(), WaterRecord.created_at.desc())
        return list((await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all())

    async def count_water(self, *, start_date: date | None = None, end_date: date | None = None) -> int:
        stmt = select(func.count()).select_from(WaterRecord).where(
            WaterRecord.user_id == self.user_id,
            WaterRecord.deleted_at.is_(None),
        )
        stmt = self._apply_date_range(stmt, WaterRecord.date, start_date, end_date)
        return int((await self.session.execute(stmt)).scalar_one())

    async def latest_water(self, target_date: date | None = None) -> WaterRecord | None:
        stmt = self._water_stmt()
        if target_date is not None:
            stmt = stmt.where(WaterRecord.date == target_date)
        stmt = stmt.order_by(WaterRecord.date.desc(), WaterRecord.created_at.desc()).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_bowel(self, record: BowelRecord) -> BowelRecord:
        record.user_id = self.user_id
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_bowel(self, record_id: uuid.UUID) -> BowelRecord | None:
        return (
            await self.session.execute(self._bowel_stmt().where(BowelRecord.id == record_id))
        ).scalar_one_or_none()

    async def list_bowel(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 20,
        ascending: bool = False,
    ) -> list[BowelRecord]:
        stmt = self._apply_date_range(self._bowel_stmt(), BowelRecord.date, start_date, end_date)
        stmt = stmt.order_by(BowelRecord.date.asc() if ascending else BowelRecord.date.desc(), BowelRecord.created_at.desc())
        return list((await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all())

    async def count_bowel(self, *, start_date: date | None = None, end_date: date | None = None) -> int:
        stmt = select(func.count()).select_from(BowelRecord).where(
            BowelRecord.user_id == self.user_id,
            BowelRecord.deleted_at.is_(None),
        )
        stmt = self._apply_date_range(stmt, BowelRecord.date, start_date, end_date)
        return int((await self.session.execute(stmt)).scalar_one())

    async def latest_bowel(self, target_date: date | None = None) -> BowelRecord | None:
        stmt = self._bowel_stmt()
        if target_date is not None:
            stmt = stmt.where(BowelRecord.date == target_date)
        stmt = stmt.order_by(BowelRecord.date.desc(), BowelRecord.created_at.desc()).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def soft_delete(self, record: object) -> None:
        if hasattr(record, "deleted_at"):
            record.deleted_at = datetime.now(UTC)
        await self.session.flush()

    @staticmethod
    def _apply_date_range(stmt, date_column, start_date: date | None, end_date: date | None):
        if start_date is not None:
            stmt = stmt.where(date_column >= start_date)
        if end_date is not None:
            stmt = stmt.where(date_column <= end_date)
        return stmt


__all__ = ["BodyRepository"]

