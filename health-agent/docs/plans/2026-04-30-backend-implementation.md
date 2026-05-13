# 健康管家后端 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于后端 specs 文档，从零搭建健康管家 FastAPI 后端项目，实现所有 API 端点和业务逻辑，V1 阶段使用 Supabase + pgvector。

**Architecture:** 分层架构 API → Service → Repository → DB/Integration，单体部署，模块自治。

**Tech Stack:** Python 3.11+ · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Supabase (PostgreSQL 15+ / Auth) · pgvector · DashScope (qwen-plus / text-embedding-v3) · **LangGraph + langchain-openai（所有 LLM 推理的唯一入口）** · Alembic · pytest · uvicorn

**Specs 目录:** `docs/specs/backend/` — 所有实现细节参考此目录下的 spec 文档。

**关键架构 Spec（执行前必读）：**

- `00-architecture/overview.md` — 分层与调用路径（AI 路径 vs 纯 CRUD 路径）
- `00-architecture/agents.md` — **Agent 层总纲：所有 LLM 推理的唯一入口**。涉及 LLM 的 Task 必读
- `00-architecture/integrations.md` — Embedding / pgvector 技术细节
- `00-architecture/project-structure.md` — 目录结构约定
- `03-shared/services.md` — Agent/Service 职责边界

---

## Phase 0: 项目初始化与基础设施

**目标：** 搭建 FastAPI 项目骨架，配置依赖、目录结构、数据库连接、基础中间件。

**参考 spec：** `00-architecture/overview.md`、`00-architecture/project-structure.md`、`00-architecture/agents.md`（Agent 目录约定）

### Task 0.1: 初始化项目

**Files:**
- Create: `health-agent/backend/` (项目根目录)

- [x] **Step 1: 创建项目目录和 pyproject.toml**

```bash
mkdir -p health-agent/backend
cd health-agent/backend
```

定义依赖：fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, pydantic, pydantic-settings, python-jose[cryptography], openai, langgraph, alembic, pytest, httpx

- [x] **Step 2: 创建完整目录结构**

按 `project-structure.md` 创建所有目录和 `__init__.py`。

- [x] **Step 3: 创建 FastAPI 入口 main.py**

配置 CORS、全局异常处理器、路由注册、lifespan 事件。

- [x] **Step 4: 创建配置管理 config.py**

使用 pydantic-settings，从环境变量读取：DATABASE_URL、SUPABASE_URL、SUPABASE_JWT_SECRET、DASHSCOPE_API_KEY 等。

- [x] **Step 5: 验证项目启动**

```bash
uvicorn app.main:app --reload
```

- [x] **Step 6: Commit**

---

### Task 0.2: 数据库连接与基础模型

**参考 spec：** `03-shared/database-schema.md`

**Files:**
- Create: `app/db/session.py`
- Create: `app/db/base.py`
- Create: `app/db/models/base.py`

- [x] **Step 1: 配置 SQLAlchemy async engine + session**
- [x] **Step 2: 创建 Base 模型**（id UUID、created_at、updated_at 通用字段）
- [x] **Step 3: 创建 TimestampMixin 和 SoftDeleteMixin**
- [x] **Step 4: 配置 Alembic 数据库迁移**
- [x] **Step 5: Commit**

---

### Task 0.3: 核心工具层

**参考 spec：** `03-shared/services.md`、`00-architecture/api-design.md`

**Files:**
- Create: `app/core/exceptions.py`
- Create: `app/core/responses.py`
- Create: `app/core/pagination.py`
- Create: `app/core/security.py`
- Create: `app/core/deps.py`

- [x] **Step 1: 实现异常体系**（AppException → NotFoundException / ValidationException / ExternalServiceException）
- [x] **Step 2: 实现全局异常处理器**（注册到 FastAPI，返回统一错误 JSON）
- [x] **Step 3: 实现统一响应格式**（success() / paginated() 工具函数）
- [x] **Step 4: 实现分页工具**（offset-based，page / page_size / sort_by / sort_order）
- [x] **Step 5: Commit**

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

