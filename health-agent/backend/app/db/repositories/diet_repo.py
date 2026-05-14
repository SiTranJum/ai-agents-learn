"""饮食记录 Repository。"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.diet import DietItem, DietRecord

MEAL_SORT_ORDER = {
    "breakfast": 1,
    "lunch": 2,
    "dinner": 3,
    "snack": 4,
}


class DietRepository:
    """按 user_id 隔离的饮食记录仓储。"""

    def __init__(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        self.session = session
        self.user_id = user_id

    def _base_stmt(self) -> Select[tuple[DietRecord]]:
        return (
            select(DietRecord)
            .options(selectinload(DietRecord.items))
            .where(DietRecord.user_id == self.user_id, DietRecord.deleted_at.is_(None))
        )

    async def create_record(
        self,
        *,
        meal_type: str,
        record_date: date,
        items: list[DietItem],
    ) -> DietRecord:
        record = DietRecord(
            user_id=self.user_id,
            meal_type=meal_type,
            date=record_date,
            items=items,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_record(self, record_id: uuid.UUID) -> DietRecord | None:
        stmt = self._base_stmt().where(DietRecord.id == record_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_records(
        self,
        *,
        start_date: date,
        end_date: date,
        meal_type: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[DietRecord]:
        stmt = self._base_stmt().where(DietRecord.date >= start_date, DietRecord.date <= end_date)
        if meal_type:
            stmt = stmt.where(DietRecord.meal_type == meal_type)
        stmt = stmt.order_by(DietRecord.date.desc(), DietRecord.meal_type.asc()).offset(offset).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def count_records(
        self,
        *,
        start_date: date,
        end_date: date,
        meal_type: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(DietRecord).where(
            DietRecord.user_id == self.user_id,
            DietRecord.deleted_at.is_(None),
            DietRecord.date >= start_date,
            DietRecord.date <= end_date,
        )
        if meal_type:
            stmt = stmt.where(DietRecord.meal_type == meal_type)
        return int((await self.session.execute(stmt)).scalar_one())

    async def replace_items(self, record: DietRecord, items: list[DietItem]) -> DietRecord:
        record.items.clear()
        await self.session.flush()
        record.items.extend(items)
        await self.session.flush()
        return record

    async def soft_delete(self, record: DietRecord) -> None:
        record.deleted_at = datetime.now(UTC)
        await self.session.flush()

    async def soft_delete_by_date_meal(self, record_date: date, meal_type: str) -> int:
        """软删除指定日期+餐次的所有记录，返回删除数量。"""
        stmt = self._base_stmt().where(
            DietRecord.date == record_date,
            DietRecord.meal_type == meal_type,
        )
        records = list((await self.session.execute(stmt)).scalars().all())
        now_utc = datetime.now(UTC)
        for record in records:
            record.deleted_at = now_utc
        await self.session.flush()
        return len(records)


__all__ = ["MEAL_SORT_ORDER", "DietRepository"]
