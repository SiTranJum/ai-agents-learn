"""将 LangGraph 事件翻译为业务侧流式事件。"""

from __future__ import annotations

from typing import Any, AsyncIterator, Mapping

from app.streaming.events import StreamEvent, StreamEventType

CHAT_NODE_LABELS: Mapping[str, str] = {
    "identify_intent": "正在识别你的意图...",
    "recall_memories": "正在召回相关记忆...",
    "search_knowledge": "正在检索相关知识...",
    "assemble_prompt": "正在整理上下文...",
    "call_llm": "正在生成回复...",
    "wrap_response": "正在整理最终结果...",
    "parse_text": "正在分析饮食文本...",
    "parse_photo_mock": "正在分析图片内容...",
    "standardize_units": "正在标准化食物单位...",
    "enrich_nutrition": "正在计算营养信息...",
    "infer_meal_type": "正在判断餐次...",
    "narrate_learning": "正在为你讲解...",
    "confirm_save": "请确认饮食记录...",
    "save_record": "正在保存记录...",
    "parse_body_text": "正在分析身体数据...",
    "handle_plan_turn": "正在为你准备计划...",
}

SUGGESTION_NODE_LABELS: Mapping[str, str] = {
    "collect_data": "正在收集健康数据...",
    "recall_memories": "正在召回相关记忆...",
    "search_knowledge": "正在检索相关知识...",
    "generate_suggestions": "正在生成建议...",
    "deduplicate_filter": "正在整理建议结果...",
}

PLAN_NODE_LABELS: Mapping[str, str] = {
    "confirm_goal": "正在确认你的目标...",
    "analyze_status": "正在分析你的档案与状态...",
    "draft_plan": "正在起草计划...",
    "safety_validate": "正在进行安全校验...",
    "persist_plan": "正在保存计划...",
    "handle_plan_turn": "正在为你准备计划...",
}


async def translate_langgraph_events(
    agent: Any,
    state: dict[str, Any],
    *,
    node_labels: Mapping[str, str] | None = None,
    config: dict[str, Any] | None = None,
) -> AsyncIterator[StreamEvent]:
    labels = node_labels if node_labels is not None else CHAT_NODE_LABELS
    cfg = config or {}
    text_visible_nodes = {"call_llm", "narrate_learning"}
    saw_text_delta = False

    async for ev in agent.astream_events(state, version="v2", config=cfg):
        kind = ev.get("event")
        name = ev.get("name", "")
        data = ev.get("data") or {}
        metadata = ev.get("metadata") or {}

        if kind == "on_chain_start" and name in labels:
            yield StreamEvent(type=StreamEventType.STATUS, data={"node": name, "label": labels[name]})
            continue

        if kind == "on_chat_model_stream":
            source_node = metadata.get("langgraph_node", "")
            if source_node not in text_visible_nodes:
                continue
            chunk = data.get("chunk")
            content = _extract_text(chunk)
            if content:
                saw_text_delta = True
                yield StreamEvent(type=StreamEventType.TEXT_DELTA, data={"content": content})
            continue

        if kind == "on_tool_start":
            yield StreamEvent(
                type=StreamEventType.TOOL_CALL,
                data={
                    "tool": name,
                    "label": labels.get(name, f"正在调用 {name} ..."),
                    "args_summary": _short_repr(data.get("input")),
                },
            )
            continue

        if kind == "on_tool_end":
            yield StreamEvent(
                type=StreamEventType.TOOL_RESULT,
                data={"tool": name, "summary": _short_repr(data.get("output"))},
            )
            continue

        if kind == "on_chain_end" and name == "wrap_response":
            output = data.get("output") or {}
            ai_response = output.get("ai_response")
            if ai_response and not saw_text_delta:
                yield StreamEvent(type=StreamEventType.TEXT_DELTA, data={"content": str(ai_response)})
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


def _extract_text(chunk: Any) -> str:
    if chunk is None:
        return ""
    content = getattr(chunk, "content", chunk)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content) if content else ""


def _short_repr(value: Any, max_len: int = 80) -> str:
    if value is None:
        return ""
    text = str(value)
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _maybe_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return {"value": str(value)}


def _interrupt_values(snapshot: Any) -> list[dict[str, Any]]:
    """从 graph state 快照里提取所有挂起的 interrupt 载荷（HumanPrompt dict）。

    LangGraph 把待恢复的 interrupt 挂在 ``snapshot.tasks[].interrupts[].value``。
    用 ``aget_state(config)`` 拿到 snapshot 后调用本函数最稳，跨版本兼容。
    """
    values: list[dict[str, Any]] = []
    tasks = getattr(snapshot, "tasks", None) or []
    for task in tasks:
        for intr in getattr(task, "interrupts", None) or []:
            val = getattr(intr, "value", None)
            if isinstance(val, dict):
                values.append(val)
    return values


def snapshot_has_pending_interrupt(snapshot: Any) -> bool:
    """判断 graph snapshot 是否处于中断态。

    LangGraph 跨版本 / 不同节点拓扑下，``snapshot.next`` 表达"暂停"并不可靠
    （会出现空 tuple 等情况），唯一可靠的信号是 ``snapshot.tasks[].interrupts``
    里有挂起的 interrupt。两者任一非空都视为暂停态。
    """
    if getattr(snapshot, "next", None):
        return True
    return bool(_interrupt_values(snapshot))


async def emit_interrupt_events(agent: Any, config: dict[str, Any]) -> AsyncIterator[StreamEvent]:
    """流跑完后检查是否被 interrupt 暂停，若是则发 CHOICE/CARD + PAUSED 事件。

    用法（在业务端点流末尾）::

        async for ev in translate_langgraph_events(agent, graph_input, config=cfg):
            yield ev
        paused = False
        async for ev in emit_interrupt_events(agent, cfg):
            paused = True
            yield ev
        if not paused:
            yield StreamEvent(type=DONE, ...)
    """
    snapshot = await agent.aget_state(config)
    if not snapshot_has_pending_interrupt(snapshot):
        return  # 未处于中断态
    for hp in _interrupt_values(snapshot):
        kind = hp.get("kind")
        prompt_id = hp.get("prompt_id", "")
        domain = hp.get("domain")
        if kind == "choice":
            yield StreamEvent(
                type=StreamEventType.CHOICE,
                data={
                    "prompt_id": prompt_id,
                    "question": hp.get("question"),
                    "options": hp.get("options", []),
                    "allow_free_text": hp.get("allow_free_text", False),
                },
            )
        elif kind == "card":
            card = hp.get("card")
            if card:
                yield StreamEvent(type=StreamEventType.CARD, data={"card": card})
        yield StreamEvent(
            type=StreamEventType.PAUSED,
            data={"prompt_id": prompt_id, "kind": kind or "choice", "domain": domain},
        )


__all__ = [
    "CHAT_NODE_LABELS",
    "PLAN_NODE_LABELS",
    "SUGGESTION_NODE_LABELS",
    "emit_interrupt_events",
    "snapshot_has_pending_interrupt",
    "translate_langgraph_events",
]
