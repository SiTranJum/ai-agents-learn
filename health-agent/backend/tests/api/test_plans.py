"""Phase 8 - plans API tests."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient

from app.dependencies import get_current_user_with_profile, get_plan_agent, get_plan_service
from app.main import app
from app.schemas.auth import CurrentUser
from app.schemas.plan import (
    CheckInCreate,
    CheckInResponse,
    PlanDraft,
    PlanProgress,
    PlanResponse,
    PlanStatus,
    PlanTargets,
    PlanTask,
    PlanType,
)


def _response(plan_id: uuid.UUID | None = None) -> PlanResponse:
    now = datetime.now(UTC)
    return PlanResponse(
        id=plan_id or uuid.uuid4(),
        name="减重计划",
        goal_description="我想减重",
        plan_type=PlanType.weight_loss,
        status=PlanStatus.active,
        start_date=date.today(),
        target_date=date.today() + timedelta(days=83),
        targets=PlanTargets(daily_calories=1800, weight_target=70),
        tasks=[PlanTask(id=uuid.uuid4(), description="每天步行", frequency="每天")],
        created_at=now,
        updated_at=now,
    )


class _FakePlanService:
    def __init__(self) -> None:
        self.active = False
        self.plan = _response()

    async def has_active_plan(self) -> bool:
        return self.active

    async def list_plans(self, *, status=None, page=1, page_size=20):
        _ = status, page, page_size
        return [self.plan], 1

    async def get_plan(self, plan_id: uuid.UUID):
        return _response(plan_id)

    async def update_plan(self, plan_id: uuid.UUID, data):
        _ = data
        return _response(plan_id)

    async def terminate_plan(self, plan_id: uuid.UUID, reason=None) -> None:
        _ = plan_id, reason

    async def create_check_in(self, plan_id: uuid.UUID, data: CheckInCreate):
        return CheckInResponse(
            id=uuid.uuid4(),
            plan_id=plan_id,
            task_id=data.task_id,
            date=data.date,
            completed=data.completed,
            note=data.note,
            created_at=datetime.now(UTC),
        )

    async def get_progress(self, plan_id: uuid.UUID):
        return PlanProgress(plan_id=plan_id, total_days=84, elapsed_days=1, compliance_rate=0, streak_days=0)

    async def list_execution_records(self, plan_id: uuid.UUID, **kwargs):
        _ = plan_id, kwargs
        return [], 0


class _FakePlanAgent:
    async def ainvoke(self, state: dict[str, Any]):
        draft = PlanDraft(
            name="减重计划",
            goal_description=state["goal_description"],
            plan_type=PlanType.weight_loss,
            start_date=date.today(),
            target_date=date.today() + timedelta(days=83),
            targets=PlanTargets(daily_calories=1800, weight_target=70),
            tasks=[],
        )
        return {"result": _response(), "draft": draft}


@pytest.fixture
async def plan_overrides():
    service = _FakePlanService()

    async def _current_user() -> CurrentUser:
        user = CurrentUser(id=uuid.uuid4(), email="user@example.com")
        user.profile = object()
        return user

    async def _service() -> _FakePlanService:
        return service

    def _agent() -> _FakePlanAgent:
        return _FakePlanAgent()

    app.dependency_overrides[get_current_user_with_profile] = _current_user
    app.dependency_overrides[get_plan_service] = _service
    app.dependency_overrides[get_plan_agent] = _agent
    try:
        yield service
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_plan_endpoint(client: AsyncClient, plan_overrides) -> None:
    resp = await client.post("/api/v1/plans", json={"goal_description": "我想减重"})

    assert resp.status_code == 201
    assert resp.json()["data"]["plan_type"] == "weight_loss"


@pytest.mark.asyncio
async def test_plan_list_detail_check_in_and_progress(client: AsyncClient, plan_overrides) -> None:
    plan_id = str(uuid.uuid4())

    listed = await client.get("/api/v1/plans")
    detail = await client.get(f"/api/v1/plans/{plan_id}")
    check_in = await client.post(f"/api/v1/plans/{plan_id}/check-ins", json={"completed": True})
    progress = await client.get(f"/api/v1/plans/{plan_id}/progress")
    deleted = await client.delete(f"/api/v1/plans/{plan_id}")

    assert listed.status_code == 200
    assert listed.json()["pagination"]["total"] == 1
    assert detail.status_code == 200
    assert check_in.status_code == 201
    assert progress.status_code == 200
    assert deleted.status_code == 200

