"""AI suggestion schemas."""
# ruff: noqa: RUF001

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

DISCLAIMER = "本建议仅用于日常健康管理参考，不能替代专业医疗诊断或治疗。"


class SuggestionType(StrEnum):
    diet_advice = "diet_advice"
    goal_advice = "goal_advice"
    trend_advice = "trend_advice"
    proactive_insight = "proactive_insight"


class SuggestionRequestType(StrEnum):
    daily = "daily"
    meal = "meal"
    insight = "insight"


class SuggestionPriority(StrEnum):
    high = "high"
    medium = "medium"
    low = "low"


class FeedbackRating(StrEnum):
    helpful = "helpful"
    not_helpful = "not_helpful"
    dismissed = "dismissed"


class SuggestionItem(BaseModel):
    id: UUID
    type: SuggestionType
    title: str
    content: str
    basis: str | None = None
    priority: SuggestionPriority
    expires_at: datetime | None = None
    created_at: datetime


class DailySuggestionResponse(BaseModel):
    suggestions: list[SuggestionItem] = Field(max_length=3)
    generated_at: datetime
    disclaimer: str = DISCLAIMER


class NutritionSummary(BaseModel):
    calories: float = 0
    protein: float = 0
    fat: float = 0
    carbs: float = 0


class MealSuggestionResponse(BaseModel):
    suggestion_id: UUID
    meal_type: str
    consumed_today: NutritionSummary
    remaining: NutritionSummary
    suggestions: list[str] = Field(max_length=5)
    reasoning: str
    disclaimer: str = DISCLAIMER


class InsightItem(BaseModel):
    id: UUID
    dimension: str
    finding: str
    suggestion: str
    data_support: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime


class InsightResponse(BaseModel):
    insights: list[InsightItem] = Field(max_length=3)
    period: str
    disclaimer: str = DISCLAIMER


class FeedbackCreate(BaseModel):
    rating: FeedbackRating


class SuggestionDraft(BaseModel):
    type: SuggestionType = SuggestionType.proactive_insight
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=500)
    basis: str | None = Field(default=None, max_length=500)
    priority: SuggestionPriority = SuggestionPriority.medium
    meal_type: str | None = None
    dimension: str | None = None
    data_support: dict[str, Any] = Field(default_factory=dict)


class SuggestionAgentOutput(BaseModel):
    suggestions: list[SuggestionDraft] = Field(default_factory=list, max_length=5)
    reasoning: str = "基于当前健康数据和目标生成。"


__all__ = [
    "DISCLAIMER",
    "DailySuggestionResponse",
    "FeedbackCreate",
    "FeedbackRating",
    "InsightItem",
    "InsightResponse",
    "MealSuggestionResponse",
    "NutritionSummary",
    "SuggestionAgentOutput",
    "SuggestionDraft",
    "SuggestionItem",
    "SuggestionPriority",
    "SuggestionRequestType",
    "SuggestionType",
]


