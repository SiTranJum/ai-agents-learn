# 健康管家 AI Agent · Backend 项目认知地图（PROJECT MAP）

> 本文档为项目级"认知地图"，用于建立整体结构认知，不涉及接口与代码实现细节。后续可基于第十二节的 PROJECT_MAP 逐模块深入分析。

## 一、项目概述

| 维度 | 内容 |
|------|------|
| 项目目标 | 一个 AI-first 的个人健康管理后端，以对话式交互为核心，帮助用户管理饮食、体重、运动、睡眠等健康数据 |
| 业务背景 | "像和朋友聊天一样管理健康"——AI 懂用户习惯、记得目标、主动关心进展；区别于传统表单式健康 App |
| 核心用户 | 有健康管理意识的普通用户、需要控制饮食/体重的人群、健身爱好者、慢性病患者 |
| 系统定位 | 多 Agent（LangGraph）+ RAG + 记忆系统 的 AI 应用后端，对外提供 REST + SSE 流式 API |
| 主要解决的问题 | ① 自然语言记录健康数据（免手填表单）② 个性化健康建议 ③ AI 记住用户长期偏好与目标 ④ 计划制定与执行追踪 |

## 二、技术架构

### 技术栈
- 语言/框架：Python + FastAPI（异步）
- ORM/数据库：SQLAlchemy（async）+ PostgreSQL + **pgvector**（向量列）
- 数据库迁移：Alembic
- LLM：通义千问 DashScope（OpenAI 兼容模式），Chat 用 `qwen-plus`，Embedding 用 `text-embedding-v3`（1024 维）
- Agent 编排：**LangGraph**（StateGraph + Subgraph）+ LangChain
- 认证：Supabase Auth（JWT，HS256；后端只校验 token，不提供注册登录端点）
- 流式：SSE（Server-Sent Events）

### 系统架构（四层）
```
HTTP/SSE 路由 (api/v1)  →  Service 层 (services, 无 LLM)  →  Agent 层 (agents, LangGraph + LLM)
                                      ↓
                       基础设施: db(Repository) / integrations(Embedding+pgvector) / streaming(SSE)
```

### 服务划分
单体应用（modular monolith），按领域分模块，未拆分微服务。

### 第三方依赖 / 中间件
- DashScope（LLM + Embedding）
- Supabase（PostgreSQL 托管 + Auth）
- pgvector（PostgreSQL 扩展，做向量检索）
- ❌ 未使用 Redis（仅在 `pending_action_store` 注释中作为生产可选项）
- ❌ 未使用 MQ（无 Kafka/RabbitMQ/Celery）

## 三、项目目录结构分析

| 一级目录 | 职责 |
|---------|------|
| `app/api/v1` | HTTP 路由层（≈对应 Spring Controller），处理请求、SSE 包装、委托给 Service |
| `app/services` | 业务服务层（≈Service），**100% 无 LLM 调用**，做 CRUD、计算、校验、存取 |
| `app/agents` | AI Agent 层（LangGraph），LLM 编排、意图识别、工具调用、流式推理 |
| `app/db/models` | 数据模型（≈Entity / JPA @Entity），定义表结构 |
| `app/db/repositories` | 数据访问层（≈DAO / Repository），强制多租户用户隔离 |
| `app/schemas` | Pydantic DTO（请求/响应模型，≈VO/DTO） |
| `app/integrations` | 外部集成：`embedding`（DashScope 向量）、`vector`（pgvector 检索） |
| `app/streaming` | SSE 流式基础设施：编码、心跳、LangGraph 事件翻译、埋点 |
| `app/core` | 横切关注点：异常、日志、分页、统一响应、安全、链路追踪 |
| `app/config.py` `app/dependencies.py` | 配置（pydantic-settings）与依赖注入 |
| `alembic/versions` | 数据库迁移脚本（Phase 1~12 演进） |
| `tests` | 单元/集成测试（按 agents/api/services/repositories/streaming 分类） |

## 四、模块划分

