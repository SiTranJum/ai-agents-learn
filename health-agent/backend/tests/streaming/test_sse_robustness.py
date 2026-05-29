"""P4 健壮性测试：心跳 / 取消传播 / Total Timeout（T12-T14）。

测试范围：``app/streaming/sse.py`` 的核心鲁棒性行为：

- T12：业务事件间隔超过 heartbeat_interval 时自动发送心跳帧
- T13：客户端断开时 CancelledError 正确传播到 producer，业务流被取消
- T14：业务流总时长超过 total_timeout 时发送 error 事件并关闭

不依赖 FastAPI 端点，直接驱动 ``sse_response`` 返回的 ``StreamingResponse``，
避免外部 LLM 依赖，让测试快速且确定性强。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

import pytest

from app.streaming import StreamEvent, StreamEventType, sse_response


def _parse_frames(raw: bytes) -> list[tuple[str, dict]]:
    """把 SSE 字节流解析为 (event_name, data_dict) 列表。"""
    frames: list[tuple[str, dict]] = []
    text = raw.decode("utf-8")
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_name = ""
        data_str = ""
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_name = line[len("event: "):]
            elif line.startswith("data: "):
                data_str = line[len("data: "):]
        try:
            data = json.loads(data_str) if data_str else {}
        except json.JSONDecodeError:
            data = {"_raw": data_str}
        frames.append((event_name, data))
    return frames


async def _consume(response, max_bytes: int = 1024 * 1024) -> bytes:
    """从 StreamingResponse 收集所有字节（直到流结束）。"""
    chunks: list[bytes] = []
    total = 0
    async for chunk in response.body_iterator:
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            break
    return b"".join(chunks)


# ============ T12: 心跳 ============


@pytest.mark.asyncio
async def test_heartbeat_emitted_when_no_business_events() -> None:
    """业务流 stall 时应自动发送心跳帧。

    构造一个 0.3s 才发首个事件的 generator，配合 0.1s 心跳间隔，
    应该在首个业务事件之前观察到至少 1 个 heartbeat。
    """

    async def slow_gen() -> AsyncIterator[StreamEvent]:
        await asyncio.sleep(0.3)
        yield StreamEvent(type=StreamEventType.DONE, data={"message_id": "m1"})

    response = await sse_response(
        slow_gen(),
        heartbeat_interval=0.1,
        total_timeout=5,
    )
    raw = await _consume(response)
    frames = _parse_frames(raw)

    heartbeats = [f for f in frames if f[0] == "heartbeat"]
    dones = [f for f in frames if f[0] == "done"]

    assert len(heartbeats) >= 1, f"expected heartbeat frames, got: {frames}"
    assert len(dones) == 1
    assert dones[0][1] == {"message_id": "m1"}


@pytest.mark.asyncio
async def test_no_heartbeat_when_events_flow_continuously() -> None:
    """业务流持续吐数据时不应有心跳。

    每 0.05s 一个事件，心跳间隔 0.5s，整个流约 0.15s，期间不该插入心跳。
    """

    async def fast_gen() -> AsyncIterator[StreamEvent]:
        for i in range(3):
            yield StreamEvent(type=StreamEventType.TEXT_DELTA, data={"content": f"t{i}"})
            await asyncio.sleep(0.05)
        yield StreamEvent(type=StreamEventType.DONE, data={"message_id": "m"})

    response = await sse_response(fast_gen(), heartbeat_interval=0.5, total_timeout=5)
    raw = await _consume(response)
    frames = _parse_frames(raw)

    heartbeats = [f for f in frames if f[0] == "heartbeat"]
    text_deltas = [f for f in frames if f[0] == "text_delta"]

    assert len(heartbeats) == 0, f"unexpected heartbeats: {frames}"
    assert len(text_deltas) == 3


# ============ T13: 取消传播 ============


@pytest.mark.asyncio
async def test_cancellation_propagates_to_producer() -> None:
    """主消费循环被取消时，producer 应收到 CancelledError 并清理。

    模拟"客户端断开"：在生成器跑到一半时取消主任务。
    断开后应不再有事件输出，且 generator 的 finally 块能执行。
    """
    cleanup_done = asyncio.Event()

    async def long_gen() -> AsyncIterator[StreamEvent]:
        try:
            for i in range(100):
                yield StreamEvent(type=StreamEventType.TEXT_DELTA, data={"content": f"t{i}"})
                await asyncio.sleep(0.05)
        finally:
            cleanup_done.set()

    response = await sse_response(long_gen(), heartbeat_interval=10, total_timeout=10)

    received: list[bytes] = []

    async def consume_with_cancel() -> None:
        async for chunk in response.body_iterator:
            received.append(chunk if isinstance(chunk, bytes) else chunk.encode())
            # 拿到第一帧后立刻断开
            break

    await asyncio.wait_for(consume_with_cancel(), timeout=2)

    # 关闭 body_iterator —— 模拟 ASGI 客户端断开
    aclose = getattr(response.body_iterator, "aclose", None)
    if aclose is not None:
        await aclose()

    # producer 应在合理时间内被清理
    try:
        await asyncio.wait_for(cleanup_done.wait(), timeout=2)
    except asyncio.TimeoutError:
        pytest.fail("producer did not clean up after consumer cancelled")

    assert len(received) >= 1


# ============ T14: Total Timeout ============


@pytest.mark.asyncio
async def test_total_timeout_emits_error_and_closes() -> None:
    """超过 total_timeout 时应发送 error 帧并关闭流。"""

    async def hanging_gen() -> AsyncIterator[StreamEvent]:
        yield StreamEvent(type=StreamEventType.META, data={"message_id": "m"})
        # 远超 total_timeout 的 sleep
        await asyncio.sleep(10)
        yield StreamEvent(type=StreamEventType.DONE, data={"message_id": "m"})

    response = await sse_response(
        hanging_gen(),
        heartbeat_interval=10,  # 故意比 total_timeout 大，避免心跳干扰
        total_timeout=0.3,
    )
    raw = await asyncio.wait_for(_consume(response), timeout=3)
    frames = _parse_frames(raw)

    errors = [f for f in frames if f[0] == "error"]
    dones = [f for f in frames if f[0] == "done"]

    assert len(errors) == 1, f"expected exactly 1 error frame, got: {frames}"
    assert errors[0][1]["code"] == "TOTAL_TIMEOUT"
    assert errors[0][1]["retriable"] is True
    assert len(dones) == 0  # hanging 的 done 不应到达


@pytest.mark.asyncio
async def test_business_exception_emits_stream_error() -> None:
    """业务 generator 抛异常时应发送 STREAM_ERROR 帧。"""

    async def boom_gen() -> AsyncIterator[StreamEvent]:
        yield StreamEvent(type=StreamEventType.META, data={"message_id": "m"})
        raise RuntimeError("intentional test error")

    response = await sse_response(boom_gen(), heartbeat_interval=10, total_timeout=5)
    raw = await asyncio.wait_for(_consume(response), timeout=3)
    frames = _parse_frames(raw)

    errors = [f for f in frames if f[0] == "error"]
    metas = [f for f in frames if f[0] == "meta"]

    assert len(metas) == 1
    assert len(errors) == 1
    assert errors[0][1]["code"] == "STREAM_ERROR"
    assert errors[0][1]["retriable"] is True
