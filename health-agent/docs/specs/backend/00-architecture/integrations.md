# LLM 与向量数据库集成

> 本文档定义 DashScope LLM、Embedding 和 pgvector 的集成方案，包括客户端封装、Prompt 管理、重试策略和各模块的使用方式。
>
> 实现依据：`00-architecture/overview.md`，`docs/prd/v1/05-ai-memory.md`，`docs/prd/v1/06-rag-knowledge.md`

---

## 1. DashScope LLM 集成

### 1.1 客户端封装

使用 OpenAI SDK 兼容接口调用 DashScope。

```python
# app/integrations/llm/client.py
from openai import AsyncOpenAI

class LLMClient:
    """DashScope LLM 客户端，基于 OpenAI SDK 兼容接口"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,  # https://dashscope.aliyuncs.com/compatible-mode/v1
        )
        self.model = model  # qwen-plus

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: dict | None = None,
    ) -> LLMResponse:
        """发送 chat completion 请求"""
        ...

    async def chat_with_json(
        self,
        messages: list[ChatMessage],
        schema: type[BaseModel],
        temperature: float = 0.3,
    ) -> BaseModel:
        """发送请求并解析为结构化 JSON（用于饮食解析、记忆提取等）"""
        ...
```

### 1.2 输入输出类型

```python
# app/integrations/llm/schemas.py
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str

class LLMResponse(BaseModel):
    content: str
    usage: TokenUsage

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

### 1.3 重试策略

| 错误类型 | 重试次数 | 退避策略 | 说明 |
|---------|---------|---------|------|
| 网络超时 | 3 次 | 指数退避（1s, 2s, 4s） | 临时网络问题 |
| 429 Rate Limit | 3 次 | 按 Retry-After 头等待 | API 限流 |
| 500 服务端错误 | 2 次 | 指数退避（2s, 4s） | 服务端临时故障 |
| 400 请求错误 | 不重试 | — | 请求本身有问题 |
| 其他错误 | 不重试 | — | 抛出 `LLM_SERVICE_UNAVAILABLE` |

### 1.4 超时配置

| 场景 | 超时时间 | 说明 |
|------|---------|------|
| 饮食解析 | 30s | 结构化输出，通常较快 |
| 对话回复 | 60s | 可能涉及记忆召回 + 知识检索 |
| 记忆提取 | 30s | 后台异步处理 |
| 建议生成 | 45s | 需要综合多种数据 |

## 2. Prompt 模板管理

### 2.1 组织方式

每个场景一个 Python 文件，包含 system prompt 和 few-shot examples。

```
app/integrations/llm/prompts/
├── diet_parse.py          # 饮食文本解析
├── memory_extract.py      # 记忆提取
├── plan_create.py         # 计划创建
├── suggestion.py          # 建议生成
├── intent.py              # 意图识别
└── consolidate.py         # 记忆合并
```

### 2.2 Prompt 模板结构

```python
# app/integrations/llm/prompts/diet_parse.py

SYSTEM_PROMPT = """你是一个饮食记录解析助手。
用户会用自然语言描述他们吃了什么，你需要将其解析为结构化的食物列表。

输出 JSON 格式：
{
    "foods": [
        {
            "name": "食物名称",
            "amount": 数量,
            "unit": "单位（克/毫升/个/碗/杯等）",
            "cooking_method": "烹饪方式（可选）"
        }
    ],
    "meal_type": "breakfast|lunch|dinner|snack（如果能推断）",
    "confidence": 0.0-1.0
}

规则：
1. 模糊描述要给出合理估算（"一碗饭" → 200g）
2. 多个食物要全部列出
3. 如果无法识别，confidence 设为 0
"""

FEW_SHOT_EXAMPLES = [
    {
        "user": "中午吃了一碗米饭，一份红烧肉，一个炒青菜",
        "assistant": '{"foods": [{"name": "米饭", "amount": 200, "unit": "克"}, {"name": "红烧肉", "amount": 150, "unit": "克", "cooking_method": "红烧"}, {"name": "青菜", "amount": 200, "unit": "克", "cooking_method": "炒"}], "meal_type": "lunch", "confidence": 0.9}'
    },
]

def build_messages(user_input: str) -> list[dict]:
    """构建完整的 messages 列表"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for example in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["assistant"]})
    messages.append({"role": "user", "content": user_input})
    return messages
```

## 3. Embedding 集成

### 3.1 客户端封装

```python
# app/integrations/embedding/client.py
class EmbeddingClient:
    """DashScope Embedding 客户端"""

    def __init__(self, api_key: str, base_url: str, model: str, dimensions: int):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model          # text-embedding-v3
        self.dimensions = dimensions  # 1024

    async def embed(self, text: str) -> list[float]:
        """生成单条文本的 embedding 向量"""
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成 embedding（最多 25 条/次）"""
        ...
