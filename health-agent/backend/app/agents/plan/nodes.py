"""Plan agent nodes."""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, cast

from app.agents.base import get_chat_model
from app.agents.plan.state import PlanState
from app.agents.plan.tools import persist_plan_tool, safety_check_tool
from app.agents.prompts.plan_draft import build_plan_draft_messages
from app.schemas.plan import PlanDraft, PlanTargets, PlanTaskUpdate, PlanType

logger = logging.getLogger(__name__)


def _infer_plan_type(goal: str, explicit: str | PlanType | None) -> PlanType:
    if explicit:
        return PlanType(str(explicit))
    if any(keyword in goal for keyword in ["减重", "减肥", "减脂", "瘦", "体重"]):
        return PlanType.weight_loss
    if any(keyword in goal for keyword in ["营养", "蛋白", "饮食", "控糖"]):
        return PlanType.nutrition_adjustment
    return PlanType.habit_formation


def _default_draft(state: PlanState) -> PlanDraft:
    goal = state.get("goal_description") or "改善健康习惯"
    plan_type = _infer_plan_type(goal, state.get("plan_type"))
    profile = state.get("profile")
    current_weight = getattr(profile, "current_weight", None)
    target_weight = getattr(profile, "target_weight", None)
    daily_calories = getattr(profile, "daily_calorie_target", None) or 1800
    if plan_type == PlanType.weight_loss:
        name = "减重计划"
        weight_target = target_weight or (float(current_weight) - 3 if current_weight else 70)
        tasks = [
            PlanTaskUpdate(description=f"每日热量控制在 {daily_calories} kcal 左右", frequency="每天"),
            PlanTaskUpdate(description="每周至少 3 次中等强度运动", frequency="每周3次"),
            PlanTaskUpdate(description="晚餐减少含糖饮料和高油食物", frequency="每天", time_period="晚餐"),
        ]
    elif plan_type == PlanType.nutrition_adjustment:
        name = "营养调整计划"
        weight_target = target_weight
        tasks = [
            PlanTaskUpdate(description="每日蛋白质摄入不少于 80g", frequency="每天"),
            PlanTaskUpdate(description="每餐至少 1 份蔬菜", frequency="每天"),
            PlanTaskUpdate(description="减少加工食品和含糖饮料", frequency="每天"),
        ]
    else:
        name = "习惯养成计划"
        weight_target = target_weight
        tasks = [
            PlanTaskUpdate(description="每日步数达到 8000 步", frequency="每天"),
            PlanTaskUpdate(description="每日饮水约 2000ml", frequency="每天"),
            PlanTaskUpdate(description="保持规律作息", frequency="每天", time_period="晚上"),
        ]
    start = date.today()
    return PlanDraft(
        name=name,
        goal_description=goal,
        plan_type=plan_type,
        start_date=start,
        target_date=start + timedelta(days=83),
        targets=PlanTargets(
            daily_calories=int(daily_calories),
            protein_target=90,
            fat_target=55,
            carbs_target=220,
            weight_target=weight_target,
        ),
        tasks=tasks,
    )


async def confirm_goal(state: PlanState) -> dict[str, Any]:
    """Confirm the goal text is usable for plan drafting."""
    goal = (state.get("goal_description") or "").strip()
    if not goal:
        return {"error": "goal_required"}
    return {"goal_analysis": f"用户目标已确认：{goal}"}


async def analyze_status(state: PlanState) -> dict[str, Any]:
    """Deterministically summarize available profile data for drafting."""
    profile = state.get("profile")
    summary = (
        f"当前体重={getattr(profile, 'current_weight', None)}, "
        f"目标体重={getattr(profile, 'target_weight', None)}, "
        f"身高={getattr(profile, 'height', None)}"
    )
    return {"status_analysis": summary}


async def draft_plan(state: PlanState) -> dict[str, Any]:
    """Generate a PlanDraft with LLM structured output and deterministic fallback.

    SDK/API 说明：``get_chat_model`` 返回 DashScope 兼容 ChatOpenAI；
    ``with_structured_output(PlanDraft)`` 要求模型输出符合 Pydantic schema 的结构。
    """
    fallback = _default_draft(state)
    try:
        model = cast(Any, get_chat_model(temperature=0.3, timeout=60)).with_structured_output(PlanDraft)
        draft = await model.ainvoke(
            build_plan_draft_messages(
                state.get("goal_description") or "",
                str(state.get("plan_type")) if state.get("plan_type") else None,
                state.get("profile"),
            )
        )
        return {"draft": draft}
    except Exception as exc:  # pragma: no cover - local/dev fallback without API key
        logger.info("plan draft fallback used: %s", exc)
        return {"draft": fallback}


async def safety_validate(state: PlanState) -> dict[str, Any]:
    """Run deterministic safety validation before persistence."""
    service = state.get("plan_service")
    draft = state.get("draft")
    if service is None or draft is None:
        return {"safety_violations": ["PLAN_DRAFT_MISSING"]}
    violations = safety_check_tool(service, draft, state.get("profile"))
    return {"safety_violations": violations}


async def persist_plan(state: PlanState) -> dict[str, Any]:
    """Persist the validated draft through PlanService."""
    service = state.get("plan_service")
    draft = state.get("draft")
    violations = state.get("safety_violations", [])
    if service is None or draft is None:
        return {"error": "plan_service_or_draft_missing"}
    if violations:
        return {"error": violations[0]}
    result = await persist_plan_tool(service, draft)
    return {"result": result}


async def analyze_deviation(state: PlanState) -> dict[str, Any]:
    """Analyze execution deviations for modification suggestions.

    Phase 8 先提供最小子图能力：读取确定性规则命中结果，不在 Service 中调用 LLM。
    后续可在本节点补充 LLM 分析。
    """
    service = state.get("plan_service")
    plan_id = state.get("plan_id")
    if service is None or plan_id is None:
        return {"modification_reasons": []}
    reasons = await service.run_modification_rules(plan_id)
    return {"modification_reasons": reasons}


async def suggest_modification(state: PlanState) -> dict[str, Any]:
    """Return user-confirmable modification suggestions.

    本节点只返回建议文本，不自动更新计划；用户确认后仍通过 ``PUT /plans/{id}`` 修改。
    """
    reasons = state.get("modification_reasons", []) or []
    suggestions = [f"建议根据原因调整计划：{reason}" for reason in reasons]
    return {"modification_suggestions": suggestions}


__all__ = [
    "analyze_deviation",
    "analyze_status",
    "confirm_goal",
    "draft_plan",
    "persist_plan",
    "safety_validate",
    "suggest_modification",
]



