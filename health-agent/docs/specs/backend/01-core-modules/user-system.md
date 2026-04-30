# 用户系统模块

> 本文档定义用户系统模块的完整后端实现规范，包括 API 端点、Pydantic 数据模型、业务逻辑、Service 接口和模块依赖。
>
> 实现依据：`docs/prd/v1/01-user-system.md`，`00-architecture/overview.md`，`00-architecture/auth.md`

---

## 1. 模块职责

- 用户注册 / 登录 / 登出（委托 Supabase Auth，具体实现见 `00-architecture/auth.md`）
- 健康档案管理（身高、体重、年龄、性别、目标、活动水平）
- 饮食偏好管理（饮食类型、过敏原、禁忌食物、不喜欢的食物）
- 健康信息管理（疾病、用药、医疗限制）
- 用户设置管理（交互模式）

本模块不处理认证流程本身（注册/登录/Token），认证由 `auth` 模块负责。本模块聚焦于认证后的用户数据管理。

---

## 2. API 端点

所有端点必须认证。基础路径：`/api/v1/users/`。

| 方法 | 路径 | 说明 | 请求体 | 响应体 |
|------|------|------|--------|--------|
| GET | `/users/me` | 获取当前用户完整信息 | 无 | `UserFullResponse` |
| PUT | `/users/me/profile` | 更新健康档案 | `UserProfileUpdate` | `UserProfileResponse` |
| PUT | `/users/me/preferences` | 更新饮食偏好 | `UserPreferencesUpdate` | `UserPreferencesResponse` |
| PUT | `/users/me/health-info` | 更新健康信息 | `UserHealthInfoUpdate` | `UserHealthInfoResponse` |
| PUT | `/users/me/settings` | 更新用户设置 | `UserSettingsUpdate` | `UserSettingsResponse` |

### 2.1 路由定义

```python
# app/api/v1/users.py
from fastapi import APIRouter, Depends
from app.schemas.user import (
    UserFullResponse, UserProfileUpdate, UserProfileResponse,
    UserPreferencesUpdate, UserPreferencesResponse,
    UserHealthInfoUpdate, UserHealthInfoResponse,
    UserSettingsUpdate, UserSettingsResponse,
)
from app.schemas.common import ApiResponse
from app.services.user_service import UserService
from app.dependencies import get_current_user, get_user_service
from app.schemas.auth import CurrentUser

router = APIRouter()

@router.get("/me", response_model=ApiResponse[UserFullResponse])
async def get_current_user_info(
    user: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """获取当前用户完整信息（档案 + 偏好 + 健康信息 + 设置）"""
    return await service.get_full_profile(user.id)

@router.put("/me/profile", response_model=ApiResponse[UserProfileResponse])
async def update_profile(
    data: UserProfileUpdate,
    user: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """更新健康档案，未传字段保持不变"""
    return await service.update_profile(user.id, data)

@router.put("/me/preferences", response_model=ApiResponse[UserPreferencesResponse])
async def update_preferences(
    data: UserPreferencesUpdate,
    user: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """更新饮食偏好"""
    return await service.update_preferences(user.id, data)

@router.put("/me/health-info", response_model=ApiResponse[UserHealthInfoResponse])
async def update_health_info(
    data: UserHealthInfoUpdate,
    user: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """更新健康信息"""
    return await service.update_health_info(user.id, data)

@router.put("/me/settings", response_model=ApiResponse[UserSettingsResponse])
async def update_settings(
    data: UserSettingsUpdate,
    user: CurrentUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """更新用户设置"""
    return await service.update_settings(user.id, data)
```

---

## 3. 数据模型（Pydantic Schemas）

所有 schema 定义在 `app/schemas/user.py`。

### 3.1 枚举类型

```python
# app/schemas/user.py
from enum import Enum

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class ActivityLevel(str, Enum):
    sedentary = "sedentary"      # 久坐：办公室工作，很少运动
    light = "light"              # 轻度：每周运动 1-3 次
    moderate = "moderate"        # 中度：每周运动 3-5 次
    heavy = "heavy"              # 重度：每周运动 6-7 次或体力劳动

class DietType(str, Enum):
    normal = "normal"            # 无特殊偏好
    vegetarian = "vegetarian"    # 素食（不吃肉）
    vegan = "vegan"              # 纯素（不吃任何动物制品）
    keto = "keto"                # 生酮饮食
    low_carb = "low_carb"       # 低碳水
    low_fat = "low_fat"         # 低脂
    mediterranean = "mediterranean"  # 地中海饮食

class InteractionMode(str, Enum):
    efficiency = "efficiency"    # 高效模式：简洁回复，直接给结论
    confirmation = "confirmation"  # 确认模式：操作前确认
    learning = "learning"        # 学习模式：附带解释和建议
```

