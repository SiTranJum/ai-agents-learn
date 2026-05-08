# API 接口契约（前后端共享真相源）

> **定位**：本文档是前后端接口对齐的**唯一真相源**。后端 Pydantic Schema 和前端 TS 类型均以本文档为准。
>
> 改接口 → 先改本文档 → 再改两端代码。
>
> 后端详细 API 规范（URL 设计、分页、错误码体系等）见 `docs/specs/backend/00-architecture/api-design.md`。
> 本文档只定义**前后端对接所需的响应结构与字段级契约**。

---

## 1. 统一响应信封

前端 `apiClient`（`src/core/api/client.ts`）已实现自动剥壳：
- 成功时返回 `body.data`（裸 T）；
- 错误时抛出 `ApiError { status, code, message }`。

前端 Service 层拿到的永远是**裸数据**，不需要处理信封。

### 1.1 成功响应

```jsonc
// 单资源
{ "data": { ... }, "message": "ok" }

// 分页列表
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

// 无数据操作（如删除）
{ "data": null, "message": "删除成功" }
```

### 1.2 字段命名约定

| 层 | 风格 | 示例 |
|---|---|---|
| 后端 JSON（HTTP 传输） | **snake_case** | `birth_date`、`current_weight`、`goal_type` |
| 前端 TS 内部 | **camelCase** | `birthDate`、`currentWeight`、`goalType` |

前端在 Service 层的 `mapBackendToXxx` / `toXxxPayload` 函数中做转换。

### 1.3 错误响应

```jsonc
{
  "error": {
    "code": "DIET_RECORD_NOT_FOUND",   // 业务错误码，见 api-design.md §4
    "message": "饮食记录不存在",
    "details": null                     // 校验错误时为 [{ field, message }]
  }
}
```

前端 `handleResponse` 优先读 `body.error.code` / `body.error.message`。

---

## 2. 共享枚举

前后端必须使用**完全一致**的枚举值。

### 2.1 Gender

```
male | female | other
```

### 2.2 ActivityLevel

```
sedentary | light | moderate | heavy
```

### 2.3 GoalType

```
lose_fat | gain_muscle | maintain | healthy_diet
```

### 2.4 DietType

```
balanced | low_carb | high_protein | vegetarian | vegan | keto | low_fat | mediterranean
```

### 2.5 InteractionMode

```
efficiency | confirmation | learning
```

---

## 3. 用户模块接口契约

### 3.1 GET /users/me — 获取当前用户

**认证**：Bearer JWT（必须）

**响应**：`200 ApiResponse<UserFullResponse>`

```jsonc
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "onboarding_completed": false,
    "profile": {
      "nickname": "小明",          // string | null
      "gender": "male",           // Gender | null
      "birth_date": "1990-01-15", // ISO date string | null
      "height": 175.0,            // float | null, cm
      "current_weight": 70.0,     // float | null, kg
      "target_weight": 65.0,      // float | null, kg
      "activity_level": "moderate", // ActivityLevel | null
      "goal_type": "lose_fat",    // GoalType | null
      "daily_calorie_target": 1800, // int | null, kcal
      "profile_completeness": 0.85  // float 0.0~1.0
    },
    "preferences": {
      "diet_type": "balanced",    // DietType | null
      "allergies": ["花生"],       // string[]
      "forbidden_foods": ["动物内脏"], // string[]
      "disliked_foods": ["苦瓜"]   // string[]
    },
    "health_info": {
      "diseases": ["高血压"],      // string[]
      "medications": "降压药",     // string | null
      "medical_restrictions": "低盐饮食" // string | null
    },
    "settings": {
      "interaction_mode": "confirmation" // InteractionMode
    },
    "created_at": "2026-05-01T10:00:00Z", // ISO datetime | null
    "updated_at": "2026-05-08T14:30:00Z"  // ISO datetime | null
  },
  "message": "ok"
}
```

**前端映射关系**（`UserFullResponseRaw` → `AuthUserProfile`）：

| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|---|---|---|
| `id` | `id` | — |
| `email` | `email` | — |
| `onboarding_completed` | `onboardingCompleted` | — |
| `profile.nickname` | `nickname` | null → `''` |
| `profile.gender` | `gender` | null → `'male'` (默认) |
| `profile.birth_date` | `birthDate` | null → `''` |
| `profile.height` | `height` | null → `0` |
| `profile.current_weight` | `weight` | null → `0` |
| `profile.target_weight` | `targetWeight` | null → `undefined` |
| `profile.activity_level` | `activityLevel` | null → `'moderate'` |
| `profile.goal_type` | `goalType` | null → `'maintain'` |
| `profile.daily_calorie_target` | `dailyCalorieTarget` | null → `undefined` |
| `preferences.diet_type` | `dietType` | null → `undefined` |
| `preferences.allergies` | `allergies` | — |
| `preferences.forbidden_foods` | `restrictions` | **字段名不同** |
| `health_info.diseases` | `diseases` | — |
| `health_info.medications` | `medications` | null → `undefined` |
| `health_info.medical_restrictions` | `medicalAdvice` | **字段名不同** |
| `created_at` | `createdAt` | null → `new Date().toISOString()` |
| `updated_at` | `updatedAt` | null → `new Date().toISOString()` |

