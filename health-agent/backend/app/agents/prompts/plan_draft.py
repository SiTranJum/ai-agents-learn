"""Prompt builders for plan agent."""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

PLAN_DRAFT_SYSTEM = """你是健康管家 AI Agent 的计划制定专家。
请根据用户目标生成安全、可执行的健康计划草案。
要求：
- 只生成计划草案，不做医疗诊断。
- 计划周期必须在 1-24 周。
- 减重速度不要超过每周 1kg。
- 每日热量目标不能明显低于基础代谢。
- 任务要具体、可打卡、适合普通用户执行。
"""


def build_plan_draft_messages(goal_description: str, plan_type: str | None, profile: Any) -> list[Any]:
    """Build LangChain messages for structured plan draft generation.

    SDK/API 说明：返回 ``SystemMessage`` / ``HumanMessage`` 列表，供
    ``ChatOpenAI.with_structured_output(PlanDraft).ainvoke(messages)`` 使用。
    """
    profile_text = {
        "gender": getattr(profile, "gender", None),
        "birth_date": str(getattr(profile, "birth_date", None)),
        "height": getattr(profile, "height", None),
        "current_weight": getattr(profile, "current_weight", None),
        "target_weight": getattr(profile, "target_weight", None),
        "daily_calorie_target": getattr(profile, "daily_calorie_target", None),
    }
    return [
        SystemMessage(content=PLAN_DRAFT_SYSTEM),
        HumanMessage(
            content=(
                f"用户目标：{goal_description}\n"
                f"计划类型（可能为空）：{plan_type}\n"
                f"用户档案：{profile_text}\n"
                "请输出 PlanDraft 结构。"
            )
        ),
    ]


__all__ = ["build_plan_draft_messages"]


