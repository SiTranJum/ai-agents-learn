"""Plan API endpoints."""

from __future__ import annotations

import asyncio
import uuid
from contextlib import suppress
from datetime import date, datetime, timezone
from typing import Annotated, Any, AsyncIterator

from fastapi import APIRouter, Query, status

from app.agents.plan.conversation import run_plan_conversation
from app.core.exceptions import ConflictException, ValidationException
from app.core.responses import paginated, success
from app.dependencies import (
    CurrentUserWithProfileDep,
    MemoryServiceDep,
    PlanAgentDep,
    PlanServiceDep,
)
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.plan import (
    AdjustmentProposalResponse,
    CheckInCreate,
    CheckInResponse,
    DailyExecution,
    DailyTargetCurve,
    DailyTargetPoint,
    ExecutionStatus,
    OverallCompliance,
    PlanAnalysisResponse,
    PlanCreate,
    PlanDimension,
    PlanProgress,
    PlanResponse,
    PlanStatus,
    PlanStreamRequest,
    PlanTerminateRequest,
    PlanUpdate,
    ProposalStatus,
    SubPlanCreate,
    SubPlanResponse,
    SubPlanUpdate,
)
from app.services.plan_check_in_task import generate_exercise_record_from_check_in
from app.streaming import StreamEvent, StreamEventType, sse_response

router = APIRouter(prefix="/plans", tags=["plans"])
_BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()

_PLAN_WAIT_STATUS_LABELS = (
    "正在理解你的目标...",
    "正在读取你的档案和记忆...",
    "正在判断信息是否足够...",
    "正在起草阶段化计划...",
    "正在进行安全校验...",
)


def _resolve_stream_message(payload: PlanStreamRequest) -> str:
    if payload.type == "text":
        if not payload.message:
            raise ValidationException("Missing plan message", code="PLAN_MESSAGE_REQUIRED")
        return payload.message
    if payload.type == "choice_response":
        if payload.free_text:
            return payload.free_text
        if payload.selected_value:
            return payload.selected_value
        raise ValidationException("Missing choice response", code="PLAN_CHOICE_REQUIRED")
    if payload.type == "card_action":
        return payload.message or f"[card_action] {payload.action_id or 'action'}"
    raise ValidationException("Unsupported request type", code="PLAN_STREAM_TYPE_INVALID")


def _chunk_text(text: str, chunk_size: int = 80) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


def _plan_draft_intro_text(card: dict[str, Any]) -> str:
    if card.get("type") != "plan_draft":
        return ""
    return "\n\n我把草案放在下面了。先看目标、周期和第一阶段任务；需要看完整阶段时再展开。\n"


@router.post("", response_model=ApiResponse[PlanResponse], status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreate,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    plan_agent: PlanAgentDep,
) -> dict[str, Any]:
    if await service.has_active_plan():
        raise ConflictException("Active plan already exists", code="PLAN_ALREADY_ACTIVE")
    result = await plan_agent.ainvoke(
        {
            "user_id": str(user.id),
            "goal_description": payload.goal_description,
            "plan_type": payload.plan_type,
            "profile": user.profile,
            "plan_service": service,
        }
    )
    if result.get("error"):
        raise ValidationException("Plan creation failed", code=str(result["error"]))
    data = result["result"]
    return success(data.model_dump(mode="json"))