> **注意两个字段名差异**：
> - `forbidden_foods` ↔ `restrictions`（后端用"禁忌食物"，前端用"饮食限制"）
> - `medical_restrictions` ↔ `medicalAdvice`（后端用"医疗限制"，前端用"医嘱"）
>
> 这些差异在 `userService.ts` 的 mapping 函数中处理，不做统一重命名。

### 3.2 POST /users/me/onboarding — 提交 Onboarding

**认证**：Bearer JWT（必须）

**语义**：
- 一次性写入 Onboarding 全量数据（profile + preferences + health_info）
- 字段全部 Optional，未传字段不改数据库原值
- 成功后 `onboarding_completed = true`
- **幂等**：已完成用户再次调用等价于一次聚合更新

**请求体**：`OnboardingPayload`

```jsonc
{
  "profile": {                          // Optional，整段不传则不改
    "nickname": "小明",                  // Optional[str]
    "gender": "male",                   // Optional[Gender]
    "birth_date": "1990-01-15",         // Optional[date]
    "height": 175.0,                    // Optional[float] 100-250
    "current_weight": 70.0,             // Optional[float] 30-300
    "target_weight": 65.0,              // Optional[float] 30-300
    "activity_level": "moderate",       // Optional[ActivityLevel]
    "goal_type": "lose_fat",            // Optional[GoalType]
    "daily_calorie_target": 1800        // Optional[int] 500-6000
  },
  "preferences": {                      // Optional
    "diet_type": "balanced",            // Optional[DietType]
    "allergies": ["花生"],               // Optional[list[str]]
    "forbidden_foods": ["动物内脏"],      // Optional[list[str]]
    "disliked_foods": []                // Optional[list[str]]
  },
  "health_info": {                      // Optional
    "diseases": ["高血压"],              // Optional[list[str]]
    "medications": "降压药",             // Optional[str]
    "medical_restrictions": "低盐饮食"   // Optional[str]
  }
}
```

**响应**：`200 ApiResponse<UserFullResponse>`（结构同 §3.1）

**前端调用**：`userService.saveOnboarding(data)` → `toOnboardingPayload` 转换 → `apiClient.post('/users/me/onboarding', payload)`

### 3.3 PUT /users/me/profile — 更新健康档案

**认证**：Bearer JWT

**请求体**：`UserProfileUpdate`（字段同 §3.2 的 `profile` 段）

**响应**：`200 ApiResponse<UserProfileResponse>`

```jsonc
{
  "data": {
    "nickname": "小明",
    "gender": "male",
    "birth_date": "1990-01-15",
    "height": 175.0,
    "current_weight": 70.0,
    "target_weight": 65.0,
    "activity_level": "moderate",
    "goal_type": "lose_fat",
    "daily_calorie_target": 1800,
    "profile_completeness": 0.85
  },
  "message": "ok"
}
```

### 3.4 PUT /users/me/preferences — 更新饮食偏好

**认证**：Bearer JWT

**请求体**：`UserPreferencesUpdate`（字段同 §3.2 的 `preferences` 段）

**响应**：`200 ApiResponse<UserPreferencesResponse>`

```jsonc
{
  "data": {
    "diet_type": "balanced",
    "allergies": ["花生"],
    "forbidden_foods": ["动物内脏"],
    "disliked_foods": ["苦瓜"]
  },
  "message": "ok"
}
```

### 3.5 PUT /users/me/health-info — 更新健康信息

**认证**：Bearer JWT

**请求体**：`UserHealthInfoUpdate`（字段同 §3.2 的 `health_info` 段）

**响应**：`200 ApiResponse<UserHealthInfoResponse>`

```jsonc
{
  "data": {
    "diseases": ["高血压"],
    "medications": "降压药",
    "medical_restrictions": "低盐饮食"
  },
  "message": "ok"
}
```

### 3.6 PUT /users/me/settings — 更新用户设置

**认证**：Bearer JWT

**请求体**：`UserSettingsUpdate`

```jsonc
{ "interaction_mode": "efficiency" }
```

**响应**：`200 ApiResponse<UserSettingsResponse>`

```jsonc
{
  "data": {
    "interaction_mode": "efficiency"
  },
  "message": "ok"
}
```

---

## 4. 后续模块契约（待各模块开发时补充）

以下模块的端点汇总见 `api-design.md` §7。详细请求/响应字段在各模块进入开发阶段时添加到本文档。

- §5 饮食模块（`/diet/*`）
- §6 身体数据模块（`/body/*`）
- §7 计划模块（`/plans/*`）
- §8 AI 对话模块（`/ai/*`）
- §9 AI 建议模块（`/suggestions/*`）
- §10 知识库模块（`/knowledge/*`）

---

## 5. 变更日志

| 日期 | 变更 |
|------|------|
| 2026-05-08 | 初版：用户模块全量契约（§1-§3），统一信封、枚举、映射关系 |
