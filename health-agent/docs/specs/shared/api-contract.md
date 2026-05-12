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

- §5 饮食模块（`/diet/*`）✅ 已补充（**纯 CRUD**，自然语言解析改由 `/ai/chat` 承担）
- §6 身体数据模块（`/body/*`）✅ 已补充
- §7 计划模块（`/plans/*`）
- §8 AI 对话模块（`/ai/*`）✅ 草案
- §9 AI 建议模块（`/suggestions/*`）
- §10 知识库模块（`/knowledge/*`）✅ 已补充

---

## 5. 饮食模块接口契约（纯 CRUD）

> **架构变更（2026-05-09）**：
> - 原 `POST /diet/parse` 端点**已移除**。自然语言饮食解析改走 `/ai/chat` → diet subgraph，前端由对话 UI 承载"解析卡片 + 用户确认"的交互。
> - `POST /diet/records` 仅接受**结构化输入**（meal_type + date + foods[]），`input_text` / `image_url` 字段已下线。
> - 相关背景见 `docs/specs/backend/00-architecture/overview.md` §3.3 端点分类表。

### 5.1 共享枚举

`MealType`: `breakfast | lunch | dinner | snack`

`DataSource`: `database | api | llm_estimate`

> 前端 `DietRecord.status = empty | pending | recorded | editing` 是 UI 本地状态，不落库、不出现在后端响应中。

### 5.2 POST /diet/records — 创建饮食记录（结构化）

**认证**：Bearer JWT（必须）

**请求体**：`DietRecordCreate`

```jsonc
{
  "meal_type": "lunch",
  "date": "2026-05-09",
  "foods": [
    {
      "name": "米饭",
      "amount": 1,
      "unit": "碗",
      "amount_grams": 200,          // 可选，后端会按常见单位估算
      "cooking_method": null,
      "calories": 232,              // 可选；缺失时后端通过 RAG 查询补全
      "protein": 5.2,
      "fat": 0.6,
      "carbs": 51.8,
      "fiber": 0.6,
      "sodium": 4,
      "data_source": "database",
      "food_id": "uuid-or-null"
    }
  ]
}
```

**约束**：`foods` 必填且非空；单条记录最多 20 个食物项；`date` 不能是未来日期。

**响应**：`201 ApiResponse<DietRecordResponse>`

**自然语言入口**：想让 LLM 从文本/图片解析出 foods，前端调用 `/ai/chat` 并等待 diet subgraph 返回解析卡片消息，用户确认后前端用**本接口**提交。

### 5.3 GET /diet/records — 查询饮食记录列表

**查询参数**：`start_date` 必填，`end_date` 可选，`meal_type` 可选，`page` 默认 1，`page_size` 默认 20 最大 50。

**响应**：`200 PaginatedResponse<DietRecordResponse>`

### 5.4 GET /diet/records/{id} — 饮食记录详情

**响应**：`200 ApiResponse<DietRecordResponse>`；不存在返回 `404 DIET_RECORD_NOT_FOUND`。

### 5.5 PUT /diet/records/{id} — 更新饮食记录

**请求体**：`DietRecordUpdate`

```jsonc
{
  "meal_type": "dinner",
  "date": "2026-05-09",
  "foods": [{ "name": "苹果", "amount": 1, "unit": "个", "amount_grams": 200 }]
}
```

**响应**：`200 ApiResponse<DietRecordResponse>`

### 5.6 DELETE /diet/records/{id} — 删除饮食记录

软删除，幂等。

```jsonc
{ "data": null, "message": "删除成功" }
```

### 5.7 GET /diet/daily-summary — 每日汇总

**查询参数**：`date=YYYY-MM-DD`

**响应**：`200 ApiResponse<DailySummary>`

```jsonc
{
  "data": {
    "date": "2026-05-09",
    "meals": { "breakfast": [], "lunch": [], "dinner": [], "snack": [] },
    "total_nutrition": {
      "total_calories": 930,
      "total_protein": 50,
      "total_fat": 28,
      "total_carbs": 110,
      "total_fiber": null,
      "total_sodium": null
    },
    "target_nutrition": null,
    "completion_rate": {}
  },
  "message": "ok"
}
```

