"""全局 Chat Agent 包。

`chat_agent` 是后端所有 LLM 推理的唯一入口（唯一由 API 层直接触发的 Agent）。
其他领域（diet/body/plan 等）以 subgraph 形式被本包的全局 Graph 组装。

Phase 6 会在本包内填充 ``graph.py``；当前仅暴露 :class:`ChatState`，供领域
subgraph 提前按照统一 state 签名开发。
"""
# ruff: noqa: RUF002

from app.agents.chat.state import ChatState

__all__ = ["ChatState"]
