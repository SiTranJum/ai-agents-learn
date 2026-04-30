"""课程 16：Embedding + 向量数据库实战（Milvus 版本）。"""

from __future__ import annotations

import io
import os
import sys
from typing import Any

from openai import OpenAI
from pymilvus import MilvusClient

# ========== Windows 终端中文输出修复 ==========
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# ========== API / DB 配置 ==========

# OpenAI SDK 走 DashScope 兼容层：
# - embeddings.create -> text-embedding-v3
# - chat.completions.create -> qwen-plus
dashscope_client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY", "sk-non"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 这里默认连接本机 Docker Milvus standalone（19530）
MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
COLLECTION_NAME = "food_knowledge"


# ========== 第 1 步：Embedding 函数 ==========

def get_embedding(text: str) -> list[float]:
    """
    调用通义千问 Embedding API，把文本转成向量

    参数：
    - text: 要向量化的文本

    返回：
    - 向量（list of float），维度 1024

    Java 类比：
    RestTemplate.postForObject("/embeddings", request, EmbeddingResponse.class)
    """
    response = dashscope_client.embeddings.create(
        model="text-embedding-v3",
        input=text,
    )
    return response.data[0].embedding


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    批量向量化（一次 API 调用处理多条文本，比逐条调用更快更省钱）

    参数：
    - texts: 文本列表

    返回：
    - 向量列表

    Java 类比：类似 JDBC 的 batch insert，一次处理多条
    """
    response = dashscope_client.embeddings.create(
        model="text-embedding-v3",
        input=texts  # 传入列表，一次处理多条
    )
    # response.data 是一个列表，每个元素对应一条文本的向量
    # 按 index 排序确保顺序一致
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in sorted_data]


# ========== 第 2 步：准备知识库 ==========

# 食物营养知识库（实际项目中这些数据来自权威文献）
KNOWLEDGE_BASE = [
    "鸡胸肉每100g含蛋白质31g，脂肪1.2g，热量133卡，嘌呤含量141mg（中等嘌呤）。是减脂期最推荐的蛋白质来源之一。",
    "鸡蛋一个约50g，含蛋白质6g，脂肪5g，热量70卡，嘌呤含量低。蛋黄含胆固醇较高，但每天1-2个对健康人群无害。",
    "白米饭每100g热量约116卡，碳水化合物26g，GI值较高（83）。糖尿病患者建议搭配蔬菜食用，或替换为糙米饭（GI值68）。",
    "牛肉每100g含蛋白质26g，脂肪10g，热量250卡，嘌呤含量较高（约150mg）。痛风患者应限制摄入。",
    "三文鱼每100g含蛋白质20g，脂肪13g，热量208卡，富含omega-3脂肪酸。omega-3有助于减轻关节炎症，对心血管健康有益。",
    "紫薯每100g热量约82卡，碳水化合物20g，富含花青素和膳食纤维。GI值较低（55），适合糖尿病患者。嘌呤含量极低（约12mg）。",
    "燕麦每100g热量约379卡，但饱腹感强。含β-葡聚糖，有助于降低胆固醇。GI值中等（55-69），适合减脂期作为主食替代。",
    "西兰花每100g热量仅34卡，含维生素C 89mg，膳食纤维2.6g。是减脂期最推荐的蔬菜之一，可以大量食用。",
    "豆腐每100g热量约76卡，含蛋白质8g。植物蛋白来源，嘌呤含量中等。痛风急性期建议避免，缓解期可适量食用。",
    "香蕉一根约120g，热量约105卡，富含钾元素。运动前30分钟吃一根香蕉可以提供快速能量。不建议减脂期大量食用，糖分较高。",
]


# ========== 第 3 步：构建向量数据库 ==========

def build_vector_db() -> tuple[MilvusClient, str]:
    """
    离线阶段：把知识库文档向量化并存入 Milvus

    流程：
    1. 创建 Milvus 客户端
    2. 创建 Collection
    3. 批量调用 Embedding API
    4. 插入 Milvus

    Java 类比：类似 Spring Batch 的 ETL（读取->Embedding->入库）
    """
    print("=" * 60)
    print("开始构建向量数据库")
    print("=" * 60)

    # MilvusClient 是 Python SDK 的高层客户端，封装了建表/插入/检索。
    client = MilvusClient(uri=MILVUS_URI)

    # has_collection / drop_collection：检查并重建集合，避免脏数据干扰课程演示。
    if client.has_collection(collection_name=COLLECTION_NAME):
        client.drop_collection(collection_name=COLLECTION_NAME)
        print(f"\n已删除旧的 Collection '{COLLECTION_NAME}'")

    # 批量向量化
    print(f"\n开始向量化知识库（共 {len(KNOWLEDGE_BASE)} 条）...")
    print("  调用 Embedding API（批量处理）...")
    vectors = get_embeddings_batch(KNOWLEDGE_BASE)
    print(f"  ✓ 向量化完成，维度：{len(vectors[0])}")

    # create_collection：
    # - dimension: 向量维度，必须与 embedding 长度一致
    # - metric_type: 相似度度量，语义检索常用 COSINE
    client.create_collection(
        collection_name=COLLECTION_NAME,
        dimension=len(vectors[0]),
        metric_type="COSINE",
    )

    # insert(data=[...])：每条记录是 dict，对应 Java 里一行实体对象。
    rows: list[dict[str, Any]] = []
    for index, (text, vector) in enumerate(zip(KNOWLEDGE_BASE, vectors)):
        rows.append(
            {
                "id": index,
                "vector": vector,
                "text": text,
            }
        )

    print("\n插入 Milvus...")
    client.insert(collection_name=COLLECTION_NAME, data=rows)

    print(f"\n✓ 向量数据库构建完成！共 {len(KNOWLEDGE_BASE)} 条数据")
    return client, COLLECTION_NAME


# ========== 第 4 步：RAG 问答 ==========

def rag_answer(client: MilvusClient, collection_name: str, query: str, top_k: int = 3) -> str:
    """
    在线阶段：用户提问 → 检索 → LLM 回答

    流程：
    1. 把用户问题向量化
    2. 在 Milvus 中检索最相似的文档
    3. 把检索结果拼入 Prompt
    4. 调用通义千问生成回答

    参数：
    - client: MilvusClient 实例
    - collection_name: 集合名
    - query: 用户问题
    - top_k: 检索几条相关文档
    """
    print(f"\n{'='*60}")
    print(f"用户问题：{query}")
    print(f"{'='*60}")

    # 第 1 步：问题向量化
    print(f"\n[1] 向量化用户问题...")
    query_vector = get_embedding(query)

    # 第 2 步：Milvus 检索
    # search() 参数说明：
    # - data: 查询向量列表，支持批量查询
    # - limit: top_k
    # - output_fields: 返回哪些标量字段
    print(f"\n[2] 检索相关知识（top {top_k}）...")
    results = client.search(
        collection_name=collection_name,
        data=[query_vector],
        limit=top_k,
        output_fields=["text"],
    )

    hits = results[0] if results else []
    retrieved_docs = [hit.get("entity", {}).get("text", "") for hit in hits]
    distances = [hit.get("distance", 0.0) for hit in hits]

    for i, (text, dist) in enumerate(zip(retrieved_docs, distances)):
        print(f"  #{i+1}（距离 {dist:.4f}）：{text[:50]}...")

    # 第 3 步：拼入 Prompt
    context = "\n".join([f"- {doc}" for doc in retrieved_docs])

    messages = [
        {"role": "system", "content": (
            "你是健康管家 AI。根据以下参考资料回答用户问题。\n"
            "规则：\n"
            "1. 优先使用参考资料中的数据，不要编造数字\n"
            "2. 如果参考资料中没有相关信息，明确告诉用户\n"
            "3. 回答简洁，2-3 句话即可\n"
            "4. 如果涉及疾病相关建议，提醒用户咨询医生"
        )},
        {"role": "user", "content": (
            f"参考资料：\n{context}\n\n"
            f"用户问题：{query}"
        )}
    ]

    # 第 4 步：调用 LLM
    print(f"\n[3] 调用 qwen-plus 生成回答...")
    response = dashscope_client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        temperature=0.3  # 低温度，让回答更忠于参考资料
    )
    answer = response.choices[0].message.content

    print(f"\n[回答] {answer}")
    return answer


# ========== 主程序 ==========

if __name__ == "__main__":
    print("\n课程 16：Embedding + 向量数据库实战\n")

    # 第 1 步：构建向量数据库（离线阶段）
    client, collection_name = build_vector_db()

    # 第 2 步：RAG 问答（在线阶段）
    print("\n\n" + "=" * 60)
    print("开始 RAG 问答测试")
    print("=" * 60)

    # 测试 1：查询具体营养数据
    rag_answer(client, collection_name, "鸡胸肉多少卡？")

    # 测试 2：痛风患者饮食建议
    rag_answer(client, collection_name, "痛风患者可以吃豆腐吗？")

    # 测试 3：减脂期食物推荐
    rag_answer(client, collection_name, "减脂期吃什么蔬菜好？")

    # 测试 4：知识库中没有的内容
    rag_answer(client, collection_name, "榴莲的热量是多少？")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