前端 `dietService.getDietByDate(date)` 推荐调用本接口。若某餐无记录，前端生成 `status: 'empty'` 卡片；`target_nutrition` 为空时可沿用 mock 默认目标 1800/225/90/60。

### 5.8 GET /diet/weekly-summary — 每周汇总

**查询参数**：`start_date=YYYY-MM-DD`

**响应**：`200 ApiResponse<WeeklySummary>`

### 5.9 字段模型

#### DietRecordResponse

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 记录 ID |
| `meal_type` | MealType | 餐次 |
| `date` | date | 记录日期 |
| `foods` | FoodItemResponse[] | 食物条目 |
| `nutrition_summary` | NutritionSummary | 单餐营养汇总 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

#### FoodItemResponse / ParsedFood

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 食物条目 ID，`ParsedFood` 中无此字段 |
| `name` | string | 食物名称 |
| `amount` | number | 用户表达的数量，如 `1` |
| `unit` | string | 用户表达的单位，如 `碗` |
| `amount_grams` | number | 标准克数，用于营养计算 |
| `cooking_method` | string \| null | 烹饪方式 |
| `calories` | number | 当前份量热量 kcal |
| `protein` | number | 当前份量蛋白质 g |
| `fat` | number | 当前份量脂肪 g |
| `carbs` | number | 当前份量碳水 g |
| `fiber` | number \| null | 当前份量膳食纤维 g |
| `sodium` | number \| null | 当前份量钠 mg |
| `data_source` | DataSource | 营养数据来源 |
| `food_id` | UUID \| null | 命中的知识库食物 ID |

#### NutritionSummary

| 字段 | 类型 | 说明 |
|---|---|---|
| `total_calories` | number | 总热量 kcal |
| `total_protein` | number | 总蛋白质 g |
| `total_fat` | number | 总脂肪 g |
| `total_carbs` | number | 总碳水 g |
| `total_fiber` | number \| null | 总膳食纤维 g |
| `total_sodium` | number \| null | 总钠 mg |

---

## 6. 身体数据模块接口契约

> **Phase 5 设计取舍**：身体数据模块是纯 CRUD，不触发 LLM。接口字段优先贴合前端 `features/data` mock：后端 HTTP 仍使用 snake_case，前端 Service 层映射为 camelCase。

### 6.1 共享枚举

`BodyRecordType`: `weight | measurement | sleep | exercise | water | bowel`

`TimeRange`: `7d | 30d | 90d | 365d`

`SleepQuality`: `excellent | good | fair | poor`

`BowelStatus`: `normal | constipation | diarrhea`

`MeasurementMetric`: `waist | hip | thigh | arm`

### 6.2 端点总览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/body/weight` | 创建体重记录 |
| GET | `/body/weight` | 分页查询体重记录 |
| PUT | `/body/weight/{id}` | 更新体重记录 |
| DELETE | `/body/weight/{id}` | 删除体重记录（软删除） |
| POST/GET/PUT/DELETE | `/body/measurement[/{id}]` | 围度记录 CRUD |
| POST/GET/PUT/DELETE | `/body/sleep[/{id}]` | 睡眠记录 CRUD |
| POST/GET/PUT/DELETE | `/body/exercise[/{id}]` | 运动记录 CRUD |
| POST/GET/PUT/DELETE | `/body/water[/{id}]` | 饮水记录；POST 为按日期累加，PUT 为设置累计值 |
| POST/GET/PUT/DELETE | `/body/bowel[/{id}]` | 排便记录 CRUD |
| GET | `/body/today?date=YYYY-MM-DD` | 指定日期 6 类记录聚合，前端 `getTodayRecords()` 对接 |
| GET | `/body/latest` | 每类最新一条记录聚合 |
| GET | `/body/trends` | 趋势数据 |

列表接口通用查询参数：`start_date` 可选，`end_date` 可选，`page` 默认 1，`page_size` 默认 20 最大 50。

### 6.3 请求体

#### WeightRecordCreate / Update

```jsonc
{
  "date": "2026-05-09",
  "weight": 66.0,
  "note": "空腹称重"
}
```

#### MeasurementRecordCreate / Update

```jsonc
{
  "date": "2026-05-09",
  "waist": 82.0,
  "hip": 94.0,
  "thigh": 54.0,
  "arm": 29.0,
  "note": null
}
```

约束：`waist | hip | thigh | arm` 至少一项非空。