```

### 3.2 使用场景

| 场景 | 输入 | 存储位置 |
|------|------|---------|
| 记忆存储 | 记忆条目内容 | `memories.embedding` |
| 记忆召回 | 用户消息 | 不存储，仅用于查询 |
| 知识库构建 | 食物名称+描述 / 健康建议内容 | `knowledge_docs.embedding` / `foods.embedding` |
| 知识库检索 | 用户查询 | 不存储，仅用于查询 |

## 4. pgvector 集成

### 4.1 客户端封装

```python
# app/integrations/vector/pgvector_client.py
class PgVectorClient:
    """pgvector 向量搜索封装"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def similarity_search(
        self,
        table_class,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict | None = None,
        score_threshold: float = 0.0,
    ) -> list[VectorSearchResult]:
        """
        余弦相似度搜索

        参数：
        - table_class: SQLAlchemy 模型类（必须有 embedding 列）
        - query_embedding: 查询向量
        - top_k: 返回前 k 条结果
        - filters: 额外过滤条件（如 user_id、category 等）
        - score_threshold: 最低相似度阈值
        """
        ...

class VectorSearchResult(BaseModel):
    id: UUID
    score: float       # 余弦相似度 0-1
    content: str       # 原始内容
    metadata: dict     # 附加元数据
```

### 4.2 索引配置

```sql
-- pgvector 索引（在 Alembic 迁移中创建）

-- 记忆表向量索引
CREATE INDEX idx_memories_embedding ON memories
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 食物知识库向量索引
CREATE INDEX idx_foods_embedding ON foods
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

-- 健康建议知识库向量索引
CREATE INDEX idx_knowledge_docs_embedding ON knowledge_docs
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);
```

### 4.3 向量维度

统一使用 text-embedding-v3 的 1024 维向量。所有 embedding 列定义为 `Vector(1024)`。

## 5. LangGraph 使用场景

### 5.1 使用原则

LangGraph 用于需要多步骤编排的 AI 流程，简单的单次 LLM 调用不使用 LangGraph。

### 5.2 场景列表

| 场景 | Graph 文件 | 节点 |
|------|-----------|------|
| AI 对话 | `chat_graph.py` | 意图识别 → 记忆召回 → 知识检索 → prompt 组装 → LLM 调用 → 记忆提取 → 响应 |
| 记忆提取 | `memory_graph.py` | 对话分析 → 关键信息提取 → 质量评分 → 分类存储 |
| 建议生成 | `suggestion_graph.py` | 数据收集 → 记忆召回 → 知识检索 → LLM 生成 → 去重过滤 |

### 5.3 Graph 定义模式

```python
# app/graphs/chat_graph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict

class ChatState(TypedDict):
    """对话处理状态"""
    user_message: str
    user_id: str
    session_id: str
    intent: str | None
    memories: list[dict]
    knowledge: list[dict]
    prompt_messages: list[dict]
    ai_response: str | None
    extracted_memories: list[dict]

def build_chat_graph() -> StateGraph:
    graph = StateGraph(ChatState)

    graph.add_node("identify_intent", identify_intent)
    graph.add_node("recall_memories", recall_memories)
    graph.add_node("search_knowledge", search_knowledge)
    graph.add_node("assemble_prompt", assemble_prompt)
    graph.add_node("call_llm", call_llm)
    graph.add_node("extract_memories", extract_memories)

    graph.set_entry_point("identify_intent")
    graph.add_edge("identify_intent", "recall_memories")
    graph.add_edge("recall_memories", "search_knowledge")
    graph.add_edge("search_knowledge", "assemble_prompt")
    graph.add_edge("assemble_prompt", "call_llm")
    graph.add_edge("call_llm", "extract_memories")
    graph.add_edge("extract_memories", END)

    return graph.compile()
```

## 6. 各模块对集成层的依赖

| 模块 | LLM Chat | Embedding | pgvector | LangGraph |
|------|----------|-----------|----------|-----------|
| 饮食记录 | 文本解析、图片识别 | — | — | — |
| AI 对话 | 对话回复 | 查询向量 | 记忆召回 | chat_graph |
| AI 记忆 | 记忆提取、合并 | 记忆向量 | 记忆存储/搜索 | memory_graph |
| RAG 知识库 | — | 查询向量 | 知识检索 | — |
| 计划系统 | 计划生成 | — | — | — |
| AI 建议 | 建议生成 | 查询向量 | 记忆召回 + 知识检索 | suggestion_graph |
