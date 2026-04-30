---
module: challenge
description: Challenge - 自动生成
tables: ['challenge_config', 'challenge_progress', 'challenge_task', 'challenge_task_config']
category: 自动生成模块
---

# challenge

## 模块概述

本模块包含 4 个表，由数据库表结构自动生成。

## 表结构

### challenge_config 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | bigint | NO | PRI | None | auto_increment |
| config_type | varchar(50) | NO | MUL | None |  |
| day_index | int | NO |  | None |  |
| area_id | bigint | NO |  | None |  |
| bundle | varchar(255) | NO | MUL | None |  |
| challenge_hint | varchar(255) | YES |  | None |  |
| money | decimal(5,2) | YES |  | None |  |
| scope | varchar(50) | YES |  | ALL |  |
| status | tinyint | NO |  | 1 |  |
| create_time | datetime | NO |  | None |  |
| update_time | datetime | NO |  | None |  |

### challenge_progress 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | bigint | NO | PRI | None | auto_increment |
| user_id | varchar(64) | NO | MUL | None |  |
| biz_date | date | NO |  | None |  |
| day_index | int | NO |  | None |  |
| scene | varchar(56) | NO |  | None |  |
| platform_scope | varchar(56) | NO |  | None |  |
| completed | tinyint | YES |  | 0 |  |
| bundle | varchar(255) | NO | MUL | None |  |
| area_id | bigint | YES |  | None |  |
| config_id | bigint | YES | MUL | None |  |
| reward_claimed | tinyint | YES |  | 0 |  |
| reward_amount | int | YES |  | 0 |  |
| reward_money | decimal(18,6) | YES |  | 0.000000 |  |
| create_time | datetime | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| update_time | datetime | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |
| challenge_hint | varchar(255) | YES |  | None |  |

### challenge_task 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | bigint | NO | PRI | None | auto_increment |
| progress_id | bigint | NO | MUL | None |  |
| config_id | bigint | YES | MUL | None |  |
| user_id | varchar(64) | NO | MUL | None |  |
| biz_date | date | NO |  | None |  |
| order_no | int | NO |  | None |  |
| desc_text | varchar(255) | NO |  | None |  |
| coins | int | NO |  | None |  |
| money | decimal(18,6) | NO |  | 0.000000 |  |
| type | varchar(56) | NO |  | None |  |
| scene | varchar(56) | NO | MUL | None |  |
| target_progress | int | NO |  | None |  |
| target_app_count | int | YES |  | None |  |
| current_progress | int | YES |  | 0 |  |
| is_complete | tinyint | YES |  | 0 |  |
| platform_scope | varchar(64) | YES |  | ALL_3P |  |
| create_time | datetime | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| update_time | datetime | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |
| finish_time | datetime | YES |  | None |  |

### challenge_task_config 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | bigint | NO | PRI | None | auto_increment |
| challenge_config_id | bigint | NO | MUL | None |  |
| order_num | int | NO | MUL | None |  |
| task_desc | varchar(255) | YES |  | None |  |
| coins | int | YES |  | None |  |
| money | decimal(18,6) | NO |  | 0.000000 |  |
| is_rewarded | tinyint(1) | YES |  | None |  |
| task_type | varchar(50) | YES |  | None |  |
| target_progress | int | YES |  | None |  |
| target_app_count | int | YES |  | None |  |
| offer_type | int | NO |  | 1 |  |
| status | tinyint | NO |  | 1 |  |
| create_time | datetime | NO |  | None |  |
| update_time | datetime | NO |  | None |  |

