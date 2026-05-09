"""RAG 知识库服务。"""

from __future__ import annotations

import uuid

from app.core.exceptions import ExternalServiceException, NotFoundException, ValidationException
from app.db.models.knowledge import Food, KnowledgeDoc
from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.integrations.embedding import EmbeddingClient
from app.schemas.knowledge import (
    FoodCategory,
    FoodDetailResponse,
    FoodSearchResponse,
    KnowledgeSearchResult,
    NutritionInfo,
    PortionInfo,
)


class RagService:
    """食物营养和健康建议检索服务。

    本服务不做 LLM 推理, 只调用 EmbeddingClient 和 pgvector 检索。
    """

    def __init__(self, repo: KnowledgeRepository, embedding_client: EmbeddingClient) -> None:
        self.repo = repo
        self.embedding_client = embedding_client

    async def search_foods(self, query: str, limit: int = 10) -> list[FoodSearchResponse]:
        normalized = query.strip()
        if not normalized:
            raise ValidationException("搜索关键词不能为空", code="INVALID_QUERY")
        limit = min(max(limit, 1), 50)

        matches = await self.repo.search_food_exact_or_alias(normalized, limit)
        if len(matches) < limit:
            try:
                embedding = await self.embedding_client.embed(normalized)
            except Exception as exc:
                if matches:
                    return self._food_search_responses(matches)
                raise ExternalServiceException(
                    "Embedding 服务暂时不可用", code="EMBEDDING_SERVICE_ERROR"
                ) from exc
            exclude_ids = {food.id for food, _ in matches}
            semantic = await self.repo.search_food_by_embedding(
                embedding,
                limit=limit - len(matches),
                exclude_ids=exclude_ids,
            )
            matches.extend(semantic)

        matches.sort(key=lambda item: item[1], reverse=True)
        return self._food_search_responses(matches[:limit])

    async def get_food_detail(self, food_id: uuid.UUID) -> FoodDetailResponse:
        food = await self.repo.get_food_by_id(food_id)
        if food is None:
            raise NotFoundException("食物不存在", code="FOOD_NOT_FOUND")
        return self._food_detail_response(food)

    async def search_knowledge(
        self, query: str, category: str | None = None, top_k: int = 5
    ) -> list[KnowledgeSearchResult]:
        normalized = query.strip()
        if not normalized:
            raise ValidationException("检索文本不能为空", code="INVALID_QUERY")
        top_k = min(max(top_k, 1), 20)
        try:
            embedding = await self.embedding_client.embed(normalized)
        except Exception as exc:
            raise ExternalServiceException(
                "Embedding 服务暂时不可用", code="EMBEDDING_SERVICE_ERROR"
            ) from exc

        rows = await self.repo.search_knowledge_by_embedding(
            embedding,
            category=category,
            top_k=top_k,
        )
        return [self._knowledge_result(doc, score) for doc, score in rows]

    async def lookup_nutrition(
        self, food_name: str, amount: float = 100, unit: str = "g"
    ) -> NutritionInfo:
        if amount <= 0:
            raise ValidationException("食物数量必须大于 0", code="INVALID_QUERY")
        food = await self.repo.get_food_by_name(food_name.strip())
        if food is None:
            matches = await self.search_foods(food_name, limit=1)
            if not matches:
                raise NotFoundException("食物不存在", code="FOOD_NOT_FOUND")
            food = await self.repo.get_food_by_id(matches[0].id)
        if food is None:
            raise NotFoundException("食物不存在", code="FOOD_NOT_FOUND")

        grams = self._amount_to_grams(food, amount, unit)
        factor = grams / 100
        base = self._nutrition_info(food)
        return NutritionInfo(
            calories=round(base.calories * factor, 2),
            protein=round(base.protein * factor, 2),
            fat=round(base.fat * factor, 2),
            carbs=round(base.carbs * factor, 2),
            fiber=round(base.fiber * factor, 2) if base.fiber is not None else None,
            sodium=round(base.sodium * factor, 2) if base.sodium is not None else None,
            sugar=round(base.sugar * factor, 2) if base.sugar is not None else None,
        )

    @staticmethod
    def _food_search_responses(matches: list[tuple[Food, float]]) -> list[FoodSearchResponse]:
        return [
            FoodSearchResponse(
                id=food.id,
                name=food.name,
                aliases=list(food.aliases or []),
                category=FoodCategory(food.category),
                calories_per_100g=food.calories_per_100g,
                match_score=round(score, 4),
            )
            for food, score in matches
        ]

    @staticmethod
    def _nutrition_info(food: Food) -> NutritionInfo:
        return NutritionInfo(
            calories=food.calories_per_100g,
            protein=food.protein_per_100g,
            fat=food.fat_per_100g,
            carbs=food.carbs_per_100g,
            fiber=food.fiber_per_100g,
            sodium=food.sodium_per_100g,
            sugar=food.sugar_per_100g,
        )

    def _food_detail_response(self, food: Food) -> FoodDetailResponse:
        return FoodDetailResponse(
            id=food.id,
            name=food.name,
            aliases=list(food.aliases or []),
            category=FoodCategory(food.category),
            nutrition_per_100g=self._nutrition_info(food),
            common_portions=[PortionInfo(**item) for item in food.common_portions or []],
            data_source=food.data_source,
        )

    @staticmethod
    def _knowledge_result(doc: KnowledgeDoc, score: float) -> KnowledgeSearchResult:
        return KnowledgeSearchResult(
            id=doc.id,
            title=doc.title,
            content=doc.content,
            score=round(score, 4),
            metadata=dict(doc.metadata_ or {}),
        )

    @staticmethod
    def _amount_to_grams(food: Food, amount: float, unit: str) -> float:
        normalized_unit = unit.strip().lower()
        if normalized_unit in {"g", "克", "gram", "grams"}:
            return amount
        for portion in food.common_portions or []:
            if portion.get("name") == unit:
                return amount * float(portion["weight_grams"])
        raise ValidationException("暂不支持该食物单位换算", code="INVALID_QUERY")


__all__ = ["RagService"]

