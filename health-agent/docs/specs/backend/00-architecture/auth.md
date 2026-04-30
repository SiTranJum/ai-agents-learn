# 认证授权方案

> 本文档定义后端认证授权的完整方案，包括 Supabase Auth 集成、JWT 验证流程、路由保护和数据隔离策略。
>
> 实现依据：`docs/prd/v1/01-user-system.md`，`00-architecture/overview.md`

---

## 1. 认证架构

### 1.1 方案选择

使用 Supabase Auth 作为认证服务，后端不自建用户认证系统。

- 注册/登录/Token 管理由 Supabase Auth 处理
- 后端只负责验证 JWT Token 和提取用户信息
- 用户密码不经过后端，直接由客户端与 Supabase Auth 交互

### 1.2 认证流程

```
客户端                    Supabase Auth              后端 API
  │                           │                        │
  │── 注册/登录 ──────────────▶│                        │
  │◀── access_token + ────────│                        │
  │    refresh_token           │                        │
  │                           │                        │
  │── API 请求 ───────────────────────────────────────▶│
  │   (Authorization: Bearer {access_token})           │
  │                           │                        │
  │                           │◀── 验证 JWT ───────────│
  │                           │── 验证结果 ────────────▶│
  │                           │                        │
  │◀── API 响应 ──────────────────────────────────────│
```

### 1.3 Token 说明

| Token | 有效期 | 用途 |
|-------|--------|------|
| `access_token` | 1 小时 | API 请求认证，JWT 格式 |
| `refresh_token` | 7 天 | 刷新 access_token |

## 2. JWT 验证

### 2.1 验证流程

后端收到请求后：

1. 从 `Authorization: Bearer {token}` 头提取 token
2. 使用 Supabase JWT Secret 验证签名
3. 检查 token 是否过期
4. 从 payload 中提取 `sub`（user_id）
5. 将 user_id 注入到请求上下文

### 2.2 实现方式

```python
# app/core/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """验证 JWT Token，返回 payload"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")
```

```python
# app/dependencies.py
from app.core.security import verify_token

async def get_current_user(payload: dict = Depends(verify_token)) -> CurrentUser:
    """从 JWT payload 中提取当前用户信息"""
    return CurrentUser(
        id=payload["sub"],
        email=payload.get("email"),
    )
```

### 2.3 CurrentUser 模型

```python
# app/schemas/auth.py
from pydantic import BaseModel
from uuid import UUID

class CurrentUser(BaseModel):
    id: UUID
    email: str | None = None
```

## 3. API 端点

### 3.1 注册

```
POST /api/v1/auth/register
```

请求体：

```python
class RegisterRequest(BaseModel):
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8, description="至少 8 位，包含字母和数字")
    nickname: str = Field(..., min_length=2, max_length=20)
```

处理流程：
1. 校验邮箱格式和密码强度
2. 调用 Supabase Auth 创建用户
3. 在 `health_profiles` 表创建空档案记录
4. 返回 access_token + refresh_token

响应：

```python
class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserBasic

class UserBasic(BaseModel):
    id: UUID
    email: str
    nickname: str
```

### 3.2 登录

```
POST /api/v1/auth/login
```

请求体：

```python
class LoginRequest(BaseModel):
    email: str
    password: str
```

处理流程：
1. 调用 Supabase Auth 验证凭据
2. 失败次数累计（5 次锁定 15 分钟）
3. 成功则返回 token

### 3.3 登出

```
POST /api/v1/auth/logout
认证：需要
```

处理流程：
1. 调用 Supabase Auth 撤销当前 session

### 3.4 刷新 Token

```
POST /api/v1/auth/refresh
```

请求体：

```python
class RefreshRequest(BaseModel):
    refresh_token: str
```

处理流程：
1. 调用 Supabase Auth 刷新 token
2. 返回新的 access_token + refresh_token

## 4. 路由保护

### 4.1 保护级别

| 级别 | 说明 | 端点 |
|------|------|------|
| 公开 | 无需认证 | `POST /auth/register`、`POST /auth/login` |
| 认证 | 需要有效 Token | 其他所有端点 |

V1 不实现角色权限（RBAC），所有认证用户权限相同。

### 4.2 路由注册

```python
# app/api/v1/router.py
from fastapi import APIRouter

# 公开路由
public_router = APIRouter()
public_router.include_router(auth_router, prefix="/auth", tags=["auth"])

# 需认证路由
protected_router = APIRouter(dependencies=[Depends(get_current_user)])
protected_router.include_router(users_router, prefix="/users", tags=["users"])
protected_router.include_router(diet_router, prefix="/diet", tags=["diet"])
protected_router.include_router(body_router, prefix="/body", tags=["body"])
protected_router.include_router(plans_router, prefix="/plans", tags=["plans"])
protected_router.include_router(ai_router, prefix="/ai", tags=["ai"])
protected_router.include_router(suggestions_router, prefix="/suggestions", tags=["suggestions"])
protected_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
```

## 5. 数据隔离

### 5.1 原则

所有业务数据表都包含 `user_id` 字段，所有查询自动 scope 到当前用户。

### 5.2 Repository 层实现

```python
# app/db/repositories/base.py
class BaseRepository:
    """所有 repository 的基类，自动注入 user_id 过滤"""

    def __init__(self, session: AsyncSession, user_id: UUID):
        self.session = session
        self.user_id = user_id

    async def get_by_id(self, model_class, id: UUID):
        """查询时自动附加 user_id 条件"""
        stmt = select(model_class).where(
            model_class.id == id,
            model_class.user_id == self.user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

### 5.3 安全保障

- Repository 基类强制 `user_id` 过滤，防止越权访问
- 创建记录时自动填充 `user_id`
- 更新/删除操作先查询确认归属，再执行操作
- 不提供跨用户查询的接口

## 6. Supabase Auth 客户端封装

```python
# app/integrations/supabase_auth/client.py
class SupabaseAuthClient:
    """封装 Supabase Auth REST API 调用"""

    def __init__(self, url: str, service_role_key: str):
        self.url = url
        self.headers = {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
        }

    async def sign_up(self, email: str, password: str) -> AuthResult:
        """注册新用户"""
        ...

    async def sign_in(self, email: str, password: str) -> AuthResult:
        """邮箱密码登录"""
        ...

    async def sign_out(self, access_token: str) -> None:
        """登出（撤销 session）"""
        ...

    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """刷新 Token"""
        ...

class AuthResult(BaseModel):
    access_token: str
    refresh_token: str
    user_id: UUID
    email: str
```
