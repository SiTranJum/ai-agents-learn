"""计划曲线生成器 + 完成率服务单元测试。

不依赖数据库：曲线生成器是纯函数；完成率服务用 fake repo 注入。
对应设计文档 §5.3 / §5.9。
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest

from app.core.exceptions import ValidationException
from app.db.models.plan import Plan, SubPlan
from app.schemas.plan import PlanDimension, TargetCurveStrategy
from app.services.plan_compliance_service import PlanComplianceService
from app.services.plan_curve_service import generate_curve


def _plan(start: date, end: date, phases: list | None = None) -> Plan:
    return Plan(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="减重",
        goal_description="lose weight",
        plan_type="weight_loss",
        status="active",
        start_date=start,
        target_date=end,
        tasks=[],
        phases=phases or [],
    )


def _sub_plan(plan: Plan, dimension: str, tasks: list | None = None, weight: float = 1.0) -> SubPlan:
    return SubPlan(
        id=uuid.uuid4(),
        user_id=plan.user_id,
        plan_id=plan.id,
        dimension=dimension,
        name=dimension,
        goal_description="gd",
        status="active",
        tasks=tasks or [],
        weight=weight,
    )


# ---------- 目标曲线生成器 ----------


def test_linear_curve_endpoints_and_count() -> None:
    plan = _plan(date(2026, 6, 1), date(2026, 6, 10))
    sub = _sub_plan(plan, "weight")
    rows = generate_curve(
        plan=plan, sub_plan=sub, strategy=TargetCurveStrategy.linear,
        unit="kg", start_value=70.0, end_value=65.0,
    )
    assert len(rows) == 10            # 6/1 ~ 6/10 闭区间共 10 天
    assert rows[0].target_value == 70.0
    assert rows[-1].target_value == 65.0
    # 中间点单调递减
    assert rows[1].target_value < rows[0].target_value


def test_constant_curve_all_equal() -> None:
    plan = _plan(date(2026, 6, 1), date(2026, 6, 5))
    sub = _sub_plan(plan, "water")
    rows = generate_curve(
        plan=plan, sub_plan=sub, strategy=TargetCurveStrategy.constant,
        unit="ml", constant_value=2000.0,
    )
    assert len(rows) == 5
    assert all(r.target_value == 2000.0 for r in rows)


def test_linear_curve_missing_values_raises() -> None:
    plan = _plan(date(2026, 6, 1), date(2026, 6, 10))
    sub = _sub_plan(plan, "weight")
    with pytest.raises(ValidationException):
        generate_curve(
            plan=plan, sub_plan=sub, strategy=TargetCurveStrategy.linear, unit="kg"
        )


def test_phased_curve_falls_back_to_linear_when_no_phases() -> None:
    plan = _plan(date(2026, 6, 1), date(2026, 6, 10))  # phases 为空
    sub = _sub_plan(plan, "weight")
    rows = generate_curve(
        plan=plan, sub_plan=sub, strategy=TargetCurveStrategy.phased,
        unit="kg", start_value=70.0, end_value=65.0,
    )
    assert len(rows) == 10
    assert rows[0].target_value == 70.0
    assert rows[-1].target_value == 65.0


# ---------- 完成率服务 ----------


class _FakeSession:
    def __init__(self, count_result: int = 0) -> None:
        self._count_result = count_result

    async def execute(self, _stmt):  # noqa: ANN001
        class _R:
            def __init__(self, value: int) -> None:
                self._value = value

            def scalar_one(self) -> int:
                return self._value

        return _R(self._count_result)


class _FakeBodyRepo:
    def __init__(self, user_id: uuid.UUID, *, exercise_count: int = 0, values: dict | None = None) -> None:
        self.user_id = user_id
        self.session = _FakeSession(count_result=exercise_count)
        self._values = values or {}

    async def list_weight(self, **kwargs):  # noqa: ANN003
        return self._values.get("weight", [])

    async def list_water(self, **kwargs):  # noqa: ANN003
        return self._values.get("water", [])

    async def list_sleep(self, **kwargs):  # noqa: ANN003
        return self._values.get("sleep", [])

    async def list_measurement(self, **kwargs):  # noqa: ANN003
        return self._values.get("measurement", [])


class _FakePlanRepo:
    def __init__(self, user_id: uuid.UUID, *, sub_plans: list, daily_targets: list) -> None:
        self.user_id = user_id
        self._sub_plans = sub_plans
        self._daily_targets = daily_targets

    async def list_sub_plans(self, _plan_id):  # noqa: ANN001
        return self._sub_plans

    async def list_daily_targets(self, _plan_id, **kwargs):  # noqa: ANN001, ANN003
        return self._daily_targets

    async def list_executions(self, _plan_id, **kwargs):  # noqa: ANN001, ANN003
        return []


def _target_row(plan: Plan, sub: SubPlan, day: date, value: float, unit: str):
    return type(
        "DT", (),
        {"date": day, "target_value": value, "unit": unit, "dimension": sub.dimension,
         "sub_plan_id": sub.id, "plan_id": plan.id},
    )()


def _weight_record(day: date, weight: float):
    return type("W", (), {"date": day, "weight": weight})()


@pytest.mark.asyncio
async def test_value_dimension_full_attainment() -> None:
    """实际体重 == 目标体重 → 达成度 1.0。"""
    plan = _plan(date(2026, 6, 1), date(2026, 6, 3))
    sub = _sub_plan(plan, "weight")
    targets = [
        _target_row(plan, sub, date(2026, 6, 1), 70.0, "kg"),
        _target_row(plan, sub, date(2026, 6, 2), 69.5, "kg"),
    ]
    body_values = {
        "weight": [_weight_record(date(2026, 6, 1), 70.0), _weight_record(date(2026, 6, 2), 69.5)]
    }
    plan_repo = _FakePlanRepo(plan.user_id, sub_plans=[sub], daily_targets=targets)
    body_repo = _FakeBodyRepo(plan.user_id, values=body_values)
    svc = PlanComplianceService(plan_repo=plan_repo, body_repo=body_repo)
    result = await svc.compute_overall(plan, as_of=date(2026, 6, 3))
    assert result.overall_compliance == 1.0
    assert result.dimensions[0].dimension == PlanDimension.weight


@pytest.mark.asyncio
async def test_task_dimension_partial_completion() -> None:
    """每周一/三/五运动，应完成数 vs 实际打卡数。"""
    plan = _plan(date(2026, 6, 1), date(2026, 6, 7))  # 6/1 周一 ~ 6/7 周日
    task = {
        "id": str(uuid.uuid4()),
        "description": "跑步",
        "exercise_type": "running",
        "schedule": {"weekdays": [1, 3, 5]},  # 周一/三/五
    }
    sub = _sub_plan(plan, "exercise", tasks=[task])
    # 6/1(一)、6/3(三)、6/5(五) → 应完成 3 次；实际打卡 2 次
    plan_repo = _FakePlanRepo(plan.user_id, sub_plans=[sub], daily_targets=[])
    body_repo = _FakeBodyRepo(plan.user_id, exercise_count=2)
    svc = PlanComplianceService(plan_repo=plan_repo, body_repo=body_repo)
    result = await svc.compute_overall(plan, as_of=date(2026, 6, 7))
    dim = result.dimensions[0]
    assert dim.expected_count == 3
    assert dim.actual_count == 2
    assert dim.compliance_rate == pytest.approx(2 / 3, abs=1e-3)


@pytest.mark.asyncio
async def test_overall_weighted_aggregation() -> None:
    """两个子计划按权重加权聚合。"""
    plan = _plan(date(2026, 6, 1), date(2026, 6, 3))
    # 运动：应完成 1 次（仅 6/1 周一），实际 1 次 → 1.0，权重 2.0
    ex_task = {"id": str(uuid.uuid4()), "description": "跑", "exercise_type": "running",
               "schedule": {"weekdays": [1]}}
    ex_sub = _sub_plan(plan, "exercise", tasks=[ex_task], weight=2.0)
    # 体重：达成度 1.0，权重 1.0
    w_sub = _sub_plan(plan, "weight", weight=1.0)
    targets = [_target_row(plan, w_sub, date(2026, 6, 1), 70.0, "kg")]
    body_values = {"weight": [_weight_record(date(2026, 6, 1), 70.0)]}

    class _MultiPlanRepo(_FakePlanRepo):
        async def list_daily_targets(self, _plan_id, **kwargs):  # noqa: ANN001, ANN003
            # 只有 weight 子计划有曲线
            if kwargs.get("sub_plan_id") == w_sub.id:
                return targets
            return []

    plan_repo = _MultiPlanRepo(plan.user_id, sub_plans=[ex_sub, w_sub], daily_targets=targets)
    body_repo = _FakeBodyRepo(plan.user_id, exercise_count=1, values=body_values)
    svc = PlanComplianceService(plan_repo=plan_repo, body_repo=body_repo)
    result = await svc.compute_overall(plan, as_of=date(2026, 6, 1))
    # (1.0*2 + 1.0*1) / 3 = 1.0
    assert result.overall_compliance == 1.0
    assert len(result.dimensions) == 2