### 3.2 请求模型

所有 PUT 端点的字段必须全部为 Optional，未传字段保持不变（符合 `api-design.md` 规范）。

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from uuid import UUID

class UserProfileUpdate(BaseModel):
    """健康档案更新请求"""
    nickname: Optional[str] = Field(None, min_length=2, max_length=20)
    gender: Optional[Gender] = None
    birth_date: Optional[date] = None
    height: Optional[float] = Field(None, ge=100, le=250, description="身高，单位 cm")
    current_weight: Optional[float] = Field(None, ge=30, le=300, description="当前体重，单位 kg")
    target_weight: Optional[float] = Field(None, ge=30, le=300, description="目标体重，单位 kg")
    activity_level: Optional[ActivityLevel] = None

class UserPreferencesUpdate(BaseModel):
    """饮食偏好更新请求"""
    diet_type: Optional[DietType] = None
    allergies: Optional[list[str]] = Field(None, max_length=20, description="过敏原列表")
    forbidden_foods: Optional[list[str]] = Field(None, max_length=50, description="禁忌食物列表")
    disliked_foods: Optional[list[str]] = Field(None, max_length=50, description="不喜欢的食物列表")

class UserHealthInfoUpdate(BaseModel):
    """健康信息更新请求"""
    diseases: Optional[list[str]] = Field(None, max_length=20, description="疾病列表")
    medications: Optional[str] = Field(None, max_length=500, description="正在服用的药物")
    medical_restrictions: Optional[str] = Field(None, max_length=500, description="医嘱或饮食限制")

class UserSettingsUpdate(BaseModel):
    """用户设置更新请求"""
    interaction_mode: Optional[InteractionMode] = None
```

### 3.3 响应模型

```python
class UserProfileResponse(BaseModel):
    """健康档案响应"""
    nickname: Optional[str] = None
    gender: Optional[Gender] = None
    birth_date: Optional[date] = None
    height: Optional[float] = None
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    profile_completeness: float = Field(description="档案完整度，0.0-1.0")

class UserPreferencesResponse(BaseModel):
    """饮食偏好响应"""
    diet_type: Optional[DietType] = None
    allergies: list[str] = []
    forbidden_foods: list[str] = []
    disliked_foods: list[str] = []

class UserHealthInfoResponse(BaseModel):
    """健康信息响应"""
    diseases: list[str] = []
    medications: Optional[str] = None
    medical_restrictions: Optional[str] = None

class UserSettingsResponse(BaseModel):
    """用户设置响应"""
    interaction_mode: InteractionMode = InteractionMode.confirmation

class UserFullResponse(BaseModel):
    """用户完整信息响应（GET /users/me）"""
    id: UUID
    email: str
    profile: UserProfileResponse
    preferences: UserPreferencesResponse
    health_info: UserHealthInfoResponse
    settings: UserSettingsResponse
```

---

## 4. 业务逻辑

### 4.1 注册时初始化

用户注册成功后（由 `auth_service` 触发），必须在 `health_profiles` 表创建一条空记录：

```python
# 由 auth_service.register() 调用
await user_service.create_empty_profile(user_id)
```

- `health_profiles` 所有业务字段初始值为 `NULL`
- `interaction_mode` 默认值为 `confirmation`
- 禁止在注册流程中要求填写档案字段

### 4.2 档案完整度计算

AI 个性化功能（饮食建议、计划生成等）依赖用户档案数据。必须提供档案完整度检查：

```python
PROFILE_REQUIRED_FIELDS = [
    "nickname", "gender", "birth_date",
    "height", "current_weight", "target_weight", "activity_level",
]

def calculate_completeness(profile: HealthProfile) -> float:
    """计算档案完整度，返回 0.0-1.0"""
    filled = sum(
        1 for field in PROFILE_REQUIRED_FIELDS
        if getattr(profile, field) is not None
    )
    return filled / len(PROFILE_REQUIRED_FIELDS)
