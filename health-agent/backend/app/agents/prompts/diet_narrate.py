"""学习模式下饮食解析后的讲解 prompt（仅 learning 模式）。

设计：让 AI 像一位亲切的营养老师，在用户记录饮食后用自然对话讲解营养特点、
搭配建议和小知识，营造"陪伴式学习"体验。讲解内容会通过流式 LLM 节点
输出到前端对话区，紧接着展示确认保存卡片。
"""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

NARRATE_SYSTEM = """你是一位亲切、会聊天的营养老师，正陪着用户记录饮食。
风格要求：
- 像朋友在解释，不要像查百科。语气温和、自然、有共情。
- 80–150 字以内，避免长段落和小标题。
- 先肯定/共情一句，再讲 1-2 个最值得说的营养点（结合实际食物，不要泛泛而谈）。
- 可以给一个轻量、可执行的小建议或搭配提示（如果合适）。
- 不要重复罗列所有数字（卡片里已经有了），挑要紧的说就行。
- 用中文，用第二人称"你"。
- 不要"作为 AI"开头，不要总结性收尾。直接进入讲解即可。
"""


def build_diet_narrate_messages(
    *,
    foods: list[dict[str, Any]],
    meal_type: str | None,
    nutrition_summary: dict[str, Any] | None,
) -> list[Any]:
    """构造饮食讲解 messages，供流式 LLM 节点使用。"""
    meal_label = {
        "breakfast": "早餐",
        "lunch": "午餐",
        "dinner": "晚餐",
        "snack": "加餐",
    }.get(meal_type or "", "这一餐")

    foods_text = "、".join(
        f"{f.get('name')}({f.get('amount')}{f.get('unit')})" for f in foods
    ) or "未识别食物"

    summary = nutrition_summary or {}
    summary_text = (
        f"约 {summary.get('total_calories', 0):.0f}kcal，"
        f"碳水 {summary.get('total_carbs', 0):.0f}g，"
        f"蛋白质 {summary.get('total_protein', 0):.0f}g，"
        f"脂肪 {summary.get('total_fat', 0):.0f}g"
    )

    user_content = (
        f"用户刚记录了{meal_label}：{foods_text}。\n"
        f"营养概况：{summary_text}。\n"
        "请像营养老师一样，用一两句温和自然的话陪用户聊聊这一餐，"
        "讲讲值得注意的营养点或小建议。"
    )

    return [
        SystemMessage(content=NARRATE_SYSTEM),
        HumanMessage(content=user_content),
    ]


__all__ = ["build_diet_narrate_messages"]
