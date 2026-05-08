"""pgvector 相似度搜索封装。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


@dataclass(frozen=True)
class VectorSearchResult(Generic[T]):
    """向量检索结果。

    Attributes:
        item: SQLAlchemy ORM 实体实例, 例如 Food、KnowledgeDoc、Memory。
        score: 余弦相似度分数, 范围通常为 0~1, 越大越相似。
    """

    item: T
    score: float


class PgVectorClient:
    """基于 SQLAlchemy + pgvector 的通用检索客户端。

    API 说明:
    - pgvector SQLAlchemy 扩展会给 ``Vector`` 列提供 ``cosine_distance`` 方法,
      生成 PostgreSQL 的 ``<=>`` 余弦距离表达式。
    - 余弦距离越小越相似; 业务更容易理解相似度分数, 所以这里返回
      ``score = 1 - cosine_distance``。
    - 本类只负责通用 SQL 拼装, 不直接暴露给 Agent; Agent 应通过 Service/Tool
      间接触发检索。
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def similarity_search(
        self,
        table_class: type[T],
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        score_threshold: float = 0.0,
    ) -> list[VectorSearchResult[T]]:
        """按余弦相似度检索 ORM 表。

        Args:
            table_class: 含 ``embedding`` Vector 列的 SQLAlchemy ORM 模型类。
            query_embedding: 查询向量, 维度必须与表的 ``embedding`` 列一致。
            top_k: 最多返回的条数。
            filters: 等值过滤条件; value 为 list/tuple/set 时生成 ``IN`` 条件,
                value 为 ``None`` 时生成 ``IS NULL`` 条件。
            score_threshold: 最低相似度分数, 低于该阈值的结果会被过滤。

        Returns:
            ``VectorSearchResult`` 列表, 按相似度从高到低排序。
        """

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")
        if not query_embedding:
            raise ValueError("query_embedding must not be empty")
        if not 0.0 <= score_threshold <= 1.0:
            raise ValueError("score_threshold must be between 0.0 and 1.0")

        embedding_column = getattr(table_class, "embedding", None)
        if embedding_column is None:
            raise ValueError("table_class must define an embedding column")

        distance = embedding_column.cosine_distance(query_embedding)
        score = (1 - distance).label("score")
        stmt: Select[tuple[T, float]] = select(table_class, score)

        stmt = self._apply_filters(stmt, table_class, filters or {})
        if score_threshold > 0:
            stmt = stmt.where(distance <= 1 - score_threshold)

        stmt = stmt.order_by(distance.asc()).limit(top_k)
        rows = (await self.session.execute(stmt)).all()
        return [VectorSearchResult(item=row[0], score=float(row[1])) for row in rows]

    @staticmethod
    def _apply_filters(
        stmt: Select[tuple[T, float]],
        table_class: type[T],
        filters: dict[str, Any],
    ) -> Select[tuple[T, float]]:
        for field_name, value in filters.items():
            column = getattr(table_class, field_name, None)
            if column is None:
                raise ValueError(f"unknown filter field: {field_name}")

            if value is None:
                stmt = stmt.where(column.is_(None))
            elif isinstance(value, list | tuple | set):
                stmt = stmt.where(column.in_(value))
            else:
                stmt = stmt.where(column == value)
        return stmt


__all__ = ["PgVectorClient", "VectorSearchResult"]

