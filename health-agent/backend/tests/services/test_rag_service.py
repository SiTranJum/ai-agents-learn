"""Phase 3 - RagService 单元测试。"""

from __future__ import annotations

import uuid

import pytest

from app.core.exceptions import NotFoundException, ValidationException
from app.db.models.knowledge import Food, KnowledgeDoc
from app.services.rag_service import RagService


def _food(name: str = "米饭") -> Food:
    return Food(
        id=uuid.uuid4(),
        name=name,
        aliases=["白米饭"],
        category="grains",
        calories_per_100g=116,
        protein_per_100g=2.6,
        fat_per_100g=0.3,
        carbs_per_100g=25.9,
        fiber_per_100g=0.3,
        sodium_per_100g=2,
        sugar_per_100g=0.1,
        common_portions=[{"name": "一碗", "weight_grams": 200}],
        data_source="test",
    )


class _FakeEmbeddingClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[str] = []

    async def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        if self.fail:
            raise RuntimeError("embedding failed")
        return [0.1, 0.2, 0.3]


class _FakeRepo:
    def __init__(self) -> None:
        self.food = _food()
        self.doc = KnowledgeDoc(
            id=uuid.uuid4(),
            title="主食不必完全戒掉",
            content="健康饮食不建议完全戒掉主食。",
            metadata_={"category": "基础营养"},
        )

    async def search_food_exact_or_alias(self, query: str, limit: int):
        if query in {"米饭", "白米饭"}:
            return [(self.food, 1.0 if query == "米饭" else 0.9)]
        return []

    async def search_food_by_embedding(self, query_embedding, *, limit, exclude_ids, score_threshold=0.5):
        return [] if self.food.id in exclude_ids else [(self.food, 0.76)]

    async def get_food_by_id(self, food_id: uuid.UUID):
        return self.food if food_id == self.food.id else None

    async def get_food_by_name(self, name: str):
        return self.food if name == self.food.name else None

    async def search_knowledge_by_embedding(self, query_embedding, *, category=None, top_k=5, score_threshold=0.5):
        if category and category != self.doc.metadata_["category"]:
            return []
        return [(self.doc, 0.88)]


@pytest.mark.asyncio
async def test_search_foods_uses_exact_match_before_embedding() -> None:
    repo = _FakeRepo()
    embedding = _FakeEmbeddingClient()
    service = RagService(repo=repo, embedding_client=embedding)  # type: ignore[arg-type]

    results = await service.search_foods("米饭", limit=1)

    assert results[0].name == "米饭"
    assert results[0].match_score == 1.0
    assert embedding.calls == []


@pytest.mark.asyncio
async def test_search_foods_falls_back_to_embedding() -> None:
    repo = _FakeRepo()
    embedding = _FakeEmbeddingClient()
    service = RagService(repo=repo, embedding_client=embedding)  # type: ignore[arg-type]

    results = await service.search_foods("米", limit=1)

    assert results[0].name == "米饭"
    assert results[0].match_score == 0.76
    assert embedding.calls == ["米"]


@pytest.mark.asyncio
async def test_search_knowledge_returns_metadata() -> None:
    service = RagService(repo=_FakeRepo(), embedding_client=_FakeEmbeddingClient())  # type: ignore[arg-type]

    results = await service.search_knowledge("主食", category="基础营养")

    assert results[0].title == "主食不必完全戒掉"
    assert results[0].score == 0.88
    assert results[0].metadata["category"] == "基础营养"


@pytest.mark.asyncio
async def test_lookup_nutrition_converts_common_portion() -> None:
    service = RagService(repo=_FakeRepo(), embedding_client=_FakeEmbeddingClient())  # type: ignore[arg-type]

    nutrition = await service.lookup_nutrition("米饭", amount=1, unit="一碗")

    assert nutrition.calories == 232
    assert nutrition.carbs == 51.8


@pytest.mark.asyncio
async def test_get_food_detail_raises_not_found() -> None:
    service = RagService(repo=_FakeRepo(), embedding_client=_FakeEmbeddingClient())  # type: ignore[arg-type]

    with pytest.raises(NotFoundException, match="食物不存在"):
        await service.get_food_detail(uuid.uuid4())


@pytest.mark.asyncio
async def test_search_foods_rejects_blank_query() -> None:
    service = RagService(repo=_FakeRepo(), embedding_client=_FakeEmbeddingClient())  # type: ignore[arg-type]

    with pytest.raises(ValidationException, match="搜索关键词不能为空"):
        await service.search_foods("   ")
