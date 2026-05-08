# 项目目录结构

> 本文档定义后端项目的完整目录结构、每个目录的职责、文件命名规范和模块边界规则。
>
> 实现依据：`00-architecture/overview.md` 系统分层设计

---

## 1. 完整目录树

```
health-agent-api/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI 应用入口
│   ├── config.py                        # 配置管理（Pydantic Settings）
│   ├── dependencies.py                  # 全局依赖注入（db session、当前用户等）
│   │
│   ├── api/                             # API 路由层
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py                # v1 路由汇总注册
│   │       ├── auth.py                  # 认证相关路由
│   │       ├── users.py                 # 用户档案路由
│   │       ├── diet.py                  # 饮食记录路由
│   │       ├── body.py                  # 身体数据路由
│   │       ├── plans.py                 # 计划系统路由
│   │       ├── ai.py                    # AI 对话路由
│   │       ├── suggestions.py           # AI 建议路由
│   │       └── knowledge.py             # 知识库查询路由
│   │
│   ├── schemas/                         # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── common.py                    # 通用模型（分页、响应包装）
│   │   ├── auth.py                      # 认证相关 schema
│   │   ├── user.py                      # 用户相关 schema
│   │   ├── diet.py                      # 饮食相关 schema
│   │   ├── body.py                      # 身体数据 schema
│   │   ├── plan.py                      # 计划相关 schema
│   │   ├── ai.py                        # AI 对话 schema
│   │   ├── suggestion.py                # 建议相关 schema
│   │   └── knowledge.py                 # 知识库 schema
│   │
│   ├── db/                              # 数据库层
│   │   ├── __init__.py
│   │   ├── session.py                   # 数据库连接和 session 管理
│   │   ├── base.py                      # SQLAlchemy Base 声明
│   │   ├── models/                      # SQLAlchemy 表模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py                  # users, health_profiles 等
│   │   │   ├── diet.py                  # diet_records, diet_items, foods
│   │   │   ├── body.py                  # weight_records, circumference_records 等
│   │   │   ├── memory.py                # memories, memory_summaries
│   │   │   ├── knowledge.py             # knowledge_docs, foods (知识库)
│   │   │   ├── plan.py                  # plans, plan_targets, plan_execution
│   │   │   ├── suggestion.py            # suggestions
│   │   │   └── chat.py                  # chat_messages
│   │   └── repositories/               # 数据访问层
│   │       ├── __init__.py
│   │       ├── base.py                  # 通用 CRUD 基类
│   │       ├── user_repo.py
│   │       ├── diet_repo.py
│   │       ├── body_repo.py
│   │       ├── memory_repo.py
│   │       ├── knowledge_repo.py
│   │       ├── plan_repo.py
│   │       ├── suggestion_repo.py
│   │       └── chat_repo.py
│   │
│   ├── services/                        # 业务逻辑层（DB CRUD + 纯算法，不做 LLM 编排）
│   │   ├── __init__.py
│   │   ├── auth_service.py              # 认证业务逻辑
│   │   ├── user_service.py              # 用户档案业务逻辑
│   │   ├── diet_service.py              # 饮食记录 CRUD + 营养计算（被 diet_agent 作为 Tool 调用）
│   │   ├── body_service.py              # 身体数据 + 趋势计算
│   │   ├── plan_service.py              # 计划 CRUD + BMR + 执行追踪（被 plan_agent 调用）
│   │   ├── memory_service.py            # 记忆存储/召回/衰减（被 memory_agent 和其他 agent 调用）
│   │   ├── rag_service.py               # RAG 检索（被各 agent 作为 Tool 调用）
│   │   └── suggestion_service.py        # 建议缓存与反馈
│   │
│   ├── integrations/                    # 外部服务集成（仅 Embedding + pgvector + Supabase）
│   │   ├── __init__.py
│   │   ├── embedding/
│   │   │   ├── __init__.py
│   │   │   └── client.py                # Embedding 生成客户端（text-embedding-v3）
│   │   ├── vector/
│   │   │   ├── __init__.py
│   │   │   └── pgvector_client.py       # pgvector 搜索封装
│   │   └── supabase_auth/
│   │       ├── __init__.py
│   │       └── client.py                # Supabase Auth 客户端
│   │   # 注意：不存在 llm/client.py。LLM 调用统一在 app/agents/ 中通过
│   │   # langchain_openai.ChatOpenAI（配 DashScope base_url）发起。
│   │
│   ├── agents/                          # LangGraph Agent 层（所有 LLM 推理的唯一入口）
│   │   ├── __init__.py
│   │   ├── base.py                      # get_chat_model() 全局模型工厂 + 通用 State 基字段
│   │   ├── prompts/                     # Prompt 模板目录（与 Graph 解耦）
│   │   │   ├── diet_parse.py
│   │   │   ├── memory_extract.py
│   │   │   ├── memory_score.py
│   │   │   ├── plan_confirm.py
│   │   │   ├── plan_analyze.py
│   │   │   ├── plan_draft.py
│   │   │   ├── suggestion_daily.py
│   │   │   ├── suggestion_meal.py
│   │   │   ├── suggestion_insight.py
│   │   │   ├── chat_system.py
│   │   │   └── consolidate.py
│   │   ├── chat/                        # 全局 AI 对话 Agent
│   │   │   ├── state.py
│   │   │   ├── nodes.py
│   │   │   ├── tools.py
│   │   │   └── graph.py                 # build_chat_agent()
│   │   ├── diet/                        # 饮食文本/图片解析 Agent
│   │   │   ├── state.py
│   │   │   ├── nodes.py                 # parse_text / enrich_nutrition / save_record
│   │   │   ├── tools.py                 # search_food / save_diet_record / get_prefs
│   │   │   └── graph.py                 # build_diet_agent()
│   │   ├── plan/                        # 计划 4 步对话创建 Agent
│   │   │   ├── state.py
│   │   │   ├── nodes.py                 # confirm_goal / analyze / draft / validate
│   │   │   ├── tools.py                 # get_profile / get_recent_diet / save_plan / calc_bmr
│   │   │   └── graph.py                 # build_plan_agent()
│   │   ├── memory/                      # 记忆提取/评分/合并 Agent
│   │   │   ├── state.py
│   │   │   ├── nodes.py                 # extract / score / filter / embed_and_store
│   │   │   ├── tools.py                 # save_memory / list_memories / embed
│   │   │   └── graph.py                 # build_memory_agent()
│   │   └── suggestion/                  # 建议生成 Agent
│   │       ├── state.py
│   │       ├── nodes.py                 # collect / recall / search_kb / generate / dedup
│   │       ├── tools.py                 # get_progress / recall_memories / search_knowledge
│   │       └── graph.py                 # build_suggestion_agent()
│   │
│   └── core/                            # 通用工具
│       ├── __init__.py
│       ├── exceptions.py                # 统一异常定义
│       ├── security.py                  # JWT 验证、权限检查
│       ├── pagination.py                # 分页工具
│       └── response.py                  # 统一响应格式化
│
├── alembic/                             # 数据库迁移
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── scripts/                             # 工具脚本
│   ├── seed_foods.py                    # 食物知识库初始化
│   ├── seed_health_tips.py              # 健康建议库初始化
│   └── generate_embeddings.py           # 批量生成 embedding
│
├── data/                                # 种子数据
│   ├── foods.json                       # 食物营养数据
│   └── health_tips.json                 # 健康建议数据
│
├── tests/
│   ├── conftest.py                      # 测试配置和 fixtures
│   ├── api/                             # API 集成测试
│   ├── services/                        # Service 单元测试
│   └── repositories/                    # Repository 单元测试
│
├── .env.example                         # 环境变量模板
├── pyproject.toml                       # 项目配置和依赖
└── README.md
```

