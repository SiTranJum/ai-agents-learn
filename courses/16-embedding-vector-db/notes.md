# 课程 16 学习笔记

## 核心概念

### Embedding 不是 LLM 做的
- Chat 模型（deepseek-chat）：输入文本 → 输出文本
- Embedding 模型（text-embedding-v3）：输入文本 → 输出向量
- 两者是完全不同的模型，类似 Java 里的两个不同 Service

### 不能跨模型 Embedding
- 离线和在线必须用同一个 Embedding 模型
- 不同模型的向量空间不同，就像不同的密码本
- 换模型 = 整个知识库要重新向量化

### 向量维度
- 维度 = 向量里有多少个数字
- text-embedding-v3：1024 维
- 维度越高，语义越丰富，但存储和计算成本越高

### 哪些需要向量化
| 内容 | 是否向量化 | 原因 |
|------|-----------|------|
| 知识库文档 | ✅ | 存入向量数据库，等着被搜索 |
| 用户问题 | ✅ | 变成向量才能去向量数据库里搜 |
| Prompt | ❌ | 直接以文本发给 Chat API |
| LLM 回答 | ❌ | Chat API 返回的就是文本 |

**向量化只服务于"搜索"这一步**

## 向量数据库对比

| 维度 | Milvus | Chroma | Pinecone | pgvector | Qdrant |
|------|--------|--------|----------|----------|--------|
| 开源 | 是 | 是 | 否（云服务） | 是（PG 插件） | 是 |
| 部署方式 | Docker / K8s | pip install | 无需部署 | 装 PG 插件 | Docker / 二进制 |
| Windows 支持 | 不支持 Lite | 支持 | 云服务，无所谓 | 支持 | 支持 |
| 数据规模 | 十亿级 | 百万级 | 十亿级 | 千万级 | 亿级 |
| 性能 | 很快 | 一般 | 快 | 一般 | 很快 |
| 分布式 | 支持 | 不支持 | 支持 | 不支持 | 支持 |
| GUI 工具 | Attu | 无 | Web 控制台 | pgAdmin | Web Dashboard |
| 生态集成 | LangChain/LlamaIndex | LangChain/LlamaIndex | LangChain/LlamaIndex | LangChain/LlamaIndex | LangChain/LlamaIndex |
| 语言 | Go + C++ | Python | 闭源 | C | Rust |
| 适合场景 | 大规模生产环境 | 开发学习、小项目 | 不想运维、快速上线 | 已有 PG、不想加组件 | 性能要求高 |

### 选择建议

```
已经有 PostgreSQL？
  → pgvector（不用额外部署，加个插件就行）

学习阶段 / 小项目 / Windows？
  → Chroma（pip install 就能用）

生产环境、数据量大？
  → Milvus 或 Qdrant

不想运维、有预算？
  → Pinecone（纯云服务，按量付费）
```

### 健康管家项目的选择

```
现在（学习阶段）：Chroma
  → Windows 能跑，简单，够用

后面（上线部署）：pgvector
  → 技术栈里已有 Supabase（底层是 PostgreSQL）
  → 直接开启 pgvector 扩展，不用额外部署向量数据库
```

## Chroma 基本操作

```python
# 创建客户端（本地持久化）
client = chromadb.PersistentClient(path="./chroma_db")

# 创建 Collection
collection = client.create_collection(
    name="food_knowledge",
    metadata={"hnsw:space": "cosine"}
    ids=["doc_0", "doc_1"],
collection.add(
    ids=["doc_0", "doc_1"],
    embeddings=[vector1, vector2],
    documents=["文本1", "文本2"]
collection.get()    # 全部数据
```

## Chroma vs Milvus 概念对照

| Chroma | Milvus | MySQL |
results = collection.query(
    query_embeddings=[query_vector],
    n_results=3,
    include=["documents", "distances"]
| embedding | vector field | (无) |
collection.count()  # 数据量
collection.get()    # 全部数据
| collection.query() | client.search() | SELECT |

## 完整 RAG 流程

```
离线阶段：
  文档 → 批量 Embedding API → 存入 Chroma

在线阶段：
  用户问题 → Embedding API → Chroma 检索 → 拼入 Prompt → Chat API
```

## 实践要点

- 批量 Embedding 比逐条快很多（`get_embeddings_batch()`）
- Chroma 的 cosine 距离：0 = 完全相同，2 = 完全相反
- 相似度 = 1 - distance/2（范围 0-1）
- Chroma 数据存在本地目录，可以直接用代码查看（`inspect_db.py`）
