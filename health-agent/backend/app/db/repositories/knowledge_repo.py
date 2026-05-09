"""知识库 Repository。"""

from __future__ import annotations

import uuid
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge import Food, KnowledgeDoc
from app.integrations.vector import PgVectorClient


class KnowledgeRepository:
    """食物与健康建议知识库仓储。

    知识库是全局数据, 不按 user_id 隔离, 因此不继承 BaseRepository。
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.vector_client = PgVectorClient(session)

    async def get_food_by_id(self, food_id: uuid.UUID) -> Food | None:
        return cast(Food | None, await self.session.get(Food, food_id))

    async def get_food_by_name(self, name: str) -> Food | None:
        stmt = select(Food).where(Food.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def search_food_exact_or_alias(self, query: str, limit: int) -> list[tuple[Food, float]]:
        exact_stmt = select(Food).where(Food.name == query).limit(limit)
        exact = list((await self.session.execute(exact_stmt)).scalars().all())
        results: list[tuple[Food, float]] = [(food, 1.0) for food in exact]

        remaining = limit - len(results)
        if remaining <= 0:
            return results

        seen_ids = {food.id for food, _ in results}
        alias_stmt = select(Food).where(Food.aliases.contains([query])).limit(remaining)
        alias_foods = list((await self.session.execute(alias_stmt)).scalars().all())
        results.extend((food, 0.9) for food in alias_foods if food.id not in seen_ids)
        return results

    async def search_food_by_embedding(
        self,
        query_embedding: list[float],
        *,
        limit: int,
        exclude_ids: set[uuid.UUID] | None = None,
        score_threshold: float = 0.5,
    ) -> list[tuple[Food, float]]:
        vector_results = await self.vector_client.similarity_search(
            Food,
            query_embedding,
            top_k=limit + len(exclude_ids or set()),
            score_threshold=score_threshold,
        )
        excluded = exclude_ids or set()
        results: list[tuple[Food, float]] = []
        for row in vector_results:
            if row.item.id in excluded:
                continue
            results.append((row.item, min(row.score, 0.8)))
            if len(results) >= limit:
                break
        return results

    async def search_knowledge_by_embedding(
        self,
        query_embedding: list[float],
        *,
        category: str | None = None,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> list[tuple[KnowledgeDoc, float]]:
        embedding_column = KnowledgeDoc.embedding
        distance = embedding_column.cosine_distance(query_embedding)
        score = (1 - distance).label("score")
        stmt = select(KnowledgeDoc, score).where(embedding_column.is_not(None))
        if category:
            stmt = stmt.where(KnowledgeDoc.metadata_["category"].astext == category)
        stmt = stmt.where(distance <= 1 - score_threshold).order_by(distance.asc()).limit(top_k)
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], float(row[1])) for row in rows]

    async def upsert_food(self, data: dict[str, Any]) -> None:
        stmt = insert(Food).values(**data)
        update_fields = {key: stmt.excluded[key] for key in data if key != "id"}
        await self.session.execute(
            stmt.on_conflict_do_update(index_elements=[Food.name], set_=update_fields)
        )

    async def upsert_knowledge_doc(self, data: dict[str, Any]) -> None:
        stmt = insert(KnowledgeDoc).values(**data)
        update_fields = {
            ("metadata" if key == "metadata_" else key): stmt.excluded[
                "metadata" if key == "metadata_" else key
            ]
            for key in data
            if key != "id"
        }
        await self.session.execute(
            stmt.on_conflict_do_update(index_elements=[KnowledgeDoc.title], set_=update_fields)
        )


__all__ = ["KnowledgeRepository"]


