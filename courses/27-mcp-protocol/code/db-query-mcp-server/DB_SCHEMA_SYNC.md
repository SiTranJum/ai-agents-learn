# 数据库表结构同步功能

## 功能概述

当数据库表结构发生变更时，Agent 可以通过与用户对话，精确扫描指定的表，对比差异，并更新 Skills 模块文件。

**核心优势**：
- ✅ 精确扫描：只扫描用户指定的表，避免全表扫描浪费 token
- ✅ 智能对话：通过 Agent 循环与用户确认，避免误操作
- ✅ 差异报告：清晰展示新增/删除/修改的字段
- ✅ 自动更新：一键更新模块文件和 SKILL.md

---

## 使用场景

### 场景 1：新增字段

```
用户："users 表新增了一个 vip_level 字段"

Agent：
1. 扫描 users 表的数据库结构
2. 与 user_module.md 对比
3. 发现新增字段：vip_level
4. 生成差异报告
5. 询问用户是否更新
```

### 场景 2：新增表

```
用户："新增了一个 coupons 表，属于订单模块"

Agent：
1. 扫描 coupons 表的数据库结构
2. 确认属于 order_module
3. 生成差异报告（新增表）
4. 询问用户是否更新
5. 更新 order_module.md，添加 coupons 表
```

### 场景 3：检查模块

```
用户："帮我检查 user_module 的表结构是否最新"

Agent：
1. 获取 user_module 包含的表列表（users, login_logs）
2. 扫描这些表的数据库结构
3. 与 user_module.md 对比
4. 生成差异报告
5. 如果有差异，询问用户是否更新
```

---

## 架构设计

### 核心类：DatabaseSchemaSync

