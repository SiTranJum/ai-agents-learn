# RAG 知识库模块 (RAG Knowledge)

> RAG 知识库是健康管家的知识支撑模块，负责食物营养知识库（500+ 食物）和健康建议知识库（180 条）的管理与检索。本模块基于 pgvector 实现向量语义搜索，为饮食记录、营养查询、AI 建议等场景提供准确的知识上下文。食物搜索采用三层匹配策略（精确匹配 → 别名匹配 → Embedding 语义搜索），确保高召回率。
>
> 实现依据：`docs/prd/v1/06-rag-knowledge.md`，`docs/specs/backend/00-architecture/overview.md`，`docs/specs/backend/00-architecture/api-design.md`

---

## 1. 模块职责

本模块承担以下核心职责：

- **食物营养知识库**：维护 500+ 种常见食物的营养数据，支持语义搜索和模糊匹配
- **健康建议知识库**：维护 180 条健康建议文档，支持向量检索为 AI 提供上下文
- **向量语义搜索**：基于 pgvector 的余弦相似度检索，支持 Embedding 语义匹配
- **食物名称模糊匹配**：三层匹配策略（精确名称 → 别名 → Embedding 语义），覆盖别名和近义词
- **种子数据管理**：提供数据初始化脚本，支持批量导入和 Embedding 生成

### 1.1 模块边界

| 本模块负责 | 本模块不负责 |
|-----------|------------|
| 食物营养数据存储与检索 | 饮食记录管理（diet_service） |
| 健康建议文档存储与检索 | AI 建议生成逻辑（suggestion_service） |
| 向量 Embedding 生成与索引 | 对话上下文组装（ai_chat_service） |
| 种子数据导入与更新 | 用户个性化偏好（memory_service） |
| 食物份量换算数据 | 营养目标计算（plan_service） |

---

## 2. API 端点

所有端点必须遵循 `api-design.md` 的统一响应格式和错误码规范。

### 2.1 端点总览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/knowledge/foods/search?q=&limit=` | 食物搜索（支持自动补全） | 必须 |
| GET | `/api/v1/knowledge/foods/{id}` | 食物详情（完整营养数据） | 必须 |

### 2.2 端点详细定义

#### GET /api/v1/knowledge/foods/search

食物搜索，支持自动补全场景。采用三层匹配策略，返回按相关度排序的结果。

- 查询参数：`q` (str, 必须, 最少 1 字符), `limit` (int, 可选, 默认=10, 最大=50)
- 响应体：`list[FoodSearchResponse]`
- 排序：按 `match_score` 降序
- 性能要求：响应时间必须 < 500ms
- 错误：400 `INVALID_QUERY`（q 为空时）

#### GET /api/v1/knowledge/foods/{id}

查询单个食物的完整营养数据，包含常见份量换算。

- 路径参数：`id` (UUID)
- 响应体：`FoodDetailResponse`
- 错误：404 `FOOD_NOT_FOUND`

---

## 3. 数据模型

所有模型使用 Pydantic v2 定义。必须遵循 `overview.md` 的类型安全原则，禁止裸 dict 传递。

### 3.1 枚举类型

```python
from enum import Enum

class FoodCategory(str, Enum):
    """食物分类"""
    grains = "grains"           # 谷物类
    meat = "meat"               # 肉类
    vegetables = "vegetables"   # 蔬菜类
    fruits = "fruits"           # 水果类
    dairy = "dairy"             # 乳制品
    beverages = "beverages"     # 饮品类
    snacks = "snacks"           # 零食类
    condiments = "condiments"   # 调味品
    nuts = "nuts"               # 坚果类
    other = "other"             # 其他
```

### 3.2 营养与份量模型

