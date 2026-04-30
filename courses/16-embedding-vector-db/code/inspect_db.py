"""查看第16课 Milvus 集合中的数据。"""

from __future__ import annotations

import io
import os
import sys

from pymilvus import MilvusClient

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
COLLECTION_NAME = "food_knowledge"


def main() -> None:
    client = MilvusClient(uri=MILVUS_URI)

    print("=" * 60)
    print("Milvus 集合检查（课程16）")
    print("=" * 60)
    print(f"URI: {MILVUS_URI}")

    collections = client.list_collections()
    print(f"所有 Collection: {collections}")

    if COLLECTION_NAME not in collections:
        print(f"未找到集合：{COLLECTION_NAME}")
        return

    stats = client.get_collection_stats(collection_name=COLLECTION_NAME)
    print(f"集合 {COLLECTION_NAME} 数据量：{stats.get('row_count', 'unknown')}")

    rows = client.query(
        collection_name=COLLECTION_NAME,
        filter="id >= 0",
        output_fields=["id", "text"],
        limit=5,
    )

    print("\n样例数据（前5条）：")
    for row in rows:
        print(f"- id={row.get('id')} text={row.get('text', '')[:90]}...")


if __name__ == "__main__":
    main()

