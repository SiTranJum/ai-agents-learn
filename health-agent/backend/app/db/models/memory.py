"""AI memory ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Memory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Long-term user memory stored with vector embedding."""

    __tablename__ = "memories"
    __table_args__ = (
        Index("idx_memories_user_status", "user_id", "status"),
        Index("idx_memories_user_type", "user_id", "memory_type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    memory_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    trigger_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class MemorySummary(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Medium-term memory summary for a date period."""

    __tablename__ = "memory_summaries"
    __table_args__ = (Index("idx_memory_summaries_user_period", "user_id", "period_start", "period_end"),)

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    summary_content: Mapped[str] = mapped_column(Text, nullable=False)
    key_facts: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    source_memory_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)), nullable=False, server_default="{}"
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)


__all__ = ["Memory", "MemorySummary"]

