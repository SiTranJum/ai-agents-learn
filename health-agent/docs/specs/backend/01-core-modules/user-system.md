# 用户系统模块

> 本文档定义用户系统模块的完整后端实现规范，包括 API 端点、Pydantic 数据模型、业务逻辑、Service 接口和模块依赖。
>
> 实现依据：`docs/prd/v1/01-user-system.md`，`00-architecture/overview.md`，`00-architecture/auth.md`
>
> **接口契约真相源**：`docs/specs/shared/api-contract.md`（前后端共享，本文档与之保持一致）

---

## 1. 模块职责

- 用户注册 / 登录 / 登出（委托 Supabase Auth，具体实现见 `00-architecture/auth.md`）
- 健康档案管理（身高、体重、年龄、性别、目标、活动水平、健康目标、每日热量目标）
- 饮食偏好管理（饮食类型、过敏原、禁忌食物、不喜欢的食物）
- 健康信息管理（疾病、用药、医疗限制）
- 用户设置管理（交互模式）
- **Onboarding 聚合提交**（一次性写入全量档案数据）

本模块不处理认证流程本身（注册/登录/Token），认证由 `auth` 模块负责。本模块聚焦于认证后的用户数据管理。

---

## 2. API 端点

所有端点必须认证。基础路径：`/api/v1/users/`。

| 方法 | 路径 | 说明 | 请求体 | 响应体 |
|------|------|------|--------|--------|
| GET | `/users/me` | 获取当前用户完整信息 | 无 | `UserFullResponse` |
| POST | `/users/me/onboarding` | 一次性提交 Onboarding 全量数据 | `OnboardingPayload` | `UserFullResponse` |
| PUT | `/users/me/profile` | 更新健康档案 | `UserProfileUpdate` | `UserProfileResponse` |
| PUT | `/users/me/preferences` | 更新饮食偏好 | `UserPreferencesUpdate` | `UserPreferencesResponse` |
| PUT | `/users/me/health-info` | 更新健康信息 | `UserHealthInfoUpdate` | `UserHealthInfoResponse` |
| PUT | `/users/me/settings` | 更新用户设置 | `UserSettingsUpdate` | `UserSettingsResponse` |

---

## 3. 数据模型（Pydantic Schemas）

所有 schema 定义在 `app/schemas/user.py`。

### 3.1 枚举类型

```python
class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class ActivityLevel(str, Enum):
    sedentary = "sedentary"      # 久坐
    light = "light"              # 轻度
    moderate = "moderate"        # 中度
    heavy = "heavy"              # 重度

class GoalType(str, Enum):
    lose_fat = "lose_fat"        # 减脂
    gain_muscle = "gain_muscle"  # 增肌
    maintain = "maintain"        # 维持
    healthy_diet = "healthy_diet"  # 健康饮食

class DietType(str, Enum):
    balanced = "balanced"            # 均衡饮食（替代旧 normal）
    low_carb = "low_carb"           # 低碳水
    high_protein = "high_protein"   # 高蛋白
    vegetarian = "vegetarian"       # 素食
    vegan = "vegan"                 # 纯素
    keto = "keto"                   # 生酮
    low_fat = "low_fat"             # 低脂
    mediterranean = "mediterranean" # 地中海

class InteractionMode(str, Enum):
    efficiency = "efficiency"
    confirmation = "confirmation"
    learning = "learning"
```

### 3.2 请求模型

所有 PUT 端点的字段必须全部为 Optional，未传字段保持不变。

