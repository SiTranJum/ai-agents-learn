"""Phase 8 - PlanService unit tests."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core.exceptions import ConflictException
from app.db.models.plan import Plan, PlanCheckIn, PlanExecution, PlanTarget
from app.schemas.plan import (
    CheckInCreate,
    ExecutionStatus,
    PlanDraft,
    PlanTargets,
    PlanTaskUpdate,
    PlanType,
)
from app.services.plan_service import PlanService


class _FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    def add(self, instance) -> None:
        _ = instance

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1


class _FakeRepo:
    def __init__(self) -> None:
        self.session = _FakeSession()
        self.user_id = uuid.uuid4()
        self.plans: list[Plan] = []
        self.targets: dict[uuid.UUID, PlanTarget] = {}
        self.check_ins: list[PlanCheckIn] = []
        self.executions: list[PlanExecution] = []

    async def has_active_plan(self) -> bool:
        return any(plan.status == "active" and plan.deleted_at is None for plan in self.plans)

    async def create_plan(self, plan: Plan, target: PlanTarget) -> Plan:
        now = datetime.now(UTC)
        plan.id = uuid.uuid4()
        plan.user_id = self.user_id
        plan.created_at = now
        plan.updated_at = now
        target.id = uuid.uuid4()
        target.user_id = self.user_id
        target.plan_id = plan.id
        target.created_at = now
        target.updated_at = now
        self.plans.append(plan)
        self.targets[plan.id] = target
        return plan

    async def get_plan(self, plan_id: uuid.UUID) -> Plan | None:
        return next((plan for plan in self.plans if plan.id == plan_id and plan.deleted_at is None), None)

    async def get_target(self, plan_id: uuid.UUID) -> PlanTarget | None:
        return self.targets.get(plan_id)

    async def list_plans(self, *, status=None, offset=0, limit=20):
        plans = [plan for plan in self.plans if plan.deleted_at is None]
        if status is not None:
            plans = [plan for plan in plans if plan.status == status.value]
        return plans[offset : offset + limit]

    async def count_plans(self, *, status=None) -> int:
        return len(await self.list_plans(status=status, offset=0, limit=100))

    async def check_in_exists(self, plan_id, task_id, target_date) -> bool:
        return any(item.plan_id == plan_id and item.task_id == task_id and item.date == target_date for item in self.check_ins)

    async def create_check_in(self, check_in: PlanCheckIn) -> PlanCheckIn:
        check_in.id = uuid.uuid4()
        check_in.user_id = self.user_id
        check_in.created_at = datetime.now(UTC)
        self.check_ins.append(check_in)
        return check_in

    async def list_executions(self, plan_id, **kwargs):
        _ = kwargs
        return [record for record in self.executions if record.plan_id == plan_id]

    async def count_executions(self, plan_id, **kwargs) -> int:
        return len(await self.list_executions(plan_id, **kwargs))

    async def soft_terminate(self, plan: Plan, reason=None) -> None:
        plan.status = "terminated"
        plan.deleted_at = datetime.now(UTC)
        plan.termination_reason = reason


def _draft() -> PlanDraft:
    return PlanDraft(
        name="减重计划",
        goal_description="我想健康减重",
        plan_type=PlanType.weight_loss,
        start_date=date.today(),
        target_date=date.today() + timedelta(days=83),
        targets=PlanTargets(daily_calories=1800, weight_target=70),
        tasks=[PlanTaskUpdate(description="每天步行 30 分钟")],
    )


@pytest.mark.asyncio
async def test_create_plan_from_draft_and_prevent_duplicate_active() -> None:
    repo = _FakeRepo()
    profile = SimpleNamespace(current_weight=75, height=175, gender="male", birth_date=date(1990, 1, 1))
    service = PlanService(repo=repo, profile=profile)  # type: ignore[arg-type]

    created = await service.create_plan_from_draft(_draft())

    assert created.name == "减重计划"
    assert created.status.value == "active"
    assert repo.session.commits == 1
    with pytest.raises(ConflictException):
        await service.create_plan_from_draft(_draft())


@pytest.mark.asyncio
async def test_check_in_duplicate_is_rejected() -> None:
    repo = _FakeRepo()
    service = PlanService(repo=repo)  # type: ignore[arg-type]
    created = await service.create_plan_from_draft(_draft())
    payload = CheckInCreate(date=date.today(), task_id=None, completed=True)

    first = await service.create_check_in(created.id, payload)

    assert first.completed is True
    with pytest.raises(ConflictException):
        await service.create_check_in(created.id, payload)


def test_bmr_execution_status_and_safety_rules() -> None:
    service = PlanService(repo=_FakeRepo())  # type: ignore[arg-type]

    assert service.calculate_bmr(70, 175, 30, "male") == 1648.8
    assert service.calculate_execution_status(1800, 1800) == ExecutionStatus.on_track
    assert service.calculate_execution_status(1500, 1800) == ExecutionStatus.deviation
    assert service.calculate_execution_status(1200, 1800) == ExecutionStatus.missed

    profile = SimpleNamespace(current_weight=80, height=175, gender="male", birth_date=date(1990, 1, 1))
    unsafe = _draft().model_copy(update={"target_date": date.today() + timedelta(days=13)})
    assert "WEIGHT_LOSS_TOO_FAST" in service.safety_check(unsafe, profile)

