"""统一的 human-in-the-loop interrupt 协议。

所有"需要等用户作答才能继续"的暂停点，都通过 :func:`ask_human` 抛出一个
``HumanPrompt``。前端用一套逻辑渲染（choice chips / 富卡片），用户作答后由 API 层
用 ``Command(resume=<答案>)`` 恢复，``ask_human`` 直接返回该答案 dict。

设计参考: docs/plans/2026-06-12-checkpointer-interrupt-pause-resume.md §2.1
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

PromptKind = Literal["choice", "card"]
PromptDomain = Literal["diet", "body", "plan"]


class ChoiceOption(BaseModel):
    """选项 chip 的单个选项（与 streaming.events.ChoiceOption 字段一致）。"""

    value: str
    label: str
    description: str | None = None


class HumanPrompt(BaseModel):
    """``interrupt()`` 抛出的统一载荷。

    - ``kind="choice"``：用 ``question`` + ``options`` 渲染选项 chips。
    - ``kind="card"``：用 ``card`` 渲染富卡片，按钮来自 ``card["actions"]``。
    """

    kind: PromptKind
    prompt_id: str
    domain: PromptDomain
    question: str | None = None
    options: list[ChoiceOption] = Field(default_factory=list)
    allow_free_text: bool = False
    card: dict[str, Any] | None = None


def ask_human(prompt: HumanPrompt) -> dict[str, Any]:
    """在节点内暂停 graph，把 ``prompt`` 抛给调用方，恢复后返回用户答案。

    返回的 dict 协议（由 API 层 ``build_resume_payload`` 构造）::

        # choice 回答
        {"prompt_id": ..., "value": "lunch"}
        {"prompt_id": ..., "free_text": "下午茶"}
        # card 回答
        {"prompt_id": ..., "action": "confirm"}
        {"prompt_id": ..., "action": "edit", "patch": {...}}
        {"prompt_id": ..., "action": "cancel"}

    重要：``interrupt()`` 第一次执行会抛出 ``GraphInterrupt`` 暂停；恢复时**整个节点
    从头重跑**，但这次 ``interrupt()`` 直接返回答案。因此调用 ``ask_human`` **之前**
    的代码必须幂等、无副作用（不要在它之前落库或发消息）。
    """
    # 延迟导入：langgraph 是可选运行时依赖，单测桩环境下不强制安装。
    from langgraph.types import interrupt

    answer = interrupt(prompt.model_dump(mode="json"))
    return answer if isinstance(answer, dict) else {"value": answer}


def choice_answer(answer: dict[str, Any]) -> str | None:
    """从 choice 类型的 resume 答案提取用户选择值。"""
    return answer.get("value") or answer.get("free_text")


def card_action(answer: dict[str, Any]) -> str:
    """从 card 类型的 resume 答案提取动作（confirm/edit/cancel/accept/revise）。"""
    return str(answer.get("action") or "confirm")


__all__ = [
    "ChoiceOption",
    "HumanPrompt",
    "ask_human",
    "card_action",
    "choice_answer",
]
