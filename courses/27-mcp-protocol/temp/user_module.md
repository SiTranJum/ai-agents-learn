---
module: user_module
description: 用户基本信息管理，包括注册、登录、账号状态
tables: [users, login_logs]
category: 核心模块
---

# 用户模块（user_module）

## 模块概述

用户模块负责管理用户的基本信息、登录记录和账号状态。

## SOP（标准操作流程）

### 查询用户信息

1. **精确查询**：优先使用 `id` 或 `username` 进行精确查询
2. **模糊查询**：必须加 `LIMIT`，避免全表扫描
3. **字段选择**：不要 SELECT *，只选择必要字段
4. **敏感字段**：`password_hash` 禁止出现在查询结果中

### 统计查询

1. 使用 `COUNT(*)` 统计数量
2. 时间范围查询使用索引字段 `created_at`
3. 分组统计使用 `GROUP BY`

### 关联查询

1. users 和 login_logs 通过 `users.id = login_logs.user_id` 关联
2. 关联查询必须指定 JOIN 类型，避免笛卡尔积

## 约束条件

### 安全约束

- **禁止查询**：`password_hash` 字段
- **禁止操作**：DELETE 用户（只能修改 status）

### 性能约束

- **必须 LIMIT**：查询结果必须加 `LIMIT`（默认 100）
- **索引使用**：优先使用 `id`、`username`、`created_at` 等索引字段

### 业务约束

- **status 字段含义**：0=禁用，1=正常，2=冻结
- **删除规则**：软删除，不物理删除用户

## 表结构概览

### users（用户表）

核心字段：
- `id` - 用户唯一标识（主键）
- `username` - 用户名（唯一索引）
- `email` - 邮箱
- `status` - 账号状态（0=禁用，1=正常，2=冻结）
- `created_at` - 注册时间

**详细字段说明请查看完整表结构（如需要，可以继续查看本文档后续内容）**

### login_logs（登录日志表）

核心字段：
- `id` - 日志 ID（主键）
- `user_id` - 用户 ID（外键）
- `login_time` - 登录时间
- `ip_address` - 登录 IP
- `status` - 登录状态（success/failed）

## 示例查询

### 查询正常状态的用户

```sql
SELECT id, username, email, created_at
FROM users
WHERE status = %s
LIMIT %s
```

参数：`[1, 100]`

### 统计用户数量

```sql
SELECT COUNT(*) as total
FROM users
WHERE status = %s
```

参数：`[1]`

### 查询用户最近登录记录

```sql
SELECT u.username, l.login_time, l.ip_address
FROM users u
INNER JOIN login_logs l ON u.id = l.user_id
WHERE u.id = %s
ORDER BY l.login_time DESC
LIMIT %s
```

参数：`[user_id, 10]`

---

## 完整表结构

### users 表详细结构

| 字段名 | 类型 | 长度 | 可空 | 默认值 | 索引 | 说明 |
|--------|------|------|------|--------|------|------|
| id | BIGINT | - | NO | AUTO_INCREMENT | PRIMARY | 用户唯一标识 |
| username | VARCHAR | 50 | NO | - | UNIQUE | 用户名 |
| email | VARCHAR | 100 | YES | NULL | INDEX | 邮箱 |
| password_hash | VARCHAR | 255 | NO | - | - | 密码哈希（禁止查询） |
| phone | VARCHAR | 20 | YES | NULL | INDEX | 手机号 |
| nickname | VARCHAR | 50 | YES | NULL | - | 昵称 |
| avatar_url | VARCHAR | 255 | YES | NULL | - | 头像 URL |
| status | TINYINT | - | NO | 1 | INDEX | 账号状态（0=禁用，1=正常，2=冻结） |
| created_at | DATETIME | - | NO | CURRENT_TIMESTAMP | INDEX | 注册时间 |
| updated_at | DATETIME | - | NO | CURRENT_TIMESTAMP ON UPDATE | - | 更新时间 |

**索引信息**：
- PRIMARY KEY: `id`
- UNIQUE KEY: `username`
- INDEX: `email`, `phone`, `status`, `created_at`

### login_logs 表详细结构

| 字段名 | 类型 | 长度 | 可空 | 默认值 | 索引 | 说明 |
|--------|------|------|------|--------|------|------|
| id | BIGINT | - | NO | AUTO_INCREMENT | PRIMARY | 日志 ID |
| user_id | BIGINT | - | NO | - | INDEX | 用户 ID（外键） |
| login_time | DATETIME | - | NO | CURRENT_TIMESTAMP | INDEX | 登录时间 |
| ip_address | VARCHAR | 45 | YES | NULL | - | 登录 IP（支持 IPv6） |
| user_agent | VARCHAR | 255 | YES | NULL | - | 浏览器信息 |
| status | VARCHAR | 20 | NO | - | INDEX | 登录状态（success/failed） |
| fail_reason | VARCHAR | 255 | YES | NULL | - | 失败原因 |

**索引信息**：
- PRIMARY KEY: `id`
- INDEX: `user_id`, `login_time`, `status`
- FOREIGN KEY: `user_id` REFERENCES `users(id)`

## 业务术语表

- **正常用户**：status = 1 的用户
- **活跃用户**：最近 30 天有登录记录的用户
- **新用户**：注册时间在最近 7 天内的用户
- **冻结用户**：status = 2，通常因违规被冻结
- **禁用用户**：status = 0，通常是用户主动注销
