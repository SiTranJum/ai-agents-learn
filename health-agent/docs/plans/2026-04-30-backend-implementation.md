# 健康管家后端 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于后端 specs 文档，从零搭建健康管家 FastAPI 后端项目，实现所有 API 端点和业务逻辑，V1 阶段使用 Supabase + pgvector。

**Architecture:** 分层架构 API → Service → Repository → DB/Integration，单体部署，模块自治。

**Tech Stack:** Python 3.11+ · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Supabase (PostgreSQL 15+ / Auth) · pgvector · DashScope (qwen-plus / text-embedding-v3) · LangGraph · Alembic · pytest · uvicorn

**Specs 目录:** `docs/specs/backend/` — 所有实现细节参考此目录下的 spec 文档。

---

## Phase 0: 项目初始化与基础设施

**目标：** 搭建 FastAPI 项目骨架，配置依赖、目录结构、数据库连接、基础中间件。

**参考 spec：** `00-architecture/overview.md`、`00-architecture/project-structure.md`

### Task 0.1: 初始化项目

**Files:**
- Create: `health-agent/backend/` (项目根目录)

- [ ] **Step 1: 创建项目目录和 pyproject.toml**

```bash
mkdir -p health-agent/backend
cd health-agent/backend
```

定义依赖：fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, pydantic, pydantic-settings, python-jose[cryptography], openai, langgraph, alembic, pytest, httpx

- [ ] **Step 2: 创建完整目录结构**

按 `project-structure.md` 创建所有目录和 `__init__.py`。

- [ ] **Step 3: 创建 FastAPI 入口 main.py**

配置 CORS、全局异常处理器、路由注册、lifespan 事件。

- [ ] **Step 4: 创建配置管理 config.py**

使用 pydantic-settings，从环境变量读取：DATABASE_URL、SUPABASE_URL、SUPABASE_JWT_SECRET、DASHSCOPE_API_KEY 等。

- [ ] **Step 5: 验证项目启动**

```bash
uvicorn app.main:app --reload
```

- [ ] **Step 6: Commit**

---

### Task 0.2: 数据库连接与基础模型

**参考 spec：** `03-shared/database-schema.md`

**Files:**
- Create: `app/db/session.py`
- Create: `app/db/base.py`
- Create: `app/db/models/base.py`

- [ ] **Step 1: 配置 SQLAlchemy async engine + session**
- [ ] **Step 2: 创建 Base 模型**（id UUID、created_at、updated_at 通用字段）
- [ ] **Step 3: 创建 TimestampMixin 和 SoftDeleteMixin**
- [ ] **Step 4: 配置 Alembic 数据库迁移**
- [ ] **Step 5: Commit**

---

### Task 0.3: 核心工具层

**参考 spec：** `03-shared/services.md`、`00-architecture/api-design.md`

**Files:**
- Create: `app/core/exceptions.py`
- Create: `app/core/responses.py`
- Create: `app/core/pagination.py`
- Create: `app/core/security.py`
- Create: `app/core/deps.py`

- [ ] **Step 1: 实现异常体系**（AppException → NotFoundException / ValidationException / ExternalServiceException）
- [ ] **Step 2: 实现全局异常处理器**（注册到 FastAPI，返回统一错误 JSON）
- [ ] **Step 3: 实现统一响应格式**（success() / paginated() 工具函数）
- [ ] **Step 4: 实现分页工具**（offset-based，page / page_size / sort_by / sort_order）
- [ ] **Step 5: Commit**

---

## Phase 1: 认证与用户系统

**目标：** 实现 Supabase Auth 集成、JWT 验证、用户档案 CRUD。

**参考 spec：** `00-architecture/auth.md`、`01-core-modules/user-system.md`

### Task 1.1: JWT 认证

**Files:**
- Create: `app/core/security.py`
- Create: `app/dependencies.py`
- Create: `app/schemas/auth.py`

- [x] **Step 1: 实现 JWT 验证函数**（解析 Bearer token、HS256 验证、提取 user_id）
- [x] **Step 2: 定义 CurrentUser schema**
- [x] **Step 3: 实现 `get_current_user` 依赖**（FastAPI Depends，验证 JWT）
- [x] **Step 4: 编写测试**
- [x] **Step 5: Commit**

---

### Task 1.2: 用户档案与自动创建

**Files:**
- Create: `app/db/models/user.py`
- Create: `app/db/repositories/user_repo.py`
- Create: `app/schemas/user.py`
- Create: `app/services/user_service.py`
- Create: `app/api/v1/users.py`
- Update: `app/dependencies.py`

