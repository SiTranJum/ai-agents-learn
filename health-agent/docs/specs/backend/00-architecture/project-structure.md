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
│   ├── services/                        # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py              # 认证业务逻辑
│   │   ├── user_service.py              # 用户档案业务逻辑
│   │   ├── diet_service.py              # 饮食记录 + AI 解析
│   │   ├── body_service.py              # 身体数据 + 趋势计算
│   │   ├── plan_service.py              # 计划创建 + 执行追踪
│   │   ├── ai_chat_service.py           # AI 对话主流程
│   │   ├── memory_service.py            # 记忆管理（提取、召回、衰减）
│   │   ├── rag_service.py               # RAG 检索
│   │   └── suggestion_service.py        # 建议生成
│   │
│   ├── integrations/                    # 外部服务集成
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── client.py                # DashScope LLM 客户端封装
│   │   │   ├── prompts/                 # Prompt 模板目录
│   │   │   │   ├── diet_parse.py        # 饮食解析 prompt
│   │   │   │   ├── memory_extract.py    # 记忆提取 prompt
│   │   │   │   ├── plan_create.py       # 计划创建 prompt
│   │   │   │   ├── suggestion.py        # 建议生成 prompt
│   │   │   │   └── intent.py            # 意图识别 prompt
│   │   │   └── schemas.py               # LLM 输入输出类型
│   │   ├── embedding/
│   │   │   ├── __init__.py
│   │   │   └── client.py                # Embedding 生成客户端
│   │   ├── vector/
│   │   │   ├── __init__.py
│   │   │   └── pgvector_client.py       # pgvector 搜索封装
│   │   └── supabase_auth/
│   │       ├── __init__.py
│   │       └── client.py                # Supabase Auth 客户端
│   │
│   ├── graphs/                          # LangGraph 流程定义
│   │   ├── __init__.py
│   │   ├── chat_graph.py                # 对话处理主流程
│   │   ├── memory_graph.py              # 记忆提取流程
│   │   └── suggestion_graph.py          # 建议生成流程
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

业务逻辑层。核心业务编排在这里。

- 职责：业务规则、数据组装、跨模块协调、AI 流程调度
- 可调用：repository 层、外部集成层、其他 service
- 禁止：直接操作数据库 session

### 2.6 `app/integrations/`

外部服务封装。隔离第三方依赖。

- 职责：LLM 调用、Embedding 生成、向量搜索、Supabase Auth
- 设计原则：对外暴露简洁接口，内部处理重试、超时、错误转换
- 切换供应商时只改这一层

### 2.7 `app/graphs/`

LangGraph 流程定义。复杂的多步骤 AI 流程在这里编排。

- 职责：定义 AI 处理的 state graph（节点、边、条件分支）
- 被 service 层调用

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
api/ ──→ services/ ──→ repositories/ ──→ db/models/
                  ──→ integrations/
                  ──→ graphs/
                  ──→ 其他 services/（通过依赖注入）
```

### 4.2 禁止的依赖

- `api/` 禁止直接调用 `repositories/` 或 `integrations/`
- `repositories/` 禁止调用 `services/` 或其他 `repositories/`
- `integrations/` 禁止调用 `services/` 或 `repositories/`
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