@router.post("/stream")
async def create_plan_stream(
    payload: PlanStreamRequest,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    memory_service: MemoryServiceDep,
):
    message_id = uuid.uuid4().hex
    user_text = _resolve_stream_message(payload)

    async def gen() -> AsyncIterator[StreamEvent]:
        yield StreamEvent(
            type=StreamEventType.META,
            data={"message_id": message_id, "session_id": payload.session_id, "started_at": datetime.now(timezone.utc).isoformat()},
        )
        yield StreamEvent(type=StreamEventType.STATUS, data={"node": "handle_plan_turn", "label": "正在理解你的计划需求..."})
        task = asyncio.create_task(
            run_plan_conversation(
                user_message=user_text,
                messages=payload.messages,
                profile=user.profile,
                plan_service=service,
                memory_service=memory_service,
                plan_type_hint=payload.plan_type_hint,
                request_type=payload.type,
                action_id=payload.action_id,
                action_payload=payload.action_payload,
            )
        )
        status_index = 0
        long_wait_notice_sent = False
        try:
            while True:
                done, _ = await asyncio.wait({task}, timeout=2.5)
                if done:
                    break
                if not long_wait_notice_sent:
                    yield StreamEvent(
                        type=StreamEventType.TEXT_DELTA,
                        data={"content": "信息够了，我正在结合你的档案起草计划草案。草案不会自动保存，确认后才会创建。\n\n"},
                    )
                    long_wait_notice_sent = True
                label = _PLAN_WAIT_STATUS_LABELS[min(status_index, len(_PLAN_WAIT_STATUS_LABELS) - 1)]
                yield StreamEvent(type=StreamEventType.STATUS, data={"node": "handle_plan_turn", "label": label})
                status_index += 1
            result = await task
        except asyncio.CancelledError:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            raise
        except ValidationException as exc:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                data={"code": exc.code or "PLAN_STREAM_FAILED", "message": exc.message, "retriable": False},
            )
            return
        except Exception as exc:  # pragma: no cover
            yield StreamEvent(
                type=StreamEventType.ERROR,
                data={"code": "PLAN_STREAM_FAILED", "message": str(exc) or "Plan conversation failed", "retriable": True},
            )
            return

        text = str(result.get("ai_response") or "")
        for chunk in _chunk_text(text):
            yield StreamEvent(type=StreamEventType.TEXT_DELTA, data={"content": chunk})
        for card in result.get("response_cards", []) or []:
            intro = _plan_draft_intro_text(card)
            if intro:
                for chunk in _chunk_text(intro):
                    yield StreamEvent(type=StreamEventType.TEXT_DELTA, data={"content": chunk})
            yield StreamEvent(type=StreamEventType.CARD, data={"card": card})
        for prompt in result.get("choice_prompts", []) or []:
            yield StreamEvent(type=StreamEventType.CHOICE, data=prompt)
        yield StreamEvent(type=StreamEventType.DONE, data={"message_id": message_id, "session_id": payload.session_id})

    return await sse_response(gen(), endpoint="plans/stream")


