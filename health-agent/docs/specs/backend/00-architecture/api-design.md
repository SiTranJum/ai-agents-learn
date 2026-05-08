# API 设计规范

> 本文档定义后端 API 的 RESTful 规范、统一响应格式、错误码体系、分页策略和所有模块的端点汇总。
>
> 实现依据：`00-architecture/overview.md`，`docs/prd/00-master-prd-v2.md`

---

## 1. RESTful 规范

### 1.1 URL 设计

- 基础路径：`/api/v1/`
- 资源名使用复数名词：`/records`、`/plans`
- 嵌套资源最多两层：`/plans/{id}/check-ins`
- URL 使用 kebab-case：`/daily-summary`

### 1.2 HTTP 方法语义

| 方法 | 语义 | 幂等 | 示例 |
|------|------|------|------|
| GET | 查询资源 | 是 | `GET /api/v1/diet/records` |
| POST | 创建资源 / 触发操作 | 否 | `POST /api/v1/diet/records` |
| PUT | 全量更新资源 | 是 | `PUT /api/v1/diet/records/{id}` |
| DELETE | 删除资源（软删除） | 是 | `DELETE /api/v1/diet/records/{id}` |

不使用 PATCH。更新操作统一用 PUT，请求体中未传的字段保持不变。

## 2. 统一响应格式

### 2.1 成功响应

```python
# 单个资源
{
    "data": { ... },
    "message": "ok"
}

# 列表资源（分页）
{
    "data": [ ... ],
    "pagination": {
        "total": 100,
        "page": 1,
        "page_size": 20,
        "total_pages": 5
    },
    "message": "ok"
}

# 无数据操作（删除等）
{
    "data": null,
    "message": "删除成功"
}
```

### 2.2 错误响应

```python
{
    "error": {
        "code": "DIET_RECORD_NOT_FOUND",
        "message": "饮食记录不存在",
        "details": null  # 可选，校验错误时包含字段级错误
    }
}
```

### 2.3 校验错误响应

```python
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求参数校验失败",
        "details": [
            {"field": "weight", "message": "体重必须在 30-300 kg 之间"},
            {"field": "date", "message": "日期不能是未来日期"}
        ]
    }
}
```

### 2.4 Pydantic 响应模型

```python
# app/schemas/common.py
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

class Pagination(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int

class ApiResponse(BaseModel, Generic[T]):
    data: T
    message: str = "ok"

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    pagination: Pagination
    message: str = "ok"

class ErrorDetail(BaseModel):
    field: str
    message: str

class ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[list[ErrorDetail]] = None

class ErrorResponse(BaseModel):
    error: ErrorBody
```

## 3. HTTP 状态码

| 状态码 | 使用场景 |
|--------|---------|
| 200 | 查询成功、更新成功、删除成功 |
| 201 | 创建成功 |
| 400 | 请求参数校验失败 |
| 401 | 未认证（Token 缺失或过期） |
| 403 | 无权限（访问他人数据） |
| 404 | 资源不存在 |
| 409 | 资源冲突（如已存在活跃计划） |
| 422 | 业务校验失败（如体重超出合理范围） |
| 500 | 服务器内部错误 |
| 503 | 外部服务不可用（LLM 调用失败） |

## 4. 业务错误码

错误码格式：`{MODULE}_{ERROR_TYPE}`，全大写，下划线分隔。

### 4.1 通用错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 请求参数校验失败 |
| `UNAUTHORIZED` | 401 | 未认证 |
| `FORBIDDEN` | 403 | 无权限 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `INTERNAL_ERROR` | 500 | 内部错误 |
| `LLM_SERVICE_UNAVAILABLE` | 503 | LLM 服务不可用 |

### 4.2 模块错误码

| 模块 | 错误码 | 说明 |
|------|--------|------|
| 用户 | `USER_NOT_FOUND` | 用户不存在 |
| 用户 | `USER_PROFILE_INCOMPLETE` | 健康档案未完善 |
| 认证 | `AUTH_INVALID_CREDENTIALS` | 邮箱或密码错误 |
| 认证 | `AUTH_EMAIL_EXISTS` | 邮箱已注册 |
| 认证 | `AUTH_ACCOUNT_LOCKED` | 账户已锁定（5 次失败） |
| 认证 | `AUTH_TOKEN_EXPIRED` | Token 已过期 |
| 饮食 | `DIET_RECORD_NOT_FOUND` | 饮食记录不存在 |
| 饮食 | `DIET_PARSE_FAILED` | AI 解析失败 |
| 饮食 | `DIET_RECORD_LIMIT_EXCEEDED` | 单条记录食物条目超过 20 个 |
| 身体 | `BODY_RECORD_NOT_FOUND` | 身体数据记录不存在 |
| 身体 | `BODY_VALUE_OUT_OF_RANGE` | 数值超出合理范围 |
| 计划 | `PLAN_NOT_FOUND` | 计划不存在 |
| 计划 | `PLAN_ALREADY_ACTIVE` | 已有活跃计划 |
| 计划 | `PLAN_DURATION_INVALID` | 计划周期不合法（1-24 周） |
| 计划 | `PLAN_CALORIES_BELOW_BMR` | 每日热量低于基础代谢 |
| AI | `AI_MEMORY_EXTRACTION_FAILED` | 记忆提取失败 |
| AI | `AI_SUGGESTION_GENERATION_FAILED` | 建议生成失败 |
| AI | `AI_SUGGESTION_NOT_FOUND` | 建议不存在 |
| 知识库 | `KNOWLEDGE_FOOD_NOT_FOUND` | 食物不存在 |

