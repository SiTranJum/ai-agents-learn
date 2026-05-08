"""Phase 2 - pgvector 检索封装测试。"""

from __future__ import annotations

import uuid

import pytest
from pgvector.sqlalchemy import Vector
from sqlalchemy import String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.integrations.vector import PgVectorClient


class _VectorDocument(Base):
    __tablename__ = "test_vector_documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(3), nullable=False)


class _FakeScalarResult:
    def __init__(self, rows: list[tuple[object, float]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[object, float]]:
        return self._rows


class _FakeSession:
    def __init__(self, rows: list[tuple[object, float]]) -> None:
        self.rows = rows
        self.statement = None

    async def execute(self, statement: object) -> _FakeScalarResult:
        self.statement = statement
        return _FakeScalarResult(self.rows)


@pytest.mark.asyncio
async def test_similarity_search_executes_cosine_distance_query() -> None:
    document = _VectorDocument(category="food", status="published", embedding=[0.1, 0.2, 0.3])
    session = _FakeSession(rows=[(document, 0.92)])
    client = PgVectorClient(session)  # type: ignore[arg-type]

    results = await client.similarity_search(
        _VectorDocument,
        [0.1, 0.2, 0.3],
        top_k=3,
        filters={"category": "food", "status": ["published", "draft"]},
        score_threshold=0.8,
    )

    assert len(results) == 1
    assert results[0].item is document
    assert results[0].score == pytest.approx(0.92)

    compiled = session.statement.compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert "test_vector_documents.embedding <=>" in sql
    assert "test_vector_documents.category =" in sql
    assert "test_vector_documents.status IN" in sql
    assert "LIMIT" in sql


@pytest.mark.asyncio
async def test_similarity_search_rejects_missing_embedding_column() -> None:
    class NoEmbedding(Base):
        __tablename__ = "test_no_embedding"

        id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    client = PgVectorClient(_FakeSession(rows=[]))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="embedding"):
        await client.similarity_search(NoEmbedding, [0.1, 0.2, 0.3])


@pytest.mark.asyncio
async def test_similarity_search_rejects_unknown_filter() -> None:
    client = PgVectorClient(_FakeSession(rows=[]))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="unknown filter"):
        await client.similarity_search(_VectorDocument, [0.1, 0.2, 0.3], filters={"missing": "x"})

