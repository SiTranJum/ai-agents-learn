"""
实验 2：Reranker 重排序

对比有无 Reranker 的检索效果：
- 纯向量检索 top 3
- 向量检索 top 5 → LLM 重排序 → 取 top 3

用通义千问做 Reranker（不需要额外模型）

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
    api_key="sk-non",
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
        name="reranker_test",
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

def vector_search(collection, query, top_k):
    query_vector = client.embeddings.create(
        model="text-embedding-v3", input=query
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "distances"]
    )

    docs = results["documents"][0]
    distances = results["distances"][0]
    return list(zip(docs, distances))


# ========== LLM Reranker ==========

def llm_rerank(query, doc_list, top_k=3):
    """
    用 LLM 对检索结果重新打分

    输入：问题 + 候选文档列表
    输出：按相关性排序后的 top_k 文档
    """
    docs_text = ""
    for i, (doc, _) in enumerate(doc_list):
        docs_text += f"文档{i}: {doc}\n"

    prompt = f"""你是一个搜索相关性评估专家。

用户问题：{query}

候选文档：
{docs_text}
请评估每个文档对回答用户问题的相关性，给出 0-10 的分数。
10 = 直接回答了问题，0 = 完全无关。

请严格按以下 JSON 格式输出，不要输出其他内容：
{{"scores": [{{"doc_index": 0, "score": 8, "reason": "简短理由"}}, ...]}}"""

    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    # 解析 LLM 返回的分数
    content = response.choices[0].message.content
    start = content.find('{')
    end = content.rfind('}') + 1
    result = json.loads(content[start:end])

    # 按分数排序
    scored_docs = []
    for item in result["scores"]:
        idx = item["doc_index"]
        score = item["score"]
        reason = item["reason"]
        doc, dist = doc_list[idx]
        scored_docs.append((doc, score, reason, dist))

    scored_docs.sort(key=lambda x: x[1], reverse=True)
    return scored_docs[:top_k]


# ========== 主程序 ==========

if __name__ == "__main__":
    print("实验 2：Reranker 重排序\n")

    collection = build_db()
    query = "痛风患者可以吃豆腐吗？"

    print(f"查询：{query}")

    # ===== 方案 1：纯向量检索 top 3 =====
    print(f"\n{'='*60}")
    print("方案 1：纯向量检索 top 3")
    print(f"{'='*60}")

    results_no_rerank = vector_search(collection, query, top_k=3)
    for i, (doc, dist) in enumerate(results_no_rerank):
        sim = 1 - dist / 2
        print(f"  #{i+1}（相似度 {sim:.3f}）：{doc[:70]}...")

    # ===== 方案 2：向量检索 top 5 → LLM 重排序 → top 3 =====
    print(f"\n{'='*60}")
    print("方案 2：向量检索 top 5 → LLM 重排序 → top 3")
    print(f"{'='*60}")

    results_top5 = vector_search(collection, query, top_k=5)
    print(f"\n粗筛 top 5：")
    for i, (doc, dist) in enumerate(results_top5):
        sim = 1 - dist / 2
        print(f"  #{i+1}（相似度 {sim:.3f}）：{doc[:70]}...")

    print(f"\nLLM 重排序中...")
    reranked = llm_rerank(query, results_top5, top_k=3)

    print(f"\n重排序后 top 3：")
    for i, (doc, score, reason, dist) in enumerate(reranked):
        sim = 1 - dist / 2
        print(f"  #{i+1}（LLM 评分 {score}/10，向量相似度 {sim:.3f}）")
        print(f"    理由：{reason}")
        print(f"    内容：{doc[:70]}...")

    print(f"\n{'='*60}")
    print("对比结论：")
    print("  纯向量检索：按语义距离排序，可能把'豆腐热量'排在'豆腐与痛风'前面")
    print("  加 Reranker：LLM 理解问题意图，把真正回答问题的文档排到前面")
    print(f"{'='*60}")