```python
class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = Field(None, min_length=2, max_length=20)
    gender: Optional[Gender] = None
    birth_date: Optional[date] = None
    height: Optional[float] = Field(None, ge=100, le=250)
    current_weight: Optional[float] = Field(None, ge=30, le=300)
    target_weight: Optional[float] = Field(None, ge=30, le=300)
    activity_level: Optional[ActivityLevel] = None
    goal_type: Optional[GoalType] = None
    daily_calorie_target: Optional[int] = Field(None, ge=500, le=6000)

class UserPreferencesUpdate(BaseModel):
    diet_type: Optional[DietType] = None
    allergies: Optional[list[str]] = Field(None, max_length=20)
    forbidden_foods: Optional[list[str]] = Field(None, max_length=50)
    disliked_foods: Optional[list[str]] = Field(None, max_length=50)

class UserHealthInfoUpdate(BaseModel):
    diseases: Optional[list[str]] = Field(None, max_length=20)
    medications: Optional[str] = Field(None, max_length=500)
    medical_restrictions: Optional[str] = Field(None, max_length=500)

class UserSettingsUpdate(BaseModel):
    interaction_mode: Optional[InteractionMode] = None

class OnboardingPayload(BaseModel):
    """聚合 profile + preferences + health_info 的一次性提交。"""
    profile: Optional[UserProfileUpdate] = None
    preferences: Optional[UserPreferencesUpdate] = None
    health_info: Optional[UserHealthInfoUpdate] = None
```

### 3.3 响应模型

```python
class UserProfileResponse(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[Gender] = None
    birth_date: Optional[date] = None
    height: Optional[float] = None
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    goal_type: Optional[GoalType] = None
    daily_calorie_target: Optional[int] = None
    profile_completeness: float  # 0.0-1.0

class UserPreferencesResponse(BaseModel):
    diet_type: Optional[DietType] = None
    allergies: list[str] = []
    forbidden_foods: list[str] = []
    disliked_foods: list[str] = []

class UserHealthInfoResponse(BaseModel):
    diseases: list[str] = []
    medications: Optional[str] = None
    medical_restrictions: Optional[str] = None

class UserSettingsResponse(BaseModel):
    interaction_mode: InteractionMode = InteractionMode.confirmation

class UserFullResponse(BaseModel):
    id: UUID
    email: str
    onboarding_completed: bool = False
    profile: UserProfileResponse
    preferences: UserPreferencesResponse
    health_info: UserHealthInfoResponse
    settings: UserSettingsResponse
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

---

## 4. 业务逻辑

### 4.1 注册时初始化

用户首次访问后端 API 时（JWT 校验通过但 `health_profiles` 中没有对应行），自动在四张表各创建一条空记录。

### 4.2 档案完整度计算

```python
PROFILE_REQUIRED_FIELDS = [
    "nickname", "gender", "birth_date",
    "height", "current_weight", "target_weight", "activity_level",
]
```

- 完整度 < 1.0 时，AI 功能可正常使用但必须在响应中附带提示
- 禁止因档案不完整而阻断核心功能

### 4.3 Onboarding 聚合提交

`POST /users/me/onboarding` 的业务逻辑：
1. 分片写入 profile / preferences / health_info（仅非 None 字段）
2. 置 `onboarding_completed = True`
3. 提交事务
4. 返回完整 `UserFullResponse`

幂等：已完成 onboarding 的用户再次调用，等价于一次聚合更新。

### 4.4 档案更新触发记忆同步

用户更新健康档案后，必须通知 `memory_service` 更新 AI 记忆（Phase 6 实现）。

### 4.5 数据验证规则

| 字段 | 验证规则 | 错误码 |
|------|---------|--------|
| `nickname` | 2-20 字符 | `VALIDATION_ERROR` |
| `height` | 100-250 cm | `VALIDATION_ERROR` |
| `current_weight` | 30-300 kg | `VALIDATION_ERROR` |
| `target_weight` | 30-300 kg | `VALIDATION_ERROR` |
| `daily_calorie_target` | 500-6000 kcal | `VALIDATION_ERROR` |
| `birth_date` | 不能是未来日期 | `VALIDATION_ERROR` |
| `allergies` | 列表最多 20 项 | `VALIDATION_ERROR` |
| `forbidden_foods` | 列表最多 50 项 | `VALIDATION_ERROR` |
| `disliked_foods` | 列表最多 50 项 | `VALIDATION_ERROR` |
| `medications` | 最多 500 字符 | `VALIDATION_ERROR` |
| `medical_restrictions` | 最多 500 字符 | `VALIDATION_ERROR` |

---

## 5. 数据库模型

数据库表定义见 `03-shared/database-schema.md`。本模块涉及的表：

| 表名 | 说明 |
|------|------|
| `auth.users` | Supabase Auth 管理，禁止直接操作 |
| `health_profiles` | 健康档案（基础信息 + 目标 + onboarding 状态） |
| `user_preferences` | 饮食偏好 |
| `user_health_info` | 健康信息 |
| `user_settings` | 用户设置 |

### 5.1 SQLAlchemy 模型

```python
class HealthProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "health_profiles"

    user_id = Column(UUID, unique=True, nullable=False, index=True)
    nickname = Column(String(20), nullable=True)
    gender = Column(String(10), nullable=True)
    birth_date = Column(Date, nullable=True)
    height = Column(Float, nullable=True)
    current_weight = Column(Float, nullable=True)
    target_weight = Column(Float, nullable=True)
    activity_level = Column(String(20), nullable=True)
    goal_type = Column(String(20), nullable=True)              # 新增
    daily_calorie_target = Column(Integer, nullable=True)      # 新增
    onboarding_completed = Column(Boolean, server_default="false")  # 新增

class UserPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_preferences"

    user_id = Column(UUID, unique=True, nullable=False, index=True)
    diet_type = Column(String(20), nullable=True)  # 改为 nullable（去掉旧 server_default "normal"）
    allergies = Column(ARRAY(String), server_default="{}")
    forbidden_foods = Column(ARRAY(String), server_default="{}")
    disliked_foods = Column(ARRAY(String), server_default="{}")

class UserHealthInfo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_health_info"
    # 无变化

class UserSetting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_settings"
    # 无变化
```

### 5.2 数据库迁移要点

需要生成 Alembic 迁移：
1. `health_profiles` 新增 `goal_type VARCHAR(20) NULL`
2. `health_profiles` 新增 `daily_calorie_target INTEGER NULL`
3. `health_profiles` 新增 `onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE`
4. `user_preferences.diet_type` 从 `NOT NULL DEFAULT 'normal'` 改为 `NULL`（已有数据中 `'normal'` 保留，后续可批量迁移为 `'balanced'` 或 `NULL`）

---

## 6. Service 接口

```python
class UserService:
    async def get_full_profile(self, user_id, *, email) -> UserFullResponse: ...
    async def complete_onboarding(self, user_id, *, email, payload) -> UserFullResponse: ...
    async def update_profile(self, user_id, data) -> UserProfileResponse: ...
    async def update_preferences(self, user_id, data) -> UserPreferencesResponse: ...
    async def update_health_info(self, user_id, data) -> UserHealthInfoResponse: ...
    async def update_settings(self, user_id, data) -> UserSettingsResponse: ...
    async def get_profile_completeness(self, user_id) -> float: ...
    async def get_profile_for_ai(self, user_id) -> dict: ...
```

---

## 7. 模块依赖

### 7.1 本模块依赖

| 依赖模块 | 用途 |
|---------|------|
| `auth`（Supabase Auth） | JWT 验证、`CurrentUser` 提取 |
| `memory_service`（Phase 6） | 档案更新后通知 AI 记忆系统同步用户画像 |

### 7.2 依赖本模块的模块

| 模块 | 调用接口 | 用途 |
|------|---------|------|
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
5. 列表字段使用 PostgreSQL `ARRAY` 类型存储
6. `interaction_mode` 默认值为 `confirmation`
7. `get_profile_for_ai()` 返回的数据必须脱敏（不含 email、user_id）
8. `DietType` 枚举已去掉旧值 `normal`，用 `balanced` 替代；数据库中已有 `normal` 值需兼容读取（service 层映射为 `balanced`）
