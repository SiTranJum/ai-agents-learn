"""
实验 3：混合检索（向量 + 关键词）

实现：
- BM25 关键词检索
- 向量检索
- RRF 合并两路结果

环境准备：pip install chromadb openai
"""

import sys
import io
import math
import re
import chromadb
from openai import OpenAI

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# ========== API 配置 ==========

embedding_client = OpenAI(
    api_key="sk-a4ae611c3f9c4df89a133e621b2b7851",
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


# ========== BM25 关键词检索 ==========

class SimpleBM25:
    """
    简化版 BM25 算法

    BM25 是 Elasticsearch 默认的排序算法
    核心思想：一个词在文档中出现越多 → 越相关
              一个词在所有文档中都出现 → 不重要

    Java 类比：类似 Lucene 的 TF-IDF 评分
    """

    def __init__(self, documents, k1=1.5, b=0.75):
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.doc_count = len(documents)
        self.doc_tokens = [self._tokenize(doc) for doc in documents]
        self.avg_doc_len = sum(len(tokens) for tokens in self.doc_tokens) / self.doc_count

        self.idf = {}
        all_tokens = set()
        for tokens in self.doc_tokens:
            all_tokens.update(set(tokens))

        for token in all_tokens:
            doc_freq = sum(1 for tokens in self.doc_tokens if token in tokens)
            self.idf[token] = math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)

    def _tokenize(self, text):
        """简单中文分词（bigram）"""
        text = re.sub(r'[^\u4e00-\u9fff]', ' ', text)
        tokens = []
        chars = text.replace(' ', '')
        for i in range(len(chars) - 1):
            tokens.append(chars[i:i+2])
        return tokens

    def search(self, query, top_k=5):
        """BM25 检索"""
        query_tokens = self._tokenize(query)
        scores = []

        for doc_idx, doc_tokens in enumerate(self.doc_tokens):
            score = 0
            doc_len = len(doc_tokens)

            for token in query_tokens:
                if token not in self.idf:
                    continue
                tf = doc_tokens.count(token)
                idf = self.idf[token]
                tf_norm = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len))
                score += idf * tf_norm

            scores.append((doc_idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ========== 向量检索 ==========

def build_vector_db():
    """构建 Chroma 向量数据库"""
    client = chromadb.Client()
    collection = client.create_collection(
        name="hybrid_test",
        metadata={"hnsw:space": "cosine"}
    )

    response = embedding_client.embeddings.create(
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


def vector_search(collection, query, top_k=5):
    """向量检索，返回 [(文档索引, 距离)]"""
    query_vector = embedding_client.embeddings.create(
        model="text-embedding-v3", input=query
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "distances"]
    )

    ranked = []
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        idx = KNOWLEDGE_BASE.index(doc)
        ranked.append((idx, dist))
    return ranked


# ========== RRF 合并 ==========

def rrf_merge(vector_results, bm25_results, k=60, top_k=3):
    """
    RRF（Reciprocal Rank Fusion）合并两路检索结果

    公式：score(doc) = Σ 1/(k + rank_i)
    """
    scores = {}

    for rank, (doc_idx, _) in enumerate(vector_results):
        scores[doc_idx] = scores.get(doc_idx, 0) + 1 / (k + rank + 1)

    for rank, (doc_idx, _) in enumerate(bm25_results):
        scores[doc_idx] = scores.get(doc_idx, 0) + 1 / (k + rank + 1)

    merged = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return merged[:top_k]


# ========== 主程序 ==========

if __name__ == "__main__":
    print("实验 3：混合检索（向量 + 关键词）\n")

    print("构建向量数据库...")
    collection = build_vector_db()
    bm25 = SimpleBM25(KNOWLEDGE_BASE)
    print("✓ 完成\n")

    # ===== 测试 1：语义问题（向量检索擅长） =====
    query1 = "吃什么对关节好？"
    print(f"{'='*60}")
    print(f"测试 1：{query1}")
    print(f"（语义问题，向量检索擅长）")
    print(f"{'='*60}")

    vec_results = vector_search(collection, query1, top_k=5)
    bm25_results = bm25.search(query1, top_k=5)
    merged = rrf_merge(vec_results, bm25_results, top_k=3)

    print(f"\n向量检索 top 3：")
    for i, (idx, dist) in enumerate(vec_results[:3]):
        print(f"  #{i+1}：{KNOWLEDGE_BASE[idx][:60]}...")

    print(f"\nBM25 关键词检索 top 3：")
    for i, (idx, score) in enumerate(bm25_results[:3]):
        print(f"  #{i+1}（BM25={score:.2f}）：{KNOWLEDGE_BASE[idx][:60]}...")

    print(f"\nRRF 混合检索 top 3：")
    for i, (idx, score) in enumerate(merged):
        print(f"  #{i+1}（RRF={score:.4f}）：{KNOWLEDGE_BASE[idx][:60]}...")

    # ===== 测试 2：精确匹配问题（关键词检索擅长） =====
    query2 = "β-葡聚糖"
    print(f"\n{'='*60}")
    print(f"测试 2：{query2}")
    print(f"（专有名词，关键词检索擅长）")
    print(f"{'='*60}")

    vec_results = vector_search(collection, query2, top_k=5)
    bm25_results = bm25.search(query2, top_k=5)
    merged = rrf_merge(vec_results, bm25_results, top_k=3)

    print(f"\n向量检索 top 3：")
    for i, (idx, dist) in enumerate(vec_results[:3]):
        print(f"  #{i+1}：{KNOWLEDGE_BASE[idx][:60]}...")

    print(f"\nBM25 关键词检索 top 3：")
    for i, (idx, score) in enumerate(bm25_results[:3]):
        print(f"  #{i+1}（BM25={score:.2f}）：{KNOWLEDGE_BASE[idx][:60]}...")

    print(f"\nRRF 混合检索 top 3：")
    for i, (idx, score) in enumerate(merged):
        print(f"  #{i+1}（RRF={score:.4f}）：{KNOWLEDGE_BASE[idx][:60]}...")

    # ===== 测试 3：综合问题 =====
    query3 = "痛风患者可以吃豆腐吗？"
    print(f"\n{'='*60}")
    print(f"测试 3：{query3}")
    print(f"（综合问题，两路互补）")
    print(f"{'='*60}")

    vec_results = vector_search(collection, query3, top_k=5)
    bm25_results = bm25.search(query3, top_k=5)
    merged = rrf_merge(vec_results, bm25_results, top_k=3)

    print(f"\n向量检索 top 3：")
    for i, (idx, dist) in enumerate(vec_results[:3]):
        print(f"  #{i+1}：{KNOWLEDGE_BASE[idx][:60]}...")

    print(f"\nBM25 关键词检索 top 3：")
    for i, (idx, score) in enumerate(bm25_results[:3]):
        print(f"  #{i+1}（BM25={score:.2f}）：{KNOWLEDGE_BASE[idx][:60]}...")

    print(f"\nRRF 混合检索 top 3：")
    for i, (idx, score) in enumerate(merged):
        print(f"  #{i+1}（RRF={score:.4f}）：{KNOWLEDGE_BASE[idx][:60]}...")

    print(f"\n{'='*60}")
    print("结论：")
    print("  测试 1：向量检索找到'omega-3 减轻关节炎症'（语义相关，无共同关键词）")
    print("  测试 2：BM25 精确匹配'β-葡聚糖'（向量检索可能匹配到其他营养素）")
    print("  测试 3：两路互补，'豆腐+痛风'的文档在两路都靠前，RRF 分数最高")
    print("=" * 60)
