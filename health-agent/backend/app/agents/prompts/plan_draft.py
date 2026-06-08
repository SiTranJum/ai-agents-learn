"""计划草案 Prompt 构造器。"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

PLAN_DRAFT_SYSTEM = """你是健康管理场景下的计划制定助手。

你的任务是根据用户当前问题、基础档案、历史记忆和近期上下文，生成一个安全、务实、可执行、分阶段的计划草案。

要求：
- 只输出计划草案，不要输出医疗诊断结论。
- 优先利用已有资料推断，不要机械追问；只有关键缺失信息才需要补问。
- 计划必须显式分阶段，每个阶段都要有阶段目标、起止时间和任务。
- 计划周期必须控制在 1 到 24 周之间。
- 如果是减重计划，减重速度不能超过每周 1kg。
- 热量目标要保守、安全，不能为了追求速度给出明显激进的建议。
- 任务描述必须具体、可打卡、可执行，避免空泛表述。
"""


def build_plan_draft_messages(
    *,
    goal_description: str,
    plan_type: str | None,
    profile: Any,
    transcript: list[dict[str, Any]] | None = None,
    memories: list[str] | None = None,
    recent_data: dict[str, Any] | None = None,
) -> list[Any]:
    """构造结构化计划草案生成所需的消息列表。"""
    profile_text = {
        "gender": getattr(profile, "gender", None),
        "birth_date": str(getattr(profile, "birth_date", None) or ""),
        "height": getattr(profile, "height", None),
        "current_weight": getattr(profile, "current_weight", None),
        "target_weight": getattr(profile, "target_weight", None),
        "daily_calorie_target": getattr(profile, "daily_calorie_target", None),
    }
    return [
        SystemMessage(content=PLAN_DRAFT_SYSTEM),
        HumanMessage(
            content=(
                f"用户本轮需求：\n{goal_description}\n\n"
                f"计划类型提示：{plan_type}\n"
                f"用户基础档案：{profile_text}\n"
                f"召回到的长期记忆：{memories or []}\n"
                f"近期客观数据或摘要：{recent_data or {}}\n"
                f"对话历史：{transcript or []}\n\n"
                "请直接输出符合 PlanDraft 结构的结果。"
            )
        ),
    ]


__all__ = ["build_plan_draft_messages"]
