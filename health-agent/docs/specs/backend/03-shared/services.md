## 1. Tool 与 Service 的边界

> 本文档中的 service，默认指**纯业务 Service**，不承担 LLM 编排。所有 LLM 推理由 `app/agents/` 内的 LangGraph Agent 完成。

### 1.1 原则

- **Agent 负责 LLM 推理与多步编排**；Service 负责 DB CRUD、纯算法、外部 API 的确定性封装。
- Service 可以被 Agent 作为 Tool 调用。
- Service 不允许反向调用 Agent 来完成基础 CRUD。
- 任何需要自然语言理解/生成的任务，都必须在 Agent 内完成。

### 1.2 现有共享服务角色重定义

| 共享服务 | 角色 |
|---------|------|
| `RagService` | 知识库/营养检索工具，被 Agent 调用 |
| `EmbeddingClient` | 向量生成工具，被 RagService / MemoryService 调用 |
| `PgVectorClient` | 向量检索工具，被 RagService / MemoryService 调用 |
| `MemoryService` | 记忆存储/召回/衰减算法与 CRUD，被 chat_agent / memory_agent 调用 |
| `PlanService` | 计划 CRUD + BMR + 执行追踪，被 plan_agent / diet_agent 调用 |
| `DietService` | 饮食记录 CRUD + 营养计算，被 diet_agent 调用 |
| `SuggestionService` | 建议缓存 + 反馈，被 suggestion_agent 调用 |

### 1.3 废弃的共享 LLM Service

以下旧概念不再使用：

- `LLMClient`
- `LLMService`
- `parse_diet_input()` / `identify_intent()` / `generate_plan()` 这类场景方法

对应能力迁移到：

- `app/agents/diet/graph.py`
- `app/agents/chat/graph.py`
- `app/agents/plan/graph.py`
- `app/agents/memory/graph.py`
- `app/agents/suggestion/graph.py`

### 1.4 通用异常与响应仍然保留

- `app/core/exceptions.py`：统一异常
- `app/core/response.py`：统一成功/分页响应包装
- `app/core/pagination.py`：分页参数与工具
- `app/core/security.py`：JWT 验证

### 1.5 依赖方向

```
api/ ──→ agents/ ──→ services/ ──→ repositories/ ──→ db/models/
                 └──→ integrations/ (embedding / pgvector / supabase_auth)
```

`agents/` 是 LLM 唯一入口；`services/` 不直接依赖 LLM。
