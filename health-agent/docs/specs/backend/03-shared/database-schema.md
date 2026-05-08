# 数据库 Schema

> 本文档定义后端所有数据库表的完整 schema，包括字段定义、类型约束、索引设计和表间关系。所有模块 specs 中的数据模型以本文档为基准。
>
> 实现依据：各模块 PRD 文档，`00-architecture/overview.md`

---

## 1. 通用约定

### 1.1 主键和通用字段

所有业务表必须包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键，默认 `gen_random_uuid()` |
| `user_id` | UUID | 外键，关联 Supabase Auth 的 `auth.users.id` |
| `created_at` | TIMESTAMPTZ | 创建时间，默认 `now()` |
| `updated_at` | TIMESTAMPTZ | 更新时间，默认 `now()`，更新时自动刷新 |

支持软删除的表额外包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `deleted_at` | TIMESTAMPTZ | 软删除时间，NULL 表示未删除 |

### 1.2 时间处理

- 所有时间字段使用 `TIMESTAMPTZ`（带时区），存储为 UTC
- 日期字段使用 `DATE` 类型
- 客户端负责时区转换

### 1.3 向量字段

使用 pgvector 扩展，向量维度统一为 1024（text-embedding-v3）。

```sql
-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;
```

## 2. 用户相关表

### 2.1 health_profiles — 健康档案

```sql
CREATE TABLE health_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    nickname    VARCHAR(20),
    gender      VARCHAR(10),          -- male / female / other
    birth_date  DATE,
    height      DECIMAL(5,1),         -- cm, 100.0-250.0
    current_weight DECIMAL(5,1),      -- kg, 30.0-300.0
    target_weight  DECIMAL(5,1),      -- kg, 30.0-300.0
    activity_level VARCHAR(20),       -- sedentary / light / moderate / heavy
    goal_type      VARCHAR(20),       -- lose_fat / gain_muscle / maintain / healthy_diet
    daily_calorie_target INTEGER,     -- kcal, 500-6000
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_health_profiles_user_id ON health_profiles(user_id);
```

### 2.2 user_preferences — 饮食偏好

```sql
CREATE TABLE user_preferences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    diet_type       VARCHAR(20),  -- balanced/low_carb/high_protein/vegetarian/vegan/keto/low_fat/mediterranean (nullable)
    allergies       TEXT[] DEFAULT '{}',
    forbidden_foods TEXT[] DEFAULT '{}',
    disliked_foods  TEXT[] DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
```

### 2.3 user_health_info — 健康信息

```sql
CREATE TABLE user_health_info (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    diseases            TEXT[] DEFAULT '{}',
    medications         TEXT,
    medical_restrictions TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_user_health_info_user_id ON user_health_info(user_id);
```

### 2.4 user_settings — 用户设置

```sql
CREATE TABLE user_settings (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    interaction_mode VARCHAR(20) DEFAULT 'confirmation',  -- efficiency/confirmation/learning
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_user_settings_user_id ON user_settings(user_id);
```

## 3. 饮食相关表

### 3.1 diet_records — 饮食记录

```sql
CREATE TABLE diet_records (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    meal_type   VARCHAR(10) NOT NULL,  -- breakfast / lunch / dinner / snack
    date        DATE NOT NULL,
    input_text  TEXT,                   -- 用户原始输入
    image_url   TEXT,                   -- 图片 URL（V1 mock）
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ            -- 软删除
);

CREATE INDEX idx_diet_records_user_date ON diet_records(user_id, date);
CREATE INDEX idx_diet_records_user_meal ON diet_records(user_id, date, meal_type);
```

### 3.2 diet_items — 食物条目

```sql
CREATE TABLE diet_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id       UUID NOT NULL REFERENCES diet_records(id) ON DELETE CASCADE,
    food_name       VARCHAR(100) NOT NULL,
    amount          DECIMAL(8,1) NOT NULL,   -- 数量
    unit            VARCHAR(20) NOT NULL,     -- 单位（克/毫升/个/碗等）
    cooking_method  VARCHAR(50),              -- 烹饪方式
    calories        DECIMAL(8,1) NOT NULL,    -- kcal
    protein         DECIMAL(8,1) NOT NULL,    -- g
    fat             DECIMAL(8,1) NOT NULL,    -- g
    carbs           DECIMAL(8,1) NOT NULL,    -- g
    fiber           DECIMAL(8,1),             -- g
    sodium          DECIMAL(8,1),             -- mg
    data_source     VARCHAR(20) NOT NULL,     -- database / api / llm_estimate
    food_id         UUID REFERENCES foods(id), -- 关联知识库食物（可选）
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_diet_items_record_id ON diet_items(record_id);
```

## 4. 身体数据表

### 4.1 weight_records — 体重记录

```sql
CREATE TABLE weight_records (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    weight      DECIMAL(5,1) NOT NULL,  -- kg, 30.0-300.0
    date        DATE NOT NULL,
    note        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);

CREATE INDEX idx_weight_records_user_date ON weight_records(user_id, date);
```

