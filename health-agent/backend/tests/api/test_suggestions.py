"""Phase 9 - suggestions API tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from app.dependencies import (
    get_current_user_with_profile,
    get_memory_service,
    get_rag_service,
    get_suggestion_agent,
    get_suggestion_service,
)
from app.main import app
from app.schemas.auth import CurrentUser
from app.schemas.suggestion import (
    DailySuggestionResponse,
    FeedbackCreate,
    InsightResponse,
    MealSuggestionResponse,
    NutritionSummary,
    SuggestionDraft,
    SuggestionItem,
    SuggestionPriority,
    SuggestionType,
)


class _FakeSuggestionService:
    def __init__(self) -> None:
        self.suggestion_id = uuid.uuid4()
        self.feedback: FeedbackCreate | None = None

    async def get_cached_daily(self):
        return None

    async def get_cached_insights(self):
        return None

    async def save_daily(self, drafts):
        _ = drafts
        return DailySuggestionResponse(
            suggestions=[
                SuggestionItem(
                    id=self.suggestion_id,
                    type=SuggestionType.proactive_insight,
                    title="今日提醒",
                    content="饮水达到 2000ml。",
                    priority=SuggestionPriority.medium,
                    created_at=datetime.now(UTC),
                )
            ],
            generated_at=datetime.now(UTC),
        )

    async def save_meal(self, meal_type, drafts, reasoning):
        _ = drafts
        return MealSuggestionResponse(
            suggestion_id=self.suggestion_id,
            meal_type=meal_type,
            consumed_today=NutritionSummary(),
            remaining=NutritionSummary(calories=600, protein=30, fat=20, carbs=75),
            suggestions=["鸡蛋", "豆腐"],
            reasoning=reasoning or "补充蛋白质",
        )

    async def save_insights(self, drafts):
        _ = drafts
        return InsightResponse(insights=[], period="last_30_days")

    async def submit_feedback(self, suggestion_id, feedback):
        self.feedback = feedback
        return SuggestionItem(
            id=suggestion_id,
            type=SuggestionType.proactive_insight,
            title="今日提醒",
            content="饮水达到 2000ml。",
            priority=SuggestionPriority.medium,
            created_at=datetime.now(UTC),
        )


class _FakeAgent:
    async def ainvoke(self, state: dict[str, Any]):
        return {
            "filtered_suggestions": [
                SuggestionDraft(type=SuggestionType.proactive_insight, title="今日提醒", content="饮水达到 2000ml。")
            ],
            "reasoning": "基于目标生成",
        }


class _FakeMemoryService:
    pass


@pytest.fixture
async def suggestion_overrides():
    service = _FakeSuggestionService()

    async def _current_user() -> CurrentUser:
        user = CurrentUser(id=uuid.uuid4(), email="user@example.com")
        user.profile = object()
        return user

    async def _service() -> _FakeSuggestionService:
        return service

    def _agent() -> _FakeAgent:
        return _FakeAgent()

    async def _memory() -> _FakeMemoryService:
        return _FakeMemoryService()

    async def _rag() -> object:
        return object()

    app.dependency_overrides[get_current_user_with_profile] = _current_user
    app.dependency_overrides[get_suggestion_service] = _service
    app.dependency_overrides[get_suggestion_agent] = _agent
    app.dependency_overrides[get_memory_service] = _memory
    app.dependency_overrides[get_rag_service] = _rag
    try:
        yield service
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_daily_meal_insights_and_feedback(client: AsyncClient, suggestion_overrides) -> None:
    daily = await client.get("/api/v1/suggestions/daily")
    meal = await client.get("/api/v1/suggestions/meal", params={"meal_type": "lunch"})
    insights = await client.get("/api/v1/suggestions/insights")
    feedback = await client.post(f"/api/v1/suggestions/{suggestion_overrides.suggestion_id}/feedback", json={"rating": "helpful"})

    assert daily.status_code == 200
    assert daily.json()["data"]["suggestions"][0]["title"] == "今日提醒"
    assert meal.status_code == 200
    assert meal.json()["data"]["suggestions"] == ["鸡蛋", "豆腐"]
    assert insights.status_code == 200
    assert feedback.status_code == 204
    assert suggestion_overrides.feedback.rating.value == "helpful"