## Phase 2: Agent 基础设施与向量能力

**目标：** 搭建 LangGraph Agent 统一入口（`app/agents/`）、Embedding 与 pgvector 向量搜索。所有 LLM 调用一律通过 Agent 发起，不再有独立的 `LLMClient` / `LLMService` 封装。

**参考 spec：** `00-architecture/agents.md`、`00-architecture/integrations.md`、`03-shared/services.md`

### Task 2.1: Agent 层骨架（替代旧的 LLM Service）

**Files:**
- Create: `app/agents/__init__.py`
- Create: `app/agents/base.py` (get_chat_model 模型工厂 + BaseAgentState)
- Create: `app/agents/prompts/__init__.py`
- Delete: `app/integrations/llm/` 整个目录（如已存在 client.py 则删除）
- Delete: `app/services/llm_service.py`（如已存在）

- [x] **Step 1: 新增依赖** — pyproject.toml 加 `langgraph`, `langchain-openai`, `langchain-core`
- [x] **Step 2: 实现 `app/agents/base.py`** — `get_chat_model(temperature, **kwargs)` 读取配置并返回 `ChatOpenAI`（DashScope 兼容）；定义 `BaseAgentState`
- [x] **Step 3: 清理废弃模块** — 删除 `app/integrations/llm/client.py`、`app/services/llm_service.py`（若存在）
- [x] **Step 4: 编写连通性测试** — 构造一个一节点 Graph，输入 "你好" → 返回字符串，验证模型工厂可用（默认跳过，设置 `RUN_LLM_INTEGRATION=1` 时运行）
- [x] **Step 5: Commit**

---

### Task 2.2: Embedding 与向量搜索

**Files:**
- Create: `app/integrations/embedding/client.py`
- Create: `app/integrations/vector/pgvector_client.py`

- [x] **Step 1: 实现 EmbeddingClient**（text-embedding-v3，1024 维，批量支持）
- [x] **Step 2: 实现 PgVectorClient**（pgvector 相似度搜索，支持过滤条件）
- [x] **Step 3: 创建 pgvector 扩展迁移**（`CREATE EXTENSION IF NOT EXISTS vector`）
- [x] **Step 4: 编写测试**
- [x] **Step 5: Commit**

> 备注：标记 [x] 的项若已在旧版 Phase 2 中完成，需按新 spec 做"反向 review"：确保 Service 不再 `from openai import OpenAI`，若存在则在 Phase 2 结束前清理。

---

## Phase 3: RAG 知识库

**目标：** 建立食物营养库和健康建议库，实现向量检索能力。`RagService` 作为 Agent 的工具被调用。

**参考 spec：** `02-ai-modules/rag-knowledge.md`、`00-architecture/agents.md`（Service 作为 Agent Tool 的约定）

### Task 3.1: 知识库数据模型

**Files:**
- Create: `app/db/models/knowledge.py`
- Create: `app/db/repositories/knowledge_repo.py`
- Create: `app/schemas/knowledge.py`

- [x] **Step 1: 创建 Food 和 KnowledgeDoc 数据库模型**（含 vector 列）
- [x] **Step 2: 创建对应 schemas**
- [x] **Step 3: 实现 KnowledgeRepository**（向量搜索 + 关键词搜索）
- [x] **Step 4: 生成迁移，创建 IVFFlat 索引**
- [x] **Step 5: Commit**

---

### Task 3.2: 种子数据与 RAG 服务

**Files:**
- Create: `app/services/rag_service.py`
- Create: `app/api/v1/knowledge.py`
- Create: `scripts/seed_knowledge.py`
- Create: `data/foods.json`
- Create: `data/health_tips.json`

