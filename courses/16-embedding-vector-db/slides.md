# 课程 16：Embedding 与向量数据库入门

---

## 第一部分：真正的 Embedding API

### 1.1 回顾课程 15

上节课我们用关键词频率模拟了 Embedding，但真正的 Embedding 是由专门的 AI 模型生成的，能捕捉文本的语义信息。

```
模拟 Embedding（课程 15）：
  "鸡蛋" → 数"鸡"出现1次，"蛋"出现1次 → [1, 1, 0, 0, ...]
  缺点：只看字面，不懂语义。"鸡蛋"和"蛋类食品"被认为完全不同

真正的 Embedding：
  "鸡蛋" → AI 模型理解语义 → [0.12, -0.34, 0.78, ...]
  "蛋类食品" → AI 模型理解语义 → [0.13, -0.32, 0.76, ...]
  两者向量非常接近！因为 AI 懂它们是同一个意思
```

### 1.2 Embedding API 怎么用

Embedding API 和 Chat API 用法类似，都是通过 OpenAI SDK 调用，只是换了个方法。

```python
# Chat API（课程 1 学过）
# client.chat.completions.create() → 返回文本
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "你好"}]
)
text = response.choices[0].message.content  # → "你好！"

# Embedding API（本课新学）
# client.embeddings.create() → 返回向量
response = client.embeddings.create(
    model="embedding-model",
    input="鸡蛋"  # 要向量化的文本
)
vector = response.data[0].embedding  # → [0.12, -0.34, 0.78, ...]
```

**Java 类比**：
```java
// Chat API = RestTemplate.postForObject("/chat", ...)
// Embedding API = RestTemplate.postForObject("/embeddings", ...)
// 同一个客户端，不同的接口
```

### 1.3 Embedding 模型选择

DeepSeek 目前不提供 Embedding API，我们用通义千问（DashScope）的 Embedding 模型。

| 提供商 | 模型名 | 维度 | 特点 |
|--------|--------|------|------|
| 通义千问 | text-embedding-v3 | 1024 | 国内可用、OpenAI SDK 兼容 |
| OpenAI | text-embedding-3-small | 1536 | 业界标准、需要海外信用卡 |
| 智谱 AI | embedding-3 | 2048 | 国内可用、中文效果好 |

**本课使用通义千问**：
- 和 DeepSeek 一样通过 OpenAI SDK 兼容模式调用
- base_url 改成 `https://dashscope.aliyuncs.com/compatible-mode/v1`

### 1.4 向量维度是什么

```
维度 = 向量里有多少个数字

embedding-3（2048 维）：
  "鸡蛋" → [0.12, -0.34, 0.78, ..., 0.56]  共 2048 个数字

text-embedding-3-small（1536 维）：
  "鸡蛋" → [0.12, -0.34, 0.78, ..., 0.56]  共 1536 个数字
```

维度越高，能表达的语义信息越丰富，但存储和计算成本也越高。

**类比**：描述一个人，用 3 个维度（身高、体重、年龄）vs 用 100 个维度（加上肤色、发型、性格...），后者区分度更高。

---

## 第二部分：Milvus 向量数据库

### 2.1 为什么需要向量数据库

课程 15 用 Python 列表存向量，遍历计算相似度。

```python
# 课程 15 的做法
for doc_vector in all_vectors:
    similarity = cosine_similarity(query_vector, doc_vector)
```

**问题**：如果知识库有 100 万条文档，每次查询都要算 100 万次余弦相似度，太慢了。

**向量数据库的作用**：通过索引加速搜索，不需要遍历全部数据。

```
Python 列表：100 万条 × 计算相似度 = 几秒
向量数据库：100 万条 × 索引检索 = 几毫秒
```

**Java 类比**：
- Python 列表 = 全表扫描 `SELECT * FROM docs`
- 向量数据库 = 加了索引 `CREATE INDEX ... USING ivfflat`

### 2.2 Milvus Lite — 无需 Docker

Milvus 支持"Lite 模式"，数据存在本地文件，不需要安装 Docker 或启动服务。

```python
# 安装
# pip install pymilvus

# 创建客户端 — 指定一个本地文件路径即可
from pymilvus import MilvusClient
client = MilvusClient("./health_kb.db")  # 数据存在这个文件里
```

**Java 类比**：类似 SQLite vs MySQL
- Milvus Lite（本地文件）= SQLite（开发学习用）
- Milvus Server（Docker）= MySQL（生产环境用）

### 2.3 核心概念对照

| Milvus 概念 | MySQL 类比 | 说明 |
|------------|-----------|------|
| Collection | Table | 存储数据的集合 |
| Field | Column | 字段定义 |
| Entity | Row | 一条数据 |
| Vector Field | 无（MySQL 没有） | 存向量的特殊字段 |
| Index | Index | 加速检索 |

### 2.4 Milvus 基本操作

**创建 Collection（建表）**：
```python
from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType

# 定义字段
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=2048),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
]

# 创建 Schema（类似 Java 的 @Entity 类）
schema = CollectionSchema(fields=fields, description="食物营养知识库")

# 创建 Collection
client.create_collection(
    collection_name="food_knowledge",
    schema=schema
)
```

**插入数据**：
```python
data = [
    {"vector": [0.12, -0.34, ...], "text": "鸡蛋每个约50g，热量70卡"},
    {"vector": [0.45, 0.23, ...], "text": "鸡胸肉每100g热量133卡"},
]
client.insert(collection_name="food_knowledge", data=data)
```

**搜索**：
```python
results = client.search(
    collection_name="food_knowledge",
    data=[query_vector],     # 查询向量
    limit=3,                 # 返回 top 3
    output_fields=["text"]   # 同时返回 text 字段
)
```

---

## 第三部分：完整 RAG Pipeline

### 3.1 架构图

```
┌──────────────────────────────────────────────┐
│                离线阶段（准备知识库）            │
│                                              │
│  知识文档                                     │
│     ↓                                        │
│  分块（Chunking）                              │
│     ↓                                        │
│  调用 Embedding API → 得到向量                 │
│     ↓                                        │
│  存入 Milvus（向量 + 原文）                    │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│                在线阶段（用户提问）              │
│                                              │
│  用户问题                                     │
│     ↓                                        │
│  调用 Embedding API → 得到查询向量             │
│     ↓                                        │
│  Milvus 检索 → 找到最相似的文档块              │
│     ↓                                        │
│  把文档块拼入 Prompt                           │
│     ↓                                        │
│  调用 LLM → 生成回答                          │
└──────────────────────────────────────────────┘
```

### 3.2 与课程 15 的对比

| 环节 | 课程 15（模拟版） | 课程 16（真实版） |
|------|-----------------|-----------------|
| Embedding | 关键词频率模拟 | 智谱 AI Embedding API |
| 向量存储 | Python 列表 | Milvus Lite |
| 搜索方式 | 遍历计算相似度 | Milvus 索引检索 |
| 可扩展性 | 几百条就慢了 | 百万级没问题 |

---

## 小结

### 核心概念

1. **Embedding API**：和 Chat API 类似，只是输入文本、输出向量
2. **向量维度**：向量里有多少个数字，维度越高语义越丰富
3. **Milvus Lite**：向量数据库的本地模式，不需要 Docker，适合学习
4. **Collection / Field / Entity**：类比 MySQL 的 Table / Column / Row
5. **完整 RAG Pipeline**：Embedding + Milvus 检索 + LLM 生成

### 环境准备

运行本课代码需要：
1. `pip install pymilvus openai`
2. 通义千问 API Key（DashScope 平台）