## 2. 目录职责说明

### 2.1 `app/api/`

路由定义层。每个文件对应一组 API 端点。

- 职责：路由注册、请求参数校验（通过 Pydantic schema）、调用 service、包装响应
- 禁止：包含业务逻辑、直接操作数据库、直接调用 LLM

```python
# 示例：app/api/v1/diet.py
from fastapi import APIRouter, Depends
from app.schemas.diet import DietRecordCreate, DietRecordResponse
from app.services.diet_service import DietService
from app.dependencies import get_current_user, get_diet_service

router = APIRouter(prefix="/diet", tags=["diet"])

@router.post("/records", response_model=DietRecordResponse)
async def create_diet_record(
    data: DietRecordCreate,
    user=Depends(get_current_user),
    service: DietService = Depends(get_diet_service),
):
    return await service.create_record(user.id, data)
```

### 2.2 `app/schemas/`

Pydantic 模型定义。分为请求模型（`*Create`、`*Update`）和响应模型（`*Response`）。

- 职责：数据校验、序列化/反序列化、API 文档生成
- 命名规范：`{Entity}Create`、`{Entity}Update`、`{Entity}Response`、`{Entity}Query`

### 2.3 `app/db/models/`

SQLAlchemy ORM 模型。每个文件对应一组相关的数据库表。

