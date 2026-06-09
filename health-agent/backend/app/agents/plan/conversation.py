"""计划页与全局 AI 共用的计划对话编排器。"""

from __future__ import annotations

import json
import logging
import math
import re
from datetime import date, timedelta
from typing import Any

from app.agents._logging import llm_call
from app.agents.base import get_chat_model
from app.agents.prompts.plan_draft import build_plan_draft_messages
from app.schemas.chat import ChatCardAction
from app.schemas.memory import MemoryRecallResult
from app.schemas.plan import (
    PlanConversationMessage,
    PlanDraft,
    PlanPhase,
    PlanPhaseDraft,
    PlanProgress,
    PlanResponse,
    PlanTargets,
    PlanTask,
    PlanTaskUpdate,
    PlanType,
)

logger = logging.getLogger(__name__)

_CREATE_KEYWORDS = (
    "plan",
    "goal",
    "weight_loss",
    "nutrition_adjustment",
    "habit_formation",
    "减重",
    "减肥",
    "减脂",
    "瘦",
    "增肌",
    "习惯",
    "计划",
    "目标",
    "饮食",
    "营养",
    "外卖",
    "零食",
    "热量",
    "喝水",
    "运动",
    "睡眠",
    "早睡",
    "作息",
)
_QUERY_KEYWORDS = ("progress", "status", "phase", "进度", "阶段", "执行", "完成", "打卡", "当前计划")
_MODIFY_KEYWORDS = ("adjust", "change", "modify", "revise", "调整", "修改", "优化", "太难", "不适合")
_GREETING_TEXTS = {"你好", "您好", "hello", "hi", "嗨", "在吗", "哈喽", "hey"}
_AFFIRMATIVE_TEXTS = {"是", "是的", "对", "对的", "嗯", "可以", "好的", "好", "确认", "yes", "ok"}


def _detect_plan_type(text: str, explicit: PlanType | None = None) -> PlanType:
    if explicit is not None:
        return explicit
    lowered = text.lower()
    if any(keyword in lowered for keyword in ("减重", "减肥", "减脂", "weight loss", "lose weight")):
        return PlanType.weight_loss
    if re.search(r"(?:减|瘦)\s*\d+(?:\.\d+)?\s*(?:kg|公斤|斤)", text, flags=re.IGNORECASE):
        return PlanType.weight_loss
    if any(keyword in lowered for keyword in ("营养", "饮食", "蛋白", "nutrition", "calorie", "meal")):
        return PlanType.nutrition_adjustment
    return PlanType.habit_formation


def _parse_duration_days(text: str) -> int | None:
    patterns = [
        (r"(\d+)\s*(?:个?月|months?)", 28),
        (r"(\d+)\s*(?:周|weeks?)", 7),
        (r"(\d+)\s*(?:天|days?)", 1),
    ]
    for pattern, multiplier in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = int(match.group(1))
            return max(7, min(value * multiplier, 168))
    return None


def _parse_target_weight(text: str) -> float | None:
    explicit = re.search(
        r"(?:目标体重|到|减到|target weight)\D{0,6}(\d+(?:\.\d+)?)\s*(?:kg|公斤)?",
        text,
        flags=re.IGNORECASE,
    )
    if explicit:
        return float(explicit.group(1))

    bare = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|公斤)", text, flags=re.IGNORECASE)
    if bare:
        prefix = text[max(0, bare.start() - 3) : bare.start()]
        if not re.search(r"[减瘦增]\s*$", prefix):
            return float(bare.group(1))
    return None


def _parse_weight_delta(text: str) -> float | None:
    match = re.search(r"(?:减|瘦)\s*(\d+(?:\.\d+)?)\s*(斤|kg|公斤)", text, flags=re.IGNORECASE)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    return value / 2 if unit == "斤" else value


def _infer_request_mode(text: str) -> str:
    lowered = text.lower()
    if any(keyword in lowered for keyword in _MODIFY_KEYWORDS):
        return "modify"
    if any(keyword in lowered for keyword in _QUERY_KEYWORDS):
        return "query"
    if any(keyword in lowered for keyword in _CREATE_KEYWORDS):
        return "create"
    if re.search(r"(?:减|瘦|增)\s*\d+(?:\.\d+)?\s*(?:kg|公斤|斤)", text, flags=re.IGNORECASE):
        return "create"
    return "unknown"


