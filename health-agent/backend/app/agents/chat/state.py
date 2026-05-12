"""全局 Chat Agent State。

`ChatState` 是整个对话 Agent 的统一状态容器，所有节点（含各领域 subgraph）
共享它。采用**单一大 TypedDict** 的方案（字段全部 Optional），避免学习阶段
过度拆分；后续若 state 字段暴增再按领域拆为嵌套 state。

字段分组（便于阅读）：

- 对话核心：``messages`` / ``user_id`` / ``session_id``
- 路由结果：``intent``
- 领域输入/输出：``diet_*`` / ``body_*`` / ``plan_*`` / ...
- 元信息：``request_id`` / ``error``

LangGraph SDK/API 说明：
- ``Annotated[list[BaseMessage], add_messages]`` 让节点返回 messages 片段时
  由框架合并而不是覆盖，这是 LangChain 对话 Graph 的标准模式。
- 所有未显式标注合并策略的字段，节点返回时均为**覆盖写入**。
"""
# ruff: noqa: RUF002,RUF003

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal, TypedDict

try:  # pragma: no cover - 仅在未安装依赖时给出提示
    from langchain_core.messages import BaseMessage
    from langgraph.graph.message import add_messages
except ModuleNotFoundError:  # pragma: no cover
    BaseMessage = Any  # type: ignore[assignment,misc]

    def add_messages(left: Any, right: Any) -> Any:  # type: ignore[no-redef]
        raise RuntimeError(
            "langgraph is required for ChatState.messages merging. "
            "Install backend dependencies with: uv pip install -e \".[dev]\""
        )


# 顶层意图标签。路由节点根据 LLM / 规则判断后写入 ``intent``，
# 全局 Graph 的条件边据此选择目标 subgraph。
Intent = Literal["diet", "body", "plan", "memory", "suggestion", "general"]


class ChatState(TypedDict, total=False):
    """全局对话 Agent 的共享状态。"""

    # ---------- 对话核心 ----------
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    session_id: str | None

    # ---------- 路由 ----------
    intent: Intent | None

    # ---------- 领域字段：饮食（diet subgraph） ----------
    # 输入
    diet_input_text: str | None
    diet_image_url: str | None
    diet_meal_type: str | None
    diet_date: date | None
    # subgraph 运行时中间态
    diet_parsed_foods: list[Any]
    diet_confidence: float
    # subgraph 产出
    diet_parse_result: Any
    diet_saved_record: Any
    # Phase 4/6 过渡兼容字段：测试或 chat_graph 可临时携带这些值。
    foods: list[Any]
    mode: str | None
    diet_service: Any

    # ---------- 元信息 ----------
    request_id: str | None
    error: str | None


__all__ = ["ChatState", "Intent"]