```

- 完整度 < 1.0 时，AI 功能可正常使用但必须在响应中附带提示
- 禁止因档案不完整而阻断核心功能

### 4.3 档案更新触发记忆同步

用户更新健康档案后，必须通知 `memory_service` 更新 AI 记忆：

```python
async def update_profile(self, user_id: UUID, data: UserProfileUpdate):
    # 1. 更新数据库
    profile = await self.repo.update_profile(user_id, data)
    # 2. 通知记忆服务（异步，不阻塞响应）
    await self.memory_service.on_profile_updated(user_id, data)
    return profile
```

触发条件：`profile`、`preferences`、`health_info` 三个端点的更新操作都必须触发记忆同步。

### 4.4 数据验证规则

| 字段 | 验证规则 | 错误码 |
|------|---------|--------|
| `nickname` | 2-20 字符 | `VALIDATION_ERROR` |
| `height` | 100-250 cm | `VALIDATION_ERROR` |
| `current_weight` | 30-300 kg | `VALIDATION_ERROR` |
| `target_weight` | 30-300 kg | `VALIDATION_ERROR` |
| `birth_date` | 不能是未来日期，不能早于 1900-01-01 | `VALIDATION_ERROR` |
| `allergies` | 列表最多 20 项 | `VALIDATION_ERROR` |
| `forbidden_foods` | 列表最多 50 项 | `VALIDATION_ERROR` |
| `disliked_foods` | 列表最多 50 项 | `VALIDATION_ERROR` |
| `medications` | 最多 500 字符 | `VALIDATION_ERROR` |
| `medical_restrictions` | 最多 500 字符 | `VALIDATION_ERROR` |

密码验证（在 `auth` 模块处理）：
- 最少 8 位字符
- 必须包含字母和数字
- 连续登录失败 5 次，锁定账户 15 分钟

---

## 5. 数据库模型

数据库表定义见 `03-shared/database-schema.md`。本模块涉及的表：

| 表名 | 说明 | 所属 |
|------|------|------|
| `auth.users` | Supabase Auth 管理的用户表 | Supabase 托管，禁止直接操作 |
| `health_profiles` | 健康档案（基础信息） | 本模块管理 |
| `user_preferences` | 饮食偏好 | 本模块管理 |
| `user_health_info` | 健康信息 | 本模块管理 |
| `user_settings` | 用户设置 | 本模块管理 |

### 5.1 SQLAlchemy 模型

```python
# app/db/models/user.py
from sqlalchemy import Column, String, Float, Date, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.db.base import Base, TimestampMixin

class HealthProfile(Base, TimestampMixin):
    """健康档案 — 基础身体信息"""
    __tablename__ = "health_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    nickname = Column(String(20), nullable=True)
    gender = Column(String(10), nullable=True)          # male / female / other
    birth_date = Column(Date, nullable=True)
    height = Column(Float, nullable=True)                # cm
    current_weight = Column(Float, nullable=True)        # kg
    target_weight = Column(Float, nullable=True)         # kg
    activity_level = Column(String(20), nullable=True)   # sedentary / light / moderate / heavy

class UserPreference(Base, TimestampMixin):
    """饮食偏好"""
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    diet_type = Column(String(20), server_default="normal")
    allergies = Column(ARRAY(String), server_default="{}")
    forbidden_foods = Column(ARRAY(String), server_default="{}")
    disliked_foods = Column(ARRAY(String), server_default="{}")

class UserHealthInfo(Base, TimestampMixin):
    """健康信息"""
    __tablename__ = "user_health_info"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    diseases = Column(ARRAY(String), server_default="{}")
    medications = Column(Text, nullable=True)
    medical_restrictions = Column(Text, nullable=True)

class UserSetting(Base, TimestampMixin):
    """用户设置"""
    __tablename__ = "user_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    interaction_mode = Column(String(20), server_default="confirmation")
```

---

## 6. Service 接口

```python
# app/services/user_service.py
from uuid import UUID
from app.schemas.user import (
    UserProfileUpdate, UserProfileResponse,
    UserPreferencesUpdate, UserPreferencesResponse,
    UserHealthInfoUpdate, UserHealthInfoResponse,
    UserSettingsUpdate, UserSettingsResponse,
    UserFullResponse,
)
from app.db.repositories.user_repo import UserRepository
from app.services.memory_service import MemoryService

