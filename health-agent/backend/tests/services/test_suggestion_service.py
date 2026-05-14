"""Phase 9 - SuggestionService tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.db.models.suggestion import Suggestion
from app.schemas.suggestion import (
    FeedbackCreate,
    FeedbackRating,
    SuggestionDraft,
    SuggestionPriority,
    SuggestionType,
)
from app.services.suggestion_service import SuggestionService


class _FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class _FakeRepo:
    def __init__(self) -> None:
        self.session = _FakeSession()
        self.rows: list[Suggestion] = []

    async def list_valid(self, *, suggestion_type=None, meal_type=None, now=None, limit=3):
        _ = now
        rows = self.rows
        if suggestion_type is not None:
            rows = [row for row in rows if row.suggestion_type == suggestion_type.value]
        if meal_type is not None:
            rows = [row for row in rows if row.meal_type == meal_type]
        return rows[:limit]

    async def create(self, suggestion: Suggestion) -> Suggestion:
        now = datetime.now(UTC)
        suggestion.id = uuid.uuid4()
        suggestion.user_id = uuid.uuid4()
        suggestion.created_at = now
        suggestion.updated_at = now
        self.rows.append(suggestion)
        return suggestion

    async def get(self, suggestion_id: uuid.UUID) -> Suggestion | None:
        return next((row for row in self.rows if row.id == suggestion_id), None)

    async def set_feedback(self, suggestion: Suggestion, rating: FeedbackRating) -> Suggestion:
        suggestion.user_feedback = rating.value
        suggestion.feedback_at = datetime.now(UTC)
        return suggestion


@pytest.mark.asyncio
async def test_save_daily_and_cache() -> None:
    repo = _FakeRepo()
    service = SuggestionService(repo=repo)  # type: ignore[arg-type]
    draft = SuggestionDraft(
        type=SuggestionType.proactive_insight,
        title="今日提醒",
        content="今天饮水达到 2000ml。",
        priority=SuggestionPriority.medium,
    )

    saved = await service.save_daily([draft])
    cached = await service.get_cached_daily()

    assert saved.suggestions[0].title == "今日提醒"
    assert cached is not None
    assert repo.session.commits == 1


@pytest.mark.asyncio
async def test_save_meal_and_feedback() -> None:
    repo = _FakeRepo()
    service = SuggestionService(repo=repo)  # type: ignore[arg-type]

    meal = await service.save_meal(
        "lunch",
        [SuggestionDraft(type=SuggestionType.diet_advice, title="午餐", content="鸡蛋, 豆腐", meal_type="lunch")],
        "补充蛋白质",
    )
    item = await service.submit_feedback(meal.suggestion_id, FeedbackCreate(rating=FeedbackRating.helpful))

    assert meal.suggestions == ["鸡蛋", "豆腐"]
    assert item.id == meal.suggestion_id
    assert repo.rows[0].user_feedback == "helpful"