- [x] **Step 1: 准备种子数据**（常见食物 100+、健康建议 50+，V1 精简版）
- [x] **Step 2: 实现种子数据导入脚本**（批量 embedding 生成 + 入库）
- [x] **Step 3: 实现 RagService**（`search_foods` / `get_food_detail` / `search_knowledge` / `lookup_nutrition`）
- [x] **Step 4: 实现 API 端点**（`GET /knowledge/foods/search`、`GET /knowledge/foods/{id}`）
- [x] **Step 5: 运行种子脚本，验证搜索效果**
- [x] **Step 6: Commit**

---

## Phase 4: 饮食记录模块（纯 CRUD + diet subgraph 预埋）

**目标：** 实现饮食记录 CRUD 与营养计算；**所有 LLM 入口统一走 `/ai/chat`**，本阶段在 `app/agents/diet/` 下提前搭好 diet subgraph（不对外暴露 API），供 Phase 6 的 `chat_graph` 挂载。

**架构变更（2026-05-09）**：
- 原计划的"`POST /diet/records` 走 `diet_agent`"方案已被推翻。饮食端点全部回归**纯 CRUD**（`API → DietService → Repository`）。
- `POST /diet/parse` 端点**已下线**；自然语言解析由 Phase 6 的 `/ai/chat` + diet subgraph 承担。
- `app/agents/diet/` 里的 state 绑定到全局 `ChatState`（见 `app/agents/chat/state.py`），节点/工具不再设独立 DietState。

**参考 spec：** `01-core-modules/diet-recording.md`、`00-architecture/agents.md`、`shared/api-contract.md` §5 §8

### Task 4.1: 饮食数据层

**Files:**
- Create: `app/db/models/diet.py`
- Create: `app/db/repositories/diet_repo.py`
- Create: `app/schemas/diet.py`

- [x] **Step 1: 创建 DietRecord 和 DietItem 数据库模型**
- [x] **Step 2: 创建饮食相关 schemas**（Create / Update / Response / ParseResult / Summary / ParsedFood）
- [x] **Step 3: 实现 DietRepository**（CRUD + 按日期范围查询 + 汇总统计）
- [x] **Step 4: 生成迁移并测试**
- [ ] **Step 5: Commit**

---

### Task 4.2: DietService（纯 CRUD + 营养算法）

**Files:**
- Create: `app/services/diet_service.py`

- [x] **Step 1: 实现 `create_record`**（API 直接调，结构化入口）
- [x] **Step 2: 实现 `create_record_from_parsed`**（diet subgraph 内部调，接收 ParsedFood 列表）
- [x] **Step 3: 实现 CRUD**（`get_record` / `list_records` / `update_record` / `delete_record`，软删除）
- [x] **Step 4: 实现营养汇总**（`get_daily_summary` / `get_weekly_summary`）
- [x] **Step 5: 内部辅助**（`food_input_to_parsed` 通过 RagService 查询营养；`_calculate_summary`）
- [x] **Step 6: 单元测试**（纯算法逻辑可 mock 依赖）
- [ ] **Step 7: Commit**

> 约束：本文件禁止 import `ChatOpenAI` 或 `openai`。任何 LLM 调用属于 chat_agent（Phase 6）。

---

### Task 4.3: diet subgraph（为 Phase 6 预埋）

**Files:**
- Create: `app/agents/chat/state.py`（全局 `ChatState`，含 `diet_*` 前缀字段）
- Create: `app/agents/diet/nodes.py`
- Create: `app/agents/diet/tools.py`
- Create: `app/agents/diet/subgraph.py`
- Create: `app/agents/prompts/diet_parse.py`

