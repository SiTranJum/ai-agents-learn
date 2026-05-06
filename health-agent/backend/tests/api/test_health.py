"""Phase 0 冒烟测试 —— 验证应用能启动，并且基础设施
（健康探针 + 错误信封）端到端工作。
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_probe(client: AsyncClient) -> None:
    """健康探针应返回 status=ok。"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_root(client: AsyncClient) -> None:
    """根路径应返回服务名等元信息。"""
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "health-agent-api"


@pytest.mark.asyncio
async def test_unknown_route_uses_error_envelope(client: AsyncClient) -> None:
    """未知路由应返回 404 并使用统一错误信封。"""
    resp = await client.get("/api/v1/this-route-does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_protected_endpoint_requires_token() -> None:
    """凡是依赖 get_current_user 的接口在缺少 token 时应抛出
    UnauthorizedException。Phase 0 暂未挂载受保护路由，因此直接
    校验依赖函数本身的行为。
    """
    from app.core.exceptions import UnauthorizedException
    from app.dependencies import get_current_user

    with pytest.raises(UnauthorizedException):
        await get_current_user(authorization=None)
