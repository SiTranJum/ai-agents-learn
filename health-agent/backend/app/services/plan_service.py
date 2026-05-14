"""Plan service.

This service is deterministic: CRUD, validation, BMR and progress calculation only.
LLM orchestration belongs to ``app.agents.plan``.
"""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.db.models.plan import Plan, PlanCheckIn, PlanExecution, PlanTarget
from app.db.repositories.plan_repo import PlanRepository
from app.schemas.diet import NutritionSummary
from app.schemas.plan import (
    CheckInCreate,
    CheckInResponse,
    DailyExecution,
    ExecutionStatus,
    PlanDraft,
    PlanProgress,
    PlanResponse,
    PlanStatus,
    PlanTargets,
    PlanTask,
    PlanTaskUpdate,
    PlanType,
    PlanUpdate,
)


class PlanService:
    """Plan CRUD and deterministic calculations. No LLM calls here."""

    def __init__(self, repo: PlanRepository, *, profile: object | None = None) -> None:
        self.repo = repo
        self.profile = profile

    async def has_active_plan(self) -> bool:
        return await self.repo.has_active_plan()

    async def create_plan_from_draft(self, draft: PlanDraft) -> PlanResponse:
        if await self.has_active_plan():
            raise ConflictException("已有活跃计划", code="PLAN_ALREADY_ACTIVE")
        violations = self.safety_check(draft, self.profile)
        if violations:
            raise ValidationException("计划安全校验失败", code=violations[0], details=[{"reason": item} for item in violations])
        plan = Plan(
            name=draft.name,
            goal_description=draft.goal_description,
            plan_type=draft.plan_type.value,
            status=PlanStatus.active.value,
            start_date=draft.start_date,
            target_date=draft.target_date,
            tasks=[self._task_to_json(task) for task in draft.tasks],
        )
        target = PlanTarget(**draft.targets.model_dump())
        created = await self.repo.create_plan(plan, target)
        await self.repo.session.commit()
        return await self._response(created)

    async def get_plan(self, plan_id: uuid.UUID) -> PlanResponse:
        plan = await self._get_plan_or_404(plan_id)
        return await self._response(plan)

    async def list_plans(
        self,
        *,
        status: PlanStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PlanResponse], int]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 50)
        plans = await self.repo.list_plans(status=status, offset=(page - 1) * page_size, limit=page_size)
        total = await self.repo.count_plans(status=status)
        return [await self._response(plan) for plan in plans], total

    async def update_plan(self, plan_id: uuid.UUID, data: PlanUpdate) -> PlanResponse:
        plan = await self._get_plan_or_404(plan_id)
        if plan.status != PlanStatus.active.value:
            raise ValidationException("计划不可修改", code="PLAN_NOT_MODIFIABLE")
        target = await self.repo.get_target(plan.id)
        if target is None:
            target = PlanTarget(user_id=self.repo.user_id, plan_id=plan.id)
            self.repo.session.add(target)
        if data.target_date is not None:
            plan.target_date = data.target_date
        for field in ["daily_calories", "protein_target", "fat_target", "carbs_target", "weight_target"]:
            value = getattr(data, field)
            if value is not None:
                setattr(target, field, value)
        if data.tasks is not None:
            plan.tasks = [self._task_to_json(task) for task in data.tasks]
        draft = PlanDraft(
            name=plan.name,
            goal_description=plan.goal_description,
            plan_type=PlanType(plan.plan_type),
            start_date=plan.start_date,
            target_date=plan.target_date,
            targets=PlanTargets(
                daily_calories=target.daily_calories,
                protein_target=target.protein_target,
                fat_target=target.fat_target,
                carbs_target=target.carbs_target,
                weight_target=target.weight_target,
            ),
            tasks=[PlanTaskUpdate(**task) for task in plan.tasks],
        )
        violations = self.safety_check(draft, self.profile)
        if violations:
            raise ValidationException("计划安全校验失败", code=violations[0], details=[{"reason": item} for item in violations])
        await self.repo.session.commit()
        return await self._response(plan)

    async def terminate_plan(self, plan_id: uuid.UUID, reason: str | None = None) -> None:
        plan = await self.repo.get_plan(plan_id)
        if plan is None:
            return
        if plan.status != PlanStatus.terminated.value:
            await self.repo.soft_terminate(plan, reason)
            await self.repo.session.commit()

    async def create_check_in(self, plan_id: uuid.UUID, data: CheckInCreate) -> CheckInResponse:
        plan = await self._get_plan_or_404(plan_id)
        if await self.repo.check_in_exists(plan.id, data.task_id, data.date):
            raise ConflictException("当天已打卡", code="CHECK_IN_DUPLICATE")
        check_in = await self.repo.create_check_in(
            PlanCheckIn(
                plan_id=plan.id,
                task_id=data.task_id,
                date=data.date,
                completed=data.completed,
                note=data.note,
            )
        )
        await self.repo.session.commit()
        return self._check_in_response(check_in)

    async def get_progress(self, plan_id: uuid.UUID) -> PlanProgress:
        plan = await self._get_plan_or_404(plan_id)
        records = await self.repo.list_executions(plan.id, desc=False, offset=0, limit=500)
        total_days = max((plan.target_date - plan.start_date).days + 1, 1)
        today = date.today()
        elapsed_days = min(max((today - plan.start_date).days + 1, 0), total_days)
        on_track = [record for record in records if record.status == ExecutionStatus.on_track.value]
        compliance_rate = len(on_track) / elapsed_days if elapsed_days > 0 else 0
        return PlanProgress(
            plan_id=plan.id,
            total_days=total_days,
            elapsed_days=elapsed_days,
            compliance_rate=round(compliance_rate, 4),
            streak_days=self._streak_days(records),
            daily_records=[self._execution_response(record) for record in records],
        )

    async def list_execution_records(
        self,
        plan_id: uuid.UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        status: ExecutionStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DailyExecution], int]:
        plan = await self._get_plan_or_404(plan_id)
        page = max(page, 1)
        page_size = min(max(page_size, 1), 50)
        records = await self.repo.list_executions(
            plan.id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        total = await self.repo.count_executions(plan.id, start_date=start_date, end_date=end_date, status=status)
        return [self._execution_response(record) for record in records], total

    async def on_diet_record_created(
        self,
        record_date: date,
        nutrition_summary: NutritionSummary | None = None,
    ) -> None:
        """饮食记录变化后同步当天活跃计划执行记录。

        Phase 10 最小闭环：API 层在饮食创建后传入当天营养汇总，
        本方法按当前活跃计划目标计算 ``PlanExecution``，并用
        ``(plan_id, date)`` 幂等 upsert。
        """
        plan = await self.repo.get_active_plan()
        if plan is None:
            return
        target = await self.repo.get_target(plan.id)
        nutrition = nutrition_summary
        if nutrition is None:
            return
        calories_target = float(getattr(target, "daily_calories", None) or 0)
        execution = PlanExecution(
            plan_id=plan.id,
            date=record_date,
            calories_consumed=float(getattr(nutrition, "total_calories", 0) or 0),
            calories_target=calories_target,
            protein=float(getattr(nutrition, "total_protein", 0) or 0),
            fat=float(getattr(nutrition, "total_fat", 0) or 0),
            carbs=float(getattr(nutrition, "total_carbs", 0) or 0),
            status=self.calculate_execution_status(
                float(getattr(nutrition, "total_calories", 0) or 0),
                calories_target,
            ).value,
        )
        await self.repo.upsert_execution(execution)
        await self.repo.session.commit()

    async def run_modification_rules(self, plan_id: uuid.UUID) -> list[str]:
        """Return deterministic rule hits only; LLM suggestions stay in plan_agent."""
        plan = await self._get_plan_or_404(plan_id)
        records = await self.repo.list_executions(plan.id, offset=0, limit=7)
        if len([record for record in records[:5] if record.status == ExecutionStatus.missed.value]) >= 5:
            return ["连续 5 天未达标，建议调整目标或任务强度"]
        if date.today() > plan.target_date:
            return ["计划已超过目标日期，建议续期或终止"]
        return []

    @staticmethod
    def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
        base = 10 * weight_kg + 6.25 * height_cm - 5 * age
        return round(base + 5 if gender == "male" else base - 161, 1)

    @staticmethod
    def calculate_execution_status(consumed: float, target: float) -> ExecutionStatus:
        if target <= 0:
            return ExecutionStatus.missed
        deviation_rate = abs(consumed - target) / target
        if deviation_rate <= 0.10:
            return ExecutionStatus.on_track
        if deviation_rate <= 0.20:
            return ExecutionStatus.deviation
        return ExecutionStatus.missed

    def safety_check(self, draft: PlanDraft, profile: object | None) -> list[str]:
        violations: list[str] = []
        days = (draft.target_date - draft.start_date).days + 1
        if days < 7 or days > 168:
            violations.append("PLAN_DURATION_INVALID")
        bmr = self._profile_bmr(profile)
        if bmr is not None and draft.targets.daily_calories is not None and draft.targets.daily_calories < bmr:
            violations.append("CALORIES_BELOW_BMR")
        current_weight = self._profile_number(profile, "current_weight")
        if (
            draft.plan_type == PlanType.weight_loss
            and current_weight is not None
            and draft.targets.weight_target is not None
            and days > 0
        ):
            loss_per_week = (current_weight - draft.targets.weight_target) / (days / 7)
            if loss_per_week > 1:
                violations.append("WEIGHT_LOSS_TOO_FAST")
        return violations

    async def _get_plan_or_404(self, plan_id: uuid.UUID) -> Plan:
        plan = await self.repo.get_plan(plan_id)
        if plan is None:
            raise NotFoundException("计划不存在", code="PLAN_NOT_FOUND")
        return plan

    async def _response(self, plan: Plan) -> PlanResponse:
        target = await self.repo.get_target(plan.id)
        return PlanResponse(
            id=plan.id,
            name=plan.name,
            goal_description=plan.goal_description,
            plan_type=PlanType(plan.plan_type),
            status=PlanStatus(plan.status),
            start_date=plan.start_date,
            target_date=plan.target_date,
            targets=PlanTargets.model_validate(target, from_attributes=True) if target else PlanTargets(),
            tasks=[PlanTask(**task) for task in plan.tasks],
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    @staticmethod
    def _task_to_json(task: PlanTaskUpdate) -> dict[str, object]:
        task_id = task.id or uuid.uuid4()
        return {
            "id": str(task_id),
            "description": task.description,
            "frequency": task.frequency,
            "time_period": task.time_period,
        }

    @staticmethod
    def _check_in_response(check_in: PlanCheckIn) -> CheckInResponse:
        return CheckInResponse(
            id=check_in.id,
            plan_id=check_in.plan_id,
            task_id=check_in.task_id,
            date=check_in.date,
            completed=check_in.completed,
            note=check_in.note,
            created_at=check_in.created_at,
        )

    @staticmethod
    def _execution_response(record: PlanExecution) -> DailyExecution:
        return DailyExecution(
            id=record.id,
            date=record.date,
            calories_consumed=record.calories_consumed,
            calories_target=record.calories_target,
            protein=record.protein,
            fat=record.fat,
            carbs=record.carbs,
            status=ExecutionStatus(record.status),
        )

    @staticmethod
    def _streak_days(records: list[PlanExecution]) -> int:
        streak = 0
        for record in sorted(records, key=lambda item: item.date, reverse=True):
            if record.status != ExecutionStatus.on_track.value:
                break
            streak += 1
        return streak

    def _profile_bmr(self, profile: object | None) -> float | None:
        weight = self._profile_number(profile, "current_weight")
        height = self._profile_number(profile, "height")
        gender = getattr(profile, "gender", None) if profile is not None else None
        birth_date = getattr(profile, "birth_date", None) if profile is not None else None
        if weight is None or height is None or birth_date is None or gender not in {"male", "female"}:
            return None
        age = max(datetime.now(UTC).date().year - birth_date.year, 1)
        return self.calculate_bmr(weight, height, age, gender)

    @staticmethod
    def _profile_number(profile: object | None, field: str) -> float | None:
        value = getattr(profile, field, None) if profile is not None else None
        if isinstance(value, int | float | str):
            return float(value)
        return None


__all__ = ["PlanService"]






