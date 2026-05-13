"""Phase 8 - plan_agent tests."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from app.agents.plan.graph import build_plan_agent
from app.schemas.plan import (
    PlanDraft,
    PlanResponse,
    PlanStatus,
    PlanTargets,
    PlanTask,
    PlanTaskUpdate,
    PlanType,
)


class _FakePlanService:
    def safety_check(self, draft: PlanDraft, profile) -> list[str]:
        _ = draft, profile
        return []

    async def create_plan_from_draft(self, draft: PlanDraft) -> PlanResponse:
        return PlanResponse(
            id=uuid.uuid4(),
            name=draft.name,
            goal_description=draft.goal_description,
            plan_type=draft.plan_type,
            status=PlanStatus.active,
            start_date=draft.start_date,
            target_date=draft.target_date,
            targets=draft.targets,
            tasks=[
                PlanTask(
                    id=task.id or uuid.uuid4(),
                    description=task.description,
                    frequency=task.frequency,
                    time_period=task.time_period,
                )
                for task in draft.tasks
            ],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


@pytest.mark.asyncio
async def test_plan_agent_creates_plan_with_deterministic_fallback(monkeypatch) -> None:
    class _BrokenModel:
        def with_structured_output(self, schema):
            raise RuntimeError("no llm")

    monkeypatch.setattr("app.agents.plan.nodes.get_chat_model", lambda *args, **kwargs: _BrokenModel())
    graph = build_plan_agent()

    state = await graph.ainvoke(
        {
            "user_id": str(uuid.uuid4()),
            "goal_description": "我想健康减重",
            "plan_type": PlanType.weight_loss,
            "profile": SimpleNamespace(current_weight=75, target_weight=70, daily_calorie_target=1800),
            "plan_service": _FakePlanService(),
        }
    )

    assert state["result"].plan_type == PlanType.weight_loss
    assert state["result"].tasks


@pytest.mark.asyncio
async def test_plan_agent_returns_error_when_safety_fails(monkeypatch) -> None:
    class _UnsafeService(_FakePlanService):
        def safety_check(self, draft: PlanDraft, profile) -> list[str]:
            _ = draft, profile
            return ["CALORIES_BELOW_BMR"]

    class _FakeModel:
        def with_structured_output(self, schema):
            class _Structured:
                async def ainvoke(self, messages):
                    _ = messages
                    return schema(
                        name="不安全计划",
                        goal_description="快速减重",
                        plan_type=PlanType.weight_loss,
                        start_date=date.today(),
                        target_date=date.today(),
                        targets=PlanTargets(daily_calories=800, weight_target=60),
                        tasks=[PlanTaskUpdate(description="少吃")],
                    )

            return _Structured()

    monkeypatch.setattr("app.agents.plan.nodes.get_chat_model", lambda *args, **kwargs: _FakeModel())
    graph = build_plan_agent()

    state = await graph.ainvoke(
        {
            "goal_description": "快速减重",
            "plan_service": _UnsafeService(),
        }
    )

    assert state["error"] == "CALORIES_BELOW_BMR"