| 模块 | 职责 | 重要程度 | 复杂度 | 依赖模块 |
|------|------|---------|--------|---------|
| Chat（对话） | 全局入口，意图识别 + 路由 + 通用对话 + 记忆触发 | ★★★★★ | 高 | Diet/Body/Plan/Memory/Knowledge |
| Plan（计划） | 健康计划制定、目标曲线展开、打卡、完成率、调整提案 | ★★★★★ | 高 | User/Body/Diet/Memory |
| Memory（记忆） | 长/中/短期分层记忆，提取→评分→去重→向量化存储与召回 | ★★★★★ | 高 | Embedding/Vector |
| Diet（饮食） | 自然语言饮食解析、营养计算、记录入库 | ★★★★☆ | 中高 | Knowledge(RAG)/Memory |
| Knowledge/RAG（知识库） | 食物营养库 + 健康文档库的向量检索 | ★★★★☆ | 中 | Embedding/Vector |
| Body（身体数据） | 体重/围度/睡眠/运动/饮水/排便 记录与趋势统计 | ★★★☆☆ | 中 | Plan(合规计算) |
| Suggestion（建议） | 每日建议/餐食建议/趋势洞察 的 LLM 生成与缓存 | ★★★☆☆ | 中 | Memory/Knowledge/Body/Diet |
| User（用户系统） | 健康档案、偏好、健康信息、设置、Onboarding | ★★★☆☆ | 中 | Memory(可选同步) |
| 基础设施（Streaming/Integrations/Core） | SSE、向量集成、异常/日志/响应封装 | ★★★★☆ | 中 | — |

## 五、模块依赖关系

```
                         ┌─────────────┐
        用户请求 ───────▶ │    Chat     │ (意图识别 + 路由入口)
                         └──────┬──────┘
            ┌───────────┬───────┼────────┬───────────────┐
            ▼           ▼       ▼        ▼               ▼
        ┌───────┐  ┌───────┐ ┌──────┐ ┌──────────┐  (general)
        │ Diet  │  │ Body  │ │ Plan │ │ Memory   │      │
        └───┬───┘  └───┬───┘ └──┬───┘ └────▲─────┘      │
            │          │        │          │ (后台异步触发) │
            └──────────┴────────┴──────────┘◀────────────┘
                       │                    │
                       ▼                    ▼
              ┌──────────────┐    ┌──────────────────┐
              │  Knowledge   │    │  Embedding +     │
              │   (RAG)      │───▶│  pgvector (向量) │
              └──────────────┘    └──────────────────┘

  Suggestion ──▶ Memory + Knowledge + Body + Diet  (聚合多源数据生成建议)
  User ──(可选)──▶ Memory  (档案变化同步到记忆)
```

### 关键调用关系
- Chat 是唯一 AI 入口，按意图把请求路由到 Diet/Body/Plan subgraph 或 general 通用链路
- Diet 记录后、Chat 通用对话后，都会**后台异步**触发 Memory 提取（不阻塞主流）
- Diet/Suggestion 通过 RAG（Knowledge）+ Embedding + pgvector 实现语义检索
- Body 数据参与 Plan 的完成率/合规计算

## 六、核心业务链路

| 链路 | 流程 | 为什么重要 |
|------|------|-----------|
| ① 对话记录链路 | 用户文本 → `identify_intent` 意图识别 → 路由到 diet/body/plan subgraph 或 general → 召回记忆 + 检索知识 + 组装 prompt → LLM 流式输出 → 后台提取记忆 → SSE 返回 | 产品核心交互入口，所有 NLP 能力的总闸 |
| ② 计划制定链路 | `POST /plans/create`（SSE）→ 确认目标 → 分析用户档案 → 起草计划 → 安全校验 → `PlanService.create` → 派生子计划 + 展开每日目标曲线 | 健康管理的"骨架"，把目标转化为可执行可追踪的日程 |
| ③ 建议生成链路 | `GET /suggestions/daily`（SSE）→ 收集用户数据 → 召回记忆 → 检索知识库 → LLM 生成 → 缓存 + SSE 返回 | 体现"主动关心"的产品价值，个性化输出 |
| ④ 记忆驱动（横切） | 各链路产生事实 → Memory 提取 → 评分去重 → 向量化存储 → 后续对话/建议召回 | 让 AI"记得用户"，是个性化与连贯性的基础 |

## 七、数据库概览

### 核心表
| 表 | 用途 | 重要程度 |
|----|------|---------|
| `plans` / `plan_sub_plans` / `plan_daily_targets` | 计划主体 + 维度子计划 + 每日目标曲线 | ★★★★★ |
| `memories` / `memory_summaries` | 长期记忆（向量）+ 中期摘要 | ★★★★★ |
| `chat_messages` | 对话消息（含卡片 JSON、软删除） | ★★★★★ |
| `diet_records` / `diet_items` | 单餐记录 + 食物营养条目 | ★★★★☆ |
| `foods` / `knowledge_docs` | 食物营养库 + 健康文档库（均带 1024 维 embedding） | ★★★★☆ |
| `body_weight_records` / `body_exercise_records` | 体重 / 运动记录 | ★★★★☆ |

