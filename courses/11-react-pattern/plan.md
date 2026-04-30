# 课程 11：ReAct 模式 — 推理与行动交替执行

## 学习目标
1. 理解 ReAct 模式的核心思想
2. 掌握 ReAct 的实现方法
3. 理解 ReAct 与普通 Agent 的区别
4. 在健康管家 Agent 中应用 ReAct 模式

## 为什么这节课重要？

ReAct 是目前最流行的 Agent 模式之一，被广泛应用于各种 AI Agent 框架中。

**问题**：普通 Agent 的思考过程是"黑盒"的，我们看不到它为什么这样做。

**ReAct 的解决方案**：让 Agent 展示思考过程（Reasoning），然后执行行动（Acting），交替进行。

## 课程内容

### 1. ReAct 模式概述（20 分钟）
- 什么是 ReAct？
- ReAct 的核心思想
- ReAct vs 普通 Agent

### 2. ReAct 的工作流程（30 分钟）
- Thought（思考）
- Action（行动）
- Observation（观察）
- 循环直到完成

### 3. 实现 ReAct Agent（40 分钟）
- Prompt 设计
- 解析 Thought 和 Action
- 执行循环

### 4. 实战：健康管家 ReAct Agent（30 分钟）
- 应用场景
- 代码实现
- 效果对比

## 预计时长
- 讲解 + 演示：约 60 分钟
- 实践：约 60 分钟
