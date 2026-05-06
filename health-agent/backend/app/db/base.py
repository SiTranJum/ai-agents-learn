"""SQLAlchemy 声明式基类与通用 Mixin。

所有 ORM 模型继承自 :class:`Base`（通常还会叠加
:class:`TimestampMixin` / :class:`SoftDeleteMixin`），便于 Alembic
基于同一个 metadata 自动生成迁移。

参考：
- ``docs/specs/backend/00-architecture/project-structure.md``
- ``docs/specs/backend/03-shared/database-schema.md``
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """项目范围内统一的声明式基类。

    具体模型放在 ``app/db/models/`` 下，并由
    ``app/db/models/__init__.py`` 提前 import，确保 Alembic
    在自动生成迁移前已经把所有模型注册进 metadata。
    """

    pass


class UUIDPrimaryKeyMixin:
    """提供使用 :func:`uuid.uuid4` 在客户端生成的 UUID 主键。

    使用 UUID 既能避免在 URL 中泄漏行数，也允许在 INSERT 之前预生成 ID
    （便于跨服务引用）。
    """

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class TimestampMixin:
    """添加由数据库维护的 ``created_at`` / ``updated_at`` 字段。

    使用 ``server_default=func.now()`` 可保证即使是通过裸 SQL 插入的
    数据（如种子脚本、迁移）也能正确填充。
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """添加可空的 ``deleted_at`` 字段实现软删除语义。

    Repository 层在查询时必须过滤 ``deleted_at IS NULL``；删除用户数据
    时使用 ``deleted_at = now()`` 而非物理 ``DELETE``。
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


__all__ = [
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
]
