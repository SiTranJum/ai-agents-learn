import os
"""
实验 4：查询改写

用 LLM 改写模糊问题，提升检索效果

三种改写策略：
1. 精确改写：消除歧义
2. 扩展改写：补充关键词
3. 多查询改写：拆成多个子问题

环境准备：pip install chromadb openai
"""

import sys
import io
import json
import chromadb
from openai import OpenAI

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# ========== API 配置 ==========

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# ========== 知识库 ==========

KNOWLEDGE_BASE = [
    "鸡胸肉每100g含蛋白质31g，脂肪1.2g，热量133卡，嘌呤含量141mg（中等嘌呤）。是减脂期最推荐的蛋白质来源之一。",
    "鸡蛋一个约50g，含蛋白质6g，脂肪5g，热量70卡，嘌呤含量低。蛋黄含胆固醇较高，但每天1-2个对健康人群无害。",
    "牛肉每100g含蛋白质26g，脂肪10g，热量250卡，嘌呤含量较高（约150mg）。痛风患者应限制摄入。富含铁元素。",
    "三文鱼每100g含蛋白质20g，脂肪13g，热量208卡，富含omega-3脂肪酸。omega-3有助于减轻关节炎症。",
    "白米饭每100g热量约116卡，碳水化合物26g，GI值较高（83）。糖尿病患者建议搭配蔬菜食用。",
    "紫薯每100g热量约82卡，GI值较低（55），适合糖尿病患者。嘌呤含量极低（约12mg），痛风患者可以放心食用。",
    "燕麦每100g热量约379卡，但饱腹感强。含β-葡聚糖，有助于降低胆固醇。适合减脂期作为主食替代。",
    "西兰花每100g热量仅34卡，含维生素C 89mg。是减脂期最推荐的蔬菜之一，可以大量食用。",
    "豆腐每100g热量约76卡，含蛋白质8g。植物蛋白来源，嘌呤含量中等。痛风急性期建议避免，缓解期可适量食用。",
    "香蕉一根约120g，热量约105卡，富含钾元素。运动前30分钟吃一根香蕉可以提供快速能量。",
]


# ========== 构建向量数据库 ==========

def build_db():
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(
        name="query_rewrite_test",
        metadata={"hnsw:space": "cosine"}
    )

    response = client.embeddings.create(
        model="text-embedding-v3",
        input=KNOWLEDGE_BASE
    )
    sorted_data = sorted(response.data, key=lambda x: x.index)
    vectors = [item.embedding for item in sorted_data]

    collection.add(
        ids=[f"doc_{i}" for i in range(len(KNOWLEDGE_BASE))],
        embeddings=vectors,
        documents=KNOWLEDGE_BASE
    )
    return collection


# ========== 向量检索 ==========

def vector_search(collection, query, top_k=3):
    query_vector = client.embeddings.create(
        model="text-embedding-v3", input=query
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "distances"]
    )
    return list(zip(results["documents"][0], results["distances"][0]))


# ========== 查询改写 ==========

def rewrite_query(query):
    """策略 1：精确改写"""
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[{
            "role": "user",
            "content": f"""请把以下用户问题改写成更明确、更适合在食物营养知识库中检索的形式。
只输出改写后的问题，不要解释。

原始问题：{query}
改写后："""
        }],
        temperature=0
    )
    return response.choices[0].message.content.strip()


def expand_query(query):
    """策略 2：扩展改写，补充同义词和关键词"""
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[{
            "role": "user",
            "content": f"""请扩展以下问题，补充相关的同义词和关键词，使其更适合检索。
保持一个问句的形式，不要拆成多个问题。

原始问题：{query}
扩展后："""
        }],
        temperature=0
    )
    return response.choices[0].message.content.strip()


def multi_query_rewrite(query):
    """策略 3：多查询改写，拆成多个子问题"""
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[{
            "role": "user",
            "content": f"""请把以下问题拆分成 2-3 个更具体的子问题，用于在食物营养知识库中检索。
用 JSON 数组格式返回，例如：["子问题1", "子问题2"]
只返回 JSON，不要其他内容。

原始问题：{query}"""
        }],
        temperature=0
    )
    content = response.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)


def multi_query_search(collection, queries, top_k=3):
    """多查询检索：每个子问题分别检索，合并去重"""
    all_docs = {}

    for query in queries:
        results = vector_search(collection, query, top_k=top_k)
        for doc, dist in results:
            if doc not in all_docs or dist < all_docs[doc]:
                all_docs[doc] = dist

    sorted_docs = sorted(all_docs.items(), key=lambda x: x[1])
    return sorted_docs[:top_k]


# ========== 工具函数 ==========

def print_results(label, results):
    print(f"\n{label}：")
    for i, (doc, dist) in enumerate(results):
        sim = 1 - dist / 2
        print(f"  #{i+1}（相似度 {sim:.3f}）：{doc[:70]}...")


# ========== 主程序 ==========

if __name__ == "__main__":
    print("实验 4：查询改写\n")

    collection = build_db()

    # ===== 测试 1：模糊问题 =====
    query1 = "吃啥好"
    print(f"{'='*60}")
    print(f"测试 1 — 原始问题：{query1}")
    print(f"{'='*60}")

    results_raw = vector_search(collection, query1)
    print_results("不改写", results_raw)

    rewritten = rewrite_query(query1)
    print(f"\n精确改写 → {rewritten}")
    results_rewritten = vector_search(collection, rewritten)
    print_results("改写后检索", results_rewritten)

    # ===== 测试 2：不明确的问题 =====
    query2 = "血糖高不能吃什么"
    print(f"\n{'='*60}")
    print(f"测试 2 — 原始问题：{query2}")
    print(f"{'='*60}")

    results_raw = vector_search(collection, query2)
    print_results("不改写", results_raw)

    expanded = expand_query(query2)
    print(f"\n扩展改写 → {expanded}")
    results_expanded = vector_search(collection, expanded)
    print_results("扩展后检索", results_expanded)

    # ===== 测试 3：复杂问题 =====
    query3 = "减脂期怎么吃"
    print(f"\n{'='*60}")
    print(f"测试 3 — 原始问题：{query3}")
    print(f"{'='*60}")

    results_raw = vector_search(collection, query3)
    print_results("不改写", results_raw)

    sub_queries = multi_query_rewrite(query3)
    print(f"\n多查询改写 →")
    for q in sub_queries:
        print(f"  - {q}")

    results_multi = multi_query_search(collection, sub_queries)
    print_results("多查询合并检索", results_multi)

    print(f"\n{'='*60}")
    print("结论：")
    print("  模糊问题（'吃啥好'）→ 精确改写后检索更有针对性")
    print("  不明确问题（'血糖高'）→ 扩展改写补充关键词，召回更多相关文档")
    print("  复杂问题（'减脂期怎么吃'）→ 拆成子问题，覆盖蛋白质、蔬菜、主食多个方面")
    print("=" * 60)
