---
module: tracking_module
description: Tracking Module - 自动生成
tables: ['user_action', 'user_action_metrics', 'user_action_record']
category: 自动生成模块
---

# tracking_module

## 模块概述

本模块包含 3 个表，由数据库表结构自动生成。

## 表结构

### user_action 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| user_action_id | int | NO | PRI | None | auto_increment |
| bundle | varchar(100) | YES |  | None |  |
| category | varchar(50) | NO |  | None |  |
| event_type | varchar(50) | NO |  | None |  |
| display_name | varchar(100) | NO |  | None |  |
| flow_id | varchar(50) | YES |  | None |  |
| report_type | tinyint | NO |  | 2 |  |
| is_deleted | tinyint | NO |  | 0 |  |
| user_action_name | varchar(64) | NO | UNI | None |  |
| user_action_arg_name | varchar(64) | YES |  | None |  |
| description | varchar(255) | YES |  | None |  |
| remark | varchar(64) | YES |  | None |  |
| create_time | datetime | NO |  | None |  |
| update_time | datetime | NO |  | None |  |
| export_flag | tinyint | NO |  | 1 |  |
| need_group_by_action_name | tinyint(1) | NO |  | 0 |  |

### user_action_metrics 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | bigint | NO | PRI | None | auto_increment |
| user_action | varchar(64) | NO |  | None |  |
| user_action_name | varchar(64) | NO |  | None |  |
| user_action_arg_name | varchar(64) | YES | MUL | None |  |
| user_action_arg_value | varchar(64) | YES | MUL | None |  |
| bundle | varchar(64) | YES | MUL | None |  |
| category | varchar(32) | YES | MUL | None |  |
| event_type | varchar(64) | YES |  | None |  |
| display_name | varchar(256) | YES | MUL | None |  |
| flow_id | varchar(32) | YES | MUL | None |  |
| date | date | NO | MUL | None |  |
| pv | bigint | YES |  | 0 |  |
| uv | bigint | YES |  | 0 |  |
| new_pv | bigint | YES |  | 0 |  |
| new_uv | bigint | YES |  | 0 |  |
| old_pv | bigint | YES |  | 0 |  |
| old_uv | bigint | YES |  | 0 |  |
| user_source | varchar(32) | YES |  | ALL |  |

### user_action_record 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| record_id | bigint | NO | PRI | None | auto_increment |
| bundle | varchar(100) | YES |  | None |  |
| user_country | varchar(20) | YES |  | None |  |
| category | varchar(50) | YES |  | None |  |
| event_type | varchar(50) | YES |  | None |  |
| flow_id | varchar(50) | YES |  | None |  |
| biz_id | varchar(64) | YES |  | None |  |
| remark | varchar(255) | YES |  | None |  |
| user_id | varchar(32) | NO |  | None |  |
| user_action | smallint | NO |  | None |  |
| user_action_name | varchar(64) | NO |  | None |  |
| user_action_arg_name | varchar(64) | NO |  |  |  |
| user_action_arg_value | varchar(512) | NO |  |  |  |
| app_version | varchar(20) | YES |  | None |  |
| unix_create_time | timestamp | NO |  | None |  |
| create_date | date | NO | MUL | None |  |
| display_name | varchar(100) | YES |  | None |  |
| need_group_by_action_name | tinyint(1) | NO |  | 0 |  |

