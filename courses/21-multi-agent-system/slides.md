# 课程 21：构建一个完整的 Multi-Agent 系统

课程 19 学了三种协作模式，课程 20 学了通信和编排。
这节课把所有东西组合起来，做一个**真正能用的健康管家 Multi-Agent 系统**。

---

## 第一部分：系统架构

### 1.1 整体设计

```
用户输入
  → Orchestrator（编排器）
      → Router Agent（意图识别）
          ├→ diet:      Pipeline（解析 → 营养 → 建议）
          ├→ analysis:  Fan-out（营养 + 运动 + 睡眠 → 汇总）
          ├→ knowledge: RAG Agent（知识问答）
          └→ chat:      Chat Agent（闲聊）
  → 返回结果给用户

所有 Agent 共享一个 AgentContext（上下文）
```

### 1.2 和微服务架构的对比

```
微服务                          我们的 Multi-Agent
──────────────────────────────────────────────────
API Gateway                     Orchestrator
Service Registry                Agent Registry
Request Context                 AgentContext
Service A → Service B           Agent A → Agent B
Circuit Breaker                 错误处理 + 重试
Distributed Tracing             执行追踪（Trace）
```

你做过微服务，这套架构你很熟。区别只是"服务"变成了"Agent"，"API 调用"变成了"LLM 调用"。

---

## 第二部分：可观测性

### 2.1 为什么需要

Multi-Agent 系统最大的痛点：**出了问题不知道哪个 Agent 出的**。

```
用户："我吃了牛肉面"
系统返回："建议你多喝水"  ← 这建议和牛肉面有什么关系？

问题可能在：
  - 解析 Agent 没提取到"牛肉面"？
  - 营养 Agent 返回了错误数据？
  - 建议 Agent 忽略了营养数据？
```

### 2.2 执行追踪（Trace）

```
类比 Java：类似 Spring Cloud Sleuth / Zipkin 的分布式追踪

每次请求生成一个 trace_id，记录每个 Agent 的：
  - 输入是什么
  - 输出是什么
  - 耗时多少
  - 是否出错
```

### 2.3 日志设计

```python
# 每个 Agent 执行时记录：
trace = {
    "trace_id": "abc123",
    "steps": [
        {
            "agent": "router",
            "input": "我吃了牛肉面",
            "output": {"intent": "diet"},
            "duration_ms": 500
        },
        {
            "agent": "parse",
            "input": "我吃了牛肉面",
            "output": {"foods": [{"name": "牛肉面"}]},
            "duration_ms": 800
        },
        ...
    ]
}
```

---

## 第三部分：错误处理

### 3.1 Multi-Agent 中的错误类型

```
1. Agent 调用失败（API 超时、限流）
   → 重试 1-2 次

2. Agent 返回格式错误（JSON 解析失败）
   → 用默认值兜底，或让 Agent 重新生成

3. Agent 返回内容不合理（营养数据明显错误）
   → 这个最难处理，需要校验逻辑

4. 路由错误（把饮食记录路由到运动 Agent）
   → 目标 Agent 发现输入不对，返回"无法处理"
```

### 3.2 策略

```
简单策略（我们先用这个）：
  - API 失败：重试 2 次
  - JSON 解析失败：返回友好的错误提示
  - 其他错误：记录日志，返回兜底回复

高级策略（后续优化）：
  - 让 LLM 自己判断输出是否合理
  - 多个 Agent 交叉验证
  - 人工审核关键决策
```

---

## 第四部分：完整实现

代码在 `code/health_multi_agent.py`，这是一个完整的健康管家 Multi-Agent 系统。

核心组件：
1. `AgentContext` — 共享上下文
2. `AgentRegistry` — Agent 注册表
3. `Orchestrator` — 编排器（含路由、管道、并行）
4. `Tracer` — 执行追踪
5. 各专业 Agent — 路由、解析、营养、建议、运动、睡眠、知识、闲聊

---

## 小结

```
课程 19-21 的完整脉络：

课程 19：为什么要 Multi-Agent？三种模式（管道、扇出、路由）
课程 20：Agent 怎么通信？编排器 + 共享上下文
课程 21：组合起来，构建完整系统 + 可观测性 + 错误处理

这三课的核心收获：
  1. Multi-Agent 本质是微服务思想在 AI 领域的应用
  2. 编排器是系统的核心，管理流程和状态
  3. 共享上下文让 Agent 能看到全局信息
  4. 可观测性是 Multi-Agent 系统的生命线
```
