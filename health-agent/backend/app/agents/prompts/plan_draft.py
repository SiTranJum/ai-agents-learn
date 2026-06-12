"""计划草案 Prompt 构造器。"""

from __future__ import annotations

from datetime import date
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

【减重计划的 weight_anchors 字段（仅 plan_type=weight_loss 时填写）】
- 只给 3 到 5 个关键锚点，不要逐日给出（逐日会很慢）。
- 必须包含起点 day_offset=0（等于用户档案 current_weight）和终点 day_offset=(target_date - start_date)（等于 weight_target）。
- 中间锚点用来体现阶段速率，例如"前两周下降快、中段平台、后期收尾"。
- 锚点的 target_weight 必须随 day_offset 单调递减或保持不变，不能回升。
- 任意两个相邻锚点之间的平均减重速率不能超过每周 1kg。
- 体重保留 1 位小数即可。后端会在锚点之间自动线性插值出每一天的目标。
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
                f"今天的日期是 {date.today().isoformat()}。计划的 start_date 必须从今天开始。\n\n"
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