### 辅助表
- 用户系统：`health_profiles`、`user_preferences`、`user_health_info`、`user_settings`
- 身体扩展：`body_measurement_records`、`body_sleep_records`、`body_water_records`、`body_bowel_records`
- 计划操作：`plan_targets`、`plan_executions`、`plan_check_ins`、`plan_analyses`、`plan_adjustment_proposals`
- 建议：`suggestions`

## 八、Redis 概览

**当前未启用 Redis。** 仅在 `app/services/pending_action_store.py` 中预留抽象接口——开发期用进程内 `dict` + TTL 保存跨 SSE 连接的会话级待决状态（如卡片操作 `diet_partial`/`plan_partial`），注释标明生产环境可替换为 Redis 实现。

## 九、MQ 概览

**当前未使用消息队列。** 异步解耦通过两种方式实现：
- LangGraph 节点内的**后台 async 任务**（如 Diet/Chat 后台触发 Memory 提取）
- `plan_check_in_task`：打卡后后台异步生成运动记录（幂等防重）

未来如需削峰/可靠投递可引入 MQ，但现阶段无此依赖。

## 十、第三方系统概览

- **DashScope（通义千问）**：LLM 推理（`qwen-plus`）+ 文本向量（`text-embedding-v3`）
- **Supabase**：托管 PostgreSQL 数据库 + Auth（JWT 认证，前端直连，后端只验签）
- **PostgreSQL + pgvector**：关系数据 + 向量检索（RAG 与记忆召回的底层引擎）

## 十一、新人学习路线

### 第一阶段（建立骨架认知）
- `app/main.py`、`app/config.py`、`app/api/v1/router.py`、`app/dependencies.py`、`app/core/*`
- `db/base.py`、`db/session.py`、`db/repositories/base.py`
- 原因：先搞清应用启动、配置、路由聚合、统一响应/异常、数据访问基模式，建立"请求怎么进来又怎么出去"的心智模型

### 第二阶段（核心数据 + 普通业务流）
- `db/models/*` 全部 + `services/*`（先看 diet/body/user 这类纯 CRUD service）
- `api/v1/diet.py`、`body.py`、`users.py`
- 原因：这些是**无 LLM 的标准 CRUD 链路**，对 Java 后端最熟悉，先吃透数据流和分层

### 第三阶段（AI 核心）
- `agents/base.py` → `agents/chat/*`（graph/nodes/state）→ 各 subgraph（diet/body/plan/memory/suggestion）
- `streaming/*`（SSE + LangGraph 事件翻译）、`integrations/*`（embedding + pgvector）、`services/memory_service.py`、`rag_service.py`、`plan_*_service.py`
- 原因：这是项目的技术壁垒与价值所在（LangGraph 编排、RAG、记忆、流式），需要前两阶段基础才能看懂上下文

## 十二、PROJECT_MAP

| 模块 | 模块职责 | 核心接口数量(约) | 核心表 | 依赖模块 |
|------|---------|----------|--------|---------|
| Chat | 对话入口、意图识别、路由、通用对话、记忆触发 | ~5 (SSE) | chat_messages | Diet/Body/Plan/Memory/Knowledge |
| Plan | 计划制定、目标曲线、打卡、完成率、调整 | ~10 | plans / plan_sub_plans / plan_daily_targets / plan_check_ins | User/Body/Diet/Memory |
| Memory | 分层记忆提取、评分、向量化存储与召回 | 内部(无独立 REST) | memories / memory_summaries | Embedding/Vector |
| Diet | 饮食 NLP 解析、营养计算、记录 | ~5 | diet_records / diet_items | Knowledge/Memory |
| Body | 身体数据记录与趋势统计 | ~8 | body_weight_records / body_exercise_records (+4) | Plan |
| Knowledge/RAG | 食物 + 健康文档向量检索 | ~2 | foods / knowledge_docs | Embedding/Vector |
| Suggestion | 每日/餐食/洞察建议生成与缓存 | ~3 (SSE) | suggestions | Memory/Knowledge/Body/Diet |
| User | 健康档案、偏好、健康信息、设置、Onboarding | ~5 | health_profiles / user_preferences / user_health_info / user_settings | Memory(可选) |
