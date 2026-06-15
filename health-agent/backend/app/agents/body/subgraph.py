"""body subgraph 装配。

**这不是独立 Agent**。作为全局 ``chat_graph`` 的一个节点，由路由节点在
``intent == "body"`` 时派发到此处。对外暴露 :func:`build_body_subgraph`。

与 diet subgraph 对称，但更简单：只有一个解析节点，解析完即结束，
结果由 ``wrap_response`` 转成 body_parse 卡片返回前端。
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, StateGraph

from app.agents.body.nodes import confirm_body_record, parse_body_text
from app.agents.chat.state import ChatState


def build_body_subgraph():
    """构建 body subgraph，返回 compiled ``StateGraph``。

    流：parse_body_text → confirm_body_record（interrupt 出确认卡片，确认后落库）。
    """
    graph = StateGraph(cast(Any, ChatState))
    graph.add_node("parse_body_text", cast(Any, parse_body_text))
    graph.add_node("confirm_body_record", cast(Any, confirm_body_record))
    graph.set_entry_point("parse_body_text")
    graph.add_edge("parse_body_text", "confirm_body_record")
    graph.add_edge("confirm_body_record", END)
    return graph.compile()


__all__ = ["build_body_subgraph"]
