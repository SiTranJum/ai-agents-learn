---
module: order_module
description: 订单管理，包括订单、订单明细、支付记录
tables: [orders, order_items, payments]
category: 核心模块
---

# 订单模块（order_module）

## 模块概述

订单模块负责管理订单、订单明细和支付记录。

## SOP（标准操作流程）

### 查询订单

1. **按订单号查询**：使用 `order_no` 精确查询
2. **按用户查询**：使用 `user_id` + 时间范围
3. **按状态查询**：必须加时间范围和 LIMIT

### 订单统计

1. 金额统计使用 `SUM(total_amount)`
2. 订单数量使用 `COUNT(*)`
3. 按日期分组使用 `DATE(created_at)`

### 关联查询

1. orders ↔ order_items：`orders.id = order_items.order_id`
2. orders ↔ payments：`orders.id = payments.order_id`

## 约束条件

### 安全约束

- **禁止操作**：DELETE 订单（只能修改 status）
- **敏感信息**：支付密码、银行卡号等不在数据库中

### 性能约束

- **必须索引**：查询必须使用索引字段（order_no, user_id, created_at）
- **时间范围**：大范围查询必须限定时间

### 业务约束

- **订单状态**：0=待支付，1=已支付，2=已发货，3=已完成，4=已取消
- **金额单位**：所有金额字段单位为"分"（整数）

## 表结构概览

### orders（订单表）

核心字段：
- `id` - 订单 ID
- `order_no` - 订单号（唯一）
- `user_id` - 用户 ID
- `total_amount` - 订单总金额（分）
- `status` - 订单状态
- `created_at` - 下单时间

### order_items（订单明细表）

核心字段：
- `id` - 明细 ID
- `order_id` - 订单 ID
- `product_id` - 商品 ID
- `quantity` - 数量
- `price` - 单价（分）

### payments（支付记录表）

核心字段：
- `id` - 支付 ID
- `order_id` - 订单 ID
- `amount` - 支付金额（分）
- `payment_method` - 支付方式
- `status` - 支付状态

## 示例查询

### 查询用户订单

```sql
SELECT id, order_no, total_amount, status, created_at
FROM orders
WHERE user_id = %s AND created_at >= %s
ORDER BY created_at DESC
LIMIT %s
```

### 统计订单金额

```sql
SELECT DATE(created_at) as date, SUM(total_amount) as total
FROM orders
WHERE status IN (1, 2, 3) AND created_at >= %s
GROUP BY DATE(created_at)
```

### 查询订单详情（含明细）

```sql
SELECT o.order_no, o.total_amount, oi.product_id, oi.quantity, oi.price
FROM orders o
INNER JOIN order_items oi ON o.id = oi.order_id
WHERE o.order_no = %s
```
