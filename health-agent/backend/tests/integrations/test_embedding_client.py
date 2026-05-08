"""Phase 2 - DashScope Embedding 客户端测试。"""

from __future__ import annotations

import pytest

from app.integrations.embedding import EmbeddingClient


class _FakeEmbeddingResponseItem:
    def __init__(self, embedding: list[float]) -> None:
        self.embedding = embedding


class _FakeEmbeddingResponse:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.data = [_FakeEmbeddingResponseItem(value) for value in embeddings]


class _FakeEmbeddingsResource:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs: object) -> _FakeEmbeddingResponse:
        self.calls.append(kwargs)
        input_value = kwargs["input"]
        if isinstance(input_value, str):
            return _FakeEmbeddingResponse([[0.1, 0.2, 0.3]])
        if not isinstance(input_value, list):
            raise TypeError("input must be str or list[str]")
        return _FakeEmbeddingResponse([[float(i)] for i, _ in enumerate(input_value)])


class _FakeAsyncOpenAI:
    def __init__(self) -> None:
        self.embeddings = _FakeEmbeddingsResource()


@pytest.mark.asyncio
async def test_embed_calls_openai_compatible_embedding_api() -> None:
    sdk_client = _FakeAsyncOpenAI()
    client = EmbeddingClient(api_key="key", client=sdk_client)

    embedding = await client.embed("苹果 100 克")

    assert embedding == [0.1, 0.2, 0.3]
    assert sdk_client.embeddings.calls == [
        {
            "model": "text-embedding-v3",
            "input": "苹果 100 克",
            "dimensions": 1024,
        }
    ]


@pytest.mark.asyncio
async def test_embed_batch_preserves_order() -> None:
    sdk_client = _FakeAsyncOpenAI()
    client = EmbeddingClient(api_key="key", client=sdk_client)

    embeddings = await client.embed_batch(["苹果", "香蕉", "牛奶"])

    assert embeddings == [[0.0], [1.0], [2.0]]


@pytest.mark.asyncio
async def test_embed_rejects_blank_text() -> None:
    client = EmbeddingClient(api_key="key", client=_FakeAsyncOpenAI())

    with pytest.raises(ValueError, match="text must not be blank"):
        await client.embed("  ")


@pytest.mark.asyncio
async def test_embed_batch_rejects_more_than_25_texts() -> None:
    client = EmbeddingClient(api_key="key", client=_FakeAsyncOpenAI())

    with pytest.raises(ValueError, match="at most 25"):
        await client.embed_batch(["text"] * 26)

