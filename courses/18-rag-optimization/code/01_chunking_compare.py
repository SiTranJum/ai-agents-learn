"""
实验 1：分块策略对比

对比三种分块策略的检索效果：
- 策略 A：固定长度（200 字，无 overlap）
- 策略 B：固定长度（200 字，overlap 50）
- 策略 C：递归分块（按段落/句子边界切分）

环境准备：pip install chromadb openai
"""

import sys
import io
import chromadb
from openai import OpenAI

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# ========== API 配置 ==========

embedding_client = OpenAI(
    api_key="sk-non",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# ========== 测试文档 ==========

DOCUMENT = """鸡胸肉每100g含蛋白质31g，脂肪1.2g，热量133卡，嘌呤含量141mg（中等嘌呤）。是减脂期最推荐的蛋白质来源之一。建议烹饪方式：水煮、清蒸、少油煎。

鸡蛋一个约50g，含蛋白质6g，脂肪5g，热量70卡，嘌呤含量低。蛋黄含胆固醇较高，但每天1-2个对健康人群无害。全蛋营养价值高于只吃蛋白。

牛肉每100g含蛋白质26g，脂肪10g，热量250卡，嘌呤含量较高（约150mg）。痛风患者应限制摄入。富含铁元素，适合贫血人群。

三文鱼每100g含蛋白质20g，脂肪13g，热量208卡，富含omega-3脂肪酸。omega-3有助于减轻关节炎症，对心血管健康有益。建议每周食用2-3次。

白米饭每100g热量约116卡，碳水化合物26g，GI值较高（83）。糖尿病患者建议搭配蔬菜食用，或替换为糙米饭（GI值68）。

紫薯每100g热量约82卡，碳水化合物20g，富含花青素和膳食纤维。GI值较低（55），适合糖尿病患者。嘌呤含量极低（约12mg），痛风患者可以放心食用。

燕麦每100g热量约379卡，但饱腹感强。含β-葡聚糖，有助于降低胆固醇。GI值中等（55-69），适合减脂期作为主食替代。建议选择原味燕麦片，避免即食燕麦（含糖高）。

西兰花每100g热量仅34卡，含维生素C 89mg，膳食纤维2.6g。是减脂期最推荐的蔬菜之一，可以大量食用。烹饪建议：焯水后快炒，保留营养。

豆腐每100g热量约76卡，含蛋白质8g。植物蛋白来源，嘌呤含量中等。痛风急性期建议避免，缓解期可适量食用。豆腐含钙丰富，适合乳糖不耐受人群。"""


# ========== 三种分块策略 ==========

def chunk_fixed(text, size=200):
    """策略 A：固定长度，无 overlap"""
    chunks = []
    for i in range(0, len(text), size):
        chunk = text[i:i + size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def chunk_fixed_overlap(text, size=200, overlap=50):
    """策略 B：固定长度，有 overlap"""
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + size].strip()
        if chunk:
            chunks.append(chunk)
        start += size - overlap
    return chunks


def chunk_recursive(text, size=200):
    """策略 C：递归分块（按段落 → 句子边界切分）"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) <= size:
            current = current + "\n\n" + para if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) > size:
                sentences = para.split('。')
                sub_chunk = ""
                for sent in sentences:
                    if not sent.strip():
                        continue
                    if len(sub_chunk) + len(sent) <= size:
                        sub_chunk = sub_chunk + "。" + sent if sub_chunk else sent
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk + "。")
                        sub_chunk = sent
                if sub_chunk:
                    chunks.append(sub_chunk)
            else:
                current = para
    if current:
        chunks.append(current)

    return chunks


# ========== Embedding ==========

def get_embeddings_batch(texts):
    response = embedding_client.embeddings.create(
        model="text-embedding-v3",
        input=texts
    )
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in sorted_data]


# ========== 构建并检索 ==========

def build_and_search(strategy_name, chunks, query):
    """构建向量数据库并检索"""
    client = chromadb.Client()  # 内存模式，不持久化
    collection = client.create_collection(
        name="test01",
        metadata={"hnsw:space": "cosine"}
    )

    # 向量化并插入
    vectors = get_embeddings_batch(chunks)
    collection.add(
        ids=[f"c_{i}" for i in range(len(chunks))],
        embeddings=vectors,
        documents=chunks
    )

    # 检索
    query_vector = embedding_client.embeddings.create(
        model="text-embedding-v3", input=query
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=3,
        include=["documents", "distances"]
    )

    # 打印结果
    print(f"\n{'='*60}")
    print(f"策略：{strategy_name}")
    print(f"分块数量：{len(chunks)}")
    print(f"平均块大小：{sum(len(c) for c in chunks) / len(chunks):.0f} 字符")

    print(f"\n分块内容：")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i}（{len(chunk)}字）：{chunk[:60]}...")

    print(f"\n检索结果 top 3：")
    for i, (text, dist) in enumerate(zip(results["documents"][0], results["distances"][0])):
        similarity = 1 - dist / 2
        print(f"  #{i+1}（相似度 {similarity:.3f}）：{text[:80]}...")


# ========== 主程序 ==========

if __name__ == "__main__":
    print("实验 1：分块策略对比\n")

    query = "痛风患者可以吃豆腐吗？"

    # 策略 A：固定长度
    chunks_a = chunk_fixed(DOCUMENT, size=200)
    build_and_search("A：固定长度（200字，无overlap）", chunks_a, query)

    # 策略 B：固定长度 + overlap
    chunks_b = chunk_fixed_overlap(DOCUMENT, size=200, overlap=50)
    build_and_search("B：固定长度（200字，overlap=50）", chunks_b, query)

    # 策略 C：递归分块
    chunks_c = chunk_recursive(DOCUMENT, size=200)
    build_and_search("C：递归分块（按段落/句子边界）", chunks_c, query)

    print("\n" + "=" * 60)
    print("对比结论：")
    print("  策略 A/B 可能把豆腐的信息切断")
    print("  策略 C 按段落切分，豆腐的完整信息在一个 chunk 里")
    print("  → 递归分块通常效果最好")
    print("=" * 60)
