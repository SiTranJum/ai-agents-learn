"""节点依赖解析：从 ``config.configurable`` 取运行时依赖（service 等）。

为什么不放 state：checkpointer 会序列化整个 state，而 service 持有 DB session、
连接等不可序列化对象。LangGraph 的 ``config.configurable`` 是运行时通道，**不进
checkpoint**，正好用来传这类依赖。

兼容性：优先从 ``config`` 取；取不到再回退到 ``state``（保留旧单测直接往 state
注入 service 的写法）。新代码一律走 config。
"""

from __future__ import annotations

from typing import Any


def get_dep(state: Any, config: Any, name: str) -> Any:
    """按 ``config.configurable[name]`` → ``state[name]`` 的顺序解析依赖。"""
    if config:
        configurable = config.get("configurable") if hasattr(config, "get") else None
        if configurable and name in configurable:
            return configurable[name]
    if hasattr(state, "get"):
        return state.get(name)
    return None


__all__ = ["get_dep"]
