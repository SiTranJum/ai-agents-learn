# 后端实现总览

> 本文档定义健康管家后端服务的技术栈、核心原则、系统分层和 V1 实现范围。所有后端模块 specs 以本文档为基准。
>
> 实现依据：`docs/prd/00-master-prd-v2.md`，前端 specs `docs/specs/frontend/00-implementation-overview.md`

---

## 1. 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 语言 | Python 3.11+ | AI 生态最成熟 |
| Web 框架 | FastAPI | 异步支持、自动 OpenAPI 文档、类型校验 |
| 数据库 | Supabase (PostgreSQL 15+) | 关系型数据 + pgvector 扩展 |
| 向量搜索 | pgvector | 与 PostgreSQL 同库，V1 不引入独立向量数据库 |
| ORM | SQLAlchemy 2.0 + asyncpg | 异步 ORM，支持 pgvector 类型 |
| 数据校验 | Pydantic v2 | 请求/响应模型、配置管理 |
| 认证 | Supabase Auth | JWT 验证，不自建认证系统 |
| LLM | DashScope (qwen-plus) | 通义千问，OpenAI SDK 兼容接口 |
| Embedding | DashScope (text-embedding-v3) | 1024 维向量 |
| AI 编排 | LangGraph | 多步骤 AI 流程（记忆、建议生成等） |
| 迁移工具 | Alembic | 数据库 schema 版本管理 |
| 测试 | pytest + httpx | 异步测试支持 |
| 包管理 | uv | 快速依赖管理 |

## 2. 核心设计原则

### 2.1 AI-Native

AI 不是附加功能，而是核心能力。饮食解析、记忆管理、建议生成都以 LLM 为中心设计。

### 2.2 模块自治

每个功能模块（用户、饮食、身体数据、AI 记忆等）自包含 router → service → repository 三层，模块间通过 service 层接口调用，禁止跨模块直接访问 repository。

### 2.3 类型安全

所有 API 接口使用 Pydantic 模型定义请求和响应，数据库操作使用 SQLAlchemy 模型，杜绝裸 dict 传递。

### 2.4 Mock-First 兼容

V1 阶段部分功能使用 mock 数据（如食物图片识别），API 接口设计必须与未来真实实现一致，切换时只改 service 层实现，不改 API 契约。

### 2.5 最简方案优先

不过度设计。V1 不引入消息队列、独立缓存层、微服务拆分。所有组件单体部署。

## 3. 系统分层

```
┌─────────────────────────────────────────────┐
│                 客户端 (Expo App)              │
└──────────────────────┬──────────────────────┘
                       │ HTTP/JSON
┌──────────────────────▼──────────────────────┐
│              API 层 (FastAPI Router)          │
│  路由定义、请求校验、响应格式化、认证中间件      │
├─────────────────────────────────────────────┤
│             Service 层 (业务逻辑)              │
│  业务编排、数据组装、AI 流程调度                 │
├─────────────────────────────────────────────┤
│           Repository 层 (数据访问)             │
│  数据库 CRUD、查询构建、事务管理                │
├──────────────┬──────────┬───────────────────┤
│  PostgreSQL  │ pgvector │  Supabase Auth    │
│  (数据存储)   │ (向量搜索) │  (认证服务)       │
└──────────────┴──────────┴───────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│            外部集成层 (Integrations)           │
│  DashScope LLM / DashScope Embedding         │
└─────────────────────────────────────────────┘
```

### 3.1 层级职责

| 层级 | 职责 | 禁止 |
|------|------|------|
| API 层 | 路由注册、参数校验、响应包装、认证检查 | 禁止包含业务逻辑 |
| Service 层 | 业务逻辑、跨模块协调、AI 流程编排 | 禁止直接操作数据库 |
| Repository 层 | SQL 查询、数据映射、事务管理 | 禁止包含业务判断 |
| 外部集成层 | LLM 调用、Embedding 生成、第三方 API | 禁止感知业务上下文 |

### 3.2 调用规则

- API 层 → Service 层 → Repository 层（单向依赖）
- Service 层可调用外部集成层
- Service 层之间可互相调用（通过依赖注入）
- Repository 层之间禁止互相调用

## 4. V1 实现范围

### 4.1 包含（Must Have）

| 模块 | 功能 |
|------|------|
| 用户系统 | 注册、登录、登出、健康档案 CRUD |
| 饮食记录 | 文本 AI 解析、营养计算、记录 CRUD、每日/每周汇总 |
| 身体追踪 | 体重记录、体围记录、辅助记录（睡眠/运动/饮水/排便）、趋势数据 |
| AI 记忆 | 三层记忆架构、记忆提取、向量召回 |
| RAG 知识库 | 食物营养库（500+ 条）、健康建议库（180 条）、向量检索 |
| 计划系统 | 对话式创建、执行追踪、进度统计 |
| AI 建议 | 饮食建议、目标建议、趋势洞察 |
| AI 对话 | 全局对话入口、意图识别、多轮对话 |

### 4.2 不包含（V2+）

- 图片识别（V1 使用 mock，返回固定解析结果）
- 语音输入
- 第三方食物 API 集成（FatSecret / Open Food Facts，V1 仅用本地库 + LLM 估算）
- 消息推送 / 主动提醒
- 付费系统 / Token 配额
- 数据导出
- 多语言

## 5. 与 PRD 的对应关系

| PRD 文档 | 后端 Spec |
|----------|----------|
| `prd/00-master-prd-v2.md` | 本文档 + `api-design.md` |
| `prd/v1/01-user-system.md` | `01-core-modules/user-system.md` |
| `prd/v1/03-diet-recording.md` | `01-core-modules/diet-recording.md` |
| `prd/v1/04-body-tracking.md` | `01-core-modules/body-tracking.md` |
| `prd/v1/05-ai-memory.md` | `02-ai-modules/ai-memory.md` |
| `prd/v1/06-rag-knowledge.md` | `02-ai-modules/rag-knowledge.md` |
| `prd/v1/07-plan-system.md` | `02-ai-modules/plan-system.md` |
| `prd/v1/08-ai-suggestion.md` | `02-ai-modules/ai-suggestion.md` |

## 6. 环境配置

### 6.1 环境变量

```python
# .env 文件结构（不含实际值）
SUPABASE_URL=                    # Supabase 项目 URL
SUPABASE_ANON_KEY=               # Supabase 匿名 Key
SUPABASE_SERVICE_ROLE_KEY=       # Supabase 服务端 Key
DATABASE_URL=                    # PostgreSQL 连接串（含 pgvector）
DASHSCOPE_API_KEY=               # 通义千问 API Key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus             # Chat 模型
EMBEDDING_MODEL=text-embedding-v3  # Embedding 模型
EMBEDDING_DIMENSIONS=1024        # 向量维度
```

### 6.2 本地开发

```bash
# 启动开发服务器
uvicorn app.main:app --reload --port 8000

# 数据库迁移
alembic upgrade head

# 运行测试
pytest tests/ -v
```
