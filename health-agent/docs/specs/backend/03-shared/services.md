# 共享服务

> 本文档定义跨模块复用的共享服务，包括 LLM 服务封装、向量服务封装和通用工具。
>
> 实现依据：`00-architecture/integrations.md`，`00-architecture/overview.md`

---

## 1. LLM Service

### 1.1 职责

封装所有 LLM 调用，提供统一接口。业务模块不直接调用 `LLMClient`，而是通过 `LLMService` 调用。

### 1.2 接口定义

```python
# app/services/llm_service.py（概念上属于 integrations，但被 services 层广泛使用）

class LLMService:
    """LLM 调用统一服务"""

    def __init__(self, llm_client: LLMClient, embedding_client: EmbeddingClient):
        self.llm = llm_client
        self.embedding = embedding_client

    async def parse_diet_input(self, text: str) -> ParseResult:
        """解析饮食文本输入为结构化食物列表"""
        messages = diet_parse.build_messages(text)
        return await self.llm.chat_with_json(messages, ParseResult, temperature=0.3)

    async def identify_intent(self, message: str, context: list[dict]) -> Intent:
        """识别用户消息意图"""
        messages = intent.build_messages(message, context)
        return await self.llm.chat_with_json(messages, Intent, temperature=0.1)

    async def extract_memories(
        self, conversation: list[dict], existing_memories: list[str]
    ) -> list[ExtractedMemory]:
        """从对话中提取记忆"""
        messages = memory_extract.build_messages(conversation, existing_memories)
        return await self.llm.chat_with_json(messages, MemoryExtractionResult, temperature=0.3)

    async def generate_plan(
        self, profile: dict, goal: str, recent_data: dict
    ) -> GeneratedPlan:
        """根据用户目标生成健康计划"""
        messages = plan_create.build_messages(profile, goal, recent_data)
        return await self.llm.chat_with_json(messages, GeneratedPlan, temperature=0.5)

    async def generate_suggestion(
        self, context: SuggestionContext
    ) -> list[SuggestionItem]:
        """生成个性化建议"""
        messages = suggestion.build_messages(context)
        return await self.llm.chat_with_json(messages, SuggestionList, temperature=0.7)

    async def chat_reply(
        self, messages: list[dict]
    ) -> str:
        """通用对话回复"""
        response = await self.llm.chat(messages, temperature=0.7)
        return response.content

    async def consolidate_memories(
        self, memories: list[str]
    ) -> str:
        """合并多条记忆为摘要"""
        messages = consolidate.build_messages(memories)
        response = await self.llm.chat(messages, temperature=0.3)
        return response.content

    async def generate_embedding(self, text: str) -> list[float]:
        """生成文本 embedding"""
        return await self.embedding.embed(text)

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成 embedding"""
        return await self.embedding.embed_batch(texts)
```

### 1.3 Token 用量追踪

```python
class TokenTracker:
    """追踪 LLM Token 使用量（V1 仅记录日志，不做限制）"""

    async def record_usage(
        self,
        user_id: UUID,
        scene: str,          # diet_parse / chat / memory / suggestion / plan
        usage: TokenUsage,
    ) -> None:
        """记录一次 LLM 调用的 token 用量"""
        logger.info(
            "llm_usage",
            user_id=str(user_id),
            scene=scene,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )
```

V1 阶段仅通过日志记录 token 用量，不做配额限制。V2 可基于此数据实现付费系统。

## 2. Vector Service

### 2.1 职责

封装向量搜索操作，提供语义检索能力。

### 2.2 接口定义

```python
# 基于 integrations/vector/pgvector_client.py 的上层封装

class VectorService:
    """向量搜索服务"""

    def __init__(self, pgvector_client: PgVectorClient, embedding_client: EmbeddingClient):
        self.vector = pgvector_client
        self.embedding = embedding_client

    async def search_memories(
        self,
        user_id: UUID,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.3,
    ) -> list[VectorSearchResult]:
        """搜索用户记忆"""
        query_embedding = await self.embedding.embed(query)
        return await self.vector.similarity_search(
            table_class=Memory,
            query_embedding=query_embedding,
            top_k=top_k,
            filters={"user_id": user_id, "status": "active"},
            score_threshold=score_threshold,
        )

    async def search_foods(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[VectorSearchResult]:
        """搜索食物知识库"""
        query_embedding = await self.embedding.embed(query)
        return await self.vector.similarity_search(
            table_class=Food,
            query_embedding=query_embedding,
            top_k=top_k,
        )

    async def search_knowledge(
        self,
        query: str,
        category: str | None = None,
        top_k: int = 5,
    ) -> list[VectorSearchResult]:
        """搜索健康建议知识库"""
        query_embedding = await self.embedding.embed(query)
        filters = {}
        if category:
            filters["metadata__category"] = category
        return await self.vector.similarity_search(
            table_class=KnowledgeDoc,
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )
```

## 3. 统一异常体系

### 3.1 异常层级

```python
# app/core/exceptions.py

class AppException(Exception):
    """应用异常基类"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

class NotFoundException(AppException):
    """资源不存在"""
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status_code=404)

class ConflictException(AppException):
    """资源冲突"""
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status_code=409)

class ValidationException(AppException):
    """业务校验失败"""
    def __init__(self, code: str, message: str, details: list[dict] | None = None):
        super().__init__(code, message, status_code=422)
        self.details = details

class ExternalServiceException(AppException):
    """外部服务异常"""
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status_code=503)
```

### 3.2 全局异常处理

```python
# app/main.py 中注册

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": getattr(exc, "details", None),
            }
        },
    )
```

## 4. 分页工具

```python
# app/core/pagination.py
from pydantic import BaseModel, Field

class PaginationParams(BaseModel):
    """分页请求参数"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: str = "desc"  # asc / desc

class Pagination(BaseModel):
    """分页响应元数据"""
    total: int
    page: int
    page_size: int
    total_pages: int

def paginate(query, params: PaginationParams):
    """对 SQLAlchemy 查询应用分页"""
    offset = (params.page - 1) * params.page_size
    return query.offset(offset).limit(params.page_size)
```

## 5. 统一响应格式化

```python
# app/core/response.py
from app.schemas.common import ApiResponse, PaginatedResponse, Pagination

def success(data, message: str = "ok") -> dict:
    """包装成功响应"""
    return {"data": data, "message": message}

def paginated(data: list, total: int, page: int, page_size: int) -> dict:
    """包装分页响应"""
    total_pages = (total + page_size - 1) // page_size
    return {
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
        "message": "ok",
    }
```

## 6. 日期时间工具

```python
# app/core/datetime_utils.py
from datetime import datetime, date, timezone

def utc_now() -> datetime:
    """当前 UTC 时间"""
    return datetime.now(timezone.utc)

def today_utc() -> date:
    """当前 UTC 日期"""
    return datetime.now(timezone.utc).date()
```

所有时间存储和比较使用 UTC。客户端负责本地时区转换。