```python
from pydantic import BaseModel, Field

class NutritionInfo(BaseModel):
    """营养成分信息（每 100g）"""
    calories: float = Field(..., ge=0, description="热量 kcal")
    protein: float = Field(..., ge=0, description="蛋白质 g")
    fat: float = Field(..., ge=0, description="脂肪 g")
    carbs: float = Field(..., ge=0, description="碳水化合物 g")
    fiber: float | None = Field(None, ge=0, description="膳食纤维 g")
    sodium: float | None = Field(None, ge=0, description="钠 mg")
    sugar: float | None = Field(None, ge=0, description="糖 g")

class PortionInfo(BaseModel):
    """常见份量信息"""
    name: str = Field(..., max_length=20, description="份量名称，如 '一碗'、'一个'、'一杯'")
    weight_grams: float = Field(..., gt=0, description="对应克数")
```

### 3.3 响应模型

```python
from uuid import UUID

class FoodSearchResponse(BaseModel):
    """食物搜索结果"""
    id: UUID
    name: str
    aliases: list[str] = Field(default_factory=list, description="别名列表")
    category: FoodCategory
    calories_per_100g: float = Field(..., ge=0, description="每 100g 热量 kcal")
    match_score: float = Field(..., ge=0, le=1, description="匹配相关度分数，1.0 为精确匹配")

class FoodDetailResponse(BaseModel):
    """食物详情响应"""
    id: UUID
    name: str
    aliases: list[str] = Field(default_factory=list, description="别名列表")
    category: FoodCategory
    nutrition_per_100g: NutritionInfo
    common_portions: list[PortionInfo] = Field(default_factory=list, description="常见份量列表")
    data_source: str = Field(..., description="数据来源，如 '中国食物成分表'")
```

### 3.4 内部服务模型

以下模型供模块间调用使用，禁止暴露到 API 层。

```python
class KnowledgeSearchRequest(BaseModel):
    """知识库检索请求（内部使用）"""
    query: str = Field(..., min_length=1, description="检索文本")
    category: str | None = Field(None, description="按分类过滤")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")

class KnowledgeSearchResult(BaseModel):
    """知识库检索结果（内部使用）"""
    id: UUID
    title: str
    content: str
    score: float = Field(..., ge=0, le=1, description="余弦相似度分数")
    metadata: dict = Field(
        default_factory=dict,
        description="元数据：category, tags, target_users, source"
    )
```

---

## 4. 食物知识库

### 4.1 数据结构

食物数据存储在 `foods` 表中，必须包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(100) | 食物名称，唯一索引 |
| aliases | TEXT[] | 别名数组，如 `["土豆", "马铃薯"]` |
| category | VARCHAR(50) | 分类，必须为 FoodCategory 枚举值 |
| calories | DECIMAL(8,2) | 每 100g 热量 kcal |
| protein | DECIMAL(8,2) | 蛋白质 g |
| fat | DECIMAL(8,2) | 脂肪 g |
| carbs | DECIMAL(8,2) | 碳水化合物 g |
| fiber | DECIMAL(8,2) | 膳食纤维 g，可为 NULL |
| sodium | DECIMAL(8,2) | 钠 mg，可为 NULL |
| sugar | DECIMAL(8,2) | 糖 g，可为 NULL |
| common_portions | JSONB | 常见份量换算，结构为 `[{"name": "一碗", "weight_grams": 200}]` |
| data_source | VARCHAR(100) | 数据来源 |
| embedding | vector(1024) | text-embedding-v3 生成的语义向量 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

所有营养数据必须归一化为每 100g 基准。禁止存储非标准化数据。

### 4.2 搜索策略

食物搜索必须按以下三层优先级执行，禁止跳过高优先级层直接走低优先级：

| 优先级 | 匹配方式 | match_score | 说明 |
|--------|---------|-------------|------|
| 1（最高） | 精确名称匹配 | 1.0 | `WHERE name = :query` |
| 2 | 别名匹配 | 0.9 | `WHERE :query = ANY(aliases)` |
| 3 | Embedding 语义搜索 | 0.0-0.8 | pgvector 余弦相似度，如 "红烧排骨" 匹配 "猪排骨" |

