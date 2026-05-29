"""SSE 流监控埋点（T15）。

通过结构化日志输出关键指标，运维侧可用 Loki / grep / ELK 聚合：

- ``chat_stream_started``：流开始（用户感知请求发起）
- ``chat_stream_first_event_ms``：首个业务事件延迟（不含 meta/heartbeat）
- ``chat_stream_total_ms``：流总时长
- ``chat_stream_done``：正常完成
- ``chat_stream_error``：异常终止（含 code）
- ``chat_stream_cancelled``：客户端断开

设计参考：``2026-05-22-streaming-chat-impl-tasks.md §T15``。

每条指标都带 ``endpoint`` 标签（``chat`` / ``suggestions/daily`` / ``plans/stream``
等）和 ``request_id``（来自 ``app.core.logging.request_id_var``，自动注入到日志）。

使用方式：业务端点不直接调；由 :func:`app.streaming.sse.sse_response` 统一埋点。
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

logger = logging.getLogger("app.streaming.metrics")


def record_started(endpoint: str) -> None:
    """流开始：发起请求。"""
    logger.info(
        "stream_metric event=chat_stream_started endpoint=%s",
        endpoint,
    )


def record_first_event(endpoint: str, elapsed_ms: float) -> None:
    """首个业务事件延迟（不计 meta/heartbeat）。"""
    logger.info(
        "stream_metric event=chat_stream_first_event_ms endpoint=%s elapsed_ms=%.0f",
        endpoint,
        elapsed_ms,
    )


def record_done(endpoint: str, elapsed_ms: float, event_count: int) -> None:
    """流正常完成。"""
    logger.info(
        "stream_metric event=chat_stream_done endpoint=%s elapsed_ms=%.0f event_count=%d",
        endpoint,
        elapsed_ms,
        event_count,
    )


def record_error(endpoint: str, elapsed_ms: float, code: str) -> None:
    """流因异常终止。"""
    logger.warning(
        "stream_metric event=chat_stream_error endpoint=%s elapsed_ms=%.0f code=%s",
        endpoint,
        elapsed_ms,
        code,
    )


def record_cancelled(endpoint: str, elapsed_ms: float) -> None:
    """客户端主动断开（CancelledError）。"""
    logger.info(
        "stream_metric event=chat_stream_cancelled endpoint=%s elapsed_ms=%.0f",
        endpoint,
        elapsed_ms,
    )


# ============ Tracking 上下文 ============


class StreamMetrics:
    """单次流的累积指标，由 ``sse_response`` 持有。"""

    __slots__ = ("endpoint", "started_at", "first_event_at", "event_count")

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.started_at = time.perf_counter()
        self.first_event_at: float | None = None
        self.event_count = 0

    def mark_event(self, event_type: str) -> None:
        """记录一个事件，仅首个非 meta/heartbeat 事件计入 first_event。"""
        self.event_count += 1
        if self.first_event_at is None and event_type not in ("meta", "heartbeat"):
            self.first_event_at = time.perf_counter()
            elapsed_ms = (self.first_event_at - self.started_at) * 1000
            record_first_event(self.endpoint, elapsed_ms)

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self.started_at) * 1000


@asynccontextmanager
async def track_stream(endpoint: str) -> AsyncIterator[StreamMetrics]:
    """上下文管理器：在 with 块开始时记录 started，
    退出时根据是否抛异常自动记录 done / cancelled / error。

    ``sse_response`` 不直接用这个 helper（它需要在事件流中累积），
    但单次性命中缓存的端点可以直接用。
    """
    record_started(endpoint)
    metrics = StreamMetrics(endpoint)
    try:
        yield metrics
    except Exception:
        record_error(endpoint, metrics.elapsed_ms(), "STREAM_EXCEPTION")
        raise
    else:
        record_done(endpoint, metrics.elapsed_ms(), metrics.event_count)


__all__ = [
    "StreamMetrics",
    "record_cancelled",
    "record_done",
    "record_error",
    "record_first_event",
    "record_started",
    "track_stream",
]
