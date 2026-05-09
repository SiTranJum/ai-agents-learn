"""知识库 ORM 模型。"""

from __future__ import annotations

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Food(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """食物营养知识库。"""

    __tablename__ = "foods"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    aliases: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    calories_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    protein_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    fiber_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    sodium_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugar_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    common_portions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    data_source: Mapped[str] = mapped_column(String(50), nullable=False, server_default="manual")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)


class KnowledgeDoc(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """健康建议知识文档。"""

    __tablename__ = "knowledge_docs"

    title: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)


__all__ = ["Food", "KnowledgeDoc"]
