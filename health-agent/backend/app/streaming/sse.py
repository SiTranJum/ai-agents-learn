"""SSE 帧编码 + 心跳 + StreamingResponse 包装。

提供两个核心 API：

- :func:`format_sse` - 把 ``StreamEvent`` 编码为符合规范的 SSE 帧字节串
- :func:`sse_response` - 把 async generator 包装为 ``StreamingResponse``，
  并自动注入心跳 + total timeout 兜底 + 监控埋点（T15）

参考: docs/plans/2026-05-21-streaming-chat-design.md §15.1
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator

from fastapi.responses import StreamingResponse

from app.streaming.events import StreamEvent, StreamEventType
from app.streaming.metrics import (
    StreamMetrics,
    record_cancelled,
    record_done,
    record_error,
    record_started,
)

logger = logging.getLogger("app.streaming")

# 默认心跳间隔（秒）。前端 idle timer 30s，留 1 倍余量。
DEFAULT_HEARTBEAT_INTERVAL = 15
# 流总时长硬上限（秒）。防止 LLM 死循环烧 token。
DEFAULT_TOTAL_TIMEOUT = 180


def format_sse(event: StreamEvent) -> bytes:
    """把 ``StreamEvent`` 编码为符合 SSE 规范的字节串。

    SSE 规范要点：
    - ``event: <type>\\n`` 指定事件名
    - ``data: <json>\\n`` 携带 payload（必须单行，多行需要多个 ``data:``）
    - ``\\n\\n`` 结束一个事件块

    我们的 data 强制 JSON，保证不含换行（``ensure_ascii=False`` 让中文不转义）。
    """
    payload = json.dumps(event.data, ensure_ascii=False, separators=(",", ":"))
    frame = f"event: {event.type.value}\ndata: {payload}\n\n"
    return frame.encode("utf-8")


async def sse_response(
    generator: AsyncIterator[StreamEvent],
    *,
    heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
    total_timeout: int = DEFAULT_TOTAL_TIMEOUT,
    endpoint: str = "unknown",
) -> StreamingResponse:
    """把 ``AsyncIterator[StreamEvent]`` 包装为 SSE ``StreamingResponse``。

    实现要点：
    - 用 ``asyncio.Queue`` 把业务事件流和心跳合并到同一个输出
    - 业务流跑在独立 Task，主循环只负责 race（业务 vs 心跳）
    - 业务 generator 抛 ``CancelledError`` 时（客户端断开）正常传播并清理
    - 业务 generator 抛业务异常时，emit 一条 error 事件再关闭
    - ``total_timeout`` 包整个流，超过即关闭并 emit error
    - T15: ``endpoint`` 标签下的监控埋点（started / first_event / done / error / cancelled）
    """
    queue: asyncio.Queue[StreamEvent | None] = asyncio.Queue()
    # 用 sentinel 表示业务流已结束（None 仅在内部使用，不暴露）
    DONE_SENTINEL: StreamEvent | None = None

    metrics = StreamMetrics(endpoint)
    record_started(endpoint)
    # 累积最终错误码（None=正常完成）
    final_error_code: list[str | None] = [None]

    async def producer() -> None:
        """业务事件 → queue。"""
        try:
            async with asyncio.timeout(total_timeout):
                async for event in generator:
                    await queue.put(event)
        except asyncio.CancelledError:
            logger.info("sse producer cancelled (client disconnect)")
            raise
        except asyncio.TimeoutError:
            logger.warning("sse producer hit total timeout (%ds)", total_timeout)
            final_error_code[0] = "TOTAL_TIMEOUT"
            await queue.put(
                StreamEvent(
                    type=StreamEventType.ERROR,
                    data={
                        "code": "TOTAL_TIMEOUT",
                        "message": "请求处理超时，请稍后重试",
                        "retriable": True,
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("sse producer raised: %s", exc)
            final_error_code[0] = "STREAM_ERROR"
            await queue.put(
                StreamEvent(
                    type=StreamEventType.ERROR,
                    data={
                        "code": "STREAM_ERROR",
                        "message": "服务出错，请稍后重试",
                        "retriable": True,
                    },
                )
            )
        finally:
            await queue.put(DONE_SENTINEL)

    async def stream() -> AsyncIterator[bytes]:
        """主循环：业务事件 / 心跳 二选一。"""
        producer_task = asyncio.create_task(producer())
        client_disconnected = False
        try:
            while True:
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=heartbeat_interval
                    )
                except asyncio.TimeoutError:
                    # 间隔内无业务事件 → 发心跳保活（不计入 metrics）
                    yield format_sse(
                        StreamEvent(type=StreamEventType.HEARTBEAT, data={})
                    )
                    continue
                if event is DONE_SENTINEL:
                    break
                metrics.mark_event(event.type.value)
                # 业务流 emit 的 error 事件也要记录
                if event.type == StreamEventType.ERROR and final_error_code[0] is None:
                    final_error_code[0] = str(event.data.get("code") or "BUSINESS_ERROR")
                yield format_sse(event)
        except asyncio.CancelledError:
            client_disconnected = True
            raise
        finally:
            if not producer_task.done():
                producer_task.cancel()
                try:
                    await producer_task
                except (asyncio.CancelledError, Exception):  # noqa: BLE001
                    pass
            # T15: 流结束时记录最终指标
            elapsed_ms = metrics.elapsed_ms()
            if client_disconnected:
                record_cancelled(endpoint, elapsed_ms)
            elif final_error_code[0] is not None:
                record_error(endpoint, elapsed_ms, final_error_code[0])
            else:
                record_done(endpoint, elapsed_ms, metrics.event_count)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # 告诉 nginx 等反向代理不要缓冲，逐帧透传
            "X-Accel-Buffering": "no",
        },
    )


__all__ = ["format_sse", "sse_response", "DEFAULT_HEARTBEAT_INTERVAL", "DEFAULT_TOTAL_TIMEOUT"]
