"""Agent 层公共基础设施。

本模块是后端所有 LLM 推理的唯一模型工厂入口。业务代码不要在
``services/`` 或 ``api/`` 层直接实例化 ChatOpenAI; 后续所有具体 Agent
节点都应通过 :func:`get_chat_model` 获取模型实例。
"""

from __future__ import annotations

from typing import Any, TypedDict

from app.config import settings

try:
    from langchain_openai import ChatOpenAI
except ModuleNotFoundError:  # pragma: no cover - 仅用于未安装依赖时给出清晰错误
    class ChatOpenAI:  # type: ignore[no-redef]
        def __init__(self, **_: Any) -> None:
            raise RuntimeError(
                "langchain-openai is required for Agent LLM calls. "
                "Install backend dependencies with: uv pip install -e \".[dev]\""
            )


class BaseAgentState(TypedDict, total=False):
    """所有 Agent State 共享的基础字段。

    TypedDict 类似 Java 中只约定字段结构的 DTO/interface: 运行时仍是
    ``dict``, 但类型检查器可以据此校验 Agent 节点读写的 key。
    """

    user_id: str
    request_id: str
    error: str | None


def get_chat_model(temperature: float = 0.3, **kwargs: Any) -> ChatOpenAI:
    """创建 DashScope OpenAI 兼容 Chat 模型。

    SDK/API 说明:
    - ``ChatOpenAI`` 来自 ``langchain-openai``, 是 LangChain 对 OpenAI
      Chat Completions 接口的封装; LangGraph 节点可以直接 ``ainvoke`` 它。
    - ``base_url`` 指向 DashScope 的 OpenAI 兼容地址, 因此虽然类名叫
      ChatOpenAI, 实际请求会发送到通义千问兼容接口。
    - ``api_key`` 从 ``DASHSCOPE_API_KEY`` 环境变量加载, 不在代码中硬编码。
    - ``model`` 默认是 ``qwen-plus``, 与项目统一模型选择保持一致。
    - ``temperature`` 控制回复随机性; 结构化解析通常用 0.3, 对话可提高到 0.7。
    - ``timeout`` / ``max_retries`` 交给 LangChain 底层客户端处理, 调用方可按
      Agent 场景通过 ``kwargs`` 覆盖。
    """

    timeout = kwargs.pop("timeout", settings.llm_timeout)
    max_retries = kwargs.pop("max_retries", settings.llm_max_retries)
    return ChatOpenAI(
        model=settings.llm_model,
        base_url=settings.dashscope_base_url,
        api_key=settings.dashscope_api_key,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
        **kwargs,
    )


__all__ = ["BaseAgentState", "get_chat_model"]

