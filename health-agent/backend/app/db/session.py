"""异步 SQLAlchemy 引擎与会话工厂。

数据库会话通过 :mod:`app.dependencies` 中的 FastAPI 依赖注入提供。
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# pool_pre_ping 可在连接失效（例如 Supabase 重启）时透明回收旧连接
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：产出一个 :class:`AsyncSession`。

    成功时由调用方决定是否 commit；发生异常自动 rollback；最终一定 close。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """应用关闭时释放数据库引擎资源。"""
    await engine.dispose()
