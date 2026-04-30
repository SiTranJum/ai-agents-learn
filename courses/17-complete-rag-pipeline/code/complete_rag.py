"""
课程 17：完整的 RAG Pipeline（Milvus 版本）

演示从文档到问答的完整流程：
1. 加载 Markdown 文档
2. 智能分块（RecursiveCharacterTextSplitter）
3. 添加元数据
4. 向量化并存入 Milvus
5. 检索 + 元数据过滤
6. LLM 生成回答

环境准备：
pip install openai pymilvus
"""

from __future__ import annotations

import io
import os
import sys
from typing import Any, Optional

from openai import OpenAI
from pymilvus import MilvusClient

# Windows 终端中文输出修复
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

# DashScope 兼容 OpenAI SDK 的客户端：
# - chat.completions.create -> 调用对话模型
# - embeddings.create -> 调用向量模型
dashscope_client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
COLLECTION_NAME = "health_knowledge"


class RecursiveCharacterTextSplitter:
    """按语义边界优先的递归分块器。"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", "。", "，", " ", ""]

    def split_text(self, text: str) -> list[str]:
        return self._split_text_recursive(text, self.separators)

    def _split_text_recursive(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]
        if not separators:
            return self._split_by_characters(text)

        separator = separators[0]
        splits = text.split(separator) if separator else list(text)

        chunks: list[str] = []
        current_chunk = ""

        for split in splits:
            if len(split) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                chunks.extend(self._split_text_recursive(split, separators[1:]))
            else:
                if len(current_chunk) + len(split) + len(separator) <= self.chunk_size:
                    current_chunk = f"{current_chunk}{separator}{split}" if current_chunk else split
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = split

        if current_chunk:
            chunks.append(current_chunk)
        return self._add_overlap(chunks)

    def _split_by_characters(self, text: str) -> list[str]:
        chunks: list[str] = []
        step = max(1, self.chunk_size - self.chunk_overlap)
        for index in range(0, len(text), step):
            chunks.append(text[index : index + self.chunk_size])
        return chunks

    def _add_overlap(self, chunks: list[str]) -> list[str]:
        if len(chunks) <= 1:
            return chunks

        overlapped = [chunks[0]]
        for index in range(1, len(chunks)):
            prev_chunk = chunks[index - 1]
            overlap_text = prev_chunk[-self.chunk_overlap :] if len(prev_chunk) > self.chunk_overlap else prev_chunk
            overlapped.append(overlap_text + chunks[index])
        return overlapped


def load_markdown_document(file_path: str) -> dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
    return {
        "text": text,
        "metadata": {
            "source": os.path.basename(file_path),
            "format": "markdown",
        },
    }


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    # OpenAI SDK embeddings.create:
    # - model: 向量模型名
    # - input: 支持字符串列表，服务端批量返回 embedding
    response = dashscope_client.embeddings.create(model="text-embedding-v3", input=texts)
    sorted_data = sorted(response.data, key=lambda item: item.index)
    return [item.embedding for item in sorted_data]


def classify_chunk(chunk: str) -> str:
    if any(keyword in chunk for keyword in ["鸡蛋", "牛肉", "三文鱼", "蛋白质"]):
        return "肉蛋类"
    if any(keyword in chunk for keyword in ["米饭", "面包", "苹果", "香蕉"]):
        return "主食水果"
    if any(keyword in chunk for keyword in ["西兰花", "豆腐", "菠菜"]):
        return "蔬菜豆制品"
    return "其他"


def build_knowledge_base_from_document(
    doc_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> tuple[MilvusClient, str]:
    print("=" * 60)
    print("构建知识库（Milvus）")
    print("=" * 60)

    print(f"\n[1] 加载文档：{doc_path}")
    doc = load_markdown_document(doc_path)
    print(f"  文档长度：{len(doc['text'])} 字符")

    print(f"\n[2] 分块（chunk_size={chunk_size}, overlap={chunk_overlap}）")
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(doc["text"])
    print(f"  分块数量：{len(chunks)}")
    print(f"  平均块大小：{sum(len(chunk) for chunk in chunks) / len(chunks):.0f} 字符")

    print("\n[3] 向量化（批量处理）")
    vectors = get_embeddings_batch(chunks)
    dimension = len(vectors[0])
    print(f"  完成，向量维度：{dimension}")

    print(f"\n[4] 存入 Milvus（{MILVUS_URI}）")
    client = MilvusClient(uri=MILVUS_URI)
    if client.has_collection(collection_name=COLLECTION_NAME):
        client.drop_collection(collection_name=COLLECTION_NAME)

    # MilvusClient.create_collection:
    # - dimension: 向量维度，必须和 embedding 长度一致
    # - metric_type: 向量相似度算法，COSINE 适合语义检索
    client.create_collection(collection_name=COLLECTION_NAME, dimension=dimension, metric_type="COSINE")

    rows: list[dict[str, Any]] = []
    for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
        rows.append(
            {
                "id": index,
                "vector": vector,
                "text": chunk,
                "source": doc["metadata"]["source"],
                "format": doc["metadata"]["format"],
                "category": classify_chunk(chunk),
                "chunk_id": index,
            }
        )

    # MilvusClient.insert:
    # - data: 每条记录是一个 dict，键名对应 Milvus 字段
    client.insert(collection_name=COLLECTION_NAME, data=rows)
    print(f"  完成，共 {len(rows)} 条数据")
    return client, COLLECTION_NAME


def rag_answer_with_metadata(
    client: MilvusClient,
    collection_name: str,
    query: str,
    category_filter: Optional[str] = None,
    top_k: int = 3,
) -> str:
    print(f"\n{'=' * 60}")
    print(f"用户问题：{query}")
    if category_filter:
        print(f"分类过滤：{category_filter}")

    query_vector = get_embeddings_batch([query])[0]
    filter_expr = f'category == "{category_filter}"' if category_filter else ""

    # MilvusClient.search:
    # - data: 查询向量列表，这里只查 1 个问题向量
    # - filter: 标量过滤表达式（类似 SQL WHERE）
    # - output_fields: 指定返回的非向量字段
    search_results = client.search(
        collection_name=collection_name,
        data=[query_vector],
        limit=top_k,
        filter=filter_expr,
        output_fields=["text", "source", "category", "chunk_id"],
    )

    hits = search_results[0] if search_results else []
    if not hits:
        return "没有检索到相关资料，请调整问题或先导入知识库。"

    print("\n[1] 检索结果")
    context_parts: list[str] = []
    for index, hit in enumerate(hits, start=1):
        entity = hit.get("entity", {})
        score = hit.get("distance", 0.0)
        text = entity.get("text", "")
        source = entity.get("source", "unknown")
        category = entity.get("category", "unknown")
        chunk_id = entity.get("chunk_id", -1)
        print(f"  #{index}（相似分数 {score:.4f}）")
        print(f"    来源：{source} | 分类：{category} | Chunk {chunk_id}")
        print(f"    内容：{text[:80]}...")
        context_parts.append(f"[来源：{source}，分类：{category}]\n{text}")

    context = "\n\n".join(context_parts)
    messages = [
        {
            "role": "system",
            "content": (
                "你是健康管家 AI。根据参考资料回答用户问题。"
                "如果资料不足，明确说明不确定。回答控制在 2-3 句话。"
            ),
        },
        {"role": "user", "content": f"参考资料：\n{context}\n\n用户问题：{query}"},
    ]

    print("\n[2] 生成回答")
    # OpenAI SDK chat.completions.create:
    # - model: qwen-plus
    # - messages: 多轮消息数组，返回 response.choices[0].message.content
    response = dashscope_client.chat.completions.create(model="qwen-plus", messages=messages)
    answer = response.choices[0].message.content
    print(f"\n回答：{answer}")
    return answer


def ensure_sample_doc(doc_path: str) -> None:
    if os.path.exists(doc_path):
        return

    sample_doc = """# 健康知识库示例