- [x] **Step 1: 创建 HealthProfile 数据库模型**
- [x] **Step 2: 创建 User schemas**（HealthProfileCreate / Update / Response）
- [x] **Step 3: 实现 UserRepository**（自动 user_id 过滤 + create_empty_profile）
- [x] **Step 4: 实现 UserService**（get_profile / update_profile / onboarding / profile_completeness）
- [x] **Step 5: 更新 dependencies.py**（添加 get_current_user_with_profile，首次访问自动创建档案）
- [x] **Step 6: 实现 API 端点**（GET /users/me、PUT /users/me/profile、POST /users/me/onboarding）
- [x] **Step 7: 生成数据库迁移并测试**
- [x] **Step 8: Commit**

---

## Phase 2: LLM 与向量集成

**目标：** 封装 DashScope LLM 调用和 pgvector 向量搜索，为后续 AI 模块提供基础能力。

**参考 spec：** `00-architecture/integrations.md`、`03-shared/services.md`

### Task 2.1: LLM 服务封装

**Files:**
- Create: `app/integrations/llm/client.py`
- Create: `app/integrations/llm/prompts/` (目录)
- Create: `app/integrations/llm/service.py`

- [ ] **Step 1: 实现 LLMClient**（AsyncOpenAI 封装，DashScope base_url，重试策略）
- [ ] **Step 2: 实现 chat() 和 chat_with_json()**（结构化输出）
- [ ] **Step 3: 创建 prompt 模板目录结构**
- [ ] **Step 4: 编写集成测试**（调用真实 API 验证连通性）
- [ ] **Step 5: Commit**

---

### Task 2.2: Embedding 与向量搜索

**Files:**
- Create: `app/integrations/embedding/client.py`
- Create: `app/integrations/vector/service.py`

- [ ] **Step 1: 实现 EmbeddingClient**（text-embedding-v3，1024 维，批量支持）
- [ ] **Step 2: 实现 VectorService**（pgvector 相似度搜索，支持过滤条件）
- [ ] **Step 3: 创建 pgvector 扩展迁移**（`CREATE EXTENSION vector`）
- [ ] **Step 4: 编写测试**
- [ ] **Step 5: Commit**

---

## Phase 3: RAG 知识库

**目标：** 建立食物营养库和健康建议库，实现向量检索能力。

**参考 spec：** `02-ai-modules/rag-knowledge.md`

### Task 3.1: 知识库数据模型

**Files:**
- Create: `app/db/models/knowledge.py`
- Create: `app/db/repositories/knowledge_repo.py`
- Create: `app/schemas/knowledge.py`

- [ ] **Step 1: 创建 Food 和 KnowledgeDoc 数据库模型**（含 vector 列）
- [ ] **Step 2: 创建对应 schemas**
- [ ] **Step 3: 实现 KnowledgeRepository**（向量搜索 + 关键词搜索）
- [ ] **Step 4: 生成迁移，创建 IVFFlat 索引**
- [ ] **Step 5: Commit**

---

### Task 3.2: 种子数据与 RAG 服务

**Files:**
- Create: `app/services/rag_service.py`
- Create: `app/api/v1/knowledge.py`
- Create: `scripts/seed_knowledge.py`
- Create: `data/foods.json`
- Create: `data/health_tips.json`

- [ ] **Step 1: 准备种子数据**（常见食物 100+ 条、健康建议 50+ 条，V1 精简版）
- [ ] **Step 2: 实现种子数据导入脚本**（批量 embedding 生成 + 入库）
- [ ] **Step 3: 实现 RagService**（食物搜索、知识检索、三层匹配策略）
- [ ] **Step 4: 实现 API 端点**（GET /knowledge/foods/search、GET /knowledge/foods/{id}）
- [ ] **Step 5: 运行种子脚本，验证搜索效果**
- [ ] **Step 6: Commit**

---

## Phase 4: 饮食记录模块

**目标：** 实现饮食记录 CRUD、AI 文本解析、营养计算。

**参考 spec：** `01-core-modules/diet-recording.md`

### Task 4.1: 饮食数据层

**Files:**
- Create: `app/db/models/diet.py`
- Create: `app/db/repositories/diet_repo.py`
- Create: `app/schemas/diet.py`

- [ ] **Step 1: 创建 DietRecord 和 DietItem 数据库模型**
- [ ] **Step 2: 创建饮食相关 schemas**（Create / Update / Response / ParseResult / Summary）
- [ ] **Step 3: 实现 DietRepository**（CRUD + 按日期范围查询 + 汇总统计）
- [ ] **Step 4: 生成迁移并测试**
- [ ] **Step 5: Commit**

---

### Task 4.2: AI 解析与营养计算

**Files:**
- Create: `app/integrations/llm/prompts/diet_parse.py`
- Create: `app/services/diet_service.py`

