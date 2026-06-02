"""LangSmith 追踪配置工厂。

统一构建 LangGraph ``astream_events(config=...)`` 所需的 ``tags`` 和
``metadata``，避免每个接口重复手写。

设计要点：
- ``tags`` 用于 LangSmith UI 顶部的快速筛选（如 ``user-xxx``、``chat``、``plan``）
- ``metadata`` 用于 trace 详情面板查看（不可直接筛选，但可全文搜索）
- ``user-{id}`` 是约定，方便按用户筛选所有相关 trace
"""

from __future__ import annotations

from typing import Any


def build_langsmith_config(
    user_id: str,
    endpoint: str,
    *,
    extra_tags: list[str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构建统一的 LangSmith 追踪配置。

    :param user_id: 当前请求的用户 ID（会以 ``user-{id}`` 形式作为 tag，
        方便在 LangSmith 上按用户筛选所有 trace）
    :param endpoint: API 路径（如 ``/api/v1/chat/stream``），用于在 metadata
        中标注请求来源
    :param extra_tags: 额外的 tag（如业务类型、子分类），如 ``["chat", "text"]``
    :param extra_metadata: 额外的 metadata（如 session_id、message_id 等
        非筛选字段）
    :return: ``{"tags": [...], "metadata": {...}}`` 可直接传给
        ``astream_events(config=...)``
    """
    tags = [f"user-{user_id}"]
    if extra_tags:
        tags.extend(extra_tags)

    metadata: dict[str, Any] = {
        "user_id": user_id,
        "endpoint": endpoint,
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    return {"tags": tags, "metadata": metadata}


__all__ = ["build_langsmith_config"]
