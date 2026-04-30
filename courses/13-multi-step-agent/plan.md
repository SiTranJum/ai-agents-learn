# 课程 13：Multi-Step Agent — 复杂任务的多步编排

## 学习目标

1. 理解 Multi-Step Agent 与 ReAct 的区别和联系
2. 掌握复杂任务的分解和编排策略
3. 学会处理多步任务中的依赖关系
4. 实现错误处理和重试机制
5. 完成一个健康场景的 Multi-Step Agent

## 知识点

### 1. Multi-Step Agent 概念
- 什么是 Multi-Step Agent
- 与 ReAct 的区别：编排 vs 自由推理
- 适用场景：复杂、结构化的任务

### 2. 任务分解策略
- 自动分解 vs 手动分解
- 任务依赖关系（DAG）
- 并行 vs 串行执行

### 3. 编排模式
- 线性编排（Sequential）
- 条件分支（Conditional）
- 循环重试（Loop with Retry）
- 并行执行（Parallel）

### 4. 错误处理
- 单步失败的处理策略
- 重试机制设计
- 降级方案（Fallback）

### 5. 实践案例
- 健康场景：制定完整的减肥方案
- 涉及多个步骤：获取档案 → 计算指标 → 生成方案 → 设置提醒

## 实践任务

1. 实现一个 Multi-Step Planner
2. 完成"制定减肥方案"的多步编排
3. 添加错误处理和重试机制

## 预计时长

60-90 分钟