- [ ] **Step 1: 编写饮食解析 prompt 模板**（文本 → 结构化食物列表）
- [ ] **Step 2: 实现 AI 解析流程**（LLM 解析 → RAG 匹配营养数据 → 计算汇总）
- [ ] **Step 3: 实现 DietService**（create / update / delete / parse / daily_summary / weekly_summary）
- [ ] **Step 4: 编写测试**（mock LLM 响应，验证解析和计算逻辑）
- [ ] **Step 5: Commit**

---

### Task 4.3: 饮食 API 端点

**Files:**
- Create: `app/api/v1/diet.py`

- [ ] **Step 1: 实现 8 个端点**（CRUD + parse + daily/weekly summary）
- [ ] **Step 2: 端到端测试**（创建记录 → 查询 → 汇总）
- [ ] **Step 3: Commit**

---

## Phase 5: 身体数据追踪模块

**目标：** 实现 6 类身体数据的 CRUD、趋势计算、异常检测。

**参考 spec：** `01-core-modules/body-tracking.md`

### Task 5.1: 身体数据层与服务

**Files:**
- Create: `app/db/models/body.py`
- Create: `app/db/repositories/body_repo.py`
- Create: `app/schemas/body.py`
- Create: `app/services/body_service.py`
- Create: `app/api/v1/body.py`

- [ ] **Step 1: 创建数据库模型**（WeightRecord、体围、睡眠、运动、饮水、排便）
- [ ] **Step 2: 创建 schemas**（各类型的 Create / Response + TrendData）
- [ ] **Step 3: 实现 BodyRepository**（CRUD + 趋势查询 + 最新值）
- [ ] **Step 4: 实现 BodyService**（数据校验、异常值检测、趋势计算）
- [ ] **Step 5: 实现 API 端点**（各类型 CRUD + trends + latest）
- [ ] **Step 6: 编写测试**
- [ ] **Step 7: Commit**

---

## Phase 6: AI 记忆系统

**目标：** 实现三层记忆架构（短期/中期/长期），记忆的写入、召回、衰减。

**参考 spec：** `02-ai-modules/ai-memory.md`

### Task 6.1: 记忆数据层

**Files:**
- Create: `app/db/models/memory.py`
- Create: `app/db/repositories/memory_repo.py`
- Create: `app/schemas/memory.py`

- [ ] **Step 1: 创建 Memory 和 MemorySummary 数据库模型**（含 vector 列）
- [ ] **Step 2: 创建记忆 schemas**
- [ ] **Step 3: 实现 MemoryRepository**（CRUD + 向量召回 + 按类型/时间过滤）
- [ ] **Step 4: 生成迁移**
- [ ] **Step 5: Commit**

---

### Task 6.2: 记忆服务与 LangGraph 流程

**Files:**
- Create: `app/integrations/llm/prompts/memory_extract.py`
- Create: `app/services/memory_service.py`
- Create: `app/graphs/memory_graph.py`

- [ ] **Step 1: 编写记忆提取 prompt**（从对话中提取关键信息 + 重要度评分）
- [ ] **Step 2: 实现 MemoryService**（write / recall / consolidate / decay）
- [ ] **Step 3: 实现 memory_graph**（LangGraph：提取 → 分类 → embedding → 存储）
- [ ] **Step 4: 编写测试**
- [ ] **Step 5: Commit**

---

## Phase 7: AI 对话系统

**目标：** 实现对话入口，串联记忆召回、prompt 组装、LLM 调用、记忆写入的完整链路。

**参考 spec：** `02-ai-modules/ai-memory.md`（对话部分）

### Task 7.1: 对话数据层与服务

**Files:**
- Create: `app/db/models/chat.py`
- Create: `app/db/repositories/chat_repo.py`
- Create: `app/schemas/chat.py`
- Create: `app/services/chat_service.py`
- Create: `app/graphs/chat_graph.py`
- Create: `app/api/v1/ai.py`

- [ ] **Step 1: 创建 ChatMessage 数据库模型**
- [ ] **Step 2: 创建对话 schemas**（ChatRequest / ChatResponse / ChatHistory）
- [ ] **Step 3: 实现 chat_graph**（LangGraph：消息接收 → 记忆召回 → prompt 组装 → LLM → 记忆提取 → 响应）
- [ ] **Step 4: 实现 ChatService**（chat / get_history）
- [ ] **Step 5: 实现 API 端点**（POST /ai/chat、GET /ai/chat/history）
- [ ] **Step 6: 端到端测试**（发送消息 → 获取回复 → 验证记忆写入）
- [ ] **Step 7: Commit**

---

## Phase 8: 计划系统

**目标：** 实现计划的 AI 创建、CRUD、打卡、进度追踪。

**参考 spec：** `02-ai-modules/plan-system.md`

### Task 8.1: 计划数据层

**Files:**
- Create: `app/db/models/plan.py`
- Create: `app/db/repositories/plan_repo.py`
- Create: `app/schemas/plan.py`