- [x] **Step 1: 定义 `ChatState`**（合并原 DietState，字段全部 Optional；后续新增领域再加前缀字段）
- [x] **Step 2: 实现 prompt 模板** — `agents/prompts/diet_parse.py` 含模糊单位换算表、few-shot
- [x] **Step 3: 实现节点**（节点签名全部 `state: ChatState -> dict`）
  - `route_input`（conditional edge：text / photo / 已结构化）
  - `parse_text`（`ChatOpenAI.with_structured_output(ParseResult)`）
  - `parse_photo_mock`（V1 返回固定 ParseResult）
  - `standardize_units`（代码确定性换算）
  - `enrich_nutrition`（Tool: `enrich_food_tool`，未命中调 LLM 估算）
  - `infer_meal_type`（按时间或已传值）
  - `save_record`（Tool: `save_diet_record_tool`，conditional：mode == "create" 时执行）
  - `trigger_memory`（Phase 6 接 memory subgraph 时再实现）
- [x] **Step 4: 组装 Subgraph** — `build_diet_subgraph()` 返回 compiled graph（in-memory checkpointer）
- [x] **Step 5: 单元测试** — mock ChatOpenAI 与 DietService，验证节点串联
- [ ] **Step 6: Commit**

> 说明：diet subgraph 在本阶段**不**通过任何 API 端点暴露；Phase 6 构建全局 `chat_graph` 时用
> `chat_graph.add_node("diet", build_diet_subgraph())` 挂载。

---

### Task 4.4: 饮食 API 端点（纯 CRUD）

**Files:**
- Create: `app/api/v1/diet.py`
- Update: `app/dependencies.py`（仅 `DietServiceDep`，**不**注入 Agent）

- [x] **Step 1: 实现端点**（全部 `API → DietService`）
  - `POST /diet/records`（结构化输入：meal_type + date + foods[]）
  - `GET /diet/records` / `GET /diet/records/{id}` / `PUT /diet/records/{id}` / `DELETE /diet/records/{id}`
  - `GET /diet/daily-summary` / `GET /diet/weekly-summary`
- [x] **Step 2: 端到端测试**（纯 CRUD，无需 mock LLM；`/diet/parse` 已下线，测试断言 404）
- [ ] **Step 3: Commit**

---

## Phase 5: 身体数据追踪模块

**目标：** 实现 6 类身体数据的 CRUD、趋势计算、异常检测。该模块不涉及 LLM。

**参考 spec：** `01-core-modules/body-tracking.md`

### Task 5.1: 身体数据层与服务

**Files:**
- Create: `app/db/models/body.py`
- Create: `app/db/repositories/body_repo.py`
- Create: `app/schemas/body.py`
- Create: `app/services/body_service.py`
- Create: `app/api/v1/body.py`

- [x] **Step 1: 创建数据库模型**（WeightRecord、体围、睡眠、运动、饮水、排便）
- [x] **Step 2: 创建 schemas**
- [x] **Step 3: 实现 BodyRepository**（CRUD + 趋势查询 + 最新值）
- [x] **Step 4: 实现 BodyService**（数据校验、异常值检测、趋势计算）
- [x] **Step 5: 实现 API 端点**（各类型 CRUD + trends + latest）
- [x] **Step 6: 编写测试**
- [ ] **Step 7: Commit**

---

## Phase 6: AI 记忆系统（memory_agent）

**目标：** 实现三层记忆架构（短期/中期/长期），通过 `memory_agent` 完成提取/评分/存储；`MemoryService` 只做 CRUD + 召回算法。

**参考 spec：** `02-ai-modules/ai-memory.md`、`00-architecture/agents.md`

### Task 6.1: 记忆数据层与 MemoryService

**Files:**
- Create: `app/db/models/memory.py`
- Create: `app/db/repositories/memory_repo.py`
- Create: `app/schemas/memory.py`
- Create: `app/services/memory_service.py`

- [x] **Step 1: 创建 Memory 和 MemorySummary 数据库模型**（含 vector 列）
- [x] **Step 2: 创建记忆 schemas**
- [x] **Step 3: 实现 MemoryRepository**
- [x] **Step 4: 实现 MemoryService**（`store_memory` / `recall_memories` / `get_long_term_profile` / `on_profile_updated`；**不含 LLM 调用**）
- [x] **Step 5: 生成迁移**
- [x] **Step 6: 单元测试**（时间衰减、类型权重、多因子评分）
- [ ] **Step 7: Commit**

