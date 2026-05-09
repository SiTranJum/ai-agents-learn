"""Phase 3 - KnowledgeRepository 单元测试。"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from app.db.repositories.knowledge_repo import KnowledgeRepository


class _FakeSession:
    def __init__(self) -> None:
        self.statement: Any | None = None

    async def execute(self, statement: Any) -> None:
        self.statement = statement


@pytest.mark.asyncio
async def test_upsert_knowledge_doc_compiles_metadata_column() -> None:
    session = _FakeSession()
    repo = KnowledgeRepository(session=session)  # type: ignore[arg-type]

    await repo.upsert_knowledge_doc(
        {
            "title": "测试文档",
            "content": "内容",
            "metadata_": {"category": "基础营养"},
            "embedding": None,
        }
    )

    compiled = str(session.statement.compile(dialect=postgresql.dialect()))
    assert "INSERT INTO knowledge_docs" in compiled
    assert "ON CONFLICT (title) DO UPDATE" in compiled
    assert "metadata = excluded.metadata" in compiled