**执行逻辑：**
1. 先执行精确匹配和别名匹配（SQL 查询），如果结果数 >= limit，直接返回
2. 结果不足时，补充 Embedding 语义搜索，去重后合并返回
3. 语义搜索结果的 `match_score` 取余弦相似度值（0-1），必须 > 0.5 才纳入结果

### 4.3 数据规模

V1 目标：500+ 种食物，覆盖 10 个分类。

| 分类 | 目标数量 | 示例 |
|------|---------|------|
| 谷物类 (grains) | 50+ | 米饭、面条、馒头、面包 |
| 肉类 (meat) | 60+ | 猪牛羊鸡鱼及各部位 |
| 蔬菜类 (vegetables) | 80+ | 常见蔬菜 |
| 水果类 (fruits) | 50+ | 常见水果 |
| 乳制品 (dairy) | 20+ | 牛奶、酸奶、奶酪 |
| 饮品类 (beverages) | 30+ | 可乐、果汁、咖啡 |
| 零食类 (snacks) | 40+ | 薯片、饼干、巧克力 |
| 调味品 (condiments) | 30+ | 油、盐、酱油、醋 |
| 坚果类 (nuts) | 20+ | 核桃、杏仁、花生 |
| 其他 (other) | 120+ | 豆制品、蛋类等 |

---

## 5. 健康建议知识库

### 5.1 数据结构

健康建议文档存储在 `knowledge_docs` 表中：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| title | VARCHAR(200) | 文档标题 |
| content | TEXT | 文档正文 |
| embedding | vector(1024) | text-embedding-v3 生成的语义向量 |
| category | VARCHAR(50) | 分类 |
| tags | TEXT[] | 标签数组 |
| target_users | TEXT[] | 适用人群，如 `["减脂用户", "糖尿病患者"]` |
| source | VARCHAR(200) | 数据来源，如 "中国营养学会推荐" |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 5.2 分类

V1 共 6 个分类，180 条知识文档：

| 分类 | 数量 | 覆盖内容 |
|------|------|---------|
| 基础营养 | 20 条 | 三大营养素、微量元素、水分摄入 |
| 减重指导 | 30 条 | 热量缺口、运动配合、习惯养成 |
| 增肌指导 | 20 条 | 蛋白质摄入、训练配合、恢复策略 |
| 慢性病饮食 | 30 条 | 糖尿病、高血压、高血脂饮食管理 |
| 食物搭配 | 30 条 | 营养素吸收、食物组合建议 |
| 常见问题 | 50 条 | 饮食与健康 FAQ |

---

## 6. RAG 检索流程

向量检索流程必须按以下步骤执行：

1. **Query Embedding**：将查询文本通过 DashScope text-embedding-v3 生成 1024 维向量
2. **pgvector 检索**：使用余弦相似度（`<=>` 操作符）在 `knowledge_docs` 表中检索 top_k 结果
3. **分数过滤**：默认阈值 0.5，低于阈值的结果必须丢弃
4. **结果排序**：按相似度分数降序返回

```python
# pgvector 检索 SQL 示例
"""
SELECT id, title, content,
       1 - (embedding <=> :query_embedding) AS score,
       category, tags, target_users, source
FROM knowledge_docs
WHERE 1 - (embedding <=> :query_embedding) > :threshold
ORDER BY embedding <=> :query_embedding
LIMIT :top_k
"""
```

禁止在查询时为已有的食物/知识文档重新生成 Embedding。Embedding 必须在种子数据导入时预生成。仅查询文本需要实时生成 Embedding。

---

## 7. 种子数据管理

### 7.1 数据格式

食物数据和健康建议数据必须以 JSON 格式存储在 `data/` 目录下：

| 文件 | 说明 |
|------|------|
| `data/foods.json` | 食物营养数据，包含名称、别名、分类、营养成分、常见份量 |
| `data/health_tips.json` | 健康建议文档，包含标题、正文、分类、标签、适用人群 |

