"""目标曲线生成服务。

将子计划的"总目标"按天展开成 DailyTarget 序列，供数据模块叠加在实际趋势图上。

策略：
- linear:  起点值 → 终点值，按天均匀过渡（默认，适合体重）
- constant: 每天目标相同（适合饮水/运动时长）
- phased:  按 ``Plan.phases`` 分段，每段内部线性插值

设计文档：``docs/plans/2026-06-09-plan-module-design.md`` §5.3
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from app.core.exceptions import ValidationException
from app.db.models.plan import DailyTarget, Plan, SubPlan
from app.schemas.plan import TargetCurveStrategy


def _phase_segments(plan: Plan) -> list[tuple[date, date]]:
    """从 Plan.phases 提取 (start, end) 区间列表。"""
    segments: list[tuple[date, date]] = []
    for phase in plan.phases or []:
        if not isinstance(phase, dict):
            continue
        start_raw = phase.get("start_date")
        end_raw = phase.get("end_date")
        if not start_raw or not end_raw:
            continue
        try:
            start = date.fromisoformat(str(start_raw))
            end = date.fromisoformat(str(end_raw))
        except ValueError:
            continue
        if end >= start:
            segments.append((start, end))
    return segments


def _linear_points(
    start_value: float, end_value: float, start_date: date, end_date: date
) -> list[tuple[date, float]]:
    """从 start→end 线性插值，inclusive 两端点。"""
    days = (end_date - start_date).days
    if days <= 0:
        return [(start_date, start_value)]
    step = (end_value - start_value) / days
    return [
        (start_date + timedelta(days=i), round(start_value + step * i, 4))
        for i in range(days + 1)
    ]


def generate_curve(
    *,
    plan: Plan,
    sub_plan: SubPlan,
    strategy: TargetCurveStrategy,
    unit: str,
    start_value: float | None = None,
    end_value: float | None = None,
    constant_value: float | None = None,
) -> list[DailyTarget]:
    """根据策略生成 DailyTarget 列表（未关联 user_id，由 repo 层填充）。

    Args:
        plan: 主计划，提供 start_date/target_date/phases。
        sub_plan: 子计划，提供 plan_id/sub_plan_id/dimension。
        strategy: 曲线策略。
        unit: 目标值单位（kg/ml/min/kcal…）。
        start_value: 起点值（linear 必填）。
        end_value: 终点值（linear 必填）。
        constant_value: 恒定值（constant 必填）。

    Raises:
        ValidationException: 策略缺少必要参数时。
    """
    rows: list[DailyTarget] = []
    if strategy == TargetCurveStrategy.linear:
        if start_value is None or end_value is None:
            raise ValidationException(
                "Linear curve requires start_value and end_value",
                code="CURVE_LINEAR_VALUES_REQUIRED",
            )
        for day, value in _linear_points(start_value, end_value, plan.start_date, plan.target_date):
            rows.append(_make_row(plan, sub_plan, day, value, unit))
        return rows

    if strategy == TargetCurveStrategy.constant:
        if constant_value is None:
            raise ValidationException(
                "Constant curve requires constant_value",
                code="CURVE_CONSTANT_VALUE_REQUIRED",
            )
        days = (plan.target_date - plan.start_date).days + 1
        for i in range(max(days, 1)):
            day = plan.start_date + timedelta(days=i)
            rows.append(_make_row(plan, sub_plan, day, constant_value, unit))
        return rows

    if strategy == TargetCurveStrategy.phased:
        if start_value is None or end_value is None:
            raise ValidationException(
                "Phased curve requires start_value and end_value",
                code="CURVE_PHASED_VALUES_REQUIRED",
            )
        segments = _phase_segments(plan)
        if not segments:
            # 退化为整段线性
            return generate_curve(
                plan=plan,
                sub_plan=sub_plan,
                strategy=TargetCurveStrategy.linear,
                unit=unit,
                start_value=start_value,
                end_value=end_value,
            )
        # 跨阶段按总进度均分起止值，每段内部线性
        total_span = sum((seg[1] - seg[0]).days + 1 for seg in segments)
        cursor_value = start_value
        days_traversed = 0
        for seg_start, seg_end in segments:
            seg_days = (seg_end - seg_start).days + 1
            days_traversed += seg_days
            seg_end_value = round(
                start_value + (end_value - start_value) * (days_traversed / total_span), 4
            )
            for day, value in _linear_points(cursor_value, seg_end_value, seg_start, seg_end):
                rows.append(_make_row(plan, sub_plan, day, value, unit))
            cursor_value = seg_end_value
        return rows

    raise ValidationException(f"Unknown curve strategy: {strategy}", code="CURVE_STRATEGY_INVALID")


def _make_row(
    plan: Plan, sub_plan: SubPlan, target_date: date, value: float, unit: str
) -> DailyTarget:
    return DailyTarget(
        id=uuid.uuid4(),
        plan_id=plan.id,
        sub_plan_id=sub_plan.id,
        dimension=sub_plan.dimension,
        date=target_date,
        target_value=float(value),
        unit=unit,
    )


__all__: list[str] = ["generate_curve"]
