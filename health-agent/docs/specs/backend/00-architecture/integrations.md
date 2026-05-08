# LLM、Embedding 与向量数据库集成

> 本文档定义 DashScope LLM / Embedding 和 pgvector 的技术细节：客户端/模型工厂、重试与超时、索引配置。**所有面向业务的 AI 编排（场景方法、流程）见 `agents.md`，本文档不再定义 `LLMService.parse_diet_input()` 这类场景封装**。
>
> 实现依据：`00-architecture/overview.md`、`00-architecture/agents.md`

---

## 1. LLM 集成（通过 LangChain + DashScope）

### 1.1 唯一入口：模型工厂

所有 LLM 推理一律通过 LangGraph Agent 发起。Agent 节点内通过 **全局模型工厂** 获取 `ChatOpenAI` 实例，禁止直接实例化。

```python
# app/agents/base.py
from langchain_openai import ChatOpenAI
from app.config import settings

def get_chat_model(temperature: float = 0.3, **kwargs) -> ChatOpenAI:
    """全局 LLM 模型工厂。DashScope 走 OpenAI 兼容接口。"""
    return ChatOpenAI(
        model=settings.llm_model,                # qwen-plus
        base_url=settings.dashscope_base_url,    # https://dashscope.aliyuncs.com/compatible-mode/v1
        api_key=settings.dashscope_api_key,
        temperature=temperature,
        timeout=kwargs.pop("timeout", 60),
        max_retries=kwargs.pop("max_retries", 3),
        **kwargs,
    )
```

### 1.2 禁止项

- 禁止新增 `app/integrations/llm/client.py`。
- 禁止在任何 Service 中 `from openai import OpenAI` 或 `from langchain_openai import ChatOpenAI`。
- 禁止在 `app/services/` 层再做一层"LLM 场景封装"（见历史 services.md v1 的 `LLMService.parse_diet_input()` 等，已废弃）。

### 1.3 重试与超时

由 LangChain `ChatOpenAI` 内置支持，无需自写重试层：

| 错误类型 | 策略 |
|---------|------|
| 网络超时 / 连接中断 | LangChain 自动按 `max_retries=3` 指数退避 |
| 429 Rate Limit | LangChain 自动识别，按 `Retry-After` 头等待 |
| 4xx（除 429）| 不重试，异常向上透出 |
| 5xx | 重试 2 次 |

默认超时：

| 场景 | 超时 | 说明 |
|------|------|------|
| 结构化解析 | 30s | temperature=0.3，通常较快 |
| 对话回复 | 60s | 含 RAG/记忆上下文 |
| 多步推理（Plan 创建等） | 90s | Agent 多节点串联 |

节点内可在 `get_chat_model(timeout=..., max_retries=...)` 按需覆盖。

### 1.4 结构化输出

用 LangChain 的 `with_structured_output` 替代旧 `chat_with_json`：

```python
from pydantic import BaseModel

class ParseResult(BaseModel):
    foods: list[...]
    meal_type: str | None
    confidence: float

async def parse_text_node(state: DietState) -> dict:
    llm = get_chat_model(temperature=0.3).with_structured_output(ParseResult)
    result: ParseResult = await llm.ainvoke(build_diet_parse_messages(state["input_text"]))
    return {"parsed": result.model_dump()}
```

---

## 2. Prompt 模板管理

### 2.1 目录

```
app/agents/prompts/
├── diet_parse.py
├── memory_extract.py
├── memory_score.py
├── plan_confirm.py
├── plan_analyze.py
├── plan_draft.py
├── suggestion_daily.py
├── suggestion_meal.py
├── suggestion_insight.py
├── chat_system.py
└── consolidate.py
```

### 2.2 模板结构

每个文件导出 `build_messages(**kwargs) -> list[dict]`，供节点调用。Few-shot 示例也在此。

---

## 3. Embedding 集成

### 3.1 客户端封装

Embedding 不是 LLM 推理，**继续保留独立 client**，被 Agent 节点或 RagService 直接调用。

```python
# app/integrations/embedding/client.py
from openai import AsyncOpenAI

class EmbeddingClient:
    """DashScope Embedding 客户端（text-embedding-v3, 1024 维）"""

    def __init__(self, api_key: str, base_url: str, model: str, dimensions: int = 1024):
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """最多 25 条/批"""
```

