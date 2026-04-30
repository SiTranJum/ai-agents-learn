"""
课程 15：RAG 基础演示

用一个最简单的例子演示 RAG 的完整流程：
1. 准备知识库（食物营养数据）
2. 把知识库文本转成向量（Embedding）
3. 用户提问时，检索最相关的知识
4. 把检索结果塞进 Prompt，让 LLM 回答

本示例用内存列表模拟向量数据库，不需要安装 Milvus。
课程 16 会用真正的向量数据库。

Java 类比：
- 知识库 = 数据库里的参考数据表
- Embedding = 把文本转成可比较的特征向量
- 向量检索 = SELECT ... ORDER BY vector_distance LIMIT 3
- RAG = Service 层先查数据库，再调 LLM
"""

import json
import sys
import io
import math
from openai import OpenAI

# ========== Windows 终端中文输出修复 ==========
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# ========== DeepSeek API 客户端 ==========
client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"
)


# ========== 第 1 步：准备知识库 ==========

# 模拟食物营养知识库（实际项目中这些数据来自权威文献）
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


# ========== 第 2 步：Embedding（向量化） ==========

def get_embedding(text):
    """
    把文本转成向量

    调用 DeepSeek 的 Embedding API（目前 DeepSeek 暂不提供 Embedding 接口，
    这里我们用一个简单的模拟实现来演示原理。课程 16 会用真正的 Embedding API）

    Java 类比：类似把一个对象序列化成 byte[]，但这里是把文本序列化成 float[]
    """
    # ========== 简易模拟 Embedding ==========
    # 真正的 Embedding 会把语义编码进向量
    # 这里用字符频率模拟，仅用于演示 RAG 流程
    # 课程 16 会用真正的 Embedding API
    chars = set(text)
    # 用常见的食物/营养相关关键词作为维度
    keywords = [
        "鸡", "蛋", "肉", "鱼", "米", "饭", "菜", "果",
        "蛋白质", "脂肪", "热量", "卡", "碳水", "纤维",
        "嘌呤", "痛风", "糖尿病", "减脂", "GI", "维生素",
        "钾", "胆固醇", "omega", "花青素", "膳食",
        "运动", "健康", "推荐", "建议", "适合"
    ]
    vector = []
    for kw in keywords:
        # 关键词出现次数作为该维度的值
        count = text.count(kw)
        vector.append(float(count))

    # 归一化（让向量长度为 1，方便计算余弦相似度）
    magnitude = math.sqrt(sum(v * v for v in vector)) or 1.0
    vector = [v / magnitude for v in vector]

    return vector


def cosine_similarity(vec1, vec2):
    """
    计算两个向量的余弦相似度

    余弦相似度 = 两个向量的点积 / (向量1的长度 × 向量2的长度)
    值域：[-1, 1]，越接近 1 表示越相似

    Java 类比：类似 Comparator，但比较的是"语义距离"而不是大小
    """
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1)) or 1.0
    magnitude2 = math.sqrt(sum(b * b for b in vec2)) or 1.0
    return dot_product / (magnitude1 * magnitude2)


# ========== 第 3 步：构建向量索引（模拟向量数据库） ==========

class SimpleVectorStore:
    """
    简易向量存储（模拟向量数据库）

    实际项目中用 Milvus / Chroma / Pinecone 等
    这里用 Python 列表模拟，演示原理

    Java 类比：类似一个 HashMap<Integer, Pair<float[], String>>
    """

    def __init__(self):
        self.vectors = []   # 存储向量
        self.texts = []     # 存储原始文本

    def add(self, text):
        """添加一条文档"""
        vector = get_embedding(text)
        self.vectors.append(vector)
        self.texts.append(text)

    def search(self, query, top_k=3):
        """
        搜索最相似的文档

        参数：
        - query: 用户的查询文本
        - top_k: 返回最相似的前 k 条

        返回：
        - [(text, similarity_score), ...] 按相似度降序排列

        Java 类比：
        SELECT text, vector_distance(query_vector, doc_vector) as score
        FROM documents
        ORDER BY score DESC
        LIMIT top_k
        """
        query_vector = get_embedding(query)

        # 计算查询向量与每条文档向量的相似度
        scores = []
        for i, doc_vector in enumerate(self.vectors):
            similarity = cosine_similarity(query_vector, doc_vector)
            scores.append((self.texts[i], similarity))

        # 按相似度降序排列，取前 top_k 条
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ========== 第 4 步：RAG 问答 ==========

def rag_answer(query, vector_store, top_k=3):
    """
    RAG 问答：检索 + 增强 + 生成

    参数：
    - query: 用户问题
    - vector_store: 向量存储
    - top_k: 检索几条相关文档

    流程：
    1. 从向量存储中检索最相关的文档
    2. 把文档内容拼入 Prompt
    3. 调用 LLM 生成回答
    """
    print(f"\n{'='*60}")
    print(f"用户问题：{query}")
    print(f"{'='*60}")

    # 第 1 步：检索
    print(f"\n[1] 检索相关知识（top {top_k}）...")
    results = vector_store.search(query, top_k=top_k)
    for i, (text, score) in enumerate(results):
        print(f"  #{i+1}（相似度 {score:.3f}）：{text[:50]}...")

    # 第 2 步：拼入 Prompt
    context = "\n".join([f"- {text}" for text, score in results])

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

    # 第 3 步：调用 LLM
    print(f"\n[2] 调用 LLM 生成回答...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.3  # 低温度，让回答更忠于参考资料
    )
    answer = response.choices[0].message.content

    print(f"\n[回答] {answer}")
    return answer


def no_rag_answer(query):
    """
    不用 RAG，直接问 LLM（用于对比）
    """
    print(f"\n{'='*60}")
    print(f"[无 RAG 对比] 用户问题：{query}")
    print(f"{'='*60}")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是健康管家 AI，回答简洁，2-3句话。"},
            {"role": "user", "content": query}
        ],
        temperature=0.3
    )
    answer = response.choices[0].message.content
    print(f"\n[回答] {answer}")
    return answer


# ========== 主程序 ==========

if __name__ == "__main__":
    print("课程 15：RAG 基础演示\n")

    # 第 1 步：构建知识库索引
    print("[准备] 构建知识库向量索引...")
    store = SimpleVectorStore()
    for doc in KNOWLEDGE_BASE:
        store.add(doc)
    print(f"  已索引 {len(KNOWLEDGE_BASE)} 条知识\n")

    # 第 2 步：测试 RAG 问答
    queries = [
        "鸡胸肉的热量和蛋白质含量是多少？",
        "我有痛风，能吃什么肉？",
        "减脂期主食吃什么好？",
        "吃什么对关节好？",
    ]

    for query in queries:
        # 有 RAG 的回答
        rag_answer(query, store)

        # 无 RAG 的回答（对比）
        no_rag_answer(query)

        print("\n" + "-" * 60)