def _is_greeting_only(text: str) -> bool:
    normalized = re.sub(r"[\s，。！？!?,.～~]+", "", text.strip().lower())
    return bool(normalized) and normalized in _GREETING_TEXTS


def _normalized_short_text(text: str) -> str:
    return re.sub(r"[\s，。！？!?,.～~]+", "", text.strip().lower())


def _is_affirmative_only(text: str) -> bool:
    normalized = _normalized_short_text(text)
    return bool(normalized) and normalized in _AFFIRMATIVE_TEXTS


def _is_identity_question(text: str) -> bool:
    normalized = _normalized_short_text(text)
    return normalized in {"你是谁", "你是干嘛的", "你能干嘛", "你会什么", "whatareyou"} or "你是谁" in text


def _user_text_from_transcript(transcript: list[PlanConversationMessage]) -> str:
    return "\n".join(message.content for message in transcript if message.role == "user")


def _has_plan_intent(text: str, plan_type_hint: PlanType | None) -> bool:
    if plan_type_hint is not None:
        return True
    lowered = text.lower()
    if any(keyword in lowered for keyword in _CREATE_KEYWORDS):
        return True
    return bool(re.search(r"(?:减|瘦|增)\s*\d+(?:\.\d+)?\s*(?:kg|公斤|斤)", text, flags=re.IGNORECASE))


def _has_concrete_goal(text: str) -> bool:
    if _parse_target_weight(text) is not None:
        return True
    if re.search(r"(?:减|瘦|增)\s*\d+(?:\.\d+)?\s*(?:kg|公斤|斤)", text, flags=re.IGNORECASE):
        return True
    goal_phrases = (
        "改善饮食",
        "控制热量",
        "少吃外卖",
        "戒零食",
        "多喝水",
        "稳定睡眠",
        "早睡",
        "运动习惯",
        "提高蛋白",
        "增肌",
    )
    return any(phrase in text for phrase in goal_phrases)


def _has_timeframe_or_constraints(text: str) -> bool:
    return _parse_duration_days(text) is not None


def _plan_goal_from_transcript(transcript: list[PlanConversationMessage]) -> str:
    user_lines = [message.content.strip() for message in transcript if message.role == "user" and message.content.strip()]
    return "；".join(user_lines)


def _latest_plan_draft_from_transcript(transcript: list[PlanConversationMessage]) -> PlanDraft | None:
    for message in reversed(transcript):
        content = message.content.strip()
        if not content.startswith("[plan_draft]"):
            continue
        raw = content.removeprefix("[plan_draft]").strip()
        try:
            return PlanDraft.model_validate_json(raw)
        except Exception as exc:  # pragma: no cover - defensive against old clients
            logger.info("failed to parse plan draft from transcript: %s", exc)
            return None
    return None


def _clarify_plan_intent_response(has_active_plan: bool) -> dict[str, Any]:
    if has_active_plan:
        text = "你好，我可以帮你查看当前计划进度、解释今天任务，或者调整现有计划。你想先看哪一项？"
    else:
        text = "你好，我可以帮你制定健康计划。你可以直接告诉我目标，比如“12 周减 4kg”、“改善饮食结构”或“建立稳定睡眠作息”。"
    return {
        "ai_response": text,
        "response_cards": [],
        "choice_prompts": [
            {
                "prompt_id": "plan_intent",
                "question": "你想先做哪类计划？",
                "options": [
                    {"value": "weight_loss", "label": "减重计划"},
                    {"value": "nutrition_adjustment", "label": "饮食调整"},
                    {"value": "habit_formation", "label": "习惯养成"},
                ],
                "allow_free_text": True,
            }
        ],
    }


def _starter_choice_prompts() -> list[dict[str, Any]]:
    return [
        {
            "prompt_id": "plan_starter",
            "question": "也可以直接选一个方向开始：",
            "options": [
                {"value": "12 周减 4kg", "label": "12 周减 4kg"},
                {"value": "8 周改善饮食结构", "label": "改善饮食"},
                {"value": "6 周建立运动习惯", "label": "运动习惯"},
            ],
            "allow_free_text": True,
        }
    ]