## 5. 分页策略

V1 使用 offset-based 分页（简单直观，适合数据量不大的场景）。

### 5.1 请求参数

```
GET /api/v1/diet/records?page=1&page_size=20&sort_by=created_at&sort_order=desc
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码，从 1 开始 |
| `page_size` | int | 20 | 每页条数，最大 100 |
| `sort_by` | string | `created_at` | 排序字段 |
| `sort_order` | string | `desc` | 排序方向：`asc` / `desc` |

### 5.2 响应格式

见 2.1 节列表资源响应格式。

## 6. 请求校验策略

- 所有请求体通过 Pydantic 模型自动校验
- 路径参数 `{id}` 统一使用 UUID 格式
- 日期参数使用 ISO 8601 格式：`2024-01-15`
- 日期时间参数使用 ISO 8601 带时区：`2024-01-15T08:30:00Z`
- 数值范围在 Pydantic 模型中用 `Field(ge=, le=)` 约束
- 枚举值使用 Python Enum 类型

## 7. API 端点汇总

### 7.1 认证模块 `/api/v1/auth/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/auth/register` | 注册 | 否 |
| POST | `/auth/login` | 登录 | 否 |
| POST | `/auth/logout` | 登出 | 是 |
| POST | `/auth/refresh` | 刷新 Token | 是 |

### 7.2 用户模块 `/api/v1/users/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/users/me` | 获取当前用户信息 | 是 |
| POST | `/users/me/onboarding` | 一次性提交 Onboarding 全量数据 | 是 |
| PUT | `/users/me/profile` | 更新健康档案 | 是 |
| PUT | `/users/me/preferences` | 更新饮食偏好 | 是 |
| PUT | `/users/me/health-info` | 更新健康信息 | 是 |
| PUT | `/users/me/settings` | 更新用户设置 | 是 |

### 7.3 饮食模块 `/api/v1/diet/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/diet/records` | 创建饮食记录 | 是 |
| GET | `/diet/records` | 查询记录列表 | 是 |
| GET | `/diet/records/{id}` | 记录详情 | 是 |
| PUT | `/diet/records/{id}` | 修改记录 | 是 |
| DELETE | `/diet/records/{id}` | 删除记录 | 是 |
| POST | `/diet/parse` | AI 解析饮食描述（不保存） | 是 |
| GET | `/diet/daily-summary` | 每日营养汇总 | 是 |
| GET | `/diet/weekly-summary` | 每周营养汇总 | 是 |

### 7.4 身体数据模块 `/api/v1/body/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/body/weight` | 记录体重 | 是 |
| GET | `/body/weight` | 体重记录列表 | 是 |
| PUT | `/body/weight/{id}` | 修改体重记录 | 是 |
| DELETE | `/body/weight/{id}` | 删除体重记录 | 是 |
| POST | `/body/circumference` | 记录体围 | 是 |
| GET | `/body/circumference` | 体围记录列表 | 是 |
| POST | `/body/sleep` | 记录睡眠 | 是 |
| GET | `/body/sleep` | 睡眠记录列表 | 是 |
| POST | `/body/exercise` | 记录运动 | 是 |
| GET | `/body/exercise` | 运动记录列表 | 是 |
| POST | `/body/water` | 记录饮水 | 是 |
| GET | `/body/water` | 饮水记录列表 | 是 |
| POST | `/body/bowel` | 记录排便 | 是 |
| GET | `/body/bowel` | 排便记录列表 | 是 |
| GET | `/body/trends` | 趋势数据 | 是 |
| GET | `/body/latest` | 各类型最新值 | 是 |

### 7.5 计划模块 `/api/v1/plans/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/plans` | 创建计划 | 是 |
| GET | `/plans` | 计划列表 | 是 |
| GET | `/plans/{id}` | 计划详情 | 是 |
| PUT | `/plans/{id}` | 更新计划 | 是 |
| DELETE | `/plans/{id}` | 终止计划 | 是 |
| POST | `/plans/{id}/check-ins` | 打卡 | 是 |
| GET | `/plans/{id}/progress` | 进度统计 | 是 |
| GET | `/plans/{id}/execution` | 执行记录列表 | 是 |

### 7.6 AI 对话模块 `/api/v1/ai/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/ai/chat` | 发送消息（对话入口） | 是 |
| GET | `/ai/chat/history` | 对话历史 | 是 |
| DELETE | `/ai/chat/sessions/{id}` | 删除对话会话 | 是 |

### 7.7 AI 建议模块 `/api/v1/suggestions/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/suggestions/daily` | 每日建议 | 是 |
| GET | `/suggestions/meal` | 餐食建议 | 是 |
| GET | `/suggestions/insights` | 健康洞察 | 是 |
| POST | `/suggestions/{id}/feedback` | 建议反馈 | 是 |

### 7.8 知识库模块 `/api/v1/knowledge/`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/knowledge/foods/search` | 食物搜索 | 是 |
| GET | `/knowledge/foods/{id}` | 食物详情 | 是 |
