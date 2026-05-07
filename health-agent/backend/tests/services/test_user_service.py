"""Phase 1 - UserService 单元测试（不依赖数据库）。"""

from __future__ import annotations

from datetime import date

from app.db.models.user import HealthProfile
from app.services.user_service import PROFILE_REQUIRED_FIELDS, UserService


def _make_profile(**fields: object) -> HealthProfile:
    p = HealthProfile()
    for k, v in fields.items():
        setattr(p, k, v)
    return p


def test_profile_completeness_zero() -> None:
    profile = _make_profile()
    assert UserService._calculate_completeness(profile) == 0.0


def test_profile_completeness_partial() -> None:
    profile = _make_profile(nickname="bob", height=170.0)
    pct = UserService._calculate_completeness(profile)
    assert pct == round(2 / len(PROFILE_REQUIRED_FIELDS), 4)


def test_profile_completeness_full() -> None:
    profile = _make_profile(
        nickname="bob",
        gender="male",
        birth_date=date(1990, 1, 1),
        height=170.0,
        current_weight=70.0,
        target_weight=65.0,
        activity_level="moderate",
    )
    assert UserService._calculate_completeness(profile) == 1.0
