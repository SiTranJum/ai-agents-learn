"""AI memory Pydantic schemas."""

from __future__ import annotations

from datetime import date as date_
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class MemoryType(StrEnum):
    food_preference = "food_preference"
    portion_habit = "portion_habit"
    behavior_pattern = "behavior_pattern"
    suggestion_feedback = "suggestion_feedback"
    health_goal = "health_goal"
    allergy = "allergy"
    exercise_habit = "exercise_habit"
    profile = "profile"
    other = "other"


class MemoryStatus(StrEnum):
    active = "active"
    pending = "pending"
    archived = "archived"


class MemoryCreate(BaseModel):
    memory_type: MemoryType
    content: str = Field(min_length=1, max_length=500)
    embedding: list[float] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    quality_score: int = Field(ge=0, le=100, default=80)
    status: MemoryStatus = MemoryStatus.active
    source: str | None = Field(default=None, max_length=50)
    trigger_type: str | None = Field(default=None, max_length=50)


class MemoryEntry(BaseModel):
    id: UUID
    user_id: UUID
    memory_type: MemoryType
    content: str
    metadata: dict[str, Any]
    quality_score: int
    status: MemoryStatus
    source: str | None = None
    trigger_type: str | None = None
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime | None = None
    access_count: int = 0
    time_decay_factor: float = Field(default=1.0, ge=0, le=1.2)


class MemoryRecallResult(MemoryEntry):
    vector_similarity: float = Field(ge=0, le=1)
    recall_score: float = Field(ge=0)


class MemorySummaryCreate(BaseModel):
    period_start: date_
    period_end: date_
    summary_content: str = Field(min_length=1, max_length=1000)
    key_facts: list[str] = Field(default_factory=list)
    source_memory_ids: list[UUID] = Field(default_factory=list)
    quality_score: float = Field(default=0, ge=0, le=100)
    status: MemoryStatus = MemoryStatus.active

    @model_validator(mode="after")
    def validate_period(self) -> MemorySummaryCreate:
        if self.period_end < self.period_start:
            raise ValueError("period_end must be greater than or equal to period_start")
        return self


class MemorySummaryEntry(BaseModel):
    id: UUID
    user_id: UUID
    period_start: date_
    period_end: date_
    summary_content: str
    key_facts: list[str]
    source_memory_ids: list[UUID]
    quality_score: float
    status: MemoryStatus
    created_at: datetime
    updated_at: datetime


class ExtractedMemory(BaseModel):
    memory_type: MemoryType
    content: str = Field(min_length=1, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None


class MemoryExtractionResult(BaseModel):
    memories: list[ExtractedMemory] = Field(default_factory=list, max_length=10)


class MemoryQualityScore(BaseModel):
    memory_type: MemoryType
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    relevance: int = Field(ge=0, le=100)
    accuracy: int = Field(ge=0, le=100)
    actionability: int = Field(ge=0, le=100)
    uniqueness: int = Field(ge=0, le=100)
    overall_score: int = Field(ge=0, le=100)
    reason: str | None = None


class MemoryScoreResult(BaseModel):
    scored_memories: list[MemoryQualityScore] = Field(default_factory=list, max_length=10)


class ConsolidatedMemorySummary(BaseModel):
    summary_content: str = Field(min_length=1, max_length=1000)
    key_facts: list[str] = Field(default_factory=list)
    quality_score: float = Field(default=80, ge=0, le=100)


__all__ = [
    "ConsolidatedMemorySummary",
    "ExtractedMemory",
    "MemoryCreate",
    "MemoryEntry",
    "MemoryExtractionResult",
    "MemoryQualityScore",
    "MemoryRecallResult",
    "MemoryScoreResult",
    "MemoryStatus",
    "MemorySummaryCreate",
    "MemorySummaryEntry",
    "MemoryType",
]