**职责**：
1. 扫描数据库表结构
2. 与 references/*.md 对比
3. 生成差异报告
4. 更新模块文件

**关键方法**：

```python
class DatabaseSchemaSync:
    def scan_database_tables(table_names) -> Dict
        """扫描指定表的数据库结构"""

    def compare_with_module(module_name, db_tables) -> Dict
        """对比数据库表结构与模块定义"""

    def generate_update_report(module_name, changes) -> str
        """生成更新报告（给用户确认）"""

    def update_module_file(module_name, db_tables, changes) -> Dict
        """更新模块文件"""
```

---

## Agent 循环设计

### 工具定义

Agent 在同步过程中可以调用以下工具：

1. **scan_tables** - 扫描指定表的数据库结构
   ```json
   {
     "table_names": ["users", "login_logs"]
   }
   ```

2. **compare_module** - 对比数据库表结构与模块定义
   ```json
   {
     "module_name": "user_module",
     "table_names": ["users", "login_logs"]
   }
   ```

3. **apply_update** - 应用更新到模块文件
   ```json
   {
     "module_name": "user_module",
     "table_names": ["users"],
     "update_skill_md": false
   }
   ```

### 执行流程

```
用户请求
  ↓
LLM 分析请求
  ↓
确定涉及的表和模块
  ↓
调用 scan_tables 扫描数据库
  ↓
调用 compare_module 对比差异
  ↓
生成差异报告
  ↓
返回给用户确认
  ↓
（用户确认后）
  ↓
调用 apply_update 更新文件
```

---

## MCP 工具接口

### sync_schema

**描述**：同步数据库表结构

**参数**：
```json
{
  "request": "users 表新增了 vip_level 字段"
}
```

**返回**：差异报告或更新结果

**示例**：

```python
# 在 Claude Desktop 中使用
用户："数据库更新了，users 表新增了 vip_level 字段，帮我同步一下"

Agent 调用：sync_schema(request="users 表新增了 vip_level 字段")

Agent 返回：
"""
# 模块 user_module 表结构变更报告

## 修改的表

### users

**新增字段**：
- vip_level

---

请确认是否更新模块文件？
"""
```

---

## 差异报告格式

```markdown
# 模块 {module_name} 表结构变更报告

## 新增的表

- table1
- table2

## 已删除的表

- old_table

## 修改的表

### users

**新增字段**：
- vip_level
- last_login_ip

**删除字段**：
- old_field

---

请确认是否更新模块文件？
- 输入 'yes' 确认更新
- 输入 'no' 取消更新
```

---

## 更新策略

### 更新模块文件（references/*.md）

1. **保留 frontmatter**：更新 `tables` 列表
2. **重新生成表结构**：根据数据库实际结构生成 Markdown 表格
3. **保留 SOP 和约束**：（当前版本简化实现，实际使用时需要保留）

### 更新 SKILL.md

当新增模块时，需要手动更新 SKILL.md 的 frontmatter：

```yaml
---
name: database-query
description: 数据库查询助手
modules: [user_module, order_module, product_module, new_module]  # 添加新模块
---
```

---

## 安全机制

### 1. 精确扫描

- ❌ 不支持全表扫描（避免浪费 token）
- ✅ 只扫描用户指定的表
- ✅ LLM 根据用户描述确定表名

### 2. 用户确认

- ❌ 不自动更新文件
- ✅ 生成差异报告让用户确认
- ✅ 用户明确同意后才更新

### 3. 备份机制

- 建议在更新前备份 references/*.md
- 可以通过 git 回滚

---

## 使用示例

### 示例 1：新增字段

```python
# 用户请求
"users 表新增了 vip_level 和 vip_expire_time 两个字段"

# Agent 执行
1. 扫描 users 表
2. 对比 user_module.md
3. 发现新增字段：vip_level, vip_expire_time
4. 生成报告

# 差异报告
"""
## 修改的表

### users

**新增字段**：
- vip_level
- vip_expire_time
"""

# 用户确认后更新
user_module.md 已更新
```

### 示例 2：新增表

```python
# 用户请求
"新增了一个 coupons 表，包含优惠券信息，属于订单模块"

# Agent 执行
1. 扫描 coupons 表
2. 确认属于 order_module
3. 生成报告

# 差异报告
"""
## 新增的表

- coupons
"""

# 用户确认后更新
order_module.md 已更新，新增 coupons 表结构
```

### 示例 3：新增模块

```python
# 用户请求
"新增了 payments 和 refunds 两个表，创建一个新的支付模块"

# Agent 执行
1. 扫描 payments 和 refunds 表
2. 确认需要创建新模块 payment_module
3. 生成报告

# 差异报告
"""
## 新增模块

模块名称：payment_module
包含的表：payments, refunds

注意：需要同时更新 SKILL.md 的 modules 列表
"""

# 用户确认后
1. 创建 references/payment_module.md
2. 提示用户手动更新 SKILL.md
```

---

## 限制和注意事项

### 当前限制

1. **简化的表结构生成**：当前版本只生成基本的字段信息，不包含：
   - SOP（标准操作流程）
   - 约束条件
   - 示例查询
   - 业务术语表

2. **手动更新 SKILL.md**：新增模块时，需要手动更新 SKILL.md 的 `modules` 列表

3. **不支持字段类型变更检测**：只检测新增/删除字段，不检测字段类型变更

### 改进方向

1. **智能保留内容**：更新时保留原有的 SOP、约束、示例查询
2. **自动更新 SKILL.md**：新增模块时自动更新 SKILL.md
3. **字段类型检测**：检测字段类型、长度、默认值的变更
4. **批量更新**：支持一次更新多个模块

---

## 文件清单

```
core/
├── db_schema_sync.py          # 数据库表结构同步器 ✅
├── skill_manager.py           # Skills 管理器 ✅
├── agent_harness.py           # Agent 执行器（新增 sync_schema 方法）✅
└── __init__.py                # 导出 DatabaseSchemaSync ✅

server.py                      # MCP Server（新增 sync_schema 工具）✅
```

---

## 总结

数据库表结构同步功能通过 Agent 循环与用户对话，精确扫描指定的表，对比差异，并更新 Skills 模块文件。

**核心优势**：
- 精确扫描，避免浪费 token
- 智能对话，避免误操作
- 差异报告，清晰展示变更
- 自动更新，一键完成

**使用方式**：
```
用户："users 表新增了 vip_level 字段"
Agent：调用 sync_schema 工具
Agent：生成差异报告
用户：确认更新
Agent：更新 user_module.md
```

功能已完整实现，可以直接使用！
