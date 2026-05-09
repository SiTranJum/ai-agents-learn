"""导入 RAG 知识库种子数据。

用法:
    python scripts/seed_knowledge.py --skip-embeddings
    python scripts/seed_knowledge.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.db.session import AsyncSessionLocal
from app.integrations.embedding import EmbeddingClient

BASE_DIR = Path(__file__).resolve().parents[1]
FOODS_PATH = BASE_DIR / "data" / "foods.json"
HEALTH_TIPS_PATH = BASE_DIR / "data" / "health_tips.json"


def _load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _food_embedding_text(item: dict[str, Any]) -> str:
    nutrition = item["nutrition_per_100g"]
    aliases = "、".join(item.get("aliases", []))
    return (
        f"食物: {item['name']}; 别名: {aliases}; 分类: {item['category']}; "
        f"每100克营养: 热量{nutrition['calories']}千卡, "
        f"蛋白质{nutrition['protein']}克, 脂肪{nutrition['fat']}克, "
        f"碳水{nutrition['carbs']}克"
    )


def _doc_embedding_text(item: dict[str, Any]) -> str:
    metadata = item.get("metadata", {})
    tags = "、".join(metadata.get("tags", []))
    return f"标题: {item['title']}; 分类: {metadata.get('category', '')}; 标签: {tags}; 内容: {item['content']}"


async def _maybe_embed(
    embedding_client: EmbeddingClient,
    text: str,
    *,
    skip_embeddings: bool,
) -> list[float] | None:
    if skip_embeddings:
        return None
    # SDK/API 说明: EmbeddingClient 内部使用 OpenAI SDK 的 AsyncOpenAI,
    # 通过 DashScope compatible base_url 调用通义千问 text-embedding-v3。
    return await embedding_client.embed(text)


async def seed_knowledge(*, skip_embeddings: bool) -> None:
    foods = _load_json(FOODS_PATH)
    docs = _load_json(HEALTH_TIPS_PATH)
    embedding_client = EmbeddingClient()

    async with AsyncSessionLocal() as session:
        repo = KnowledgeRepository(session)
        for item in foods:
            nutrition = item["nutrition_per_100g"]
            await repo.upsert_food(
                {
                    "name": item["name"],
                    "aliases": item.get("aliases", []),
                    "category": item["category"],
                    "calories_per_100g": nutrition["calories"],
                    "protein_per_100g": nutrition["protein"],
                    "fat_per_100g": nutrition["fat"],
                    "carbs_per_100g": nutrition["carbs"],
                    "fiber_per_100g": nutrition.get("fiber"),
                    "sodium_per_100g": nutrition.get("sodium"),
                    "sugar_per_100g": nutrition.get("sugar"),
                    "common_portions": item.get("common_portions", []),
                    "data_source": item.get("data_source", "manual"),
                    "embedding": await _maybe_embed(
                        embedding_client,
                        _food_embedding_text(item),
                        skip_embeddings=skip_embeddings,
                    ),
                }
            )

        for item in docs:
            await repo.upsert_knowledge_doc(
                {
                    "title": item["title"],
                    "content": item["content"],
                    "metadata_": item.get("metadata", {}),
                    "embedding": await _maybe_embed(
                        embedding_client,
                        _doc_embedding_text(item),
                        skip_embeddings=skip_embeddings,
                    ),
                }
            )
        await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed RAG knowledge data")
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="只导入结构化数据, 不调用 DashScope Embedding API",
    )
    args = parser.parse_args()
    asyncio.run(seed_knowledge(skip_embeddings=args.skip_embeddings))


if __name__ == "__main__":
    main()