---

### Task 6.2: memory_agent

**Files:**
- Create: `app/agents/memory/state.py`
- Create: `app/agents/memory/nodes.py`
- Create: `app/agents/memory/tools.py`
- Create: `app/agents/memory/graph.py`
- Create: `app/agents/prompts/memory_extract.py`
- Create: `app/agents/prompts/memory_score.py`
- Create: `app/agents/prompts/consolidate.py`

- [x] **Step 1: 定义 MemoryExtractionState** — trigger_type / context_data / extracted / scored / approved
- [x] **Step 2: 实现 prompt 模板**（extract / score / consolidate）
- [x] **Step 3: 实现节点**（`extract` / `score` / `filter` / `embed_and_store`）— 最后一步通过 Tool 调 `MemoryService.store_memory`，节点内用 `EmbeddingClient.embed` 生成向量
- [x] **Step 4: 组装 Graph** — `build_memory_agent()`
- [x] **Step 5: 子图：consolidate_subgraph**（相似度检测 → LLM 摘要 → 归档原始）
- [x] **Step 6: 单元测试** — mock LLM 与 Embedding
- [ ] **Step 7: Commit**

---

## Phase 7: AI 对话系统（chat_agent）

**目标：** 实现 `POST /ai/chat` 的端到端流程，通过 `chat_agent` 串联意图识别、记忆召回、知识检索、LLM 回复、记忆提取。

**参考 spec：** `02-ai-modules/ai-memory.md`、`00-architecture/agents.md`

### Task 7.1: 对话数据层与 ChatService

**Files:**
- Create: `app/db/models/chat.py`
- Create: `app/db/repositories/chat_repo.py`
- Create: `app/schemas/chat.py`
- Create: `app/services/chat_service.py`

- [x] **Step 1: 创建 ChatMessage 数据库模型**
- [x] **Step 2: 创建对话 schemas**（ChatRequest / ChatResponse / ChatMessageResponse）
- [x] **Step 3: 实现 ChatService**（`get_or_create_session` / `save_message` / `get_history` / `delete_session`；**不含 LLM 调用**）
- [x] **Step 4: 生成迁移**
- [ ] **Step 5: Commit**

---

### Task 7.2: chat_agent

**Files:**
- Update: `app/agents/chat/state.py`（Phase 4 已预建 `ChatState`，此处按需补 `chat_*` 字段）
- Create: `app/agents/chat/nodes.py`
- Create: `app/agents/chat/tools.py`
- Create: `app/agents/chat/graph.py`
- Create: `app/agents/prompts/chat_system.py`
- Create: `app/api/v1/ai.py`

- [x] **Step 1: 补全 ChatState 字段**（在 Phase 4 的基础上按需增补，而不是新建）
- [x] **Step 2: 实现节点**
  - `identify_intent`（LLM + structured output，写入 `state["intent"]`）
  - `recall_memories`（Tool: MemoryService.recall_memories）
  - `search_knowledge`（Tool: RagService.search_knowledge）
  - `assemble_prompt`（代码确定性组装）
  - `call_llm`（get_chat_model, temperature=0.7）
  - `trigger_memory_extract`（`asyncio.create_task(memory_subgraph.ainvoke(...))`，不阻塞）
- [x] **Step 3: 组装 Graph** — `build_chat_agent()`
  - 挂载既有 subgraph：`chat_graph.add_node("diet", build_diet_subgraph())`（来自 Phase 4 `app/agents/diet/subgraph.py`）
  - 依次挂载 memory / plan / suggestion subgraph（随各 Phase 完工而增加）
  - 条件边：按 `state["intent"]` 路由到对应 subgraph；`general` 走直接对话
