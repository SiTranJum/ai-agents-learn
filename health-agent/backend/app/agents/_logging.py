"""Agent 层日志工具。

提供 ``log_node`` 装饰器自动追踪 LangGraph 节点的：
- 进入：节点名 + 关键 state 输入
- 退出：耗时 + 返回的 state 字段
- 异常：完整 traceback

使用方式：

    from app.agents._logging import log_node

    @log_node
    async def parse_text(state: ChatState) -> dict[str, Any]:
        ...

所有节点统一通过此装饰器输出日志，方便排查 LangGraph 流转。

日志级别：默认 INFO。如需更详细输入/输出快照，配置环境变量
``LOG_AGENT_VERBOSE=1`` 启用 DEBUG 级别状态 dump。
"""

from __future__ import annotations

import functools
import inspect
import logging
import os
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger("app.agents.flow")

_VERBOSE = os.environ.get("LOG_AGENT_VERBOSE", "0") == "1"

# 节点 state 中需要打印的关键字段（避免 dump 整个 state）
_INTERESTING_KEYS = (
    "user_id",
    "session_id",
    "intent",
    "user_message",
    "diet_input_text",
    "diet_meal_type",
    "diet_confidence",
    "trigger_type",
    "suggestion_type",
    "meal_type",
    "plan_type",
    "goal_description",
    "error",
)

F = TypeVar("F", bound=Callable[..., Any])


def _short(value: Any, max_len: int = 80) -> str:
    """把任意值压成短字符串，避免日志过长。"""
    if value is None:
        return "None"
    if isinstance(value, str):
        s = value.replace("\n", " ")
        return s if len(s) <= max_len else s[: max_len - 3] + "..."
    if isinstance(value, (list, tuple)):
        return f"[{type(value).__name__} len={len(value)}]"
    if isinstance(value, dict):
        return f"{{dict keys={list(value.keys())[:5]}}}"
    s = repr(value)
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _summarize_state(state: Any) -> str:
    """提取 state 中的关键字段做单行摘要。"""
    if not isinstance(state, dict):
        return _short(state)
    parts: list[str] = []
    for key in _INTERESTING_KEYS:
        if key in state and state[key] is not None:
            parts.append(f"{key}={_short(state[key], 40)}")
    return ", ".join(parts) if parts else "<no interesting keys>"


def _summarize_result(result: Any) -> str:
    """压缩节点返回值为 single-line 摘要。"""
    if isinstance(result, dict):
        keys = list(result.keys())
        return f"updated_keys={keys}"
    if isinstance(result, str):
        return f"-> '{_short(result, 40)}'"
    return f"-> {type(result).__name__}"


def log_node(func: F) -> F:
    """装饰 LangGraph 节点函数，自动记录进入/退出/异常。

    支持 sync 和 async 两种节点函数。
    """
    name = func.__name__

    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            state = args[0] if args else kwargs.get("state")
            logger.info("→ [%s] enter | %s", name, _summarize_state(state))
            if _VERBOSE and isinstance(state, dict):
                logger.debug("   [%s] full_state_keys=%s", name, list(state.keys()))
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.exception(
                    "✗ [%s] FAILED in %.0fms | %s", name, elapsed_ms, exc
                )
                raise
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "← [%s] done in %.0fms | %s", name, elapsed_ms, _summarize_result(result)
            )
            return result

        return async_wrapper  # type: ignore[return-value]

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        state = args[0] if args else kwargs.get("state")
        logger.info("→ [%s] enter | %s", name, _summarize_state(state))
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception("✗ [%s] FAILED in %.0fms | %s", name, elapsed_ms, exc)
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "← [%s] done in %.0fms | %s", name, elapsed_ms, _summarize_result(result)
        )
        return result

    return sync_wrapper  # type: ignore[return-value]


def log_llm_call(node_name: str, model_name: str, **extras: Any) -> None:
    """在节点内调用 LLM 前手动打日志。

    用于追踪 ``model.ainvoke()`` / ``with_structured_output`` 等具体 LLM 调用。
    """
    extra_str = ", ".join(f"{k}={_short(v, 30)}" for k, v in extras.items())
    logger.info(
        "  ⚡ [%s] LLM call: model=%s%s",
        node_name,
        model_name,
        f" | {extra_str}" if extra_str else "",
    )


__all__ = ["log_llm_call", "log_node", "logger"]