@router.get("", response_model=PaginatedResponse[PlanResponse])
async def list_plans(
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    plan_status: Annotated[PlanStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> dict[str, Any]:
    _ = user
    items, total = await service.list_plans(status=plan_status, page=page, page_size=page_size)
    return paginated([item.model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


@router.get("/{plan_id}", response_model=ApiResponse[PlanResponse])
async def get_plan(plan_id: uuid.UUID, user: CurrentUserWithProfileDep, service: PlanServiceDep) -> dict[str, Any]:
    _ = user
    data = await service.get_plan(plan_id)
    return success(data.model_dump(mode="json"))


@router.put("/{plan_id}", response_model=ApiResponse[PlanResponse])
async def update_plan(
    plan_id: uuid.UUID,
    payload: PlanUpdate,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
) -> dict[str, Any]:
    _ = user
    data = await service.update_plan(plan_id, payload)
    return success(data.model_dump(mode="json"))


@router.delete("/{plan_id}", response_model=ApiResponse[object])
async def terminate_plan(
    plan_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    payload: PlanTerminateRequest | None = None,
) -> dict[str, Any]:
    _ = user
    await service.terminate_plan(plan_id, payload.reason if payload else None)
    return success(None, message="Plan terminated")


@router.post("/{plan_id}/check-ins", response_model=ApiResponse[CheckInResponse], status_code=status.HTTP_201_CREATED)
async def create_check_in(
    plan_id: uuid.UUID,
    payload: CheckInCreate,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
) -> dict[str, Any]:
    data = await service.create_check_in(plan_id, payload)
    # 后台任务：如果是运动任务打卡，自动生成运动记录
    if payload.completed and payload.task_id is not None:
        task = asyncio.create_task(
            generate_exercise_record_from_check_in(user.id, data.id)
        )
        _BACKGROUND_TASKS.add(task)
        task.add_done_callback(_BACKGROUND_TASKS.discard)
    return success(data.model_dump(mode="json"))


@router.get("/{plan_id}/progress", response_model=ApiResponse[PlanProgress])
async def get_progress(plan_id: uuid.UUID, user: CurrentUserWithProfileDep, service: PlanServiceDep) -> dict[str, Any]:
    _ = user
    data = await service.get_progress(plan_id)
    return success(data.model_dump(mode="json"))


@router.get("/{plan_id}/execution", response_model=PaginatedResponse[DailyExecution])
async def list_execution(
    plan_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    execution_status: Annotated[ExecutionStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> dict[str, Any]:
    _ = user
    items, total = await service.list_execution_records(
        plan_id,
        start_date=start_date,
        end_date=end_date,
        status=execution_status,
        page=page,
        page_size=page_size,
    )
    return paginated([item.model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


# ---------- 子计划 ----------


@router.get("/{plan_id}/sub-plans", response_model=ApiResponse[list[SubPlanResponse]])
async def list_sub_plans(
    plan_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
) -> dict[str, Any]:
    """列出计划下的所有子计划。"""
    _ = user
    items = await service.list_sub_plans(plan_id)
    return success([item.model_dump(mode="json") for item in items])


@router.post("/{plan_id}/sub-plans", response_model=ApiResponse[SubPlanResponse], status_code=status.HTTP_201_CREATED)
async def create_sub_plan(
    plan_id: uuid.UUID,
    payload: SubPlanCreate,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
) -> dict[str, Any]:
    """创建子计划并生成目标曲线。"""
    _ = user
    data = await service.create_sub_plan(plan_id, payload)
    return success(data.model_dump(mode="json"))


@router.put("/{plan_id}/sub-plans/{sub_plan_id}", response_model=ApiResponse[SubPlanResponse])
async def update_sub_plan(
    plan_id: uuid.UUID,
    sub_plan_id: uuid.UUID,
    payload: SubPlanUpdate,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
) -> dict[str, Any]:
    """更新子计划。"""
    _ = user
    data = await service.update_sub_plan(plan_id, sub_plan_id, payload)
    return success(data.model_dump(mode="json"))


# ---------- 每日目标曲线 ----------


@router.get("/{plan_id}/daily-targets", response_model=ApiResponse[list[DailyTargetCurve]])
async def get_daily_targets(
    plan_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    dimension: Annotated[PlanDimension | None, Query()] = None,
    start_date: Annotated[date | None, Query(alias="start_date")] = None,
    end_date: Annotated[date | None, Query(alias="end_date")] = None,
) -> dict[str, Any]:
    """获取目标曲线（供数据模块消费）。按子计划/维度分组返回。"""
    _ = user
    curves = await service.get_daily_target_curves(
        plan_id, dimension=dimension, start_date=start_date, end_date=end_date
    )
    return success([curve.model_dump(mode="json") for curve in curves])


# ---------- 完成率 ----------


@router.get("/{plan_id}/compliance", response_model=ApiResponse[OverallCompliance])
async def get_compliance(
    plan_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
) -> dict[str, Any]:
    """计算整体完成率（加权聚合各子计划维度）。"""
    _ = user
    data = await service.compute_compliance(plan_id)
    return success(data.model_dump(mode="json"))


# ---------- AI 分析 ----------


@router.get("/{plan_id}/analyses", response_model=ApiResponse[list[PlanAnalysisResponse]])
async def list_analyses(
    plan_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    limit: Annotated[int, Query(ge=1, le=90)] = 30,
) -> dict[str, Any]:
    """获取 AI 分析历史（最近 N 条）。"""
    _ = user
    items = await service.list_analyses(plan_id, limit=limit)
    return success([item.model_dump(mode="json") for item in items])


# ---------- 调整提议 ----------


@router.get("/{plan_id}/proposals", response_model=ApiResponse[list[AdjustmentProposalResponse]])
async def list_proposals(
    plan_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
    proposal_status: Annotated[ProposalStatus | None, Query(alias="status")] = None,
) -> dict[str, Any]:
    """获取调整提议列表（默认 pending）。"""
    _ = user
    items = await service.list_proposals(plan_id, status=proposal_status)
    return success([item.model_dump(mode="json") for item in items])


@router.post("/{plan_id}/proposals/{proposal_id}/accept", response_model=ApiResponse[SubPlanResponse])
async def accept_proposal(
    plan_id: uuid.UUID,
    proposal_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
) -> dict[str, Any]:
    """接受调整提议 → 应用修改并重新生成目标曲线。"""
    _ = user
    data = await service.accept_proposal(plan_id, proposal_id)
    return success(data.model_dump(mode="json"))


@router.post("/{plan_id}/proposals/{proposal_id}/reject", response_model=ApiResponse[object])
async def reject_proposal(
    plan_id: uuid.UUID,
    proposal_id: uuid.UUID,
    user: CurrentUserWithProfileDep,
    service: PlanServiceDep,
) -> dict[str, Any]:
    """拒绝调整提议 → 置为 rejected 终态。"""
    _ = user
    await service.reject_proposal(plan_id, proposal_id)
    return success(None, message="Proposal rejected")


__all__ = ["router"]