def _followup_greeting_response() -> dict[str, Any]:
    return {
        "ai_response": "我在。你可以继续告诉我计划目标、周期或限制，我会根据缺的信息继续追问。",
        "response_cards": [],
        "choice_prompts": [],
    }


def _identity_response() -> dict[str, Any]:
    return {
        "ai_response": "我是你的健康计划助手，主要帮你把减重、饮食、运动或作息目标拆成可执行计划。你可以直接说目标和周期，比如“12 周减 4kg”。",
        "response_cards": [],
        "choice_prompts": [],
    }


def _ambiguous_affirmative_response() -> dict[str, Any]:
    return {
        "ai_response": "我还不知道你具体确认哪件事。请直接告诉我目标和周期，比如“12 周减 4kg”，或者点一个计划类型后补充目标。",
        "response_cards": [],
        "choice_prompts": [],
    }


def _unknown_plan_page_response(has_history: bool) -> dict[str, Any]:
    text = (
        "这句话还不足以制定计划。请告诉我一个具体目标，例如想减多少、多久完成，或者想改善哪类饮食/睡眠/运动习惯。"
        if has_history
        else "我可以帮你制定健康计划。请直接说目标和周期，例如“12 周减 4kg”。"
    )
    return {
        "ai_response": text,
        "response_cards": [],
        "choice_prompts": [] if has_history else _starter_choice_prompts(),
    }


def _clarify_missing_details_response(text: str) -> dict[str, Any]:
    if not _has_concrete_goal(text):
        question = "你想达成的具体结果是什么？比如目标体重、想减少几斤，或想改善哪类饮食/作息问题。"
        prompts = _starter_choice_prompts()
    else:
        question = "目标方向我明白了。再补充一下你希望多久完成，以及有没有饮食、运动、作息上的限制或偏好。"
        prompts = [
            {
                "prompt_id": "plan_duration",
                "question": "你希望用多久来完成？",
                "options": [
                    {"value": "4 周", "label": "4 周"},
                    {"value": "8 周", "label": "8 周"},
                    {"value": "12 周", "label": "12 周"},
                ],
                "allow_free_text": True,
            }
        ]
    return {
        "ai_response": question,
        "response_cards": [],
        "choice_prompts": prompts,
    }


def _profile_snapshot(profile: object | None) -> dict[str, Any]:
    if profile is None:
        return {}
    return {
        "gender": getattr(profile, "gender", None),
        "birth_date": str(getattr(profile, "birth_date", None) or ""),
        "height": getattr(profile, "height", None),
        "current_weight": getattr(profile, "current_weight", None),
        "target_weight": getattr(profile, "target_weight", None),
        "daily_calorie_target": getattr(profile, "daily_calorie_target", None),
    }


def _memory_lines(items: list[MemoryRecallResult]) -> list[str]:
    return [item.content for item in items if getattr(item, "content", "").strip()]