- [x] **Step 4: 实现 API 端点**
  - `POST /ai/chat` → ChatService 保存 user msg → `chat_agent.ainvoke` → ChatService 保存 assistant msg（含结构化 cards，参见 `api-contract.md` §8.1）
  - `GET /ai/chat/history` → ChatService
  - `DELETE /ai/chat/sessions/{id}` → ChatService
- [x] **Step 5: 端到端测试**（mock LLM，验证意图路由 → diet subgraph → 返回解析卡片）
- [ ] **Step 6: Commit**

---

## Phase 8: 计划系统（plan_agent）

**目标：** 通过 `plan_agent` 实现 4 步对话创建、修改建议；`PlanService` 做 CRUD + BMR + 执行追踪。

**参考 spec：** `02-ai-modules/plan-system.md`、`00-architecture/agents.md`

### Task 8.1: 计划数据层与 PlanService

**Files:**
- Create: `app/db/models/plan.py`
- Create: `app/db/repositories/plan_repo.py`
- Create: `app/schemas/plan.py`
- Create: `app/services/plan_service.py`

- [x] **Step 1: 创建 Plan、PlanTarget、PlanExecution、PlanCheckIn 数据库模型**
- [x] **Step 2: 创建计划 schemas**（Create / Update / Response / CheckIn / Progress / PlanDraft）
- [x] **Step 3: 实现 PlanRepository**
- [x] **Step 4: 实现 PlanService**
  - CRUD：`create_plan_from_draft` / `get_plan` / `list_plans` / `update_plan` / `terminate_plan`
  - 打卡 / 进度 / 执行记录
  - 纯算法：`calculate_bmr` / `calculate_execution_status` / `safety_check`
  - `has_active_plan` / `on_diet_record_created` / `run_modification_rules`
  - **不含 LLM 调用**
- [x] **Step 5: 生成迁移**
- [x] **Step 6: 单元测试**（BMR、达标状态、安全校验）
- [ ] **Step 7: Commit**

---

### Task 8.2: plan_agent + API

**Files:**
- Create: `app/agents/plan/state.py`
- Create: `app/agents/plan/nodes.py`
- Create: `app/agents/plan/tools.py`
- Create: `app/agents/plan/graph.py`
- Create: `app/agents/prompts/plan_confirm.py`
- Create: `app/agents/prompts/plan_analyze.py`
- Create: `app/agents/prompts/plan_draft.py`
- Create: `app/api/v1/plans.py`

- [x] **Step 1: 定义 PlanState**
- [x] **Step 2: 实现节点**（`confirm_goal` / `analyze_status` / `draft_plan` / `safety_validate` / `persist_plan`）
- [x] **Step 3: 实现 modification_subgraph**（`analyze_deviation` / `suggest_modification`）
- [x] **Step 4: 组装 Graph** — `build_plan_agent()`（含创建主图和修改子图）
- [x] **Step 5: 实现 API 端点**
  - `POST /plans` → PlanService.has_active_plan 校验 → `plan_agent.ainvoke`
  - CRUD / check-ins / progress / execution → PlanService
- [x] **Step 6: 端到端测试**
- [ ] **Step 7: Commit**

---

## Phase 9: AI 建议系统（suggestion_agent）

**目标：** 通过 `suggestion_agent` 实现每日/餐食/洞察三类建议；`SuggestionService` 做缓存与反馈。

**参考 spec：** `02-ai-modules/ai-suggestion.md`、`00-architecture/agents.md`

### Task 9.1: suggestion_agent + Service + API

**Files:**
- Create: `app/db/models/suggestion.py`
- Create: `app/db/repositories/suggestion_repo.py`
- Create: `app/schemas/suggestion.py`
- Create: `app/services/suggestion_service.py`
- Create: `app/agents/suggestion/state.py`
- Create: `app/agents/suggestion/nodes.py`
- Create: `app/agents/suggestion/tools.py`
- Create: `app/agents/suggestion/graph.py`
- Create: `app/agents/prompts/suggestion_daily.py`
- Create: `app/agents/prompts/suggestion_meal.py`
- Create: `app/agents/prompts/suggestion_insight.py`
- Create: `app/api/v1/suggestions.py`

