"""Plan repository."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.plan import Plan, PlanCheckIn, PlanExecution, PlanTarget
from app.schemas.plan import ExecutionStatus, PlanStatus


class PlanRepository:
    """User-scoped plan repository."""

    def __init__(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def has_active_plan(self) -> bool:
        stmt = select(Plan.id).where(
            Plan.user_id == self.user_id,
            Plan.status == PlanStatus.active.value,
            Plan.deleted_at.is_(None),
        ).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    async def get_active_plan(self) -> Plan | None:
        stmt = select(Plan).where(
            Plan.user_id == self.user_id,
            Plan.status == PlanStatus.active.value,
            Plan.deleted_at.is_(None),
        ).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_plan(self, plan: Plan, target: PlanTarget) -> Plan:
        plan.user_id = self.user_id
        self.session.add(plan)
        await self.session.flush()
        target.user_id = self.user_id
        target.plan_id = plan.id
        self.session.add(target)
        await self.session.flush()
        return plan

    async def get_plan(self, plan_id: uuid.UUID) -> Plan | None:
        stmt = select(Plan).where(
            Plan.user_id == self.user_id,
            Plan.id == plan_id,
            Plan.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_target(self, plan_id: uuid.UUID) -> PlanTarget | None:
        stmt = select(PlanTarget).where(
            PlanTarget.user_id == self.user_id,
            PlanTarget.plan_id == plan_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_plans(
        self,
        *,
        status: PlanStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Plan]:
        stmt = select(Plan).where(Plan.user_id == self.user_id, Plan.deleted_at.is_(None))
        if status is not None:
            stmt = stmt.where(cast(Any, Plan.status) == status.value)
        stmt = stmt.order_by(Plan.created_at.desc()).offset(offset).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def count_plans(self, *, status: PlanStatus | None = None) -> int:
        stmt = select(func.count()).select_from(Plan).where(Plan.user_id == self.user_id, Plan.deleted_at.is_(None))
        if status is not None:
            stmt = stmt.where(cast(Any, Plan.status) == status.value)
        return int((await self.session.execute(stmt)).scalar_one())

    async def list_executions(
        self,
        plan_id: uuid.UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        status: ExecutionStatus | None = None,
        offset: int = 0,
        limit: int = 20,
        desc: bool = True,
    ) -> list[PlanExecution]:
        stmt = select(PlanExecution).where(
            PlanExecution.user_id == self.user_id,
            PlanExecution.plan_id == plan_id,
        )
        if start_date is not None:
            stmt = stmt.where(PlanExecution.date >= start_date)
        if end_date is not None:
            stmt = stmt.where(PlanExecution.date <= end_date)
        if status is not None:
            stmt = stmt.where(cast(Any, PlanExecution.status) == status.value)
        order_col = PlanExecution.date.desc() if desc else PlanExecution.date.asc()
        stmt = stmt.order_by(order_col).offset(offset).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_execution(self, plan_id: uuid.UUID, target_date: date) -> PlanExecution | None:
        stmt = select(PlanExecution).where(
            PlanExecution.user_id == self.user_id,
            PlanExecution.plan_id == plan_id,
            PlanExecution.date == target_date,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def upsert_execution(self, execution: PlanExecution) -> PlanExecution:
        existing = await self.get_execution(execution.plan_id, execution.date)
        if existing is None:
            execution.user_id = self.user_id
            self.session.add(execution)
            await self.session.flush()
            return execution
        existing.calories_consumed = execution.calories_consumed
        existing.calories_target = execution.calories_target
        existing.protein = execution.protein
        existing.fat = execution.fat
        existing.carbs = execution.carbs
        existing.status = execution.status
        await self.session.flush()
        return existing

    async def count_executions(
        self,
        plan_id: uuid.UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        status: ExecutionStatus | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(PlanExecution).where(
            PlanExecution.user_id == self.user_id,
            PlanExecution.plan_id == plan_id,
        )
        if start_date is not None:
            stmt = stmt.where(PlanExecution.date >= start_date)
        if end_date is not None:
            stmt = stmt.where(PlanExecution.date <= end_date)
        if status is not None:
            stmt = stmt.where(cast(Any, PlanExecution.status) == status.value)
        return int((await self.session.execute(stmt)).scalar_one())

    async def create_check_in(self, check_in: PlanCheckIn) -> PlanCheckIn:
        check_in.user_id = self.user_id
        self.session.add(check_in)
        await self.session.flush()
        return check_in

    async def check_in_exists(self, plan_id: uuid.UUID, task_id: uuid.UUID | None, target_date: date) -> bool:
        stmt = select(PlanCheckIn.id).where(
            PlanCheckIn.user_id == self.user_id,
            PlanCheckIn.plan_id == plan_id,
            PlanCheckIn.date == target_date,
        )
        if task_id is None:
            stmt = stmt.where(PlanCheckIn.task_id.is_(None))
        else:
            stmt = stmt.where(cast(Any, PlanCheckIn.task_id) == task_id)
        return (await self.session.execute(stmt.limit(1))).scalar_one_or_none() is not None

    async def soft_terminate(self, plan: Plan, reason: str | None = None) -> None:
        now = datetime.now(UTC)
        plan.status = PlanStatus.terminated.value
        plan.terminated_at = now
        plan.termination_reason = reason
        plan.deleted_at = now
        await self.session.flush()


__all__ = ["PlanRepository"]