- [ ] **Step 1: 创建 Plan、PlanTarget、PlanExecution 数据库模型**
- [ ] **Step 2: 创建计划 schemas**（Create / Update / Response / CheckIn / Progress）
- [ ] **Step 3: 实现 PlanRepository**
- [ ] **Step 4: 生成迁移**
- [ ] **Step 5: Commit**

---

### Task 8.2: 计划服务与 API

**Files:**
- Create: `app/integrations/llm/prompts/plan_generate.py`
- Create: `app/services/plan_service.py`
- Create: `app/api/v1/plans.py`

- [ ] **Step 1: 编写计划生成 prompt**（结合用户档案 + 记忆生成个性化计划）
- [ ] **Step 2: 实现 PlanService**（AI 创建 / CRUD / check-in / progress / 自动修正触发）
- [ ] **Step 3: 实现 API 端点**（8 个端点）
- [ ] **Step 4: 编写测试**
- [ ] **Step 5: Commit**

---

## Phase 9: AI 建议系统

**目标：** 实现每日建议、餐食建议、健康洞察的生成与缓存。

**参考 spec：** `02-ai-modules/ai-suggestion.md`

### Task 9.1: 建议数据层与服务

**Files:**
- Create: `app/db/models/suggestion.py`
- Create: `app/db/repositories/suggestion_repo.py`
- Create: `app/schemas/suggestion.py`
- Create: `app/integrations/llm/prompts/suggestion_generate.py`
- Create: `app/services/suggestion_service.py`
- Create: `app/graphs/suggestion_graph.py`
- Create: `app/api/v1/suggestions.py`

- [ ] **Step 1: 创建 Suggestion 数据库模型**
- [ ] **Step 2: 创建建议 schemas**
- [ ] **Step 3: 编写建议生成 prompt**（每日/餐食/洞察三种模板）
- [ ] **Step 4: 实现 suggestion_graph**（LangGraph：数据收集 → 分析 → 生成 → 质量检查）
- [ ] **Step 5: 实现 SuggestionService**（daily / meal / insights + 缓存策略）
- [ ] **Step 6: 实现 API 端点**（3 个端点）
- [ ] **Step 7: 编写测试**
- [ ] **Step 8: Commit**

---

## Phase 10: 全局联调与收尾

**目标：** 串联所有模块，验证完整业务流程，补充测试。

### Task 10.1: 跨模块集成

- [ ] **Step 1: 饮食记录触发记忆更新**（diet_service → memory_service）
- [ ] **Step 2: 身体数据变化触发记忆更新**（body_service → memory_service）
- [ ] **Step 3: 档案更新触发记忆更新**（user_service → memory_service）
- [ ] **Step 4: 饮食记录触发计划执行追踪**（diet_service → plan_service）
- [ ] **Step 5: Commit**

---

### Task 10.2: 完整流程验证

- [ ] **Step 1: 验证 Auth 流程**（注册 → 登录 → 获取 token → 访问受保护端点）
- [ ] **Step 2: 验证用户档案流程**（创建 → 更新 → onboarding）
- [ ] **Step 3: 验证饮食流程**（AI 解析 → 创建记录 → 查询 → 汇总）
- [ ] **Step 4: 验证身体数据流程**（记录 → 趋势 → 异常检测）
- [ ] **Step 5: 验证 AI 对话流程**（发消息 → 记忆召回 → 回复 → 记忆写入）
- [ ] **Step 6: 验证计划流程**（AI 创建 → 打卡 → 进度）
- [ ] **Step 7: 验证建议流程**（每日建议 → 餐食建议 → 洞察）
- [ ] **Step 8: 修复发现的问题**
- [ ] **Step 9: Final Commit**

---

## 进度追踪

| Phase | 名称 | Task 数 | 状态 |
|-------|------|---------|------|
| 0 | 项目初始化与基础设施 | 3 | ⬜ 未开始 |
| 1 | 认证与用户系统 | 2 | ✅ 已完成 |
| 2 | LLM 与向量集成 | 2 | ⬜ 未开始 |
| 3 | RAG 知识库 | 2 | ⬜ 未开始 |
| 4 | 饮食记录模块 | 3 | ⬜ 未开始 |
| 5 | 身体数据追踪模块 | 1 | ⬜ 未开始 |
| 6 | AI 记忆系统 | 2 | ⬜ 未开始 |
| 7 | AI 对话系统 | 1 | ⬜ 未开始 |
| 8 | 计划系统 | 2 | ⬜ 未开始 |
| 9 | AI 建议系统 | 1 | ⬜ 未开始 |
| 10 | 全局联调与收尾 | 2 | ⬜ 未开始 |
| **总计** | | **21 Tasks** | |
