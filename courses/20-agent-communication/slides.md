# 课程 20：Agent 间通信与编排

课程 19 我们学了三种协作模式，但代码里 Agent 之间是直接函数调用的。
这节课解决一个关键问题：**Agent 之间怎么传递信息、怎么协调工作？**

---

## 第一部分：Agent 间通信的三种方式

### 1.1 方式一：直接调用（课程 19 的做法）

```python
# Agent A 直接调用 Agent B
result_a = agent_a(user_input)
result_b = agent_b(result_a)  # 直接把 A 的输出传给 B
```

```
优点：简单直接
缺点：Agent 之间强耦合，A 必须知道 B 的存在
类比 Java：Service A 直接 new ServiceB() 调用，没有接口抽象
```

### 1.2 方式二：消息传递（Message Passing）

Agent 之间不直接调用，而是通过**消息**通信。

```
Agent A → 发消息到消息总线 → Agent B 从总线取消息

消息格式：
{
  "from": "parse_agent",
  "to": "nutrition_agent",
  "type": "food_parsed",
  "data": {"foods": [{"name": "牛肉面", "amount": "一碗"}]}
}
```

```
优点：Agent 解耦，可以灵活替换
缺点：多了一层间接，调试稍复杂
类比 Java：Spring Event / RabbitMQ / Kafka
```

### 1.3 方式三：共享状态（Shared State / Blackboard）

所有 Agent 读写同一个"黑板"，每个 Agent 看到黑板上的信息后决定自己要不要行动。

```
共享状态（黑板）：
{
  "user_input": "我吃了牛肉面，跑了5公里",
  "parsed_foods": null,       ← 解析 Agent 看到这个是 null，开始工作
  "nutrition_data": null,     ← 营养 Agent 等 parsed_foods 有值后工作
  "exercise_data": null,      ← 运动 Agent 看到 user_input 有运动信息，开始工作
  "final_advice": null        ← 建议 Agent 等所有数据就绪后工作
}
```

```
优点：天然支持并行，Agent 自主决策
缺点：需要管理并发，状态可能冲突
类比 Java：Redis 共享缓存 / 数据库共享表
```

### 1.4 对比总结

| 方式 | 耦合度 | 灵活性 | 复杂度 | 适用场景 |
|------|--------|--------|--------|---------|
| 直接调用 | 高 | 低 | 低 | 简单管道，Agent 数量少 |
| 消息传递 | 低 | 高 | 中 | Agent 需要解耦，可能动态增减 |
| 共享状态 | 低 | 高 | 中 | 多个 Agent 需要看到全局信息 |

**实际项目中**：通常混合使用。我们的健康管家会用**共享状态 + 编排器**的组合。

---

## 第二部分：消息格式设计

### 2.1 结构化消息

Agent 之间传递 JSON，字段明确。

```python
# 定义消息格式
message = {
    "from": "parse_agent",       # 发送者
    "to": "nutrition_agent",     # 接收者
    "type": "food_parsed",       # 消息类型
    "data": {                    # 消息内容
        "foods": [{"name": "牛肉面", "amount": "一碗"}]
    },
    "timestamp": "2026-04-13T10:00:00"
}
```

**优点**：下游 Agent 可以精确解析，不会误解。
**缺点**：需要提前约定 Schema，不够灵活。

### 2.2 自然语言消息

Agent 之间传递自然语言文本。

```python
# Agent A 的输出直接作为 Agent B 的输入
agent_a_output = "用户吃了一碗牛肉面，大约 500 克，加了一个鸡蛋"
agent_b_input = agent_a_output  # 直接传文本
```

**优点**：灵活，不需要约定格式。
**缺点**：下游 Agent 需要自己理解，可能误解。

### 2.3 实际选择

```
简单系统（< 5 个 Agent）：自然语言就够了
复杂系统（> 5 个 Agent）：结构化消息更可靠
混合方案：Agent 内部用自然语言思考，Agent 之间用结构化消息通信
```

---

## 第三部分：编排器（Orchestrator）

### 3.1 什么是编排器

编排器是 Multi-Agent 系统的"指挥官"，负责：

```
1. 接收用户请求
2. 决定调用哪些 Agent、什么顺序
3. 管理 Agent 之间的数据传递
4. 处理异常和重试
5. 汇总结果返回给用户
```

```
类比 Java：
  - Spring 的 DispatcherServlet（路由 + 编排）
  - 工作流引擎（如 Camunda / Activiti）
  - 微服务编排器（如 Netflix Conductor）
```

### 3.2 编排器 vs 路由器

```
路由器（课程 19）：只做分发，选一个 Agent 执行
编排器（本课）：分发 + 协调 + 状态管理 + 结果汇总

路由器：switch-case
编排器：工作流引擎
```

### 3.3 编排器的两种风格

```
风格 1：硬编码编排（代码定义流程）
  if intent == "diet":
      step1 = parse_agent(input)
      step2 = nutrition_agent(step1)
      step3 = advice_agent(step2)
  
  优点：流程清晰，容易调试
  缺点：加新流程要改代码

风格 2：LLM 驱动编排（让 LLM 决定流程）
  orchestrator_agent("用户说了XXX，你有这些Agent可用：[...]，请决定调用顺序")
  
  优点：灵活，能处理意外情况
  缺点：不可控，可能做出错误决策
```

**我们的选择**：先用硬编码编排（可靠），关键决策点用 LLM（灵活）。

---

## 第四部分：共享上下文

### 4.1 AgentContext：所有 Agent 共享的"黑板"

```python
# AgentContext 就是一个字典，所有 Agent 都能读写
# 类比 Java：类似 Spring 的 ApplicationContext 或 ThreadLocal
context = {
    "user_input": "原始输入",
    "user_profile": {"name": "张三", "goal": "减肥"},
    "parsed_data": None,
    "nutrition_data": None,
    "exercise_data": None,
    "final_advice": None,
    "history": []  # 执行历史，记录每个 Agent 做了什么
}
```

### 4.2 为什么需要共享上下文

```
场景：建议 Agent 需要知道用户的减肥目标

没有共享上下文：
  建议 Agent 只看到营养数据 → 给出通用建议

有共享上下文：
  建议 Agent 看到营养数据 + 用户目标是减肥 → 给出针对性建议
  "你今天摄入 1800 卡，对于你的减肥目标来说偏高了 200 卡"
```

---

## 小结

```
本课三个核心概念：

1. 通信方式：直接调用 → 消息传递 → 共享状态（解耦程度递增）
2. 编排器：Multi-Agent 的指挥官，管理流程和状态
3. 共享上下文：Agent 之间的"黑板"，让每个 Agent 都能看到全局信息

下节课（21）：把这些概念组合起来，构建一个完整的 Multi-Agent 系统
```