class UserService:
    def __init__(self, repo: UserRepository, memory_service: MemoryService):
        self.repo = repo
        self.memory_service = memory_service

    async def create_empty_profile(self, user_id: UUID) -> None:
        """注册时创建空档案记录。由 auth_service 调用。"""
        ...

    async def get_full_profile(self, user_id: UUID) -> UserFullResponse:
        """获取用户完整信息（档案 + 偏好 + 健康信息 + 设置）。
        若 health_profiles 记录不存在，抛出 USER_NOT_FOUND。"""
        ...

    async def update_profile(self, user_id: UUID, data: UserProfileUpdate) -> UserProfileResponse:
        """更新健康档案。更新后触发 memory_service.on_profile_updated()。"""
        ...

    async def update_preferences(self, user_id: UUID, data: UserPreferencesUpdate) -> UserPreferencesResponse:
        """更新饮食偏好。更新后触发 memory_service.on_profile_updated()。"""
        ...

    async def update_health_info(self, user_id: UUID, data: UserHealthInfoUpdate) -> UserHealthInfoResponse:
        """更新健康信息。更新后触发 memory_service.on_profile_updated()。"""
        ...

    async def update_settings(self, user_id: UUID, data: UserSettingsUpdate) -> UserSettingsResponse:
        """更新用户设置。不触发记忆同步。"""
        ...

    async def get_profile_completeness(self, user_id: UUID) -> float:
        """返回档案完整度 0.0-1.0。供其他模块调用。"""
        ...

    async def get_profile_for_ai(self, user_id: UUID) -> dict:
        """返回 AI 上下文所需的用户档案摘要。供 ai_chat_service、suggestion_service 调用。"""
        ...
```

### 6.1 Repository 接口

```python
# app/db/repositories/user_repo.py
from app.db.repositories.base import BaseRepository
from app.db.models.user import HealthProfile

class UserRepository(BaseRepository):
    async def get_by_user_id(self, user_id: UUID) -> HealthProfile | None:
        """根据 user_id 查询档案"""
        ...

    async def create_empty(self, user_id: UUID) -> HealthProfile:
        """创建空档案记录"""
        ...

    async def update_fields(self, user_id: UUID, fields: dict) -> HealthProfile:
        """更新指定字段（仅更新非 None 的字段）"""
        ...
```

---

## 7. 模块依赖

### 7.1 本模块依赖

| 依赖模块 | 用途 |
|---------|------|
| `auth`（Supabase Auth） | JWT 验证、`CurrentUser` 提取 |
| `memory_service` | 档案更新后通知 AI 记忆系统同步用户画像 |

### 7.2 依赖本模块的模块

| 模块 | 调用接口 | 用途 |
|------|---------|------|
| `auth_service` | `create_empty_profile()` | 注册时初始化档案 |
| `ai_chat_service` | `get_profile_for_ai()` | 对话时获取用户上下文 |
| `suggestion_service` | `get_profile_for_ai()` | 生成个性化建议 |
| `diet_service` | `get_profile_for_ai()` | 饮食解析时参考偏好和限制 |
| `plan_service` | `get_profile_completeness()` | 创建计划前检查档案完整度 |

---

## 8. 实现约束

1. 所有档案字段必须为 Optional（支持渐进式完善），禁止在注册时强制填写
2. PUT 请求中未传的字段保持数据库原值不变，禁止置为 NULL
3. 数值范围验证必须在 Pydantic 层完成（`Field(ge=, le=)`），禁止在 service 层重复校验
4. `health_profiles` 表与 `auth.users` 通过 `user_id` 关联，禁止在本模块直接操作 `auth.users` 表
5. 密码相关逻辑（强度验证、登录失败锁定）由 `auth` 模块处理，本模块禁止涉及密码
6. 列表字段（`allergies`、`forbidden_foods`、`disliked_foods`、`diseases`）使用 PostgreSQL `ARRAY` 类型存储
7. `interaction_mode` 默认值为 `confirmation`，前端未设置时使用此默认值
8. `get_profile_for_ai()` 返回的数据必须脱敏（不含 email、user_id），仅包含 AI 推理所需的健康信息
