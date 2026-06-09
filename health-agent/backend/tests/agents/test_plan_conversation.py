"""Plan conversation guardrail tests."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.agents.plan.conversation import run_plan_conversation
from app.schemas.plan import (
    PlanConversationMessage,
    PlanDraft,
    PlanPhase,
    PlanPhaseDraft,
    PlanResponse,
    PlanStatus,
    PlanTargets,
    PlanTask,
    PlanTaskUpdate,
    PlanType,
)


class _FakePlanService:
    def __init__(self) -> None:
        self.saved: PlanDraft | None = None

    async def get_active_plan(self):
        return None

    def normalize_draft(self, draft):
        return draft

    def safety_check(self, draft, profile) -> list[str]:
        _ = draft, profile
        return []

    async def create_plan_from_draft(self, draft: PlanDraft) -> PlanResponse:
        self.saved = draft
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
            phases=[
                PlanPhase(
                    id=phase.id or uuid.uuid4(),
                    title=phase.title,
                    goal=phase.goal,
                    start_date=phase.start_date,
                    end_date=phase.end_date,
                    tasks=[
                        PlanTask(
                            id=task.id or uuid.uuid4(),
                            description=task.description,
                            frequency=task.frequency,
                            time_period=task.time_period,
                        )
                        for task in phase.tasks
                    ],
                )
                for phase in draft.phases
            ],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


class _BrokenModel:
    def with_structured_output(self, schema):
        _ = schema
        raise RuntimeError("llm disabled in tests")


def _draft() -> PlanDraft:
    start = date.today()
    task = PlanTaskUpdate(description="每天步行 30 分钟")
    return PlanDraft(
        name="减重计划",
        goal_description="12 周减 4kg",
        plan_type=PlanType.weight_loss,
        start_date=start,
        target_date=start + timedelta(days=83),
        targets=PlanTargets(daily_calories=1800, weight_target=71),
        tasks=[task],
        phases=[
            PlanPhaseDraft(
                title="第一阶段",
                goal="建立稳定节奏",
                start_date=start,
                end_date=start + timedelta(days=41),
                tasks=[task],
            )
        ],
    )


@pytest.mark.asyncio
async def test_greeting_starts_plan_guidance() -> None:
    result = await run_plan_conversation(
        user_message="你好",
        messages=[],
        profile=None,
        plan_service=_FakePlanService(),
    )

    assert "可以帮你制定健康计划" in result["ai_response"]
    assert result["response_cards"] == []
    assert result["choice_prompts"]


@pytest.mark.asyncio
async def test_repeated_greeting_does_not_repeat_choice_prompt() -> None:
    result = await run_plan_conversation(
        user_message="你好",
        messages=[
            PlanConversationMessage(role="user", content="你好"),
            PlanConversationMessage(role="assistant", content="我可以帮你制定健康计划。"),
        ],
        profile=None,
        plan_service=_FakePlanService(),
    )

    assert result["ai_response"].startswith("我在")
    assert result["response_cards"] == []
    assert result["choice_prompts"] == []


@pytest.mark.asyncio
async def test_identity_question_gets_identity_answer() -> None:
    result = await run_plan_conversation(
        user_message="你是谁",
        messages=[],
        profile=None,
        plan_service=_FakePlanService(),
    )

    assert "健康计划助手" in result["ai_response"]
    assert result["response_cards"] == []
    assert result["choice_prompts"] == []


@pytest.mark.asyncio
async def test_affirmative_without_context_does_not_create_plan() -> None:
    result = await run_plan_conversation(
        user_message="是的",
        messages=[],
        profile=None,
        plan_service=_FakePlanService(),
    )

    assert "不知道你具体确认哪件事" in result["ai_response"]
    assert result["response_cards"] == []
    assert result["choice_prompts"] == []


@pytest.mark.asyncio
async def test_unknown_followup_does_not_repeat_generic_greeting() -> None:
    result = await run_plan_conversation(
        user_message="然后呢",
        messages=[
            PlanConversationMessage(role="user", content="你好"),
            PlanConversationMessage(role="assistant", content="我可以帮你制定健康计划。"),
        ],
        profile=None,
        plan_service=_FakePlanService(),
    )

    assert "不足以制定计划" in result["ai_response"]
    assert result["response_cards"] == []
    assert result["choice_prompts"] == []


@pytest.mark.asyncio
async def test_missing_details_returns_choice_prompts() -> None:
    result = await run_plan_conversation(
        user_message="我想减肥",
        messages=[],
        profile=None,
        plan_service=_FakePlanService(),
    )

    assert "具体结果" in result["ai_response"]
    assert result["response_cards"] == []
    assert result["choice_prompts"]


@pytest.mark.asyncio
async def test_affirmative_with_pending_draft_saves_plan() -> None:
    draft = _draft()
    service = _FakePlanService()

    result = await run_plan_conversation(
        user_message="好的",
        messages=[PlanConversationMessage(role="system", content=f"[plan_draft] {draft.model_dump_json()}")],
        profile=None,
        plan_service=service,
    )

    assert service.saved == draft
    assert "已保存" in result["ai_response"]
    assert result["response_cards"][0]["type"] == "plan_saved"


@pytest.mark.asyncio
async def test_complete_weight_loss_request_generates_draft_without_treating_delta_as_target(
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.agents.plan.conversation.get_chat_model", lambda *args, **kwargs: _BrokenModel())

    result = await run_plan_conversation(
        user_message="12 周减 4kg",
        messages=[],
        profile=SimpleNamespace(current_weight=75, target_weight=None, daily_calorie_target=1800),
        plan_service=_FakePlanService(),
    )

    card = result["response_cards"][0]
    draft = card["payload"]["draft"]
    assert card["type"] == "plan_draft"
    assert draft["plan_type"] == "weight_loss"
    assert draft["targets"]["weight_target"] == 71