### 3.2 使用场景

| 场景 | 输入 | 存储位置 |
|------|------|---------|
| 记忆存储 | memory content | `memories.embedding` |
| 记忆召回 | 用户消息 | 不存储 |
| 食物知识库构建 | 食物名+别名+描述 | `foods.embedding` |
| 健康建议库构建 | title + content | `knowledge_docs.embedding` |
| 检索查询 | 查询文本 | 不存储 |

---

## 4. pgvector 集成

### 4.1 封装

```python
# app/integrations/vector/pgvector_client.py
class PgVectorClient:
    async def similarity_search(
        self,
        table_class,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict | None = None,
        score_threshold: float = 0.0,
    ) -> list[VectorSearchResult]: ...
```

被 `RagService`、`MemoryRepository` 调用，**不直接暴露给 Agent 节点**。Agent 通过 Tool 调用 Service/Repository 触发向量检索。

### 4.2 索引

```sql
-- Alembic 迁移中创建
CREATE EXTENSION IF NOT EXISTS vector;

CREATE INDEX idx_memories_embedding ON memories
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_foods_embedding ON foods
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE INDEX idx_knowledge_docs_embedding ON knowledge_docs
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

### 4.3 向量维度

统一 1024 维（text-embedding-v3 默认）。所有 `embedding` 列定义为 `Vector(1024)`。

---

## 5. Agent 层入口速查

本节是 **全部** AI 业务入口，任何新增 AI 场景必须创建或扩展对应 Agent，不得绕过：

| Agent | 文件 | 典型触发 |
|-------|------|---------|
| `chat_agent` | `app/agents/chat/graph.py` | `POST /api/v1/ai/chat` |
| `diet_agent` | `app/agents/diet/graph.py` | `POST /api/v1/diet/records`、`POST /api/v1/diet/parse` |
| `plan_agent` | `app/agents/plan/graph.py` | `POST /api/v1/plans`、计划修改建议 |
| `memory_agent` | `app/agents/memory/graph.py` | 饮食记录/反馈/计划执行后异步触发 |
| `suggestion_agent` | `app/agents/suggestion/graph.py` | `GET /api/v1/suggestions/*` |

Graph 内部结构见各 Agent 的模块 spec（`02-ai-modules/*.md`、`01-core-modules/diet-recording.md`）。

### 5.1 状态持久化

- **V1**：全部使用 `MemorySaver()`（in-memory checkpointer）。
- **V2+**：可切换 `PostgresSaver`（LangGraph 官方支持 Postgres），启用对话断点续跑。
- 切换只需改 `StateGraph.compile(checkpointer=...)`，Graph 结构不变。

---

## 6. 各模块对基础层的依赖

| 模块 | LLM（via Agent） | Embedding | pgvector | 对应 Agent |
|------|------------------|-----------|----------|------------|
| 饮食记录 | 文本/图片解析、澄清 | — | — | diet_agent |
| AI 对话 | 意图识别、回复 | 记忆召回查询 | 记忆检索 | chat_agent |
| AI 记忆 | 提取、评分、合并 | 记忆向量、查询 | 记忆存储/搜索 | memory_agent |
| RAG 知识库 | — | 查询向量 | 食物/知识检索 | 无（仅作为 Tool） |
| 计划系统 | 4 步创建、修改建议 | — | — | plan_agent |
| AI 建议 | 建议生成 | 召回查询 | 记忆 + 知识检索 | suggestion_agent |

---

## 7. 配置与依赖

### 7.1 依赖清单（pyproject.toml）

```
langchain-openai     # ChatOpenAI + DashScope 兼容
langgraph            # 流程编排
langchain-core       # BaseMessage、Tool 抽象
openai               # EmbeddingClient 直接用 AsyncOpenAI
pgvector             # SQLAlchemy Vector 列
```

### 7.2 环境变量

```
DASHSCOPE_API_KEY=
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v3
EMBEDDING_DIMENSIONS=1024
```

无需 `ANTHROPIC_API_KEY`、`OPENAI_API_KEY` 等；所有 LLM 调用走 DashScope 兼容端点。
