"""计划完成率计算服务。

口径定义（详见 ``docs/plans/2026-06-09-plan-module-design.md`` §5.9）：

任务型维度（exercise）：
    单维度完成率 = 已完成任务次数 / 应完成任务次数（截至今日）
    "应完成次数" 由 ``schedule.weekdays`` 在 [start_date, today] 区间内推算

数值型维度（weight/water/sleep/measurement/nutrition）：
    单日达成度 = 1 - min(1, |实际值 - 目标值| / 容差带)
    单维度完成率 = 平均(各有记录日的单日达成度)

整体完成率：
    Σ(子计划完成率 × 子计划权重) / Σ(子计划权重)
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.db.models.plan import Plan, SubPlan
from app.db.repositories.body_repo import BodyRepository
from app.db.repositories.plan_repo import PlanRepository
from app.schemas.plan import (
    DimensionCompliance,
    OverallCompliance,
    PlanDimension,
)

# 数值型维度的容差带（绝对值或目标值的相对比例）
_TOLERANCE_ABS: dict[str, float] = {
    PlanDimension.weight.value: 0.5,           # ±0.5 kg
    PlanDimension.sleep.value: 30.0,           # ±30 分钟
}
_TOLERANCE_RATIO: dict[str, float] = {
    PlanDimension.water.value: 0.20,           # 目标的 ±20%
    PlanDimension.nutrition.value: 0.10,       # 热量的 ±10%
    PlanDimension.measurement.value: 0.05,     # 围度的 ±5%
}

_TASK_DIMENSIONS = {PlanDimension.exercise.value}


class PlanComplianceService:
    """组合 PlanRepository + BodyRepository 计算完成率。"""

    def __init__(self, plan_repo: PlanRepository, body_repo: BodyRepository) -> None:
        self.plan_repo = plan_repo
        self.body_repo = body_repo

    async def compute_overall(
        self, plan: Plan, *, as_of: date | None = None
    ) -> OverallCompliance:
        """计算主计划的整体完成率（加权聚合各子计划）。"""
        today = as_of or date.today()
        sub_plans = await self.plan_repo.list_sub_plans(plan.id)
        dimensions: list[DimensionCompliance] = []
        weighted_sum = 0.0
        weight_total = 0.0
        for sub_plan in sub_plans:
            metric = await self._compute_dimension(plan, sub_plan, today)
            dimensions.append(metric)
            weight = max(sub_plan.weight, 0.0)
            weighted_sum += metric.compliance_rate * weight
            weight_total += weight
        overall = round(weighted_sum / weight_total, 4) if weight_total > 0 else 0.0
        return OverallCompliance(
            plan_id=plan.id,
            overall_compliance=overall,
            dimensions=dimensions,
        )

    async def _compute_dimension(
        self, plan: Plan, sub_plan: SubPlan, today: date
    ) -> DimensionCompliance:
        if sub_plan.dimension in _TASK_DIMENSIONS:
            return await self._compute_task_dimension(plan, sub_plan, today)
        return await self._compute_value_dimension(plan, sub_plan, today)

    # ---------- 任务型维度（运动） ----------

    async def _compute_task_dimension(
        self, plan: Plan, sub_plan: SubPlan, today: date
    ) -> DimensionCompliance:
        window_start = plan.start_date
        window_end = min(today, plan.target_date)
        expected = self._expected_task_count(sub_plan.tasks or [], window_start, window_end)
        actual = await self._actual_task_count(sub_plan.id, window_start, window_end)
        rate = round(min(actual, expected) / expected, 4) if expected > 0 else 0.0
        return DimensionCompliance(
            dimension=PlanDimension(sub_plan.dimension),
            sub_plan_id=sub_plan.id,
            compliance_rate=rate,
            expected_count=expected,
            actual_count=actual,
        )

    @staticmethod
    def _expected_task_count(
        tasks: list[dict[str, Any]], start: date, end: date
    ) -> int:
        """根据每个任务的 schedule.weekdays 累加 [start, end] 内应完成次数。"""
        if end < start:
            return 0
        # 预生成 [start, end] 各天的 ISO 周几
        from datetime import timedelta  # noqa: PLC0415

        weekdays_in_window: list[int] = []
        cursor = start
        while cursor <= end:
            weekdays_in_window.append(cursor.isoweekday())
            cursor += timedelta(days=1)
        total = 0
        for task in tasks:
            if not isinstance(task, dict):
                continue
            schedule = task.get("schedule") or {}
            weekdays = schedule.get("weekdays") if isinstance(schedule, dict) else None
            if not weekdays:
                # 没有 schedule 视为每天
                total += len(weekdays_in_window)
                continue
            weekday_set = {int(w) for w in weekdays if isinstance(w, int | str)}
            total += sum(1 for w in weekdays_in_window if w in weekday_set)
        return total

    async def _actual_task_count(
        self, sub_plan_id: Any, start: date, end: date
    ) -> int:
        """已生成的、关联本子计划的运动记录数（来源 source=plan_task）。"""
        from sqlalchemy import func, select  # noqa: PLC0415

        from app.db.models.body import ExerciseRecord  # noqa: PLC0415

        stmt = select(func.count()).select_from(ExerciseRecord).where(
            ExerciseRecord.user_id == self.body_repo.user_id,
            ExerciseRecord.deleted_at.is_(None),
            ExerciseRecord.sub_plan_id == sub_plan_id,
            ExerciseRecord.date >= start,
            ExerciseRecord.date <= end,
        )
        return int((await self.body_repo.session.execute(stmt)).scalar_one())

    # ---------- 数值型维度 ----------

    async def _compute_value_dimension(
        self, plan: Plan, sub_plan: SubPlan, today: date
    ) -> DimensionCompliance:
        window_start = plan.start_date
        window_end = min(today, plan.target_date)
        targets = await self.plan_repo.list_daily_targets(
            plan.id,
            sub_plan_id=sub_plan.id,
            start_date=window_start,
            end_date=window_end,
        )
        target_by_date = {t.date: t.target_value for t in targets}
        actuals = await self._actual_values(plan, sub_plan.dimension, window_start, window_end)
        attainments: list[float] = []
        for target_date, target_value in target_by_date.items():
            actual_value = actuals.get(target_date)
            if actual_value is None:
                continue
            tol = self._tolerance(sub_plan.dimension, target_value)
            if tol <= 0:
                attainments.append(1.0 if actual_value == target_value else 0.0)
                continue
            deviation = abs(actual_value - target_value)
            attainments.append(max(0.0, 1.0 - min(1.0, deviation / tol)))
        if not attainments:
            return DimensionCompliance(
                dimension=PlanDimension(sub_plan.dimension),
                sub_plan_id=sub_plan.id,
                compliance_rate=0.0,
                average_attainment=None,
            )
        avg = sum(attainments) / len(attainments)
        return DimensionCompliance(
            dimension=PlanDimension(sub_plan.dimension),
            sub_plan_id=sub_plan.id,
            compliance_rate=round(avg, 4),
            average_attainment=round(avg, 4),
        )

    @staticmethod
    def _tolerance(dimension: str, target_value: float) -> float:
        if dimension in _TOLERANCE_ABS:
            return _TOLERANCE_ABS[dimension]
        ratio = _TOLERANCE_RATIO.get(dimension)
        if ratio is None:
            return abs(target_value) * 0.10
        return abs(target_value) * ratio

    async def _actual_values(
        self, plan: Plan, dimension: str, start: date, end: date
    ) -> dict[date, float]:
        """从 BodyRepository 读取该维度在窗口内的"每日实际值"。"""
        if dimension == PlanDimension.weight.value:
            records = await self.body_repo.list_weight(
                start_date=start, end_date=end, offset=0, limit=500, ascending=True
            )
            return {r.date: float(r.weight) for r in records}
        if dimension == PlanDimension.water.value:
            records = await self.body_repo.list_water(
                start_date=start, end_date=end, offset=0, limit=500, ascending=True
            )
            return {r.date: float(r.amount_ml) for r in records}
        if dimension == PlanDimension.sleep.value:
            records = await self.body_repo.list_sleep(
                start_date=start, end_date=end, offset=0, limit=500, ascending=True
            )
            return {r.date: float(r.duration_minutes) for r in records}
        if dimension == PlanDimension.measurement.value:
            records = await self.body_repo.list_measurement(
                start_date=start, end_date=end, offset=0, limit=500, ascending=True
            )
            # 围度暂以腰围为代表值；后续按子计划具体维度细化
            return {r.date: float(r.waist) for r in records if r.waist is not None}
        if dimension == PlanDimension.nutrition.value:
            executions = await self.plan_repo.list_executions(
                plan.id,
                start_date=start,
                end_date=end,
                offset=0,
                limit=500,
                desc=False,
            )
            return {e.date: float(e.calories_consumed) for e in executions}
        return {}


__all__ = ["PlanComplianceService"]