def _build_default_draft(
    *,
    goal: str,
    profile: object | None,
    plan_type: PlanType,
    duration_days: int | None,
    target_weight: float | None,
) -> PlanDraft:
    start = date.today()
    total_days = duration_days or 84
    end = start + timedelta(days=total_days - 1)
    current_weight = getattr(profile, "current_weight", None)
    daily_calories = getattr(profile, "daily_calorie_target", None) or 1800
    resolved_weight = target_weight or getattr(profile, "target_weight", None)
    if resolved_weight is None and current_weight is not None and plan_type == PlanType.weight_loss:
        resolved_weight = float(current_weight) - 3
    if plan_type == PlanType.weight_loss:
        title = "减重计划"
        tasks = [
            PlanTaskUpdate(description=f"每日热量控制在约 {int(daily_calories)} kcal"),
            PlanTaskUpdate(description="每天步行或运动至少 30 分钟"),
            PlanTaskUpdate(description="晚餐尽量清淡，避免含糖饮料", time_period="晚餐"),
        ]
    elif plan_type == PlanType.nutrition_adjustment:
        title = "营养调整计划"
        tasks = [
            PlanTaskUpdate(description="每顿正餐都加入优质蛋白来源"),
            PlanTaskUpdate(description="每天至少两餐加入蔬菜"),
            PlanTaskUpdate(description="减少高加工零食和含糖饮料"),
        ]
    else:
        title = "习惯养成计划"
        tasks = [
            PlanTaskUpdate(description="每天步数达到 8000 步"),
            PlanTaskUpdate(description="每天饮水约 2000 ml"),
            PlanTaskUpdate(description="保持稳定作息", time_period="晚上"),
        ]
    phase_split = max(total_days // 2, 1)
    phases = [
        PlanPhaseDraft(
            title="第一阶段",
            goal="先建立稳定的基础执行节奏，降低一开始的执行压力。",
            start_date=start,
            end_date=min(end, start + timedelta(days=phase_split - 1)),
            tasks=tasks[:2],
        ),
        PlanPhaseDraft(
            title="第二阶段",
            goal="在维持稳定节奏的基础上，提升执行质量并逐步固化习惯。",
            start_date=min(end, start + timedelta(days=phase_split)),
            end_date=end,
            tasks=tasks,
        ),
    ]
    if phases[1].start_date > phases[1].end_date:
        phases = [PlanPhaseDraft(title="第一阶段", goal="安全完成当前计划。", start_date=start, end_date=end, tasks=tasks)]
    return PlanDraft(
        name=title,
        goal_description=goal,
        plan_type=plan_type,
        start_date=start,
        target_date=end,
        targets=PlanTargets(
            daily_calories=int(daily_calories) if daily_calories else None,
            protein_target=90,
            fat_target=55,
            carbs_target=220,
            weight_target=resolved_weight,
        ),
        tasks=tasks,
        phases=phases,
    )


async def _generate_draft(
    *,
    goal: str,
    transcript: list[PlanConversationMessage],
    profile: object | None,
    memories: list[MemoryRecallResult],
    plan_type_hint: PlanType | None,
) -> PlanDraft:
    plan_type = _detect_plan_type(goal, plan_type_hint)
    duration_days = _parse_duration_days(goal)
    target_weight = _parse_target_weight(goal)
    weight_delta = _parse_weight_delta(goal)
    fallback = _build_default_draft(
        goal=goal,
        profile=profile,
        plan_type=plan_type,
        duration_days=duration_days,
        target_weight=target_weight
        if target_weight is not None
        else (
            float(getattr(profile, "current_weight", 0) or 0) - weight_delta
            if weight_delta is not None and getattr(profile, "current_weight", None) is not None
            else None
        ),
    )
    try:
        model = get_chat_model(temperature=0.2, timeout=60).with_structured_output(PlanDraft)
        async with llm_call("plan_conversation_draft", "qwen-plus", goal=goal):
            draft = await model.ainvoke(
                build_plan_draft_messages(
                    goal_description=goal,
                    plan_type=plan_type.value,
                    profile=profile,
                    transcript=[message.model_dump(mode="json") for message in transcript],
                    memories=_memory_lines(memories),
                )
            )
        return draft
    except Exception as exc:  # pragma: no cover - dev fallback without model access
        logger.info("plan conversation fallback draft used: %s", exc)
        return fallback


def _violation_message(violations: list[str], adjusted: PlanDraft, profile: object | None) -> str:
    explanations: list[str] = []
    if "CALORIES_BELOW_BMR" in violations:
        bmr = None
        if profile is not None:
            try:
                weight = float(getattr(profile, "current_weight", 0) or 0)
                height = float(getattr(profile, "height", 0) or 0)
                birth_date = getattr(profile, "birth_date", None)
                gender = getattr(profile, "gender", None)
                if weight and height and birth_date and gender in {"male", "female"}:
                    age = max(date.today().year - birth_date.year, 1)
                    bmr = round(10 * weight + 6.25 * height - 5 * age + (5 if gender == "male" else -161), 1)
            except Exception:  # pragma: no cover
                bmr = None
        if adjusted.targets.daily_calories is not None:
            if bmr is not None:
                explanations.append(
                    f"你给出的热量目标低于估算安全下限，按当前档案推测基础代谢大约在 {math.ceil(bmr)} kcal 左右。"
                    f"我已经把计划调整到更安全的 {adjusted.targets.daily_calories} kcal。"
                )
            else:
                explanations.append(
                    f"你给出的热量目标偏低，我已先调整为更安全的 {adjusted.targets.daily_calories} kcal。"
                )
    if "WEIGHT_LOSS_TOO_FAST" in violations:
        explanations.append("你设定的减重速度过快，我已把周期放宽到更安全的范围。")
    if "PLAN_DURATION_INVALID" in violations:
        explanations.append("你设定的周期不在安全支持范围内，我已调整到 1 到 24 周的合理区间。")
    if not explanations:
        explanations.append("我发现当前草案存在安全问题，已经先调整成更稳妥的版本。")
    return "".join(explanations) + "如果你接受这个调整后的版本，直接确认即可，我会继续保存计划。"


def _draft_card(draft: PlanDraft, *, violations: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "plan_draft",
        "payload": {
            "draft": draft.model_dump(mode="json"),
            "violations": violations or [],
        },
        "actions": [
            ChatCardAction(kind="accept_plan_draft", label="确认创建").model_dump(mode="json"),
            ChatCardAction(kind="revise_plan_draft", label="继续调整").model_dump(mode="json"),
        ],
    }


def _saved_card(plan: PlanResponse) -> dict[str, Any]:
    return {
        "type": "plan_saved",
        "payload": {
            "plan_id": str(plan.id),
            "plan": plan.model_dump(mode="json"),
        },
        "actions": [
            ChatCardAction(kind="view_plan_detail", label="查看计划").model_dump(mode="json"),
        ],
    }


def _progress_card(plan: PlanResponse, progress: PlanProgress) -> dict[str, Any]:
    return {
        "type": "plan_progress",
        "payload": {
            "plan_id": str(plan.id),
            "plan_name": plan.name,
            "status": plan.status.value,
            "completed_tasks": progress.completed_tasks,
            "total_tasks": progress.total_tasks,
            "compliance_rate": progress.compliance_rate,
            "streak_days": progress.streak_days,
            "current_phase": _current_phase_label(plan.phases),
        },
        "actions": [
            ChatCardAction(kind="view_plan_detail", label="查看详情").model_dump(mode="json"),
        ],
    }


def _current_phase_label(phases: list[PlanPhase]) -> str | None:
    if not phases:
        return None
    today = date.today()
    for phase in phases:
        if phase.start_date <= today <= phase.end_date:
            return phase.title
    return phases[0].title


def _transcript(messages: list[PlanConversationMessage], latest_message: str | None) -> list[PlanConversationMessage]:
    transcript = list(messages)
    if latest_message:
        if not transcript or transcript[-1].role != "user" or transcript[-1].content != latest_message:
            transcript.append(PlanConversationMessage(role="user", content=latest_message))
    return transcript


def _message_from_action(action_id: str | None, payload: dict[str, Any] | None) -> str:
    if action_id == "accept_plan_draft":
        return "请保存这个计划。"
    if action_id == "revise_plan_draft":
        return "我想继续调整这个计划。"
    if action_id == "view_plan_detail":
        return "查看计划详情。"
    if payload:
        return json.dumps(payload, ensure_ascii=True)
    return action_id or ""


def _query_text(plan: PlanResponse, progress: PlanProgress) -> str:
    phase = _current_phase_label(plan.phases) or "当前阶段"
    compliance = round(progress.compliance_rate * 100)
    return (
        f"你当前的激活计划是《{plan.name}》。"
        f"当前阶段：{phase}。"
        f"今日任务完成：{progress.completed_tasks}/{progress.total_tasks}。"
        f"近期执行达标率：{compliance}%。"
        f"当前连续达标天数：{progress.streak_days} 天。"
    )


def _modification_text(plan: PlanResponse, reasons: list[str]) -> str:
    if reasons:
        return f"我看了《{plan.name}》当前执行情况，建议你这样调整：" + " ".join(reasons)
    return (
        f"《{plan.name}》目前整体还算稳定。"
        "如果你想修改，可以直接告诉我要调整热量、周期、任务强度还是计划目标。"
    )


async def run_plan_conversation(
    *,
    user_message: str | None,
    messages: list[PlanConversationMessage],
    profile: object | None,
    plan_service: Any,
    memory_service: Any | None = None,
    plan_type_hint: PlanType | None = None,
    request_type: str = "text",
    action_id: str | None = None,
    action_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return plan conversation output compatible with streaming chat wrapper."""

    resolved_message = user_message or _message_from_action(action_id, action_payload)
    transcript = _transcript(messages, resolved_message)

    if request_type == "card_action" and action_id == "accept_plan_draft":
        draft_payload = (action_payload or {}).get("draft", action_payload or {})
        draft = PlanDraft.model_validate(draft_payload)
        saved = await plan_service.create_plan_from_draft(draft)
        return {
            "ai_response": f"《{saved.name}》已保存。接下来你可以在详情页查看阶段、任务和执行进度。",
            "response_cards": [_saved_card(saved)],
            "choice_prompts": [],
        }

    if request_type == "card_action" and action_id == "revise_plan_draft":
        return {
            "ai_response": "告诉我你想改哪一部分：目标、周期、热量、阶段任务，还是整个计划方向。",
            "response_cards": [],
            "choice_prompts": [],
        }

    active_plan = await plan_service.get_active_plan()
    mode = _infer_request_mode(resolved_message or "")

    if _is_identity_question(resolved_message or ""):
        return _identity_response()

    if _is_affirmative_only(resolved_message or ""):
        pending_draft = _latest_plan_draft_from_transcript(transcript)
        if pending_draft is not None:
            saved = await plan_service.create_plan_from_draft(pending_draft)
            return {
                "ai_response": f"《{saved.name}》已保存。接下来你可以在详情页查看阶段、任务和执行进度。",
                "response_cards": [_saved_card(saved)],
                "choice_prompts": [],
            }
        return _ambiguous_affirmative_response()

    if _is_greeting_only(resolved_message or ""):
        if len(transcript) > 1:
            return _followup_greeting_response()
        return _clarify_plan_intent_response(active_plan is not None)

    if active_plan is not None and mode == "query":
        progress = await plan_service.get_progress(active_plan.id)
        return {
            "ai_response": _query_text(active_plan, progress),
            "response_cards": [_progress_card(active_plan, progress)],
            "choice_prompts": [],
        }

    if active_plan is not None and mode == "modify":
        reasons = await plan_service.run_modification_rules(active_plan.id)
        progress = await plan_service.get_progress(active_plan.id)
        return {
            "ai_response": _modification_text(active_plan, reasons),
            "response_cards": [_progress_card(active_plan, progress)],
            "choice_prompts": [],
        }

    if active_plan is not None and mode == "create":
        progress = await plan_service.get_progress(active_plan.id)
        return {
            "ai_response": "你已经有一个激活中的计划了。我可以先帮你解释当前进度，或者先调整现有计划，再决定是否新建。",
            "response_cards": [_progress_card(active_plan, progress)],
            "choice_prompts": [],
        }

    if not (resolved_message or "").strip():
        return {
            "ai_response": "先告诉我你想达成什么结果，比如“12 周减 4kg”、“改善饮食结构”或者“建立稳定睡眠作息”。",
            "response_cards": [],
            "choice_prompts": [],
        }

    combined_user_text = _user_text_from_transcript(transcript)
    if not _has_plan_intent(combined_user_text, plan_type_hint):
        return _unknown_plan_page_response(len(transcript) > 1)
    if not _has_concrete_goal(combined_user_text) or not _has_timeframe_or_constraints(combined_user_text):
        return _clarify_missing_details_response(combined_user_text)

    recalled: list[MemoryRecallResult] = []
    if memory_service is not None:
        try:
            recalled = await memory_service.recall_memories(combined_user_text, intent="create_plan", top_k=4)
        except Exception as exc:  # pragma: no cover - graceful degradation
            logger.info("plan memory recall skipped: %s", exc)

    draft = await _generate_draft(
        goal=_plan_goal_from_transcript(transcript),
        transcript=transcript,
        profile=profile,
        memories=recalled,
        plan_type_hint=plan_type_hint,
    )
    draft = plan_service.normalize_draft(draft)
    violations = plan_service.safety_check(draft, profile)
    if violations:
        adjusted = plan_service.build_safe_adjusted_draft(draft, violations)
        return {
            "ai_response": _violation_message(violations, adjusted, profile),
            "response_cards": [_draft_card(adjusted, violations=violations)],
            "choice_prompts": [],
        }

    return {
        "ai_response": "我已经结合你的档案和本轮需求起草了一版分阶段计划。你先看看，如果合适就直接确认保存。",
        "response_cards": [_draft_card(draft)],
        "choice_prompts": [],
    }


__all__ = ["run_plan_conversation"]
