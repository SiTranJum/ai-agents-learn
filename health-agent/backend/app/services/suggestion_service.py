"""AI suggestion service.

This service only handles cache persistence and feedback. LLM orchestration belongs
to ``app.agents.suggestion``.
"""
# ruff: noqa: RUF001

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time, timedelta

from app.core.exceptions import NotFoundException
from app.db.models.suggestion import Suggestion
from app.db.repositories.suggestion_repo import SuggestionRepository
from app.schemas.suggestion import (
    DailySuggestionResponse,
    FeedbackCreate,
    InsightItem,
    InsightResponse,
    MealSuggestionResponse,
    NutritionSummary,
    SuggestionDraft,
    SuggestionItem,
    SuggestionPriority,
    SuggestionType,
)


class SuggestionService:
    """Suggestion cache and feedback service. No LLM calls here."""

    def __init__(self, repo: SuggestionRepository) -> None:
        self.repo = repo

    async def get_cached_daily(self) -> DailySuggestionResponse | None:
        rows = await self.repo.list_valid(suggestion_type=SuggestionType.proactive_insight, limit=3)
        if not rows:
            return None
        return DailySuggestionResponse(suggestions=[self._item(row) for row in rows], generated_at=rows[0].created_at)

    async def get_cached_insights(self) -> InsightResponse | None:
        rows = await self.repo.list_valid(suggestion_type=SuggestionType.trend_advice, limit=3)
        if not rows:
            return None
        return InsightResponse(insights=[self._insight(row) for row in rows], period="last_30_days")

    async def save_daily(self, drafts: list[SuggestionDraft]) -> DailySuggestionResponse:
        expires_at = self._next_midnight()
        rows = await self._save_many(drafts[:3], default_type=SuggestionType.proactive_insight, expires_at=expires_at)
        await self.repo.session.commit()
        return DailySuggestionResponse(suggestions=[self._item(row) for row in rows], generated_at=rows[0].created_at)

    async def save_insights(self, drafts: list[SuggestionDraft]) -> InsightResponse:
        expires_at = self._next_monday()
        rows = await self._save_many(drafts[:3], default_type=SuggestionType.trend_advice, expires_at=expires_at)
        await self.repo.session.commit()
        return InsightResponse(insights=[self._insight(row) for row in rows], period="last_30_days")

    async def save_meal(self, meal_type: str, drafts: list[SuggestionDraft], reasoning: str) -> MealSuggestionResponse:
        expires_at = self._next_midnight()
        draft = drafts[0] if drafts else self._fallback_meal_draft(meal_type)
        draft.meal_type = meal_type
        row = await self.repo.create(self._model_from_draft(draft, default_type=SuggestionType.diet_advice, expires_at=expires_at))
        await self.repo.session.commit()
        foods = [item.strip() for item in row.content.replace("，", ",").split(",") if item.strip()][:5]
        if not foods:
            foods = [row.content]
        return MealSuggestionResponse(
            suggestion_id=row.id,
            meal_type=meal_type,
            consumed_today=NutritionSummary(),
            remaining=NutritionSummary(calories=600, protein=30, fat=20, carbs=75),
            suggestions=foods,
            reasoning=reasoning or row.basis or "根据今日摄入和计划目标推荐。",
        )

    async def submit_feedback(self, suggestion_id: uuid.UUID, feedback: FeedbackCreate) -> SuggestionItem:
        row = await self.repo.get(suggestion_id)
        if row is None:
            raise NotFoundException("建议不存在", code="SUGGESTION_NOT_FOUND")
        updated = await self.repo.set_feedback(row, feedback.rating)
        await self.repo.session.commit()
        return self._item(updated)

    async def _save_many(
        self,
        drafts: list[SuggestionDraft],
        *,
        default_type: SuggestionType,
        expires_at: datetime,
    ) -> list[Suggestion]:
        if not drafts:
            drafts = [self._fallback_daily_draft() if default_type == SuggestionType.proactive_insight else self._fallback_insight_draft()]
        seen: set[str] = set()
        rows: list[Suggestion] = []
        for draft in drafts:
            key = draft.content.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            rows.append(await self.repo.create(self._model_from_draft(draft, default_type=default_type, expires_at=expires_at)))
        return rows

    @staticmethod
    def _model_from_draft(draft: SuggestionDraft, *, default_type: SuggestionType, expires_at: datetime) -> Suggestion:
        return Suggestion(
            suggestion_type=(draft.type or default_type).value,
            title=draft.title,
            content=draft.content,
            basis=draft.basis,
            priority=(draft.priority or SuggestionPriority.medium).value,
            meal_type=draft.meal_type,
            dimension=draft.dimension,
            data_support=draft.data_support,
            context={},
            expires_at=expires_at,
        )

    @staticmethod
    def _item(row: Suggestion) -> SuggestionItem:
        return SuggestionItem(
            id=row.id,
            type=SuggestionType(row.suggestion_type),
            title=row.title,
            content=row.content,
            basis=row.basis,
            priority=SuggestionPriority(row.priority),
            expires_at=row.expires_at,
            created_at=row.created_at,
        )

    @staticmethod
    def _insight(row: Suggestion) -> InsightItem:
        return InsightItem(
            id=row.id,
            dimension=row.dimension or "health_pattern",
            finding=row.title,
            suggestion=row.content,
            data_support=row.data_support or {},
            generated_at=row.created_at,
        )

    @staticmethod
    def _next_midnight() -> datetime:
        tomorrow = datetime.now(UTC).date() + timedelta(days=1)
        return datetime.combine(tomorrow, time.min, tzinfo=UTC)

    @staticmethod
    def _next_monday() -> datetime:
        today = datetime.now(UTC).date()
        days = 7 - today.weekday()
        return datetime.combine(today + timedelta(days=days), time.min, tzinfo=UTC)

    @staticmethod
    def _fallback_daily_draft() -> SuggestionDraft:
        return SuggestionDraft(
            type=SuggestionType.proactive_insight,
            title="今日小提醒",
            content="今天优先完成一件可量化的小事：饮水达到 2000ml，并记录每一餐。",
            basis="基于通用健康管理目标生成。",
            priority=SuggestionPriority.medium,
        )

    @staticmethod
    def _fallback_insight_draft() -> SuggestionDraft:
        return SuggestionDraft(
            type=SuggestionType.trend_advice,
            title="记录连续性洞察",
            content="最近数据记录越完整，AI 越能发现饮食和体重变化之间的关系。建议连续记录 7 天。",
            basis="基于数据完整性规则生成。",
            priority=SuggestionPriority.low,
            dimension="data_completeness",
            data_support={"period": "last_30_days"},
        )

    @staticmethod
    def _fallback_meal_draft(meal_type: str) -> SuggestionDraft:
        return SuggestionDraft(
            type=SuggestionType.diet_advice,
            title=f"{meal_type} 餐食建议",
            content="鸡蛋, 豆腐, 绿叶蔬菜",
            basis="优先补充蛋白质和蔬菜。",
            priority=SuggestionPriority.medium,
            meal_type=meal_type,
        )


__all__ = ["SuggestionService"]


