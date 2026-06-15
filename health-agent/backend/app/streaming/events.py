"""业务级 SSE 事件定义（Pydantic）。

事件协议参考: docs/plans/2026-05-21-streaming-chat-design.md §4.2
前端镜像类型: src/features/ai/demo/types.ts （T6 阶段会迁移到正式位置）

设计要点：
- ``data`` 字段的 schema 由 ``type`` 决定，运行时不做强校验，
  但每种 payload 都有 Pydantic 模型可被业务代码引用，确保类型对齐。
- ``StreamEvent.data`` 用 ``dict[str, Any]`` 而非 Union，是因为 Pydantic v2
  的 discriminated union 在 SSE 这种"频繁序列化的简单事件"场景下负担过重，
  让翻译层手动 build dict 更直观。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class StreamEventType(str, Enum):
    """SSE 事件类型枚举。"""

    META = "meta"
    STATUS = "status"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TEXT_DELTA = "text_delta"
    CHOICE = "choice"
    CARD = "card"
    PAUSED = "paused"
    DONE = "done"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class StreamEvent(BaseModel):
    """通用 SSE 事件包装。

    ``type`` 决定 ``data`` 的结构（见同文件下各 Payload 模型）。
    """

    type: StreamEventType
    data: dict[str, Any] = Field(default_factory=dict)


# ============ 各 type 对应的 payload 模型 ============


class MetaPayload(BaseModel):
    """流开始的第一条事件，告知客户端 message_id 和 session_id。"""

    message_id: str
    session_id: UUID
    started_at: datetime


class StatusPayload(BaseModel):
    """节点切换时显示的状态文案，例如"正在分析饮食..."。"""

    label: str
    node: str | None = None


class ToolCallPayload(BaseModel):
    """工具调用开始。"""

    tool: str
    label: str
    args_summary: str | None = None


class ToolResultPayload(BaseModel):
    """工具调用结束。"""

    tool: str
    summary: str | None = None


class TextDeltaPayload(BaseModel):
    """LLM 流式 token 增量。"""

    content: str


class ChoiceOption(BaseModel):
    """选项 chip 的单个选项。"""

    value: str
    label: str
    description: str | None = None


class ChoicePayload(BaseModel):
    """请用户选择 / 提供文本。"""

    prompt_id: str
    question: str | None = None
    options: list[ChoiceOption]
    allow_free_text: bool = False


class CardPayload(BaseModel):
    """嵌入消息时间线的富卡片。

    ``card`` 直接用 dict，避免与现有 ``ChatCard`` 强耦合，
    业务代码负责保证字段对齐 frontend 的 ChatCard 接口。
    """

    card: dict[str, Any]


class DonePayload(BaseModel):
    """流正常结束。"""

    message_id: str


class PausedPayload(BaseModel):
    """graph 被 interrupt 暂停，等待用户对 ``prompt_id`` 作答。

    前端收到 ``paused`` 后进入 WAITING_INPUT 态：下一条用户输入要走"恢复"通道，
    带上 ``prompt_id``（choice_response / card_action）。
    """

    prompt_id: str
    kind: str  # "choice" | "card"
    domain: str | None = None


class ErrorPayload(BaseModel):
    """流被异常终止。"""

    code: str
    message: str
    retriable: bool = True


__all__ = [
    "CardPayload",
    "ChoiceOption",
    "ChoicePayload",
    "DonePayload",
    "ErrorPayload",
    "MetaPayload",
    "PausedPayload",
    "StatusPayload",
    "StreamEvent",
    "StreamEventType",
    "TextDeltaPayload",
    "ToolCallPayload",
    "ToolResultPayload",
]