## 蛋白质来源

### 鸡蛋
鸡蛋一个约50g，含蛋白质6g，脂肪5g，热量70卡，嘌呤含量低。

### 牛肉
牛肉每100g含蛋白质26g，脂肪10g，热量250卡，嘌呤含量较高。

### 三文鱼
三文鱼每100g含蛋白质20g，脂肪13g，热量208卡，富含omega-3脂肪酸。

## 主食和水果

### 米饭
米饭每100g约116卡，主要提供碳水化合物。

### 苹果
苹果每100g约52卡，膳食纤维丰富。

## 蔬菜和豆制品

### 西兰花
西兰花低热量高纤维，富含维生素C。

### 豆腐
豆腐是优质植物蛋白来源，脂肪含量较低。
"""
    with open(doc_path, "w", encoding="utf-8") as file:
        file.write(sample_doc)
    print(f"示例文档已创建：{doc_path}")


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(script_dir, "health_knowledge.md")

    ensure_sample_doc(doc_path)
    client, collection_name = build_knowledge_base_from_document(doc_path, chunk_size=300, chunk_overlap=50)

    print("\n" + "=" * 60)
    print("RAG 问答测试")
    print("=" * 60)

    rag_answer_with_metadata(client, collection_name, "鸡蛋和牛肉哪个更适合减脂期补蛋白？")
    rag_answer_with_metadata(client, collection_name, "痛风患者可以吃什么蛋白质来源？", category_filter="肉蛋类")
    rag_answer_with_metadata(client, collection_name, "减脂期推荐吃什么？")


if __name__ == "__main__":
    main()
