"""Repository 基类。

提供：
- 自动注入 ``user_id`` 上下文，所有派生类的查询都强制按当前用户过滤
- 通用 ``commit / refresh`` 帮助方法

参见 ``docs/specs/backend/00-architecture/auth.md`` §5。
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """所有 repository 的基类。

    使用方式：派生类显式声明 ``model``，由具体方法在 SQL 中拼接
    ``model.user_id == self.user_id`` 以保证数据隔离。
    """

    def __init__(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def flush(self) -> None:
        await self.session.flush()
