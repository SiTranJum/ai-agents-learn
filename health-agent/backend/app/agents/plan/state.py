"""Plan agent state."""

from __future__ import annotations

from typing import Any, TypedDict

from app.schemas.plan import PlanDraft, PlanResponse, PlanType


class PlanState(TypedDict, total=False):
    user_id: str
    goal_description: str
    plan_type: PlanType | str | None
    plan_id: str
    profile: Any
    plan_service: Any
    memory_service: Any
    goal_analysis: str
    status_analysis: str
    draft: PlanDraft
    safety_violations: list[str]
    modification_reasons: list[str]
    modification_suggestions: list[str]
    result: PlanResponse
    error: str | None


__all__ = ["PlanState"]


