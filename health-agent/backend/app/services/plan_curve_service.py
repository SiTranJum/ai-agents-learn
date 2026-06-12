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


# 减重曲线相邻日变化上限（kg），约对应每周 1kg 安全速率
_WEIGHT_DAILY_DROP_LIMIT = 0.15


def build_curve_from_anchors(
    *,
    plan: Plan,
    sub_plan: SubPlan,
    anchors: list[tuple[int, float]],
    unit: str = "kg",
    expected_current_weight: float | None = None,
    expected_target_weight: float | None = None,
) -> list[DailyTarget]:
    """从 LLM 直出的锚点（3-5个）插值成逐日曲线，并做校验（方案 C）。

    Args:
        anchors: [(day_offset, target_weight), ...] —— LLM 给 3-5 个关键点，含首尾。
        expected_current_weight: 校验第一个锚点必须等于此值（允许 ±0.5kg 容差）。
        expected_target_weight:  校验最后一个锚点必须等于此值（允许 ±0.5kg 容差）。

    Raises:
        ValidationException: 锚点数量不合规 / 不单调 / 速率超限 / 端点不匹配 时抛出。
    """
    if not anchors:
        raise ValidationException("weight_anchors is empty", code="ANCHORS_EMPTY")
    if len(anchors) < 2:
        raise ValidationException(
            f"weight_anchors must have at least 2 anchors (start+end), got {len(anchors)}",
            code="ANCHORS_TOO_FEW",
        )
    total_days = (plan.target_date - plan.start_date).days + 1

    # 1) 排序锚点 + 终点 off-by-one 容错
    # LLM 常把"N 天计划"的终点放在 day_offset=N，而合法范围是 0..total_days-1。
    # 若最后一个锚点正好越界 1 天，clamp 回 total_days-1，避免误判拒绝。
    sorted_anchors = sorted(anchors, key=lambda x: x[0])
    if sorted_anchors[-1][0] == total_days:
        last_off, last_w = sorted_anchors[-1]
        sorted_anchors[-1] = (total_days - 1, last_w)
    first_offset, first_weight = sorted_anchors[0]
    last_offset, last_weight = sorted_anchors[-1]

    # 2) 端点校验
    if first_offset != 0:
        raise ValidationException(
            f"weight_anchors must start at day_offset=0, got {first_offset}",
            code="ANCHORS_START_OFFSET_INVALID",
        )
    if last_offset != total_days - 1:
        raise ValidationException(
            f"weight_anchors must end at day_offset={total_days-1}, got {last_offset}",
            code="ANCHORS_END_OFFSET_INVALID",
        )
    if expected_current_weight is not None and abs(first_weight - expected_current_weight) > 0.5:
        raise ValidationException(
            f"weight_anchors start={first_weight} != current_weight={expected_current_weight}",
            code="ANCHORS_START_MISMATCH",
        )
    if expected_target_weight is not None and abs(last_weight - expected_target_weight) > 0.5:
        raise ValidationException(
            f"weight_anchors end={last_weight} != target_weight={expected_target_weight}",
            code="ANCHORS_END_MISMATCH",
        )

    # 3) 单调性 + 相邻锚点间平均速率校验
    for i in range(1, len(sorted_anchors)):
        prev_offset, prev_w = sorted_anchors[i - 1]
        cur_offset, cur_w = sorted_anchors[i]
        delta_weight = cur_w - prev_w
        delta_days = cur_offset - prev_offset
        if delta_weight > 1e-6:
            raise ValidationException(
                f"weight_anchors not monotonic at offset={cur_offset} (prev={prev_w}, cur={cur_w})",
                code="ANCHORS_NOT_MONOTONIC",
            )
        # 平均速率 = delta_weight / delta_days，不能超过 1kg/7天 = 约 0.143kg/天
        if delta_days > 0:
            avg_daily_drop = abs(delta_weight) / delta_days
            if avg_daily_drop > _WEIGHT_DAILY_DROP_LIMIT + 1e-6:
                raise ValidationException(
                    f"weight_anchors segment drop too fast: {delta_weight}kg over {delta_days} days "
                    f"(avg {avg_daily_drop:.3f} kg/day)",
                    code="ANCHORS_DROP_TOO_FAST",
                )

    # 4) 在锚点间线性插值，生成逐日点（避免重复锚点）
    interpolated_points: list[tuple[int, float]] = []
    for i in range(len(sorted_anchors) - 1):
        start_offset, start_weight = sorted_anchors[i]
        end_offset, end_weight = sorted_anchors[i + 1]
        seg_start = plan.start_date + timedelta(days=start_offset)
        seg_end = plan.start_date + timedelta(days=end_offset)
        # 插值该段,但只取到倒数第二个点(避免终点重复)
        points_in_seg = _linear_points(start_weight, end_weight, seg_start, seg_end)
        for day, weight in points_in_seg[:-1]:  # 不含终点
            offset = (day - plan.start_date).days
            interpolated_points.append((offset, weight))
    # 最后补上真正的终点
    interpolated_points.append((last_offset, last_weight))

    # 5) 落地为 DailyTarget
    rows: list[DailyTarget] = []
    for offset, weight in interpolated_points:
        day = plan.start_date + timedelta(days=offset)
        rows.append(_make_row(plan, sub_plan, day, weight, unit))
    return rows


__all__: list[str] = ["build_curve_from_anchors", "generate_curve"]
