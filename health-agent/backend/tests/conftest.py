"""测试套件共享 fixtures。

Phase 0 仅做：设置测试环境标记 + 暴露针对 FastAPI 应用的
``httpx.AsyncClient``。模块特有 fixtures（数据库、认证）随对应阶段补齐。
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

# 必须在导入应用之前设置环境，确保 settings 能感知到测试模式
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_DEBUG", "true")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """构造一个直接打到 ASGI 应用的异步 HTTP 客户端。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
