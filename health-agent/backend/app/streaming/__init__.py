"""SSE 流式响应基础设施。

模块职责：
- ``events`` - 业务级 ``StreamEvent`` 定义（Pydantic 模型）
- ``sse`` - SSE 帧编码 + 心跳 + StreamingResponse 包装
- ``translator`` - LangGraph ``astream_events(version="v2")`` → 业务事件翻译

业务端点典型用法::

    from app.streaming import sse_response, translate_langgraph_events
    from app.streaming.events import StreamEvent, StreamEventType

    @router.post("/chat")
    async def chat(...):
        async def gen():
            yield StreamEvent(type=StreamEventType.META, data={...})
            async for ev in translate_langgraph_events(agent, state, ...):
                yield ev
            yield StreamEvent(type=StreamEventType.DONE, data={...})
        return await sse_response(gen())

设计参考: docs/plans/2026-05-21-streaming-chat-design.md §4-§5
任务规格: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T3
"""

from app.streaming.events import (
    CardPayload,
    ChoiceOption,
    ChoicePayload,
    DonePayload,
    ErrorPayload,
    MetaPayload,
    StatusPayload,
    StreamEvent,
    StreamEventType,
    TextDeltaPayload,
    ToolCallPayload,
    ToolResultPayload,
)
from app.streaming.sse import format_sse, sse_response
from app.streaming.translator import translate_langgraph_events

__all__ = [
    "CardPayload",
    "ChoiceOption",
    "ChoicePayload",
    "DonePayload",
    "ErrorPayload",
    "MetaPayload",
    "StatusPayload",
    "StreamEvent",
    "StreamEventType",
    "TextDeltaPayload",
    "ToolCallPayload",
    "ToolResultPayload",
    "format_sse",
    "sse_response",
    "translate_langgraph_events",
]
