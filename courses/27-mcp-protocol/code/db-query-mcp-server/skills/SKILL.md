---
name: database-query
description: 数据库查询助手，支持用户、订单、商品等模块的查询
category: database
modules: [user_module, order_module, product_module, challenge, tracking_module]
owner: database-team
---
# 数据库查询 Skill

## 概述

本 Skill 提供数据库查询能力，支持多个业务模块的数据查询。

## 可用模块

当前支持以下业务模块，每个模块的详细信息请查看 `references/` 目录：

1. **user** - 用户模块，包含用户基本信息、登录记录、账号状态管理
2. **challenge** - 任务模块，包含任务配置、任务进度、任务奖励等信息

## 使用说明

### 第一步：选择模块

根据用户问题，判断涉及哪个业务模块。例如：
- 用户相关问题 → user
- 任务相关问题 → challenge

### 第二步：加载模块详情

调用 `load_reference` 工具加载对应模块的详细信息：

```
load_reference(skill_name="database-query", reference_file="user.md")
```

### 第三步：生成 SQL

根据模块的表结构、SOP、约束条件，生成精准的 SQL 语句。

### 第四步：执行查询

调用 `execute_sql` 工具执行 SQL 并返回结果。

## 通用规则

### SQL 生成规则

1. **参数化查询**：必须使用 `%s` 占位符，防止 SQL 注入
2. **LIMIT 限制**：所有查询必须加 LIMIT（默认 100），除非是聚合查询
3. **字段选择**：优先选择必要字段，避免 SELECT *
4. **敏感字段**：禁止查询密码、密钥等敏感字段

### 安全规则

1. **禁止操作**：DROP、TRUNCATE、ALTER 等危险操作
2. **写操作限制**：UPDATE/DELETE/INSERT 需要用户确认（当前版本禁止）
3. **权限控制**：严格遵守各模块定义的约束条件

## 错误处理

如果遇到以下情况，请诚实告知用户：

1. 模块信息不足 → 提示需要加载 reference
2. 表结构不明确 → 建议查看具体模块文档
3. 查询超出权限 → 说明安全限制原因
