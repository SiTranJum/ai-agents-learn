# 课程 25：CrewAI 角色驱动架构

## 学习目标
1. 深入理解 CrewAI 的角色驱动设计哲学
2. 掌握 Agent/Task/Crew 三层模型的内部机制
3. 理解 CrewAI 的任务调度和协作流程
4. 对比 CrewAI 与 LangGraph 在 Multi-Agent 场景的差异
5. 能用 CrewAI 实现角色化的 Multi-Agent 系统

## 课程内容

### 1. CrewAI 的设计哲学（20 分钟）

#### 1.1 核心理念：Agent 是有角色的团队成员
```
CrewAI 的隐喻：一个项目组
- Agent = 团队成员（有角色、技能、目标）
- Task = 工作任务（有描述、预期输出、负责人）
- Crew = 项目组（管理成员和任务的执行）
- Process = 工作模式（串行/层级/共识）
```

#### 1.2 与 LangGraph 的本质差异
```
LangGraph：图编排（开发者定义流程）
- 开发者画图 → 定义节点和边 → 控制每一步
- 适合：流程明确、需要精确控制的场景

CrewAI：角色协作（Agent 自主协作）
- 开发者定义角色和任务 → Agent 自主协作完成
- 适合：任务可以自然分工、角色职责清晰的场景
```

### 2. Agent/Task/Crew 三层模型深度解析（40 分钟）

#### 2.1 Agent 的内部结构
```python
from crewai import Agent

agent = Agent(
    role="营养分析师",           # 角色名称
    goal="分析用户饮食并给出建议",  # 目标
    backstory="你是一位有10年经验的营养师...",  # 背景故事
    tools=[food_search_tool],    # 可用工具
    llm=llm,                     # 使用的 LLM
    verbose=True,                # 是否输出详细日志
    allow_delegation=True,       # 是否允许委派任务给其他 Agent
    max_iter=5,                  # 最大迭代次数
    memory=True                  # 是否启用记忆
)
```

**Agent 的执行机制**：
- 内部使用 ReAct 模式（Thought → Action → Observation）
- `backstory` 会注入到 System Prompt 中
- `goal` 影响 Agent 的决策方向
- `allow_delegation` 控制是否可以把子任务交给其他 Agent

#### 2.2 Task 的内部结构
```python
from crewai import Task

task = Task(
    description="分析用户今天的饮食记录，计算总热量",
    expected_output="包含每餐热量和总热量的分析报告",
    agent=nutrition_agent,       # 负责的 Agent
    context=[previous_task],     # 依赖的前置任务（获取其输出）
    tools=[calorie_calculator],  # 任务专用工具
    output_file="report.md"      # 输出到文件
)
```

**Task 的执行机制**：
- `context` 实现任务间的数据传递
- 前置任务的输出会注入到当前任务的 Prompt 中
- `expected_output` 引导 Agent 生成符合预期的输出

#### 2.3 Crew 的编排机制
```python
from crewai import Crew, Process

crew = Crew(
    agents=[nutrition_agent, exercise_agent, report_agent],
    tasks=[analyze_diet, suggest_exercise, generate_report],
    process=Process.sequential,  # 串行执行
    verbose=True,
    memory=True
)

result = crew.kickoff()
```

**Process 类型**：
- `sequential`：任务按顺序执行，前一个的输出传给下一个
- `hierarchical`：有一个 Manager Agent 负责分配和协调任务

### 3. CrewAI 内部执行流程（30 分钟）

#### 3.1 Sequential Process 执行流程
```
crew.kickoff() 的内部流程：

1. 初始化所有 Agent（注入 role、goal、backstory 到 Prompt）
2. 按顺序遍历 tasks
3. 对每个 task：
   a. 收集 context（前置任务的输出）
   b. 构造完整 Prompt（task description + context + expected_output）
   c. 调用 agent.execute_task(task)
   d. Agent 内部执行 ReAct 循环
   e. 保存 task 输出
4. 返回最终结果
```

#### 3.2 Hierarchical Process 执行流程
```
层级模式：Manager Agent 负责协调

1. Manager Agent 接收所有任务
2. Manager 决定任务分配顺序
3. Manager 将任务委派给合适的 Agent
4. Agent 执行任务并返回结果
5. Manager 审核结果，决定是否需要重做
6. 所有任务完成后，Manager 汇总输出
```

#### 3.3 Agent 间的委派机制
```python
# 当 allow_delegation=True 时
# Agent A 可以在执行过程中把子任务交给 Agent B

# 内部实现：
# 1. Agent A 在 ReAct 循环中决定需要委派
# 2. 框架自动创建一个 DelegationTool
# 3. Agent A 调用 DelegationTool，指定目标 Agent 和任务
# 4. 目标 Agent 执行子任务并返回结果
# 5. Agent A 继续自己的任务
```

### 4. CrewAI 的记忆系统（20 分钟）

#### 4.1 三层记忆
```
CrewAI 的记忆架构：
├─ Short-term Memory：当前任务的上下文
├─ Long-term Memory：跨任务的经验积累
└─ Entity Memory：实体信息（人、地点、概念）
```

#### 4.2 记忆如何影响 Agent 行为
- 短期记忆：当前对话上下文
- 长期记忆：Agent 从过去任务中学到的经验
- 实体记忆：记住用户提到的关键实体

### 5. 实战：用 CrewAI 构建健康管理团队（35 分钟）

#### 5.1 角色设计
```
健康管理 Crew：
├─ 营养分析师 Agent：分析饮食、计算热量
├─ 运动教练 Agent：制定运动计划
└─ 健康报告 Agent：汇总分析、生成报告
```

#### 5.2 完整实现
（使用通义千问 API，包含详细注释）

### 6. CrewAI vs LangGraph 深度对比（20 分钟）

| 维度 | CrewAI | LangGraph |
|------|--------|-----------|
| 抽象层次 | 高（角色/任务） | 低（节点/边） |
| 流程控制 | 框架管理 | 开发者定义 |
| 灵活性 | 中等 | 高 |
| Multi-Agent | 原生支持 | 需要自己编排 |
| 调试难度 | 较高（黑盒） | 较低（可追踪） |
| 适用场景 | 角色明确的协作 | 复杂流程控制 |

### 7. 练习（25 分钟）

#### 练习 1：设计一个 3 Agent 的健康咨询 Crew
#### 练习 2：对比 Sequential 和 Hierarchical 模式的效果差异

## 预计时长
约 3 小时

## 完成标准
- 理解 CrewAI 的角色驱动设计
- 能用 CrewAI 实现 Multi-Agent 系统
- 理解 CrewAI 与 LangGraph 的适用场景差异
