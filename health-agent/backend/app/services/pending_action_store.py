"""PendingAction 存储：跨 SSE 连接的会话级待决状态。

开发期用进程内 dict（足够单实例 demo 用），生产切 Redis 带 TTL。

设计参考: docs/plans/2026-05-21-streaming-chat-design.md §8
任务规格: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T8
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from app.schemas.pending_action import PendingAction

logger = logging.getLogger("app.services.pending_action")

DEFAULT_TTL_SECONDS = 1800  # 30 分钟


class PendingActionStore(Protocol):
    """抽象接口。生产可替换为 Redis 实现。"""

    async def get(self, session_id: str) -> PendingAction | None: ...
    async def set(self, session_id: str, action: PendingAction) -> None: ...
    async def delete(self, session_id: str) -> None: ...


class InMemoryPendingActionStore:
    """进程内实现，适合开发和单实例部署。"""

    def __init__(self) -> None:
        self._store: dict[str, PendingAction] = {}
        self._lock = asyncio.Lock()

    async def get(self, session_id: str) -> PendingAction | None:
        async with self._lock:
            action = self._store.get(session_id)
            if action is None:
                return None
            if action.is_expired():
                del self._store[session_id]
                logger.debug("pending_action expired for session %s", session_id)
                return None
            return action

    async def set(self, session_id: str, action: PendingAction) -> None:
        async with self._lock:
            self._store[session_id] = action
            logger.debug(
                "pending_action set for session %s, prompt_id=%s, expires=%s",
                session_id,
                action.prompt_id,
                action.expires_at.isoformat(),
            )

    async def delete(self, session_id: str) -> None:
        async with self._lock:
            self._store.pop(session_id, None)
            logger.debug("pending_action deleted for session %s", session_id)


def create_pending_action(
    prompt_id: str,
    options: list[dict],
    *,
    diet_partial: dict | None = None,
    plan_partial: dict | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> PendingAction:
    """工厂函数：创建 PendingAction 并自动设置过期时间。"""
    from app.streaming.events import ChoiceOption

    return PendingAction(
        prompt_id=prompt_id,
        options=[ChoiceOption(**o) if isinstance(o, dict) else o for o in options],
        diet_partial=diet_partial,
        plan_partial=plan_partial,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
    )


# 全局单例（开发期）
_store_instance: InMemoryPendingActionStore | None = None


def get_pending_action_store() -> InMemoryPendingActionStore:
    """获取全局 PendingAction 存储实例。"""
    global _store_instance
    if _store_instance is None:
        _store_instance = InMemoryPendingActionStore()
    return _store_instance


__all__ = [
    "InMemoryPendingActionStore",
    "PendingActionStore",
    "create_pending_action",
    "get_pending_action_store",
]