#### SleepRecordCreate / Update

```jsonc
{
  "date": "2026-05-09",
  "bed_time": "23:30",
  "wake_time": "07:00",
  "quality": "good",
  "note": null
}
```

后端自动计算 `duration`（分钟），支持跨天睡眠。

#### ExerciseRecordCreate / Update

```jsonc
{
  "date": "2026-05-09",
  "type": "跑步",
  "duration": 30,
  "calories": 260,
  "note": null
}
```

`calories` 可选；缺失时后端按常见 MET 值粗略估算。

#### WaterRecordCreate / Update

```jsonc
{
  "date": "2026-05-09",
  "amount": 500,
  "target": 2000
}
```

语义：`POST /body/water` 的 `amount` 是“本次新增饮水量”，同日已有记录时累加；`PUT /body/water/{id}` 的 `amount` 是“当日累计饮水量”。

#### BowelRecordCreate / Update

```jsonc
{
  "date": "2026-05-09",
  "time": "09:30",
  "status": "normal",
  "note": null
}
```

### 6.4 响应模型

#### WeightRecordResponse

```jsonc
{
  "id": "uuid",
  "date": "2026-05-09",
  "weight": 66.0,
  "bmi": 22.8,
  "change": -0.2,
  "note": "空腹称重",
  "anomaly_warning": null,
  "created_at": "2026-05-09T08:00:00Z",
  "updated_at": "2026-05-09T08:00:00Z"
}
```

#### 其他记录响应字段

| 类型 | 字段 |
|---|---|
| `MeasurementRecordResponse` | `id`, `date`, `waist`, `hip`, `thigh`, `arm`, `note`, `anomaly_warning`, `created_at`, `updated_at` |
| `SleepRecordResponse` | `id`, `date`, `bed_time`, `wake_time`, `duration`, `quality`, `note`, `created_at`, `updated_at` |
| `ExerciseRecordResponse` | `id`, `date`, `type`, `duration`, `calories`, `note`, `created_at`, `updated_at` |
| `WaterRecordResponse` | `id`, `date`, `amount`, `target`, `created_at`, `updated_at` |
| `BowelRecordResponse` | `id`, `date`, `time`, `status`, `note`, `created_at`, `updated_at` |

### 6.5 GET /body/today — 今日记录聚合

**查询参数**：`date=YYYY-MM-DD`

**响应**：`200 ApiResponse<TodayRecords>`

```jsonc
{
  "data": {
    "weight": null,
    "measurement": null,
    "sleep": null,
    "exercise": null,
    "water": { "id": "uuid", "date": "2026-05-09", "amount": 1500, "target": 2000, "created_at": "...", "updated_at": "..." },
    "bowel": null
  },
  "message": "ok"
}
```

前端空卡片仍由 UI 本地根据 `null` 生成，不落库。

### 6.6 GET /body/trends — 趋势数据

**查询参数**：

- `type`: BodyRecordType，必填
- `period`: TimeRange，默认 `30d`
- `metric`: MeasurementMetric，可选；仅 `type=measurement` 时有效，默认 `waist`

**响应**：`200 ApiResponse<TrendResponse>`

```jsonc
{
  "data": {
    "type": "weight",
    "period": "30d",
    "metric": "weight",
    "data_points": [{ "date": "2026-05-09", "value": 66.0 }],
    "statistics": { "min": 66.0, "max": 70.0, "average": 68.1, "latest": 66.0, "change": -4.0 },
    "target": 60.0
  },
  "message": "ok"
}
```

趋势值约定：`weight=kg`，`measurement=cm`，`sleep=小时`，`exercise=分钟`，`water=ml`，`bowel=次/天`。`365d` 返回自然周均值点。

### 6.7 前端 mock/type 映射

| 后端字段 | 前端字段 |
|---|---|
| `bed_time` / `wake_time` | `bedTime` / `wakeTime` |
| `anomaly_warning` | `anomalyWarning` |
| `created_at` / `updated_at` | `createdAt` / `updatedAt` |
| `data_points` | `dataPoints` |

其他字段（如 `weight`, `amount`, `target`, `duration`, `quality`, `status`）与前端 mock 保持同名。

---

## 8. AI 对话模块接口契约（草案）