- [ ] **Step 1: 创建 Suggestion 数据库模型** + schemas
- [ ] **Step 2: 实现 suggestion_agent** — 节点：collect_data / recall_memories / search_knowledge / generate_suggestions / deduplicate_filter
- [ ] **Step 3: 实现 SuggestionService**（缓存读写、反馈写入、反馈后 `memory_agent.ainvoke(trigger="suggestion_feedback", ...)`；**不含 LLM 调用**）
- [ ] **Step 4: 实现 API 端点**（`GET /suggestions/daily` / `meal` / `insights`、`POST /suggestions/{id}/feedback`）
- [ ] **Step 5: 端到端测试**
- [ ] **Step 6: Commit**

---

## Phase 10: 全局联调与收尾

**目标：** 串联所有模块，验证完整业务流程，补充测试。

### Task 10.1: 跨模块集成

- [ ] **Step 1: diet_agent 末节点触发 memory_agent** — 验证饮食记录后记忆提取异步执行
- [ ] **Step 2: body_service 变化触发 memory_agent**（通过 API 层封装）
- [ ] **Step 3: user_service 档案更新触发 MemoryService.on_profile_updated**
- [ ] **Step 4: diet_service.on_record_created 触发 PlanService.on_diet_record_created**
- [ ] **Step 5: Commit**

---

### Task 10.2: 完整流程验证

- [ ] **Step 1: 验证 Auth 流程**（注册 → 登录 → 获取 token → 访问受保护端点）
- [ ] **Step 2: 验证用户档案流程**（创建 → 更新 → onboarding）
- [ ] **Step 3: 验证饮食流程**（diet_agent 解析 → 创建记录 → 查询 → 汇总）
- [ ] **Step 4: 验证身体数据流程**（记录 → 趋势 → 异常检测）
- [ ] **Step 5: 验证 AI 对话流程**（chat_agent：发消息 → 记忆召回 → 回复 → 记忆写入）
- [ ] **Step 6: 验证计划流程**（plan_agent 创建 → 打卡 → 进度）
- [ ] **Step 7: 验证建议流程**（suggestion_agent：每日 → 餐食 → 洞察 → 反馈）
- [ ] **Step 8: Lint 检查**：grep 整个 `app/services/` 确保没有 `ChatOpenAI` 或 `from openai`
- [ ] **Step 9: 修复发现的问题**
- [ ] **Step 10: Final Commit**

---

## 进度追踪

| Phase | 名称 | Task 数 | 状态 |
|-------|------|---------|------|
| 0 | 项目初始化与基础设施 | 3 | ✅ 已完成 |
| 1 | 认证与用户系统 | 2 | ✅ 已完成 |
| 2 | Agent 基础设施与向量能力 | 2 | ✅ 已完成（按新 spec 做 reverse-review） |
| 3 | RAG 知识库 | 2 | ✅ 已完成 |
| 4 | 饮食记录模块（diet_agent） | 4 | ✅ 已完成（待 commit） |
| 5 | 身体数据追踪模块 | 1 | ✅ 已完成（待 commit） |
| 6 | AI 记忆系统（memory_agent） | 2 | ✅ 已完成（待 commit） |
| 7 | AI 对话系统（chat_agent） | 2 | ✅ 已完成（待 commit） |
| 8 | 计划系统（plan_agent） | 2 | ✅ 已完成（待 commit） |
| 9 | AI 建议系统（suggestion_agent） | 1 | ⬜ 未开始 |
| 10 | 全局联调与收尾 | 2 | ⬜ 未开始 |
| **总计** | | **23 Tasks** | |
