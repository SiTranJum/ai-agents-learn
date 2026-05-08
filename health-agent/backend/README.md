# health-agent-api

健康管家 AI Agent 后端服务。

**Tech stack**: Python 3.11+ · FastAPI · SQLAlchemy 2.0 (async) · Pydantic v2 · Supabase (PostgreSQL + Auth) · pgvector · DashScope (qwen-plus / text-embedding-v3) · LangGraph · Alembic.

参考：`docs/specs/backend/` · 实施计划：`docs/plans/2026-04-30-backend-implementation.md`。

---

## 快速开始

### 1. 安装依赖

推荐使用 [uv](https://docs.astral.sh/uv/)：

```bash
uv venv
uv pip install -e ".[dev]"
```

或使用 pip：

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 然后编辑 .env，填入 Supabase / DashScope 等真实凭据
```

关键变量：

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | Supabase Postgres 连接串（`postgresql+asyncpg://...`） |
| `SUPABASE_JWT_SECRET` | 用于校验前端传来的 Bearer JWT |
| `DASHSCOPE_API_KEY` | 通义千问 API Key |
| `LLM_MODEL` | 默认 `qwen-plus` |
| `EMBEDDING_MODEL` | 默认 `text-embedding-v3`（1024 维） |

### 3. 数据库迁移

```bash
alembic upgrade head
```

> Phase 0 暂无业务表迁移；Phase 1 起每个模块会随 PR 一并提交迁移文件。

### 4. 启动开发服务器

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- 健康探针: <http://localhost:8000/health>

### 5. 运行测试

```bash
pytest
```

---

## 项目结构

详细说明见 `docs/specs/backend/00-architecture/project-structure.md`。

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口（CORS、异常处理、lifespan）
│   ├── config.py            # pydantic-settings 配置
│   ├── dependencies.py      # 全局依赖（DB session、当前用户）
│   ├── api/v1/              # 路由层
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── services/            # 业务逻辑层
│   ├── db/
│   │   ├── base.py          # SQLAlchemy Base + 通用 Mixin
│   │   ├── session.py       # AsyncEngine / AsyncSession
│   │   ├── models/          # ORM 模型（按模块拆分）
│   │   └── repositories/    # 数据访问层
│   ├── agents/              # LangGraph Agent：所有 LLM 推理的唯一入口
│   ├── integrations/        # Embedding / pgvector / Supabase 等外部集成
│   └── core/                # 异常、响应、安全、分页等通用工具
├── alembic/                 # 数据库迁移
├── scripts/                 # 工具脚本（seed_*, generate_embeddings 等）
├── data/                    # 种子数据（foods.json、health_tips.json）
└── tests/                   # pytest 测试
```

### 分层依赖规则

```
api/  →  agents/  →  services/  →  repositories/  →  db/models/
          │             ↘ integrations/
          └──────────────↗
```

- `api/` 严禁直接调用 `repositories/` 或 `integrations/`
- 涉及 LLM 推理的业务必须通过 `agents/`，禁止在 `services/` 中直接调用 Chat/LLM SDK
- `repositories/` 严禁调用 `services/` 或其它 repository
- `integrations/` 严禁感知业务上下文

---

## 统一响应契约

成功：
```json
{ "data": { ... }, "message": "ok" }
```

分页：
```json
{ "data": [ ... ], "pagination": { "total": 100, "page": 1, "page_size": 20, "total_pages": 5 }, "message": "ok" }
```

错误：
```json
{ "error": { "code": "USER_NOT_FOUND", "message": "用户不存在", "details": null } }
```

错误码体系参见 `docs/specs/backend/00-architecture/api-design.md` §4。

---

## 实施进度

参见 `docs/plans/2026-04-30-backend-implementation.md`。当前：**Phase 0 — 项目初始化与基础设施**。
