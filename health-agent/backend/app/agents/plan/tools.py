"""Tool wrappers for plan agent."""

from __future__ import annotations

from app.schemas.plan import PlanDraft, PlanResponse
from app.services.plan_service import PlanService


async def persist_plan_tool(service: PlanService, draft: PlanDraft) -> PlanResponse:
    """Persist a validated plan draft through PlanService."""
    return await service.create_plan_from_draft(draft)


def safety_check_tool(service: PlanService, draft: PlanDraft, profile: object | None) -> list[str]:
    """Run deterministic safety checks through PlanService."""
    return service.safety_check(draft, profile)


__all__ = ["persist_plan_tool", "safety_check_tool"]

