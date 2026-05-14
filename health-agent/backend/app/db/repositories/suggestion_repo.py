"""AI suggestion repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.suggestion import Suggestion
from app.schemas.suggestion import FeedbackRating, SuggestionType


class SuggestionRepository:
    """User-scoped suggestion repository."""

    def __init__(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def list_valid(
        self,
        *,
        suggestion_type: SuggestionType | None = None,
        meal_type: str | None = None,
        now: datetime | None = None,
        limit: int = 3,
    ) -> list[Suggestion]:
        now = now or datetime.now(UTC)
        stmt = select(Suggestion).where(
            Suggestion.user_id == self.user_id,
            (Suggestion.expires_at.is_(None) | (Suggestion.expires_at > now)),
        )
        if suggestion_type is not None:
            stmt = stmt.where(cast(Any, Suggestion.suggestion_type) == suggestion_type.value)
        if meal_type is not None:
            stmt = stmt.where(cast(Any, Suggestion.meal_type) == meal_type)
        stmt = stmt.order_by(Suggestion.created_at.desc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def create(self, suggestion: Suggestion) -> Suggestion:
        suggestion.user_id = self.user_id
        self.session.add(suggestion)
        await self.session.flush()
        return suggestion

    async def get(self, suggestion_id: uuid.UUID) -> Suggestion | None:
        stmt = select(Suggestion).where(
            Suggestion.user_id == self.user_id,
            Suggestion.id == suggestion_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def set_feedback(self, suggestion: Suggestion, rating: FeedbackRating) -> Suggestion:
        suggestion.user_feedback = rating.value
        suggestion.feedback_at = datetime.now(UTC)
        await self.session.flush()
        return suggestion


__all__ = ["SuggestionRepository"]