> Phase 6 正式落地。本节先锁定**契约轮廓**，供前端同步规划"对话式饮食记录"交互。

### 8.1 POST /ai/chat — 统一 AI 对话入口

**架构定位**：整个后端**唯一**的 LLM 触发端点。内部进入全局 ``chat_graph``，由条件边路由到各领域 subgraph（diet / body / plan / memory / suggestion / general）。

**请求体**：

```jsonc
{
  "session_id": "uuid-or-null",   // null 表示新会话
  "message": "午饭吃了一碗米饭和100g鸡胸肉",
  "context": {                     // 可选，前端附加的上下文
    "image_url": null,             // 当前消息附带图片 URL
    "referenced_date": "2026-05-09"
  }
}
```

**响应**（流式 SSE 或一次性 JSON，Phase 6 决定）：

```jsonc
{
  "data": {
    "session_id": "uuid",
    "messages": [
      {
        "role": "assistant",
        "content": "我识别到午餐有两项食物：",
        "cards": [                 // 结构化卡片；饮食分支返回解析卡片
          {
            "type": "diet_parse",
            "payload": {           // 字段与 §5.9 ParsedFood 一致
              "foods": [ ... ],
              "meal_type": "lunch",
              "confidence": 0.86,
              "suggested_date": "2026-05-09"
            },
            "actions": [
              { "kind": "confirm_create_diet_record" },
              { "kind": "edit_diet_items" }
            ]
          }
        ]
      }
    ]
  },
  "message": "ok"
}
```

**前端流程**（饮食场景）：

1. 用户在对话框输入自然语言/上传图片 → `POST /ai/chat`
2. 后端 Graph 路由到 diet subgraph，返回 `diet_parse` 卡片
3. 前端渲染卡片（食物项、置信度、缺项高亮）
4. 用户点击"确认保存" → 前端调用 `POST /diet/records`（§5.2），传入卡片中的 `foods`
5. 后端持久化后返回 `DietRecordResponse`；前端追加到当天记录列表

### 8.2 GET /ai/chat/history — 会话历史（草案）

Phase 6 定义。预期返回 `{ sessions: [{ id, title, last_message_at }] }`。

### 8.3 DELETE /ai/chat/sessions/{id} — 清除会话（草案）

Phase 6 定义。纯 CRUD。

---



## 10. 知识库模块接口契约

### 10.1 FoodCategory

```
grains | meat | vegetables | fruits | dairy | beverages | snacks | condiments | nuts | other
```

### 10.2 GET /knowledge/foods/search — 食物搜索

**查询参数**：`q` 必填，`limit` 可选 1-50 默认 10。

**响应**：`200 ApiResponse<FoodSearchResponse[]>`

```jsonc
{
  "data": [
    {
      "id": "uuid",
      "name": "米饭",
      "aliases": ["白米饭", "熟米饭"],
      "category": "grains",
      "calories_per_100g": 116.0,
      "match_score": 1.0
    }
  ],
  "message": "ok"
}
```

### 10.3 GET /knowledge/foods/{id} — 食物详情

**响应**：`200 ApiResponse<FoodDetailResponse>`；不存在返回 `404 FOOD_NOT_FOUND`。

### 10.4 字段模型

`FoodSearchResponse`: `id`, `name`, `aliases`, `category`, `calories_per_100g`, `match_score`。

`FoodDetailResponse`: `id`, `name`, `aliases`, `category`, `nutrition_per_100g`, `common_portions`, `data_source`。

---

## 11. 变更日志

| 日期 | 变更 |
|------|------|
| 2026-05-08 | 初版：用户模块全量契约（§1-§3），统一信封、枚举、映射关系 |
| 2026-05-08 | Phase 3：补充知识库模块契约（§10），包含食物搜索与详情接口 |
| 2026-05-09 | Phase 4：补充饮食模块契约（§5），包含 parse、records、summary 接口 |
| 2026-05-09 | 架构重构：饮食模块改为**纯 CRUD**；下线 `/diet/parse`；`POST /diet/records` 收窄为结构化输入；新增 §8 AI 对话模块契约草案（`/ai/chat` 作为唯一 LLM 入口） |
| 2026-05-09 | Phase 5：补充身体数据模块契约（§6），覆盖 6 类记录 CRUD、today/latest 聚合、trends 趋势与前端 mock 映射 |
