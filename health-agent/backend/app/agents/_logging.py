"""Agent 层日志工具。

提供 ``log_node`` 装饰器自动追踪 LangGraph 节点的：
- 进入：节点名 + 关键 state 输入
- 退出：耗时 + 返回字段及其值（关键字段）
- 异常：完整 traceback

提供 ``llm_call`` 上下文管理器追踪单次 LLM 调用耗时：
- 进入：打印 ⚡ LLM call 开始
- 退出：打印 ✓ LLM done in Xms

使用方式：

    from app.agents._logging import log_node, llm_call

    @log_node
    async def parse_text(state: ChatState) -> dict[str, Any]:
        async with llm_call("parse_text", "qwen-plus", input=text):
            result = await model.ainvoke(messages)

日志级别：默认 INFO。如需更详细输入/输出快照，配置环境变量
``LOG_AGENT_VERBOSE=1`` 启用 DEBUG 级别状态 dump。
"""

from __future__ import annotations

import contextlib
import functools
import inspect
import logging
import os
import time
from typing import Any, AsyncIterator, Callable, TypeVar

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
    """压缩节点返回值，同时打出关键字段的值（不只是 key 名）。

    之前只打 updated_keys=['intent']，看不出决策结果。
    现在对 _INTERESTING_KEYS 中的字段直接打值，其余字段只打名字。
    """
    if not isinstance(result, dict):
        if isinstance(result, str):
            return f"-> '{_short(result, 40)}'"
        return f"-> {type(result).__name__}"

    interesting: list[str] = []
    other_keys: list[str] = []
    for k, v in result.items():
        if k in _INTERESTING_KEYS:
            interesting.append(f"{k}={_short(v, 40)}")
        else:
            other_keys.append(k)

    parts: list[str] = []
    if interesting:
        parts.append(", ".join(interesting))
    if other_keys:
        parts.append(f"keys={other_keys}")
    return " | ".join(parts) if parts else "{}"


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


@contextlib.asynccontextmanager
async def llm_call(node_name: str, model_name: str, **extras: Any) -> AsyncIterator[None]:
    """追踪单次 LLM 调用耗时的异步上下文管理器。

    替代原来的 ``log_llm_call()`` 函数，现在能精确打出 LLM 本身花了多久，
    而不是把 LLM 耗时藏在节点总耗时里。

    用法::

        async with llm_call("parse_text", "qwen-plus", input_text=text):
            result = await model.ainvoke(messages)

    输出::

        ⚡ [parse_text] LLM call: model=qwen-plus | input_text=...
        ✓ [parse_text] LLM done in 1823ms
    """
    extra_str = ", ".join(f"{k}={_short(v, 30)}" for k, v in extras.items())
    logger.info(
        "  ⚡ [%s] LLM call: model=%s%s",
        node_name,
        model_name,
        f" | {extra_str}" if extra_str else "",
    )
    start = time.perf_counter()
    try:
        yield
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error("  ✗ [%s] LLM FAILED in %.0fms | %s", node_name, elapsed_ms, exc)
        raise
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("  ✓ [%s] LLM done in %.0fms", node_name, elapsed_ms)


# 保留旧函数名作为兼容别名，避免一次性改太多文件
def log_llm_call(node_name: str, model_name: str, **extras: Any) -> None:
    """已废弃：请改用 ``async with llm_call(...)``。保留仅供兼容。"""
    extra_str = ", ".join(f"{k}={_short(v, 30)}" for k, v in extras.items())
    logger.info(
        "  ⚡ [%s] LLM call: model=%s%s",
        node_name,
        model_name,
        f" | {extra_str}" if extra_str else "",
    )


__all__ = ["llm_call", "log_llm_call", "log_node", "logger"]
