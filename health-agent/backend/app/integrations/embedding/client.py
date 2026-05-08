"""DashScope Embedding 客户端封装。

Embedding 是确定性工具能力, 不属于 LLM 推理编排, 因此不放进 LangGraph。
后续 RAG、Memory 等模块可以直接注入本客户端生成查询向量或入库向量。
"""

from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from app.config import settings

MAX_BATCH_SIZE = 25


class EmbeddingClient:
    """通义千问 DashScope ``text-embedding-v3`` 客户端。

    SDK/API 说明:
    - ``AsyncOpenAI`` 是 OpenAI Python SDK 的异步客户端; DashScope 提供
      OpenAI 兼容接口, 所以只需配置 ``base_url`` 即可调用通义千问服务。
    - ``client.embeddings.create(...)`` 对应 Embeddings API: 输入文本, 返回
      ``response.data``, 其中每个元素包含一个 ``embedding`` 浮点数组。
    - ``dimensions`` 固定为 1024, 后续 pgvector 列也统一使用 ``Vector(1024)``。
    - API Key 从环境变量 ``DASHSCOPE_API_KEY`` 读取, 禁止硬编码。
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model or settings.embedding_model
        self.dimensions = dimensions or settings.embedding_dimensions
        self._client = client or AsyncOpenAI(
            api_key=api_key or settings.dashscope_api_key,
            base_url=base_url or settings.dashscope_base_url,
        )

    async def embed(self, text: str) -> list[float]:
        """为单条文本生成向量。

        SDK/API 说明:
        - ``input`` 传字符串时, Embeddings API 返回一个 ``data[0]``。
        - ``model`` 使用 ``text-embedding-v3``。
        - ``dimensions`` 要与数据库向量列维度一致, 否则 pgvector 无法比较。
        """

        normalized = text.strip()
        if not normalized:
            raise ValueError("text must not be blank")

        response = await self._client.embeddings.create(
            model=self.model,
            input=normalized,
            dimensions=self.dimensions,
        )
        return list(response.data[0].embedding)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成文本向量, 保持输入顺序返回。

        SDK/API 说明:
        - ``input`` 传字符串列表时, Embeddings API 返回同等数量的 ``data``。
        - DashScope 批量请求建议一次不超过 25 条; 更大的任务由调用方分批。
        - 返回值是二维列表: 外层对应每条文本, 内层是 1024 维 float 向量。
        """

        if not texts:
            return []
        if len(texts) > MAX_BATCH_SIZE:
            raise ValueError(f"embed_batch accepts at most {MAX_BATCH_SIZE} texts")

        normalized = [text.strip() for text in texts]
        if any(not text for text in normalized):
            raise ValueError("texts must not contain blank values")

        response = await self._client.embeddings.create(
            model=self.model,
            input=normalized,
            dimensions=self.dimensions,
        )
        return [list(item.embedding) for item in response.data]


__all__ = ["MAX_BATCH_SIZE", "EmbeddingClient"]

