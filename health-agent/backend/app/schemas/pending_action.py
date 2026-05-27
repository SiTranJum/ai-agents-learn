"""PendingAction 数据模型。

当 AI 需要向用户澄清信息（如"哪一餐？"）时，会在 session 级别存储一个
PendingAction，记录：
- 已经解析出的部分结果（如食物列表）
- 等待用户回答的问题（prompt_id + options）
- 过期时间（30 分钟）

下一次请求带着 prompt_id 进来时，后端读取 PendingAction，合并用户回答，
继续生成最终结果。

设计参考: docs/plans/2026-05-21-streaming-chat-design.md §8
任务规格: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T8
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.streaming.events import ChoiceOption


class PendingAction(BaseModel):
    """跨 SSE 连接的待决状态。"""

    prompt_id: str
    expected_kind: Literal["choice", "free_text"] = "choice"
    options: list[ChoiceOption] = Field(default_factory=list)

    # 已识别但等用户确认的部分结果
    diet_partial: dict[str, Any] | None = None
    plan_partial: dict[str, Any] | None = None

    # 过期时间（UTC）
    expires_at: datetime

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


__all__ = ["PendingAction"]
