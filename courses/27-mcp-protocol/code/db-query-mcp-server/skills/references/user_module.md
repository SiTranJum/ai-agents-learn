---
module: user_module
description: User Module - 自动生成
tables: ['admin_user', 'app_user', 'user_feedback', 'user_token']
category: 自动生成模块
---

# user_module

## 模块概述

本模块包含 4 个表，由数据库表结构自动生成。

## 表结构

### admin_user 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | bigint | NO | PRI | None | auto_increment |
| account | varchar(50) | NO | MUL | None |  |
| pwd | varchar(100) | NO |  | None |  |
| email | varchar(100) | YES |  | None |  |
| phone | varchar(20) | YES |  | None |  |
| name | varchar(100) | YES |  | None |  |
| avatar | varchar(200) | YES |  | None |  |
| create_time | datetime | NO |  | None |  |
| update_time | datetime | NO |  | None |  |
| enable | tinyint | YES |  | 1 |  |
| source_type | varchar(20) | NO |  | INTERNAL |  |
| third_party_id | varchar(20) | YES |  | None |  |

### app_user 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | bigint | NO | PRI | None | auto_increment |
| code | varchar(10) | NO |  | None |  |
| bundle | varchar(100) | NO | MUL | None |  |
| country | varchar(10) | YES |  | None |  |
| current_country | varchar(10) | YES |  | None |  |
| current_app_version | varchar(64) | YES |  | None |  |
| register_app_version | varchar(32) | YES |  | None |  |
| email | varchar(100) | YES |  | None |  |
| phone | varchar(20) | YES |  | None |  |
| name | varchar(100) | YES |  | None |  |
| avatar | varchar(200) | YES |  | None |  |
| open_id | varchar(100) | YES |  | None |  |
| fcm_token | varchar(255) | YES |  | None |  |
| gaid | varchar(36) | YES |  | None |  |
| gaid_num | int | YES |  | 0 |  |
| status | tinyint | NO | MUL | 0 |  |
| type | tinyint | YES |  | None |  |
| last_login_time | datetime | NO |  | None |  |
| create_time | datetime | NO | MUL | None |  |
| update_time | datetime | NO |  | None |  |
| device_id | varchar(50) | YES | UNI | None |  |
| appsflyer_Id | varchar(50) | YES |  | None |  |
| is_auth | tinyint(1) | NO |  | 0 |  |
| time_zone | varchar(50) | YES |  | None |  |
| utc_offset | varchar(10) | YES |  | None |  |
| language | varchar(512) | YES | MUL | en |  |
| newcomer_guide_status | tinyint | NO |  | 0 |  |
| ga_instance_id | varchar(255) | YES |  | None |  |

### user_feedback 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | bigint unsigned | NO | PRI | None | auto_increment |
| user_id | bigint | NO | MUL | None |  |
| email | varchar(255) | YES | MUL | None |  |
| star | int | YES | MUL | None |  |
| issue | text | YES |  | None |  |
| create_time | datetime | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| update_time | datetime | NO |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |
| feedback_status | tinyint | YES | MUL | 0 |  |

### user_token 表详细结构

| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |
|--------|------|------|-----|--------|------|
| id | bigint unsigned | NO | PRI | None | auto_increment |
| user_id | bigint | NO | MUL | None |  |
| token | varchar(5120) | NO | MUL | None |  |
| refresh_token | varchar(5120) | NO |  | None |  |
| device_id | varchar(128) | NO |  | None |  |
| bundle | varchar(64) | NO |  | None |  |
| login_ip | varchar(45) | NO |  | None |  |
| login_time | datetime | NO | MUL | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| expire_time | datetime | NO | MUL | None |  |
| device_type | tinyint | NO |  | None |  |
| login_type | tinyint | NO |  | None |  |
| status | tinyint | NO |  | 1 |  |
| version | varchar(16) | YES |  | None |  |

