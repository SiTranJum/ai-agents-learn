"""计划打卡后台任务：任务完成 → 自动生成运动记录。

触发链路：
    用户对运动任务打卡 (POST /plans/{id}/check-ins, completed=true)
        │  仅写 plan_check_ins，立即返回（不阻塞接口）
        ▼
    投递后台任务 enqueue(generate_exercise_record, check_in_id)
        │  沿用项目现有 asyncio.create_task 后台模式
        ▼ 后台执行
    1. 读取 check_in → 找到 task_id → 读 SubPlan.tasks 里的任务定义
    2. 幂等校验：按 (task_id, date) 查 body_exercise_records 是否已存在
       - 已存在 → 跳过（防重复）
    3. 用任务的 target（exercise_type/duration/calories）生成 ExerciseRecord
       source="plan_task"，回填 plan_id/sub_plan_id/task_id
    4. 写入成功 → 该日该任务的"实际完成"即被数据模块感知

设计文档：``docs/plans/2026-06-09-plan-module-design.md`` §5.5
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.body import ExerciseRecord
from app.db.models.plan import PlanCheckIn, SubPlan
from app.db.repositories.body_repo import BodyRepository
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def generate_exercise_record_from_check_in(
    user_id: uuid.UUID,
    check_in_id: uuid.UUID,
) -> None:
    """后台任务：从打卡记录自动生成运动记录（幂等）。

    Args:
        user_id: 用户 ID（用于构造 repo）
        check_in_id: 打卡记录 ID
    """
    async with AsyncSessionLocal() as session:
        try:
            check_in = await _get_check_in(session, user_id, check_in_id)
            if check_in is None:
                logger.warning("Check-in not found: %s", check_in_id)
                return
            if not check_in.completed:
                # 打卡标记为未完成，不生成记录
                return
            if check_in.task_id is None:
                # 非任务级打卡（可能是子计划级或计划级），跳过
                return
            # 幂等校验：同一任务同一天只生成一次
            existing = await _existing_exercise(session, user_id, check_in.task_id, check_in.date)
            if existing is not None:
                logger.info(
                    "ExerciseRecord already exists for task=%s date=%s, skip",
                    check_in.task_id,
                    check_in.date,
                )
                return
            # 读取任务定义（从 SubPlan.tasks JSONB）
            sub_plan = await _get_sub_plan_for_task(session, user_id, check_in.plan_id, check_in.task_id)
            if sub_plan is None:
                logger.warning(
                    "SubPlan not found for check-in plan=%s task=%s",
                    check_in.plan_id,
                    check_in.task_id,
                )
                return
            task_def = _find_task(sub_plan.tasks, check_in.task_id)
            if task_def is None:
                logger.warning("Task not found in SubPlan tasks: %s", check_in.task_id)
                return
            # 生成 ExerciseRecord
            exercise_type = task_def.get("exercise_type") or "unknown"
            target = task_def.get("target") or {}
            duration = int(target.get("duration_minutes") or 30)
            calories = int(target.get("calories") or 0)
            record = ExerciseRecord(
                user_id=user_id,
                date=check_in.date,
                exercise_type=exercise_type,
                duration_minutes=duration,
                calories=calories,
                note=check_in.note,
                plan_id=check_in.plan_id,
                sub_plan_id=sub_plan.id,
                task_id=check_in.task_id,
                source="plan_task",
            )
            body_repo = BodyRepository(session=session, user_id=user_id)
            await body_repo.create_exercise(record)
            await session.commit()
            logger.info(
                "Generated ExerciseRecord id=%s for check-in=%s task=%s date=%s",
                record.id,
                check_in_id,
                check_in.task_id,
                check_in.date,
            )
        except Exception:
            logger.exception("Failed to generate exercise record for check-in=%s", check_in_id)
            await session.rollback()


async def _get_check_in(
    session: AsyncSession, user_id: uuid.UUID, check_in_id: uuid.UUID
) -> PlanCheckIn | None:
    stmt = select(PlanCheckIn).where(
        PlanCheckIn.user_id == user_id,
        PlanCheckIn.id == check_in_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def _existing_exercise(
    session: AsyncSession, user_id: uuid.UUID, task_id: uuid.UUID, target_date
) -> ExerciseRecord | None:
    stmt = select(ExerciseRecord).where(
        ExerciseRecord.user_id == user_id,
        ExerciseRecord.task_id == task_id,
        ExerciseRecord.date == target_date,
        ExerciseRecord.deleted_at.is_(None),
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def _get_sub_plan_for_task(
    session: AsyncSession, user_id: uuid.UUID, plan_id: uuid.UUID, task_id: uuid.UUID
) -> SubPlan | None:
    """找到包含指定 task_id 的 SubPlan（遍历 tasks JSONB）。"""
    from sqlalchemy import cast, func  # noqa: PLC0415
    from sqlalchemy.dialects.postgresql import JSONB  # noqa: PLC0415

    # 用 PostgreSQL JSONB 函数 jsonb_array_elements 查找任务
    stmt = select(SubPlan).where(
        SubPlan.user_id == user_id,
        SubPlan.plan_id == plan_id,
        SubPlan.deleted_at.is_(None),
        func.jsonb_array_elements(cast(SubPlan.tasks, JSONB)).op("->>")(
            "id"
        ) == str(task_id),
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def _find_task(tasks: list[dict], task_id: uuid.UUID) -> dict | None:
    """从 tasks JSONB 列表中找出 id 匹配的任务定义。"""
    for task in tasks:
        if not isinstance(task, dict):
            continue
        try:
            if uuid.UUID(str(task.get("id"))) == task_id:
                return task
        except (ValueError, TypeError):
            continue
    return None


__all__ = ["generate_exercise_record_from_check_in"]
