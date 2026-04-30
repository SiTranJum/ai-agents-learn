# Skills 三层架构设计

## 架构概览

Skills 采用三层渐进式加载架构，最大程度减少 token 消耗：

```
第一层：元数据（YAML frontmatter）
  ↓ 常驻上下文，~50 tokens/skill
第二层：SKILL.md 详细指令
  ↓ 按需加载，~500 tokens
第三层：附录资源（references/、scripts/）
  ↓ 按需加载，成本可控
```

## 目录结构

```
skills/
├── README.md                    # 本文件
├── user_module/                 # 用户模块 skill
│   ├── SKILL.md                 # 第二层：详细指令
│   ├── references/              # 第三层：参考文档
│   │   ├── db-schema.md         # 数据库表结构详情
│   │   └── term-glossary.md     # 业务术语表
│   └── scripts/                 # 第三层：脚本（可选）
│       └── connect-db.py        # 数据库连接脚本
└── order_module/                # 订单模块 skill（示例）
    ├── SKILL.md
    └── references/
        └── db-schema.md
```

## 第一层：元数据（YAML frontmatter）

每个 `SKILL.md` 文件开头必须包含 YAML frontmatter：

```yaml
---
name: user_module
description: 用户基本信息管理，包含注册、登录、账号状态等
category: 用户管理
tags: [users, login, authentication]
tables: [users, login_logs]
owner: 后端团队
---
```

**字段说明**：
- `name`: skill 唯一标识（必填）
- `description`: 简短描述，1-2 句话（必填）
- `category`: 业务分类（可选）
- `tags`: 关键词标签（可选）
- `tables`: 涉及的数据库表（可选）
- `owner`: 负责团队（可选）

**作用**：
- 常驻在 AI 上下文中
- 用于快速匹配用户需求
- 成本极低（~50 tokens/skill）

## 第二层：SKILL.md 详细指令

当 AI 确定 skill 相关后，加载 SKILL.md 的主体内容。

**必须包含的章节**：

### 1. SOP（标准操作流程）
具体的执行步骤

### 2. 约束条件
安全、性能、业务规则

### 3. 表结构概览
核心字段和关系，详细内容指向 references/

### 4. 示例查询
常见查询模式

### 5. 需要更多信息？
指向第三层资源

**作用**：
- 提供完成任务的具体步骤
- 中等成本（~500 tokens）
- 按需加载，避免浪费

## 第三层：附录资源

只有当 SKILL.md 明确要求时，AI 才会读取这些文件。

### references/ 目录

- `db-schema.md` - 完整的数据库表结构
- `term-glossary.md` - 业务术语表
- `data-dictionary.md` - 数据字典（可选）

### scripts/ 目录（可选）

- `connect-db.py` - 数据库连接
- `sql-generator.py` - SQL 生成
- `chart-render.py` - 图表渲染

**作用**：
- 按需分配，成本可控
- 不需要时完全不加载
- 需要时精准加载

## 渐进式加载流程

```
用户："查询所有正常状态的用户"

第一阶段（扫描元数据）：
  AI 扫描所有 skill 的 YAML frontmatter
  → 发现 user_module 的 description 包含"用户"
  → 成本：50 tokens × 10 skills = 500 tokens

第二阶段（加载详细指令）：
  AI 加载 user_module/SKILL.md
  → 看到 SOP、约束条件、表结构概览
  → 生成 SQL
  → 成本：500 tokens

第三阶段（按需加载资源）：
  如果 SQL 生成遇到问题，AI 才会：
  → 加载 references/db-schema.md 查看完整表结构
  → 成本：800 tokens（仅在需要时）

总成本：500 + 500 = 1000 tokens
（相比传统方式的 5000+ tokens，节省 80%）
```

## 创建新 Skill 的步骤

### 1. 创建目录结构
```bash
mkdir -p skills/your_module/{references,scripts}
```

### 2. 编写 SKILL.md
必须包含：
- YAML frontmatter（元数据）
- SOP（标准操作流程）
- 约束条件
- 表结构概览
- 示例查询
- 资源引用

### 3. 补充参考文档
```bash
touch skills/your_module/references/db-schema.md
touch skills/your_module/references/term-glossary.md
```

### 4. 添加脚本（可选）
```bash
touch skills/your_module/scripts/your-script.py
```

## 最佳实践

### 元数据（第一层）
- ✅ 描述简短精准（1-2 句话）
- ✅ 包含关键词（便于匹配）
- ❌ 不要写太长（增加常驻成本）

### SKILL.md（第二层）
- ✅ SOP 具体可执行
- ✅ 约束条件明确
- ✅ 表结构只写核心字段
- ✅ 示例查询覆盖常见场景
- ❌ 不要写完整表结构（放到 references/）

### 参考文档（第三层）
- ✅ 完整详细
- ✅ 结构清晰
- ✅ 易于查找
- ❌ 不要在 SKILL.md 中重复

## 总结

三层架构的核心优势：
1. **成本可控**：按需加载，避免浪费
2. **响应快速**：第一层扫描极快
3. **精准匹配**：元数据帮助快速定位
4. **易于维护**：结构清晰，职责分明

遵循这个架构，可以在保证功能完整的同时，大幅降低 token 消耗。