- 职责：表结构定义、字段类型映射、关系定义
- 所有模型继承自 `app/db/base.py` 中的 `Base`

### 2.4 `app/db/repositories/`

数据访问层。封装所有数据库操作。

- 职责：CRUD 操作、复杂查询构建、事务管理
- 禁止：包含业务判断逻辑
- 通用 CRUD 操作继承 `base.py` 中的 `BaseRepository`

### 2.5 `app/services/`

业务逻辑层。**DB CRUD 编排 + 纯算法**。

- 职责：业务规则、数据组装、纯算法（BMR、营养计算、趋势统计）、软删除、权限校验
- 可调用：repository 层、外部集成层（Embedding/pgvector）、其他 service
- 禁止：直接操作数据库 session、**直接调用 LLM**（必须走 Agent）、封装 LLM 场景方法
- 与 Agent 的关系：Service 是 Agent 的 **Tool 实现者**。饮食解析不在 service 里，而在 `diet_agent` 里；但"保存饮食记录到 DB"这种纯 CRUD 是 `DietService.create_record_from_parsed(...)`，由 Agent Tool 调用它。

### 2.6 `app/integrations/`

外部服务封装。**只剩 Embedding + pgvector + Supabase Auth**。

- 职责：Embedding 生成、向量搜索、Supabase Auth
- **不含 LLM 客户端**：LLM 调用统一在 `app/agents/` 中通过 langchain_openai 发起
- 设计原则：对外暴露简洁接口，内部处理重试、超时、错误转换

### 2.7 `app/agents/`

LangGraph Agent 层。**所有 LLM 推理的唯一入口**。

- 职责：定义 Agent 的 State、Node、Tool、Graph 编译产物
- 被 API 层直接调用（Agent-first），通过 Tool 间接调 Service
- 禁止：绕过 Service 直接操作数据库；直接 `from openai import ...`
- 详见 `00-architecture/agents.md`

### 2.8 `app/core/`

通用工具和基础设施代码。

- 职责：异常定义、安全工具、分页、响应格式化
- 原则：只放真正跨模块复用的代码，不放业务相关的工具

## 3. 命名规范

### 3.1 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| Python 文件 | snake_case | `diet_service.py` |
| 目录 | snake_case | `db/repositories/` |
| 测试文件 | `test_` 前缀 | `test_diet_service.py` |
| Prompt 模板 | snake_case，按场景命名 | `diet_parse.py` |

### 3.2 代码命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `DietService`、`DietRecord` |
| 函数/方法 | snake_case | `create_record()`、`get_daily_summary()` |
| 常量 | UPPER_SNAKE_CASE | `MAX_FOOD_ITEMS`、`DEFAULT_PAGE_SIZE` |
| Pydantic 模型 | PascalCase + 后缀 | `DietRecordCreate`、`DietRecordResponse` |
| SQLAlchemy 模型 | PascalCase（单数） | `DietRecord`、`FoodItem` |
| 数据库表名 | snake_case（复数） | `diet_records`、`food_items` |
| API 路由 | kebab-case（复数） | `/diet/records`、`/body/trends` |

## 4. 模块依赖规则

### 4.1 允许的依赖方向

```
api/ ──→ agents/ ──(Tool)──→ services/ ──→ repositories/ ──→ db/models/
     ──→ services/ ──────────────────────→ repositories/
                    ──→ integrations/ (embedding / pgvector / supabase_auth)
                    ──→ 其他 services/（通过依赖注入）

agents/ ──→ langchain_openai.ChatOpenAI（唯一 LLM 出口）
        ──→ services/（通过 Tool 封装）
        ──→ integrations/embedding（节点内可直接 embed）
```

### 4.2 禁止的依赖

- `api/` 禁止直接调用 `repositories/` 或 `integrations/`
- `repositories/` 禁止调用 `services/` 或其他 `repositories/`
- `integrations/` 禁止调用 `services/` 或 `repositories/`
- `services/` 禁止 `from langchain_openai import ChatOpenAI` 或 `from openai import OpenAI`（LLM 必须走 `agents/`）
- `core/` 禁止依赖任何业务模块

### 4.3 依赖注入

所有跨层依赖通过 FastAPI 的 `Depends` 机制注入：

```python
# app/dependencies.py
from app.services.diet_service import DietService
from app.db.repositories.diet_repo import DietRepository

async def get_diet_repo(session=Depends(get_db_session)):
    return DietRepository(session)

async def get_diet_service(repo=Depends(get_diet_repo)):
    return DietService(repo)
```