### 4.2 circumference_records — 体围记录

```sql
CREATE TABLE circumference_records (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    waist       DECIMAL(5,1),   -- cm
    hip         DECIMAL(5,1),   -- cm
    thigh       DECIMAL(5,1),   -- cm
    arm         DECIMAL(5,1),   -- cm
    date        DATE NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);

CREATE INDEX idx_circumference_records_user_date ON circumference_records(user_id, date);
```

### 4.3 sleep_records — 睡眠记录

```sql
CREATE TABLE sleep_records (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    sleep_time  TIMESTAMPTZ NOT NULL,
    wake_time   TIMESTAMPTZ NOT NULL,
    quality     VARCHAR(10) NOT NULL,  -- good / fair / poor
    date        DATE NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sleep_records_user_date ON sleep_records(user_id, date);
```

### 4.4 exercise_records — 运动记录

```sql
CREATE TABLE exercise_records (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    exercise_type    VARCHAR(20) NOT NULL,  -- walking/running/cycling/swimming/gym/yoga/other
    duration_minutes INT NOT NULL,          -- 1-600
    note             TEXT,
    date             DATE NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_exercise_records_user_date ON exercise_records(user_id, date);
```

### 4.5 water_records — 饮水记录

```sql
CREATE TABLE water_records (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    amount_ml   INT NOT NULL,           -- 累计毫升
    date        DATE NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, date)               -- 每天一条，upsert 更新
);

CREATE INDEX idx_water_records_user_date ON water_records(user_id, date);
```

### 4.6 bowel_records — 排便记录

```sql
CREATE TABLE bowel_records (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    time        TIMESTAMPTZ NOT NULL,
    status      VARCHAR(10) NOT NULL,   -- normal / hard / soft / diarrhea
    date        DATE NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_bowel_records_user_date ON bowel_records(user_id, date);
```

## 5. AI 记忆表

### 5.1 memories — 长期记忆

