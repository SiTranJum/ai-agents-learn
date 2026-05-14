"""Phase 1 - UserService 单元测试（不依赖数据库）。"""
# ruff: noqa: RUF002

from __future__ import annotations

import uuid
from datetime import date
from types import SimpleNamespace

import pytest

from app.db.models.user import HealthProfile
from app.schemas.user import UserProfileUpdate
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


class _FakeRepo:
    def __init__(self) -> None:
        self.session = SimpleNamespace(commit=self._commit)
        self.profile = _make_profile(nickname="bob")
        self.commits = 0

    async def _commit(self) -> None:
        self.commits += 1

    async def update_profile(self, fields: dict[str, object]) -> HealthProfile:
        for key, value in fields.items():
            setattr(self.profile, key, value)
        return self.profile


class _FakeMemoryService:
    def __init__(self) -> None:
        self.updated: list[dict[str, object]] = []

    async def on_profile_updated(self, updated_data: dict[str, object]):
        self.updated.append(updated_data)
        return None


@pytest.mark.asyncio
async def test_update_profile_syncs_profile_memory() -> None:
    repo = _FakeRepo()
    memory = _FakeMemoryService()
    service = UserService(repo=repo, memory_service=memory)  # type: ignore[arg-type]

    response = await service.update_profile(
        user_id=uuid.uuid4(),
        data=UserProfileUpdate.model_validate({"current_weight": 66.0}),
    )

    assert response.current_weight == 66.0
    assert memory.updated == [{"current_weight": 66.0}]


