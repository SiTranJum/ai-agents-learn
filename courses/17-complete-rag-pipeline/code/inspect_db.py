"""查看 Milvus 中 health_knowledge 集合的数据。"""

from __future__ import annotations

import io
import os
import sys

from pymilvus import MilvusClient

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
COLLECTION_NAME = "health_knowledge"


def main() -> None:
    client = MilvusClient(uri=MILVUS_URI)

    print("=" * 60)
    print("Milvus 集合检查")
    print("=" * 60)
    print(f"URI: {MILVUS_URI}")

    if not client.has_collection(collection_name=COLLECTION_NAME):
        print(f"集合不存在：{COLLECTION_NAME}")
        return

    stats = client.get_collection_stats(collection_name=COLLECTION_NAME)
    print(f"集合：{COLLECTION_NAME}")
    print(f"行数：{stats.get('row_count', 'unknown')}")

    rows = client.query(
        collection_name=COLLECTION_NAME,
        filter="id >= 0",
        output_fields=["id", "text", "source", "category", "chunk_id"],
        limit=10,
    )

    print("\n样例数据（前 10 条）：")
    for row in rows:
        text = row.get("text", "")
        print(f"- id={row.get('id')} source={row.get('source')} category={row.get('category')} chunk={row.get('chunk_id')}")
        print(f"  text={text[:100]}...")


if __name__ == "__main__":
    main()