### 7.2 初始化脚本

| 脚本 | 说明 |
|------|------|
| `scripts/seed_foods.py` | 加载 foods.json → 写入 foods 表 → 批量生成 Embedding |
| `scripts/seed_health_tips.py` | 加载 health_tips.json → 写入 knowledge_docs 表 → 批量生成 Embedding |
| `scripts/generate_embeddings.py` | 通用批量 Embedding 生成工具，支持增量更新 |

所有脚本必须支持幂等执行：重复运行不产生重复数据（基于 name/title 去重）。

### 7.3 数据更新

- **V1**：手动更新，通过脚本重新导入
- **V2**：管理后台 CRUD 界面

---

## 8. Service 接口

`RagService` 类必须提供以下方法，供其他模块调用：

```python
from uuid import UUID

class RagService:
    """RAG 知识库服务"""

    async def search_foods(
        self, query: str, limit: int = 10
    ) -> list[FoodSearchResponse]:
        """
        食物搜索，三层匹配策略。
        供 API 层和 diet_service 调用。
        """
        ...

    async def get_food_detail(
        self, food_id: UUID
    ) -> FoodDetailResponse:
        """
        获取食物完整营养详情。
        不存在时抛出 FoodNotFoundError。
        """
        ...

    async def search_knowledge(
        self, query: str, category: str | None = None, top_k: int = 5
    ) -> list[KnowledgeSearchResult]:
        """
        健康建议知识库向量检索。
        供 suggestion_service 和 ai_chat_service 调用。
        """
        ...

    async def lookup_nutrition(
        self, food_name: str, amount: float = 100, unit: str = "g"
    ) -> NutritionInfo:
        """
        按食物名称查询营养数据并按份量换算。
        供 diet_service 在饮食记录时调用。
        未找到时抛出 FoodNotFoundError。
        """
        ...
```

禁止其他模块绕过 `RagService` 直接访问 `foods` 或 `knowledge_docs` 表。

---

## 9. 模块依赖

### 9.1 依赖关系

| 方向 | 模块 | 说明 |
|------|------|------|
| 依赖 | DashScope Embedding (text-embedding-v3) | 向量生成 |
| 依赖 | pgvector | 向量索引与相似度检索 |
| 被依赖 | diet_service | 调用 `lookup_nutrition()` 获取营养数据 |
| 被依赖 | suggestion_service | 调用 `search_knowledge()` 获取建议上下文 |
| 被依赖 | ai_chat_service | 调用 `search_knowledge()` 和 `search_foods()` 提供知识上下文 |

### 9.2 依赖原则

- 本模块禁止依赖 diet_service、suggestion_service 等上层模块，避免循环依赖
- 本模块禁止直接调用 LLM（qwen-plus），仅使用 Embedding 模型
- 其他模块必须通过 `RagService` 接口调用，禁止直接 SQL 查询

---

## 10. 实现约束

### 10.1 性能要求

| 指标 | 要求 |
|------|------|
| 食物搜索响应时间 | < 500ms |
| 知识库检索响应时间 | < 1s |
| Embedding 生成 | 种子数据导入时批量生成，禁止查询时为已有数据生成 |
| 查询 Embedding | 搜索时实时生成查询文本的 Embedding |

### 10.2 数据规范

- 所有食物营养数据必须归一化为每 100g 基准
- Embedding 维度必须为 1024（text-embedding-v3 默认维度）
- 食物名称必须唯一，别名可重复（多个食物可共享别名，搜索时全部返回）
- 知识文档 content 长度建议 200-500 字，禁止超过 2000 字（影响检索质量）

### 10.3 错误处理

| 错误码 | 场景 | HTTP 状态码 |
|--------|------|------------|
| `FOOD_NOT_FOUND` | 食物 ID 不存在 | 404 |
| `INVALID_QUERY` | 搜索关键词为空 | 400 |
| `EMBEDDING_SERVICE_ERROR` | Embedding 生成失败 | 503 |
