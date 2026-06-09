"""body subgraph 节点实现。

与 diet subgraph 对称：节点读写共享 :class:`ChatState`，字段带 ``body_`` 前缀。
本 subgraph 只负责**解析**自然语言为结构化身体数据（BodyParseResult），
不直接落库——保存由前端确认卡片后走 ``/body/*`` CRUD 接口完成。
"""
# ruff: noqa: RUF001,RUF002

from __future__ import annotations

import logging
from typing import Any, cast

from app.agents._logging import llm_call, log_node
from app.agents.base import get_chat_model
from app.agents.chat.state import ChatState
from app.agents.prompts.body_parse import build_body_parse_messages
from app.core.exceptions import BusinessRuleException, ValidationException
from app.schemas.body import BodyParseResult

logger = logging.getLogger(__name__)


@log_node
async def parse_body_text(state: ChatState) -> dict[str, Any]:
    """LLM 解析身体数据自然语言描述。

    读 ``body_input_text``；写 ``body_parse_result``。

    SDK/API 说明：``with_structured_output(BodyParseResult)`` 要求模型输出
    符合 Pydantic schema 的结构（同时判断类型 + 字段 + operation）。
    """
    input_text = (state.get("body_input_text") or state.get("user_message") or "").strip()
    if not input_text:
        raise ValidationException("身体数据描述不能为空", code="INVALID_QUERY")
    try:
        chat_model = cast(Any, get_chat_model(temperature=0.1))
        model = chat_model.with_structured_output(BodyParseResult)
        async with llm_call("parse_body_text", "qwen-plus", input_text=input_text):
            parsed = await model.ainvoke(build_body_parse_messages(input_text))
    except Exception as exc:
        raise BusinessRuleException("身体数据解析失败", code="BODY_PARSE_FAILED") from exc
    return {"body_parse_result": parsed}


__all__ = ["parse_body_text"]
