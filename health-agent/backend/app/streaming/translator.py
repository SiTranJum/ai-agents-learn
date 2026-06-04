"""LangGraph ``astream_events(version="v2")`` → 业务事件翻译。

LangGraph v2 事件参考：
https://langchain-ai.github.io/langgraph/how-tos/stream-tokens/

事件类型映射（节选）：

- ``on_chain_start`` (节点开始) → :class:`StatusPayload`
- ``on_chain_end``   (节点结束) → 检查产出（card / choice）
- ``on_chat_model_stream`` → :class:`TextDeltaPayload`
- ``on_tool_start``  → :class:`ToolCallPayload`
- ``on_tool_end``    → :class:`ToolResultPayload`

约定：
- ``node_labels`` 是节点 internal 名（如 ``identify_intent``）→ 用户可见文案
  （如 ``正在识别意图...``）的映射；不在表里的节点不发 status 事件。
- 仅最外层 chain 的 ``on_chain_end`` 才检查 cards / choice_prompts，
  避免内部子图也触发卡片事件。
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Mapping

from app.streaming.events import StreamEvent, StreamEventType

logger = logging.getLogger("app.streaming")


# 默认 chat agent 的节点标签
CHAT_NODE_LABELS: Mapping[str, str] = {
    "identify_intent": "正在识别意图...",
    "recall_memories": "正在回忆相关记忆...",
    "search_knowledge": "正在查找知识库...",
    "assemble_prompt": "正在准备上下文...",
    "call_llm": "正在生成回复...",
    "wrap_response": "正在整理回复...",
    # diet 子图节点
    "parse_text": "正在分析饮食...",
    "parse_photo_mock": "正在分析图片...",
    "standardize_units": "正在标准化食物量...",
    "enrich_nutrition": "正在计算营养...",
    "infer_meal_type": "正在推断餐次...",
    "save_record": "正在保存记录...",
    # body 子图节点
    "parse_body_text": "正在分析身体数据...",
}

SUGGESTION_NODE_LABELS: Mapping[str, str] = {
    "collect_data": "正在收集健康数据...",
    "recall_memories": "正在回忆相关记忆...",
    "search_knowledge": "正在查找知识库...",
    "generate_suggestions": "AI 正在为你生成建议...",
    "deduplicate_filter": "正在整理建议...",
}

PLAN_NODE_LABELS: Mapping[str, str] = {
    "confirm_goal": "正在确认你的目标...",
    "analyze_status": "正在分析你的健康状况...",
    "draft_plan": "AI 正在为你制定计划...",
    "safety_validate": "正在做安全校验...",
    "persist_plan": "正在保存计划...",
}


async def translate_langgraph_events(
    agent: Any,
    state: dict[str, Any],
    *,
    node_labels: Mapping[str, str] | None = None,
    config: dict[str, Any] | None = None,
) -> AsyncIterator[StreamEvent]:
    """异步迭代 LangGraph 事件，翻译为业务级 :class:`StreamEvent`。

    业务端点典型调用::

        async for ev in translate_langgraph_events(
            chat_agent,
            state,
            node_labels=CHAT_NODE_LABELS,
        ):
            yield ev

    :param agent: 已编译的 LangGraph ``Runnable``
    :param state: 初始 state dict
    :param node_labels: 节点 → 用户文案 映射；为 None 时使用 :data:`CHAT_NODE_LABELS`
    :param config: 透传给 ``astream_events`` 的额外配置
    """
    labels = node_labels if node_labels is not None else CHAT_NODE_LABELS
    cfg = config or {}

    # 只有这些节点的 LLM token 流才是给用户看的自然语言。
    # 其他节点（identify_intent / parse_text 等）用 with_structured_output，
    # 输出的是 JSON 结构化数据，不应该展示给用户。
    TEXT_VISIBLE_NODES = {"call_llm"}

    async for ev in agent.astream_events(state, version="v2", config=cfg):
        kind = ev.get("event")
        name = ev.get("name", "")
        data = ev.get("data") or {}
        metadata = ev.get("metadata") or {}

        # ===== 节点开始 → status =====
        if kind == "on_chain_start" and name in labels:
            yield StreamEvent(
                type=StreamEventType.STATUS,
                data={"node": name, "label": labels[name]},
            )
            continue

        # ===== LLM token 流 → text_delta（仅 call_llm 节点） =====
        if kind == "on_chat_model_stream":
            # langgraph_node 标识当前 token 来自哪个节点
            source_node = metadata.get("langgraph_node", "")
            if source_node not in TEXT_VISIBLE_NODES:
                continue
            chunk = data.get("chunk")
            content = _extract_text(chunk)
            if content:
                yield StreamEvent(
                    type=StreamEventType.TEXT_DELTA,
                    data={"content": content},
                )
            continue

        # ===== 工具调用 =====
        if kind == "on_tool_start":
            yield StreamEvent(
                type=StreamEventType.TOOL_CALL,
                data={
                    "tool": name,
                    "label": labels.get(name, f"调用 {name}..."),
                    "args_summary": _short_repr(data.get("input")),
                },
            )
            continue

        if kind == "on_tool_end":
            yield StreamEvent(
                type=StreamEventType.TOOL_RESULT,
                data={
                    "tool": name,
                    "summary": _short_repr(data.get("output")),
                },
            )
            continue

        # ===== 节点结束：检查 cards / choice_prompts =====
        if kind == "on_chain_end" and name == "wrap_response":
            output = data.get("output") or {}
            for card in _ensure_list(output.get("response_cards")):
                yield StreamEvent(
                    type=StreamEventType.CARD,
                    data={"card": card if isinstance(card, dict) else _maybe_dump(card)},
                )
            for prompt in _ensure_list(output.get("choice_prompts")):
                yield StreamEvent(
                    type=StreamEventType.CHOICE,
                    data=prompt if isinstance(prompt, dict) else _maybe_dump(prompt),
                )


# ============ helpers ============


def _extract_text(chunk: Any) -> str:
    """从 LangChain ``AIMessageChunk`` / 其他 chunk 提取文本内容。"""
    if chunk is None:
        return ""
    content = getattr(chunk, "content", chunk)
    if isinstance(content, str):
        return content
    # LangChain 有时 content 是 list[dict]（多模态）
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                t = item.get("text")
                if isinstance(t, str):
                    parts.append(t)
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content) if content else ""


def _short_repr(value: Any, max_len: int = 80) -> str:
    """工具入参/出参的简要 repr，避免日志爆炸。"""
    if value is None:
        return ""
    s = str(value)
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _maybe_dump(value: Any) -> dict[str, Any]:
    """把 Pydantic 模型转 dict；其他类型尽力兜底。"""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return {"value": str(value)}


__all__ = ["CHAT_NODE_LABELS", "PLAN_NODE_LABELS", "SUGGESTION_NODE_LABELS", "translate_langgraph_events"]
