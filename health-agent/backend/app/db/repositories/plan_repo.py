"""Plan repository."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.plan import (
    DailyTarget,
    Plan,
    PlanAdjustmentProposal,
    PlanAnalysis,
    PlanCheckIn,
    PlanExecution,
    PlanTarget,
    SubPlan,
)
from app.schemas.plan import ExecutionStatus, PlanStatus, ProposalStatus


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

    async def list_check_ins(self, plan_id: uuid.UUID, *, target_date: date | None = None) -> list[PlanCheckIn]:
        stmt = select(PlanCheckIn).where(
            PlanCheckIn.user_id == self.user_id,
            PlanCheckIn.plan_id == plan_id,
        )
        if target_date is not None:
            stmt = stmt.where(PlanCheckIn.date == target_date)
        stmt = stmt.order_by(PlanCheckIn.date.desc(), PlanCheckIn.created_at.desc())
        return list((await self.session.execute(stmt)).scalars().all())

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

    # ---------- 子计划 ----------

    async def list_sub_plans(self, plan_id: uuid.UUID) -> list[SubPlan]:
        stmt = select(SubPlan).where(
            SubPlan.user_id == self.user_id,
            SubPlan.plan_id == plan_id,
            SubPlan.deleted_at.is_(None),
        ).order_by(SubPlan.created_at.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_sub_plan(self, sub_plan_id: uuid.UUID) -> SubPlan | None:
        stmt = select(SubPlan).where(
            SubPlan.user_id == self.user_id,
            SubPlan.id == sub_plan_id,
            SubPlan.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_sub_plan(self, sub_plan: SubPlan) -> SubPlan:
        sub_plan.user_id = self.user_id
        self.session.add(sub_plan)
        await self.session.flush()
        return sub_plan

    # ---------- 每日目标曲线 ----------

    async def replace_daily_targets(
        self, sub_plan_id: uuid.UUID, targets: list[DailyTarget]
    ) -> None:
        """重写某子计划的目标曲线（先全部物理删除再批量插入）。"""
        from sqlalchemy import delete  # noqa: PLC0415 - lazily imported

        await self.session.execute(
            delete(DailyTarget).where(
                DailyTarget.user_id == self.user_id,
                DailyTarget.sub_plan_id == sub_plan_id,
            )
        )
        for target in targets:
            target.user_id = self.user_id
            self.session.add(target)
        await self.session.flush()

    async def list_daily_targets(
        self,
        plan_id: uuid.UUID,
        *,
        sub_plan_id: uuid.UUID | None = None,
        dimension: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[DailyTarget]:
        stmt = select(DailyTarget).where(
            DailyTarget.user_id == self.user_id,
            DailyTarget.plan_id == plan_id,
        )
        if sub_plan_id is not None:
            stmt = stmt.where(DailyTarget.sub_plan_id == sub_plan_id)
        if dimension is not None:
            stmt = stmt.where(cast(Any, DailyTarget.dimension) == dimension)
        if start_date is not None:
            stmt = stmt.where(DailyTarget.date >= start_date)
        if end_date is not None:
            stmt = stmt.where(DailyTarget.date <= end_date)
        stmt = stmt.order_by(DailyTarget.date.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    # ---------- AI 分析 ----------

    async def upsert_analysis(self, analysis: PlanAnalysis) -> PlanAnalysis:
        existing = (
            await self.session.execute(
                select(PlanAnalysis).where(
                    PlanAnalysis.user_id == self.user_id,
                    PlanAnalysis.plan_id == analysis.plan_id,
                    PlanAnalysis.analysis_date == analysis.analysis_date,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            analysis.user_id = self.user_id
            self.session.add(analysis)
            await self.session.flush()
            return analysis
        existing.overall_compliance = analysis.overall_compliance
        existing.dimension_compliance = analysis.dimension_compliance
        existing.has_anomaly = analysis.has_anomaly
        existing.summary = analysis.summary
        await self.session.flush()
        return existing

    async def list_analyses(
        self, plan_id: uuid.UUID, *, limit: int = 30
    ) -> list[PlanAnalysis]:
        stmt = (
            select(PlanAnalysis)
            .where(PlanAnalysis.user_id == self.user_id, PlanAnalysis.plan_id == plan_id)
            .order_by(PlanAnalysis.analysis_date.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    # ---------- 调整提议 ----------

    async def create_proposal(self, proposal: PlanAdjustmentProposal) -> PlanAdjustmentProposal:
        proposal.user_id = self.user_id
        self.session.add(proposal)
        await self.session.flush()
        return proposal

    async def get_proposal(self, proposal_id: uuid.UUID) -> PlanAdjustmentProposal | None:
        stmt = select(PlanAdjustmentProposal).where(
            PlanAdjustmentProposal.user_id == self.user_id,
            PlanAdjustmentProposal.id == proposal_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_proposals(
        self,
        plan_id: uuid.UUID,
        *,
        status: ProposalStatus | None = None,
    ) -> list[PlanAdjustmentProposal]:
        stmt = select(PlanAdjustmentProposal).where(
            PlanAdjustmentProposal.user_id == self.user_id,
            PlanAdjustmentProposal.plan_id == plan_id,
        )
        if status is not None:
            stmt = stmt.where(cast(Any, PlanAdjustmentProposal.status) == status.value)
        stmt = stmt.order_by(PlanAdjustmentProposal.created_at.desc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def expire_pending_proposals(
        self, plan_id: uuid.UUID, *, keep_id: uuid.UUID | None = None
    ) -> None:
        """每日检查触发新提议时，把旧的 pending 置为 expired（不留痕）。"""
        stmt = select(PlanAdjustmentProposal).where(
            PlanAdjustmentProposal.user_id == self.user_id,
            PlanAdjustmentProposal.plan_id == plan_id,
            cast(Any, PlanAdjustmentProposal.status) == ProposalStatus.pending.value,
        )
        if keep_id is not None:
            stmt = stmt.where(PlanAdjustmentProposal.id != keep_id)
        proposals = (await self.session.execute(stmt)).scalars().all()
        now = datetime.now(UTC)
        for proposal in proposals:
            proposal.status = ProposalStatus.expired.value
            proposal.resolved_at = now
        await self.session.flush()


__all__ = ["PlanRepository"]



