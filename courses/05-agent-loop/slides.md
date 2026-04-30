# 课程 5：Agent 的核心循环

## 第一部分：Agent 循环的本质

### 什么是"循环"？

Agent 不是一次性执行完就结束，而是**持续地感知、思考、行动，直到任务完成**。

```
用户："帮我制定一个减肥计划"

Agent 循环：
第 1 轮：感知 → 理解用户想要减肥计划
        思考 → 需要先了解用户的基本信息
        行动 → 调用 get_user_profile()
        观察 → 得到：身高 170cm，体重 75kg，目标 65kg

第 2 轮：感知 → 已有用户信息
        思考 → 需要计算每日热量需求
        行动 → 调用 calculate_tdee(170, 75)
        观察 → 得到：TDEE = 2000 千卡

第 3 轮：感知 → 已有 TDEE
        思考 → 可以制定计划了
        行动 → 生成减肥计划
        观察 → 计划已生成

第 4 轮：感知 → 任务完成
        思考 → 可以回答用户了
        行动 → 输出最终回复
        结束循环
```

---

## 第二部分：循环的四个阶段

### 1. 感知（Perception）

理解当前状态和用户输入。

```python
# 感知阶段要回答的问题：
- 用户想做什么？
- 现在有哪些信息？
- 还缺什么信息？
```

### 2. 思考（Reasoning）

基于当前信息，决定下一步做什么。

```python
# 思考阶段要回答的问题：
- 需要调用工具吗？
- 调用哪个工具？
- 传什么参数？
- 还是可以直接回答了？
```

### 3. 行动（Action）

执行决策（调用工具或生成回复）。

```python
# 行动阶段的两种可能：
1. 调用工具 → 获取信息或执行操作
2. 生成回复 → 任务完成，结束循环
```

### 4. 观察（Observation）

查看行动的结果，更新状态。

```python
# 观察阶段要做的事：
- 工具返回了什么？
- 是否成功？
- 是否需要继续循环？
```

---

## 第三部分：用 Spring MVC 类比

你熟悉的 Spring MVC 请求处理流程：

```
用户请求 → DispatcherServlet → Controller → Service → Repository → 返回响应
```

Agent 循环类似，但是**可能需要多次调用 Service**：

```
Spring MVC（单次）：
Request → Controller.handleRequest()
       → userService.getUser()
       → return Response

Agent 循环（多次）：
用户消息 → Agent.perceive()
        → Agent.think() → 决定调用 userService
        → Agent.act() → 执行 userService.getUser()
        → Agent.observe() → 得到用户信息

        → Agent.think() → 决定调用 mealService
        → Agent.act() → 执行 mealService.getMeals()
        → Agent.observe() → 得到饮食记录

        → Agent.think() → 信息充足，可以回答
        → Agent.act() → 生成回复
        → 结束
```

**关键区别**：
- Spring MVC：Controller 一次性决定调用哪些 Service
- Agent：每次循环重新思考，动态决定下一步