```sql
CREATE TABLE memories (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    memory_type       VARCHAR(30) NOT NULL,
    -- food_preference / portion_habit / behavior_pattern /
    -- suggestion_feedback / health_goal / allergy / exercise_habit
    content           TEXT NOT NULL,
    embedding         vector(1024),          -- pgvector
    metadata          JSONB DEFAULT '{}',    -- 附加结构化数据
    quality_score     INT NOT NULL DEFAULT 0, -- 0-100
    status            VARCHAR(10) DEFAULT 'active',  -- active / pending / archived
    last_accessed     TIMESTAMPTZ,
    access_count      INT DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_user_type ON memories(user_id, memory_type);
CREATE INDEX idx_memories_user_status ON memories(user_id, status);
CREATE INDEX idx_memories_embedding ON memories
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 5.2 memory_summaries — 中期记忆摘要

```sql
CREATE TABLE memory_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    summary_content TEXT NOT NULL,
    key_facts       JSONB DEFAULT '[]',   -- ["fact1", "fact2", ...]
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_memory_summaries_user_period ON memory_summaries(user_id, period_start, period_end);
```

### 5.3 chat_messages — 对话历史

```sql
CREATE TABLE chat_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id  VARCHAR(50) NOT NULL,
    role        VARCHAR(10) NOT NULL,   -- user / assistant / system
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chat_messages_user_session ON chat_messages(user_id, session_id, created_at);
```

## 6. 知识库表

### 6.1 foods — 食物营养知识库

```sql
CREATE TABLE foods (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(100) NOT NULL,
    aliases           TEXT[] DEFAULT '{}',
    category          VARCHAR(20) NOT NULL,
    -- grains/meat/vegetables/fruits/dairy/beverages/snacks/condiments/nuts/other
    calories_per_100g DECIMAL(8,1) NOT NULL,
    protein_per_100g  DECIMAL(8,1) NOT NULL,
    fat_per_100g      DECIMAL(8,1) NOT NULL,
    carbs_per_100g    DECIMAL(8,1) NOT NULL,
    fiber_per_100g    DECIMAL(8,1),
    sodium_per_100g   DECIMAL(8,1),
    sugar_per_100g    DECIMAL(8,1),
    common_portions   JSONB DEFAULT '[]',
    -- [{"name": "一碗", "weight_grams": 200}, ...]
    data_source       VARCHAR(50) DEFAULT 'manual',
    embedding         vector(1024),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_foods_name ON foods(name);
CREATE INDEX idx_foods_category ON foods(category);
CREATE INDEX idx_foods_embedding ON foods
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

### 6.2 knowledge_docs — 健康建议知识库

```sql
CREATE TABLE knowledge_docs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(200) NOT NULL,
    content     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}',
    -- {"category": "...", "tags": [...], "target_users": [...], "source": "..."}
    embedding   vector(1024),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_knowledge_docs_metadata ON knowledge_docs USING gin(metadata);
CREATE INDEX idx_knowledge_docs_embedding ON knowledge_docs
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

## 7. 计划相关表

### 7.1 plans — 计划主表

```sql
CREATE TABLE plans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    plan_type       VARCHAR(30) NOT NULL,
    -- weight_loss / nutrition_adjustment / habit_formation
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    -- active / completed / terminated
    start_date      DATE NOT NULL,
    target_date     DATE NOT NULL,
    goal_description TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_plans_user_status ON plans(user_id, status);
```

### 7.2 plan_targets — 计划目标

```sql
CREATE TABLE plan_targets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id         UUID NOT NULL UNIQUE REFERENCES plans(id) ON DELETE CASCADE,
    daily_calories  INT,
    protein_target  DECIMAL(5,1),   -- g
    fat_target      DECIMAL(5,1),   -- g
    carbs_target    DECIMAL(5,1),   -- g
    weight_target   DECIMAL(5,1),   -- kg
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 7.3 plan_tasks — 计划任务

```sql
CREATE TABLE plan_tasks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id     UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    description VARCHAR(200) NOT NULL,
    frequency   VARCHAR(50),        -- "每天" / "每周3次"
    time_period VARCHAR(50),        -- "早餐" / "晚上"
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_plan_tasks_plan_id ON plan_tasks(plan_id);
```

### 7.4 plan_execution — 计划执行记录

```sql
CREATE TABLE plan_execution (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id           UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    date              DATE NOT NULL,
    calories_consumed DECIMAL(8,1),
    calories_target   DECIMAL(8,1),
    protein           DECIMAL(8,1),
    fat               DECIMAL(8,1),
    carbs             DECIMAL(8,1),
    status            VARCHAR(20) NOT NULL,  -- on_track / deviation / missed
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(plan_id, date)
);

CREATE INDEX idx_plan_execution_plan_date ON plan_execution(plan_id, date);
```

### 7.5 check_ins — 打卡记录

```sql
CREATE TABLE check_ins (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id     UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    task_id     UUID REFERENCES plan_tasks(id),
    date        DATE NOT NULL,
    completed   BOOLEAN NOT NULL DEFAULT false,
    note        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_check_ins_plan_date ON check_ins(plan_id, date);
```

## 8. 建议表

### 8.1 suggestions — AI 建议缓存

```sql
CREATE TABLE suggestions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    suggestion_type VARCHAR(30) NOT NULL,
    -- diet_advice / goal_advice / trend_advice / proactive_insight
    title           VARCHAR(200) NOT NULL,
    content         TEXT NOT NULL,
    basis           TEXT,               -- 建议依据说明
    priority        VARCHAR(10) DEFAULT 'medium',  -- high / medium / low
    user_feedback   VARCHAR(20),        -- helpful / not_helpful / dismissed
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_suggestions_user_type ON suggestions(user_id, suggestion_type);
CREATE INDEX idx_suggestions_user_expires ON suggestions(user_id, expires_at);
```

## 9. 表间关系（ER）

```
auth.users (Supabase 管理)
    │
    ├── 1:1 ── health_profiles
    ├── 1:1 ── user_preferences
    ├── 1:1 ── user_health_info
    ├── 1:1 ── user_settings
    │
    ├── 1:N ── diet_records
    │              └── 1:N ── diet_items ──▶ foods (可选关联)
    │
    ├── 1:N ── weight_records
    ├── 1:N ── circumference_records
    ├── 1:N ── sleep_records
    ├── 1:N ── exercise_records
    ├── 1:N ── water_records (每天唯一)
    ├── 1:N ── bowel_records
    │
    ├── 1:N ── memories
    ├── 1:N ── memory_summaries
    ├── 1:N ── chat_messages
    │
    ├── 1:N ── plans
    │              ├── 1:1 ── plan_targets
    │              ├── 1:N ── plan_tasks
    │              ├── 1:N ── plan_execution (每天唯一)
    │              └── 1:N ── check_ins
    │
    └── 1:N ── suggestions

foods (独立知识库，无 user_id)
knowledge_docs (独立知识库，无 user_id)
```

## 10. 迁移管理

### 10.1 Alembic 配置

- 迁移文件存放在 `alembic/versions/`
- 每次 schema 变更生成新的迁移文件
- 迁移文件命名：自动生成的 revision ID + 描述

### 10.2 初始迁移顺序

1. 启用 pgvector 扩展
2. 创建用户相关表（health_profiles, user_preferences, user_health_info, user_settings）
3. 创建知识库表（foods, knowledge_docs）
4. 创建饮食相关表（diet_records, diet_items）
5. 创建身体数据表（weight_records 等 6 张表）
6. 创建 AI 记忆表（memories, memory_summaries, chat_messages）
7. 创建计划相关表（plans, plan_targets, plan_tasks, plan_execution, check_ins）
8. 创建建议表（suggestions）
