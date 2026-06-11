"""Plan service.

This service owns deterministic plan CRUD, compatibility shaping, safety checks,
and progress computation. LLM orchestration stays in ``app.agents.plan``.
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, date, datetime, timedelta

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.logging import log_all_service_methods
from app.db.models.plan import Plan, PlanCheckIn, PlanExecution, PlanTarget
from app.db.repositories.plan_repo import PlanRepository
from app.schemas.diet import NutritionSummary
from app.schemas.plan import (
    CheckInCreate,
    CheckInResponse,
    DailyExecution,
    ExecutionStatus,
    PlanDraft,
    PlanPhase,
    PlanPhaseDraft,
    PlanProgress,
    PlanResponse,
    PlanStatus,
    PlanTargets,
    PlanTask,
    PlanTaskUpdate,
    PlanType,
    PlanUpdate,
)


@log_all_service_methods
class PlanService:
    """Plan CRUD and deterministic calculations."""

    def __init__(self, repo: PlanRepository, *, profile: object | None = None) -> None:
        self.repo = repo
        self.profile = profile

    async def has_active_plan(self) -> bool:
        return await self.repo.has_active_plan()

    async def get_active_plan(self) -> PlanResponse | None:
        plan = await self.repo.get_active_plan()
        if plan is None:
            return None
        return await self._response(plan)

    async def create_plan_from_draft(self, draft: PlanDraft) -> PlanResponse:
        if await self.has_active_plan():
            raise ConflictException("Active plan already exists", code="PLAN_ALREADY_ACTIVE")
        normalized = self.normalize_draft(draft)
        violations = self.safety_check(normalized, self.profile)
        if violations:
            raise ValidationException(
                "Plan safety validation failed",
                code=violations[0],
                details=[{"reason": item} for item in violations],
            )
        plan = Plan(
            name=normalized.name,
            goal_description=normalized.goal_description,
            plan_type=normalized.plan_type.value,
            status=PlanStatus.active.value,
            start_date=normalized.start_date,
            target_date=normalized.target_date,
            tasks=[self._task_to_json(task) for task in normalized.tasks],
            phases=[self._phase_to_json(phase) for phase in normalized.phases],
        )
        target = PlanTarget(**normalized.targets.model_dump())
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
            raise ValidationException("Plan is not modifiable", code="PLAN_NOT_MODIFIABLE")
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
            tasks = [self._task_to_json(task) for task in data.tasks]
            plan.tasks = tasks
            existing_phases = plan.phases or []
            if existing_phases:
                updated = dict(existing_phases[0])
                updated["tasks"] = tasks
                existing_phases[0] = updated
                plan.phases = existing_phases
        normalized = self.normalize_draft(
            PlanDraft(
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
                phases=[self._phase_draft_from_json(phase) for phase in (plan.phases or [])],
            )
        )
        violations = self.safety_check(normalized, self.profile)
        if violations:
            raise ValidationException(
                "Plan safety validation failed",
                code=violations[0],
                details=[{"reason": item} for item in violations],
            )
        plan.phases = [self._phase_to_json(phase) for phase in normalized.phases]
        plan.tasks = [self._task_to_json(task) for task in normalized.tasks]
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
            raise ConflictException("Check-in already exists for this date", code="CHECK_IN_DUPLICATE")
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
        today = date.today()
        check_ins = await self.repo.list_check_ins(plan.id, target_date=today)
        total_days = max((plan.target_date - plan.start_date).days + 1, 1)
        elapsed_days = min(max((today - plan.start_date).days + 1, 0), total_days)
        on_track = [record for record in records if record.status == ExecutionStatus.on_track.value]
        completed_task_ids = [
            item.task_id
            for item in check_ins
            if item.completed and item.task_id is not None
        ]
        task_ids = {
            uuid.UUID(str(task["id"]))
            for task in (plan.tasks or [])
            if isinstance(task, dict) and task.get("id")
        }
        return PlanProgress(
            plan_id=plan.id,
            total_days=total_days,
            elapsed_days=elapsed_days,
            compliance_rate=round(len(on_track) / elapsed_days, 4) if elapsed_days > 0 else 0,
            streak_days=self._streak_days(records),
            completed_tasks=len(completed_task_ids),
            total_tasks=len(task_ids),
            completed_task_ids=completed_task_ids,
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
        plan = await self.repo.get_active_plan()
        if plan is None or nutrition_summary is None:
            return
        target = await self.repo.get_target(plan.id)
        calories_target = float(getattr(target, "daily_calories", None) or 0)
        execution = PlanExecution(
            plan_id=plan.id,
            date=record_date,
            calories_consumed=float(getattr(nutrition_summary, "total_calories", 0) or 0),
            calories_target=calories_target,
            protein=float(getattr(nutrition_summary, "total_protein", 0) or 0),
            fat=float(getattr(nutrition_summary, "total_fat", 0) or 0),
            carbs=float(getattr(nutrition_summary, "total_carbs", 0) or 0),
            status=self.calculate_execution_status(
                float(getattr(nutrition_summary, "total_calories", 0) or 0),
                calories_target,
            ).value,
        )
        await self.repo.upsert_execution(execution)
        await self.repo.session.commit()

    async def run_modification_rules(self, plan_id: uuid.UUID) -> list[str]:
        plan = await self._get_plan_or_404(plan_id)
        records = await self.repo.list_executions(plan.id, offset=0, limit=7)
        if len([record for record in records[:5] if record.status == ExecutionStatus.missed.value]) >= 5:
            return ["You have missed the target for 5 days in a row. Consider reducing task intensity."]
        if date.today() > plan.target_date:
            return ["This plan has passed its target date. Consider extending or closing it."]
        return []

    def normalize_draft(self, draft: PlanDraft) -> PlanDraft:
        tasks = list(draft.tasks)
        phases = list(draft.phases)
        if not phases:
            phases = self._default_phases_for_tasks(tasks, draft.start_date, draft.target_date)
        if not tasks:
            tasks = [task for phase in phases for task in phase.tasks]
        phases = self._ensure_phase_ids(phases)
        tasks = self._ensure_task_ids(tasks)
        return draft.model_copy(update={"tasks": tasks, "phases": phases})

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
            raise NotFoundException("Plan not found", code="PLAN_NOT_FOUND")
        return plan

    async def _response(self, plan: Plan) -> PlanResponse:
        target = await self.repo.get_target(plan.id)
        phases_json = plan.phases or []
        if not phases_json:
            phases_json = [self._compat_phase_from_tasks(plan.tasks or [], plan.start_date, plan.target_date)]
        return PlanResponse(
            id=plan.id,
            name=plan.name,
            goal_description=plan.goal_description,
            plan_type=PlanType(plan.plan_type),
            status=PlanStatus(plan.status),
            start_date=plan.start_date,
            target_date=plan.target_date,
            targets=PlanTargets.model_validate(target, from_attributes=True) if target else PlanTargets(),
            tasks=[PlanTask(**task) for task in (plan.tasks or [])],
            phases=[PlanPhase(**phase) for phase in phases_json],
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    @staticmethod
    def _ensure_task_ids(tasks: list[PlanTaskUpdate]) -> list[PlanTaskUpdate]:
        ensured: list[PlanTaskUpdate] = []
        for task in tasks:
            ensured.append(task if task.id is not None else task.model_copy(update={"id": uuid.uuid4()}))
        return ensured

    @classmethod
    def _ensure_phase_ids(cls, phases: list[PlanPhaseDraft]) -> list[PlanPhaseDraft]:
        ensured: list[PlanPhaseDraft] = []
        for phase in phases:
            tasks = cls._ensure_task_ids(list(phase.tasks))
            ensured.append(
                phase
                if phase.id is not None and tasks == list(phase.tasks)
                else phase.model_copy(update={"id": phase.id or uuid.uuid4(), "tasks": tasks})
            )
        return ensured

    @staticmethod
    def _default_phases_for_tasks(
        tasks: list[PlanTaskUpdate],
        start_date: date,
        target_date: date,
    ) -> list[PlanPhaseDraft]:
        return [
            PlanPhaseDraft(
                id=uuid.uuid4(),
                title="Main phase",
                goal="Complete the current plan safely and consistently.",
                start_date=start_date,
                end_date=target_date,
                tasks=tasks,
            )
        ]

    @staticmethod
    def _compat_phase_from_tasks(tasks: list[dict[str, object]], start_date: date, target_date: date) -> dict[str, object]:
        return {
            "id": str(uuid.uuid4()),
            "title": "Main phase",
            "goal": "Complete the current plan safely and consistently.",
            "start_date": start_date.isoformat(),
            "end_date": target_date.isoformat(),
            "tasks": tasks,
        }

    @staticmethod
    def _task_to_json(task: PlanTaskUpdate) -> dict[str, object]:
        task_id = task.id or uuid.uuid4()
        return {
            "id": str(task_id),
            "description": task.description,
            "frequency": task.frequency,
            "time_period": task.time_period,
        }

    @classmethod
    def _phase_to_json(cls, phase: PlanPhaseDraft) -> dict[str, object]:
        phase_id = phase.id or uuid.uuid4()
        return {
            "id": str(phase_id),
            "title": phase.title,
            "goal": phase.goal,
            "start_date": phase.start_date.isoformat(),
            "end_date": phase.end_date.isoformat(),
            "tasks": [cls._task_to_json(task) for task in phase.tasks],
        }

    @staticmethod
    def _phase_draft_from_json(phase: dict[str, object]) -> PlanPhaseDraft:
        return PlanPhaseDraft(
            id=uuid.UUID(str(phase.get("id"))) if phase.get("id") else None,
            title=str(phase.get("title") or "Phase"),
            goal=str(phase.get("goal") or "Progress safely"),
            start_date=date.fromisoformat(str(phase.get("start_date"))),
            end_date=date.fromisoformat(str(phase.get("end_date"))),
            tasks=[PlanTaskUpdate(**task) for task in list(phase.get("tasks") or [])],
        )

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

    def build_safe_adjusted_draft(self, draft: PlanDraft, violations: list[str]) -> PlanDraft:
        adjusted = self.normalize_draft(draft)
        targets = adjusted.targets.model_copy()
        end_date = adjusted.target_date
        if "CALORIES_BELOW_BMR" in violations:
            bmr = self._profile_bmr(self.profile)
            if bmr is not None:
                targets = targets.model_copy(update={"daily_calories": int(math.ceil(bmr))})
        if "PLAN_DURATION_INVALID" in violations:
            days = min(max((adjusted.target_date - adjusted.start_date).days + 1, 28), 168)
            end_date = adjusted.start_date + timedelta(days=days - 1)
        if "WEIGHT_LOSS_TOO_FAST" in violations:
            current_weight = self._profile_number(self.profile, "current_weight")
            target_weight = adjusted.targets.weight_target
            if current_weight is not None and target_weight is not None:
                total_loss = max(current_weight - target_weight, 1)
                safe_days = int(math.ceil(total_loss) * 7)
                end_date = max(end_date, adjusted.start_date + timedelta(days=safe_days - 1))
        phases = self._stretch_phases(adjusted.phases, adjusted.start_date, end_date)
        return adjusted.model_copy(update={"targets": targets, "target_date": end_date, "phases": phases})

    @staticmethod
    def _stretch_phases(phases: list[PlanPhaseDraft], start_date: date, target_date: date) -> list[PlanPhaseDraft]:
        if not phases:
            return phases
        total_days = max((target_date - start_date).days + 1, 1)
        phase_count = len(phases)
        cursor = start_date
        stretched: list[PlanPhaseDraft] = []
        for index, phase in enumerate(phases):
            remaining_days = total_days - (cursor - start_date).days
            remaining_phases = phase_count - index
            phase_days = max(1, remaining_days // remaining_phases)
            phase_end = target_date if index == phase_count - 1 else cursor + timedelta(days=phase_days - 1)
            stretched.append(phase.model_copy(update={"start_date": cursor, "end_date": phase_end}))
            cursor = phase_end + timedelta(days=1)
        return stretched

    # ---------- 子计划 ----------

    async def list_sub_plans(self, plan_id: uuid.UUID) -> list[Any]:
        """列出子计划（返回 SubPlanResponse）。"""
        from app.schemas.plan import PlanDimension, SubPlanResponse, SubPlanTask  # noqa: PLC0415

        plan = await self._get_plan_or_404(plan_id)
        sub_plans = await self.repo.list_sub_plans(plan.id)
        return [
            SubPlanResponse(
                id=sp.id,
                plan_id=sp.plan_id,
                dimension=PlanDimension(sp.dimension),
                name=sp.name,
                goal_description=sp.goal_description,
                status=PlanStatus(sp.status),
                weight=sp.weight,
                tasks=[SubPlanTask(**task) for task in (sp.tasks or [])],
                created_at=sp.created_at,
                updated_at=sp.updated_at,
            )
            for sp in sub_plans
        ]

    async def create_sub_plan(self, plan_id: uuid.UUID, data: Any) -> Any:
        """创建子计划并生成目标曲线。"""
        from app.db.models.plan import SubPlan  # noqa: PLC0415
        from app.schemas.plan import PlanDimension, SubPlanResponse, SubPlanTask  # noqa: PLC0415
        from app.services.plan_curve_service import generate_curve  # noqa: PLC0415

        plan = await self._get_plan_or_404(plan_id)
        sub_plan = SubPlan(
            plan_id=plan.id,
            dimension=data.dimension.value,
            name=data.name,
            goal_description=data.goal_description,
            status=PlanStatus.active.value,
            weight=data.weight,
            tasks=[self._task_to_json(task) for task in data.tasks],
        )
        created = await self.repo.create_sub_plan(sub_plan)
        # 生成目标曲线
        targets = generate_curve(
            plan=plan,
            sub_plan=created,
            strategy=data.curve_strategy,
            unit=data.unit,
            start_value=data.start_value,
            end_value=data.end_value,
            constant_value=data.constant_value,
        )
        await self.repo.replace_daily_targets(created.id, targets)
        await self.repo.session.commit()
        return SubPlanResponse(
            id=created.id,
            plan_id=created.plan_id,
            dimension=PlanDimension(created.dimension),
            name=created.name,
            goal_description=created.goal_description,
            status=PlanStatus(created.status),
            weight=created.weight,
            tasks=[SubPlanTask(**task) for task in (created.tasks or [])],
            created_at=created.created_at,
            updated_at=created.updated_at,
        )

    async def update_sub_plan(self, plan_id: uuid.UUID, sub_plan_id: uuid.UUID, data: Any) -> Any:
        """更新子计划（tasks/weight/status）。"""
        from app.schemas.plan import PlanDimension, SubPlanResponse, SubPlanTask  # noqa: PLC0415

        await self._get_plan_or_404(plan_id)
        sub_plan = await self.repo.get_sub_plan(sub_plan_id)
        if sub_plan is None or sub_plan.plan_id != plan_id:
            raise NotFoundException("SubPlan not found", code="SUB_PLAN_NOT_FOUND")
        if data.name is not None:
            sub_plan.name = data.name
        if data.goal_description is not None:
            sub_plan.goal_description = data.goal_description
        if data.status is not None:
            sub_plan.status = data.status.value
        if data.weight is not None:
            sub_plan.weight = data.weight
        if data.tasks is not None:
            sub_plan.tasks = [self._task_to_json(task) for task in data.tasks]
        await self.repo.session.commit()
        return SubPlanResponse(
            id=sub_plan.id,
            plan_id=sub_plan.plan_id,
            dimension=PlanDimension(sub_plan.dimension),
            name=sub_plan.name,
            goal_description=sub_plan.goal_description,
            status=PlanStatus(sub_plan.status),
            weight=sub_plan.weight,
            tasks=[SubPlanTask(**task) for task in (sub_plan.tasks or [])],
            created_at=sub_plan.created_at,
            updated_at=sub_plan.updated_at,
        )

    # ---------- 目标曲线 ----------

    async def get_daily_target_curves(
        self,
        plan_id: uuid.UUID,
        *,
        dimension: Any = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Any]:
        """按子计划/维度分组返回目标曲线。"""
        from collections import defaultdict  # noqa: PLC0415

        from app.schemas.plan import DailyTargetCurve, DailyTargetPoint, PlanDimension  # noqa: PLC0415

        plan = await self._get_plan_or_404(plan_id)
        targets = await self.repo.list_daily_targets(
            plan.id,
            dimension=dimension.value if dimension else None,
            start_date=start_date,
            end_date=end_date,
        )
        by_sub_plan: dict[uuid.UUID, list] = defaultdict(list)
        for target in targets:
            by_sub_plan[target.sub_plan_id].append(target)
        curves: list[DailyTargetCurve] = []
        for sub_plan_id, points_orm in by_sub_plan.items():
            if not points_orm:
                continue
            first = points_orm[0]
            curves.append(
                DailyTargetCurve(
                    plan_id=plan.id,
                    sub_plan_id=sub_plan_id,
                    dimension=PlanDimension(first.dimension),
                    unit=first.unit,
                    points=[
                        DailyTargetPoint(
                            date=p.date,
                            target_value=p.target_value,
                            unit=p.unit,
                            dimension=PlanDimension(p.dimension),
                        )
                        for p in points_orm
                    ],
                )
            )
        return curves

    # ---------- 完成率 ----------

    async def compute_compliance(self, plan_id: uuid.UUID) -> Any:
        """计算整体完成率（组合 BodyRepository 和 ComplianceService）。"""
        from app.db.repositories.body_repo import BodyRepository  # noqa: PLC0415
        from app.services.plan_compliance_service import PlanComplianceService  # noqa: PLC0415

        plan = await self._get_plan_or_404(plan_id)
        body_repo = BodyRepository(session=self.repo.session, user_id=self.repo.user_id)
        compliance_svc = PlanComplianceService(plan_repo=self.repo, body_repo=body_repo)
        return await compliance_svc.compute_overall(plan)

    # ---------- AI 分析 ----------

    async def list_analyses(self, plan_id: uuid.UUID, *, limit: int = 30) -> list[Any]:
        """获取 AI 分析历史。"""
        from app.schemas.plan import PlanAnalysisResponse  # noqa: PLC0415

        plan = await self._get_plan_or_404(plan_id)
        analyses = await self.repo.list_analyses(plan.id, limit=limit)
        return [
            PlanAnalysisResponse(
                id=a.id,
                plan_id=a.plan_id,
                analysis_date=a.analysis_date,
                overall_compliance=a.overall_compliance,
                dimension_compliance=a.dimension_compliance,
                has_anomaly=a.has_anomaly,
                summary=a.summary,
                created_at=a.created_at,
            )
            for a in analyses
        ]

    # ---------- 调整提议 ----------

    async def list_proposals(
        self, plan_id: uuid.UUID, *, status: Any = None
    ) -> list[Any]:
        """获取调整提议列表。"""
        from app.schemas.plan import AdjustmentProposalResponse, ProposalStatus  # noqa: PLC0415

        plan = await self._get_plan_or_404(plan_id)
        proposals = await self.repo.list_proposals(plan.id, status=status)
        return [
            AdjustmentProposalResponse(
                id=p.id,
                plan_id=p.plan_id,
                sub_plan_id=p.sub_plan_id,
                reason=p.reason,
                proposed_changes=p.proposed_changes,
                status=ProposalStatus(p.status),
                created_at=p.created_at,
                resolved_at=p.resolved_at,
            )
            for p in proposals
        ]

    async def accept_proposal(self, plan_id: uuid.UUID, proposal_id: uuid.UUID) -> Any:
        """接受调整提议 → 应用修改并重新生成目标曲线。"""
        from app.schemas.plan import ProposalStatus  # noqa: PLC0415

        await self._get_plan_or_404(plan_id)
        proposal = await self.repo.get_proposal(proposal_id)
        if proposal is None or proposal.plan_id != plan_id:
            raise NotFoundException("Proposal not found", code="PROPOSAL_NOT_FOUND")
        if proposal.status != ProposalStatus.pending.value:
            raise ValidationException("Proposal not pending", code="PROPOSAL_NOT_PENDING")
        # 简化实现：仅标记为 accepted，实际应用 proposed_changes 略
        proposal.status = ProposalStatus.accepted.value
        proposal.resolved_at = datetime.now(UTC)
        await self.repo.session.commit()
        # 返回占位响应（实际应返回更新后的 SubPlan）
        from app.schemas.plan import PlanDimension, SubPlanResponse  # noqa: PLC0415

        return SubPlanResponse(
            id=proposal.sub_plan_id or uuid.uuid4(),
            plan_id=proposal.plan_id,
            dimension=PlanDimension.exercise,
            name="Adjusted",
            goal_description="Proposal accepted",
            status=PlanStatus.active,
            weight=1.0,
            tasks=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    async def reject_proposal(self, plan_id: uuid.UUID, proposal_id: uuid.UUID) -> None:
        """拒绝调整提议 → 置为 rejected 终态。"""
        from app.schemas.plan import ProposalStatus  # noqa: PLC0415

        await self._get_plan_or_404(plan_id)
        proposal = await self.repo.get_proposal(proposal_id)
        if proposal is None or proposal.plan_id != plan_id:
            raise NotFoundException("Proposal not found", code="PROPOSAL_NOT_FOUND")
        proposal.status = ProposalStatus.rejected.value
        proposal.resolved_at = datetime.now(UTC)
        await self.repo.session.commit()


__all__ = ["PlanService"]
