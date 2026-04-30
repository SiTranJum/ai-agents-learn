# 课程 25：CrewAI 角色驱动架构

---

## 开场：从"画流程图"到"组建团队"

上两节课我们学了 LangChain（组件组合）和 LangGraph（图编排）。

它们的共同点是：**开发者定义流程**。你画节点、连边、写条件，Agent 按你画的图走。

CrewAI 换了一种思路：**你不画流程图，你组建一个团队**。

```
LangGraph 的思维：
  "我要画一个流程：先分析 → 再检索 → 再生成 → 最后审核"

CrewAI 的思维：
  "我要组建一个团队：营养师负责分析，教练负责运动方案，报告员负责汇总"
```

类比 Java 世界：
- LangGraph ≈ Spring Batch（你定义 Step 和 Flow）
- CrewAI ≈ 一个项目管理工具（你定义角色和任务，框架负责调度）

---

## 第一部分：CrewAI 的核心概念

### 三层模型：Agent / Task / Crew

```
CrewAI 的隐喻：一个项目组

Agent = 团队成员（有角色、技能、目标）
  ↓ 被分配
Task  = 工作任务（有描述、预期输出、负责人）
  ↓ 被管理
Crew  = 项目组（管理成员和任务的执行）
```

类比你在公司里的经历：
- Agent = 开发工程师、测试工程师、产品经理
- Task = "实现登录功能"、"编写测试用例"、"写需求文档"
- Crew = 项目组，决定谁先做、谁后做、怎么协作

### 与 LangGraph 的本质差异

| | LangGraph | CrewAI |
|---|---|---|
| 核心隐喻 | 流程图 | 项目团队 |
| 开发者做什么 | 画节点和边 | 定义角色和任务 |
| 流程控制 | 开发者精确控制 | 框架自动调度 |
| 灵活性 | 高（你控制一切） | 中（框架帮你管） |
| 适合场景 | 流程复杂、需要精确控制 | 角色明确、任务可自然分工 |

---

## 第二部分：Agent — 团队成员

### Agent 的定义

```python
from crewai import Agent, LLM

# CrewAI 用自己的 LLM 类封装模型配置
# 支持 "provider/model" 格式，底层用 litellm 路由到各家 API
llm = LLM(
    model="openai/qwen-plus",  # provider/model 格式
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="sk-a4ae611c3f9c4df89a133e621b2b7851",
)

# 定义一个 Agent：营养分析师
# 类比 Java：new Employee("营养分析师", "分析饮食", skills, resume)
nutrition_agent = Agent(
    role="营养分析师",
    # role: 角色名称，会注入到 System Prompt 中
    # 类比：员工的岗位名称

    goal="分析用户的饮食记录，计算营养摄入，给出专业建议",
    # goal: 这个 Agent 的工作目标
    # 影响 Agent 的决策方向（LLM 会参考这个目标来决定行动）

    backstory="""你是一位有 10 年经验的注册营养师。
    擅长分析饮食结构，熟悉中国居民膳食指南。
    你的分析风格是数据驱动、建议具体可执行。""",
    # backstory: 角色的背景故事
    # 会完整注入到 System Prompt，影响 LLM 的回答风格和专业度
    # 类比：员工的简历和工作经历

    tools=[food_search_tool],
    # tools: 这个 Agent 可以使用的工具列表

    llm=llm,
    # llm: 使用的语言模型

    verbose=True,
    # verbose: 是否输出详细的思考过程日志

    allow_delegation=False,
    # allow_delegation: 是否允许把子任务委派给其他 Agent
    # True = 这个 Agent 可以说"这个子问题让运动教练来回答"
    # False = 必须自己完成所有工作

    max_iter=5,
    # max_iter: ReAct 循环的最大迭代次数（防止无限循环）

    memory=True,
    # memory: 是否启用记忆（短期 + 长期 + 实体记忆）
)
```

### Agent 内部执行机制

```
当 Agent 收到一个 Task 时，内部执行流程：

1. 构造 System Prompt：
   "你是 {role}。{backstory}。你的目标是 {goal}。"

2. 构造 User Prompt：
   "任务：{task.description}
    预期输出：{task.expected_output}
    上下文：{前置任务的输出}"

3. 进入 ReAct 循环（和我们课程 11 学的一样）：
   Thought → Action → Observation → Thought → ... → Final Answer

4. 返回结果
```

**关键理解**：CrewAI 的 Agent 内部就是 ReAct 模式，和我们手写的原理一样。CrewAI 的价值不在于单个 Agent 的执行，而在于**多个 Agent 的协作编排**。

---

## 第三部分：Task — 工作任务

### Task 的定义

```python
from crewai import Task

# 定义一个任务：分析饮食
# 类比 Java：new JiraTicket("分析饮食", "营养分析师", "分析报告")
analyze_diet_task = Task(
    description="""分析用户今天的饮食记录：
    早餐：牛奶 + 全麦面包
    午餐：米饭 + 红烧肉 + 青菜
    晚餐：面条 + 煎蛋
    
    请计算每餐的大致热量和营养成分。""",
    # description: 任务的详细描述
    # 会作为 User Prompt 的一部分发给 Agent

    expected_output="包含每餐热量、蛋白质、碳水、脂肪的分析表格",
    # expected_output: 期望的输出格式
    # 引导 Agent 生成符合预期的输出（类似 Prompt 中的 output format）

    agent=nutrition_agent,
    # agent: 负责执行这个任务的 Agent
)

# 定义第二个任务：生成建议（依赖第一个任务的输出）
suggest_task = Task(
    description="根据饮食分析结果，给出 3 条具体的改善建议",
    expected_output="3 条具体可执行的饮食改善建议",
    agent=nutrition_agent,
    context=[analyze_diet_task],
    # context: 前置任务列表
    # analyze_diet_task 的输出会自动注入到这个任务的 Prompt 中
    # 类比：Jira 中的"阻塞关系"，前置任务完成后才能开始
)
```

### Task 的高级参数

```python
from pydantic import BaseModel

# 结构化输出：用 Pydantic 模型定义输出格式
class DietAnalysis(BaseModel):
    total_calories: int
    protein_grams: float
    carb_grams: float
    fat_grams: float
    suggestions: list[str]

task = Task(
    description="分析饮食并给出建议",
    expected_output="结构化的饮食分析报告",
    agent=nutrition_agent,

    output_pydantic=DietAnalysis,
    # output_pydantic: 强制输出为 Pydantic 模型
    # 框架会自动让 LLM 输出 JSON 并解析为 DietAnalysis 对象
    # 类比 Java：指定返回类型 ResponseEntity<DietAnalysis>

    human_input=True,
    # human_input: 任务完成后需要人工确认
    # 类比：Jira 中的"需要审批"状态

    callback=lambda output: print(f"任务完成: {output}"),
    # callback: 任务完成后的回调函数
    # 类比 Java：CompletableFuture.thenAccept()
)
```

---

## 第四部分：Crew — 项目组

### Crew 的定义和执行

```python
from crewai import Crew, Process

# 组建项目组
# 类比：在 Jira 中创建一个 Sprint，分配人员和任务
crew = Crew(
    agents=[nutrition_agent, exercise_agent, report_agent],
    # agents: 团队成员列表

    tasks=[analyze_diet_task, suggest_exercise_task, generate_report_task],
    # tasks: 任务列表（按顺序排列）

    process=Process.sequential,
    # process: 执行模式
    # sequential = 串行（任务按顺序执行）
    # hierarchical = 层级（有 Manager Agent 负责分配）

    verbose=True,
    # verbose: 输出详细执行日志

    memory=True,
    # memory: 启用团队级别的记忆
)

# 启动执行
# 类比：Sprint 开始，团队按计划执行任务
result = crew.kickoff()
# kickoff() 返回最后一个任务的输出
```

### 两种执行模式

**Sequential（串行）**：
```
任务按顺序执行，前一个的输出传给下一个

Task 1（营养分析师）→ Task 2（运动教练）→ Task 3（报告员）
     输出 ──────────→ 作为 context ──→ 作为 context

类比：瀑布式开发，一步一步来
```

**Hierarchical（层级）**：
```
有一个 Manager Agent 负责协调

Manager Agent
  ├─ 分配 Task 1 给营养分析师
  ├─ 审核结果，决定是否需要重做
  ├─ 分配 Task 2 给运动教练
  ├─ 审核结果
  └─ 分配 Task 3 给报告员

类比：有项目经理的团队，PM 负责分配和审核
```

```python
# 层级模式需要指定 manager
crew = Crew(
    agents=[nutrition_agent, exercise_agent, report_agent],
    tasks=[task1, task2, task3],
    process=Process.hierarchical,
    manager_llm=llm,  # Manager Agent 使用的 LLM
)
```

---

## 第五部分：CrewAI 的记忆系统

### 三层记忆

```
CrewAI 的记忆架构：

Short-term Memory（短期记忆）
  └─ 当前任务执行过程中的上下文
  └─ 类比：你正在开会时的工作记忆

Long-term Memory（长期记忆）
  └─ 跨任务的经验积累（存储在本地数据库）
  └─ 类比：你从过去项目中学到的经验

Entity Memory（实体记忆）
  └─ 记住对话中提到的关键实体（人名、食物、数值等）
  └─ 类比：你记住"张三对花生过敏"这种具体信息
```

### 记忆如何影响 Agent 行为

```python
# 启用记忆后，Agent 的 Prompt 会自动注入相关记忆

# 第一次执行：
# "用户说他对花生过敏" → Entity Memory 记住

# 第二次执行：
# Agent 的 Prompt 中会自动加入：
# "已知信息：用户对花生过敏"
# → Agent 在推荐食物时会自动避开花生
```

---

## 第六部分：Flow — 事件驱动编排（CrewAI 新特性）

### Flow 是什么

Flow 是 CrewAI 新增的编排层，解决了一个问题：**Crew 内部是自主协作的，但多个 Crew 之间怎么编排？**

```
没有 Flow：
  Crew A（饮食分析团队）→ 手动传递结果 → Crew B（运动规划团队）

有了 Flow：
  Flow 自动编排多个 Crew，支持条件分支、并行、等待
```

### Flow 的基本用法

```python
from crewai.flow.flow import Flow, listen, start, router

class HealthFlow(Flow):
    """
    健康管理流程：
    收集信息 → 分析（饮食分析 Crew）→ 路由 → 生成方案
    """

    @start()  # 入口方法
    def collect_info(self):
        """收集用户信息"""
        return {"user_input": "我170cm，80kg，想减肥"}

    @listen(collect_info)  # 监听 collect_info 完成后触发
    def analyze(self, info):
        """调用饮食分析 Crew"""
        crew = Crew(agents=[...], tasks=[...])
        return crew.kickoff(inputs=info)

    @router(analyze)  # 根据分析结果路由
    def route(self, analysis):
        """根据分析结果决定下一步"""
        if analysis.total_calories > 2000:
            return "need_diet_plan"  # 需要减脂方案
        return "maintain"            # 维持现状

    @listen("need_diet_plan")  # 监听路由结果
    def create_diet_plan(self):
        """生成减脂方案"""
        crew = Crew(agents=[...], tasks=[...])
        return crew.kickoff()

    @listen("maintain")
    def send_encouragement(self):
        """发送鼓励消息"""
        return "你的饮食很健康，继续保持！"

# 执行
flow = HealthFlow()
result = flow.kickoff()
```

**Flow vs LangGraph**：
- LangGraph 用图（节点 + 边）编排
- Flow 用事件（`@start` + `@listen` + `@router`）编排
- Flow 更适合"多个 Crew 之间的协调"，LangGraph 更适合"单个 Agent 内部的复杂流程"

---

## 第七部分：CrewAI vs LangGraph 深度对比

| 维度 | CrewAI | LangGraph |
|------|--------|-----------|
| 抽象层次 | 高（角色/任务/团队） | 低（节点/边/状态） |
| 核心隐喻 | 项目团队协作 | 状态机/流程图 |
| 流程控制 | 框架自动调度 | 开发者精确定义 |
| Multi-Agent | 原生支持（Crew） | 需要自己编排 |
| 灵活性 | 中等（框架约束多） | 高（你控制一切） |
| 调试难度 | 较高（Agent 自主决策，不可预测） | 较低（流程确定，可追踪） |
| 记忆系统 | 内置三层记忆 | 需要自己实现或用 Checkpoint |
| 适用场景 | 角色明确的团队协作 | 复杂流程控制、需要精确状态管理 |

### 什么时候用 CrewAI？

- 任务可以自然分工给不同"角色"
- 不需要精确控制每一步的执行顺序
- 想快速搭建 Multi-Agent 原型

### 什么时候用 LangGraph？

- 流程复杂，有很多条件分支和循环
- 需要精确控制状态转换
- 需要 Human-in-the-loop、Checkpoint 等高级特性

### 什么时候混合使用？

```
推荐的混合方案：
- Flow 编排整体流程
- Crew 负责局部自主协作
- LangGraph 处理需要精确控制的关键节点
```

---

## 小结

### CrewAI 的核心设计

1. **角色驱动**：Agent 有 role、goal、backstory，像真实团队成员
2. **任务编排**：Task 有 description、expected_output、context，像 Jira 工单
3. **团队管理**：Crew 管理 Agent 和 Task 的执行，支持串行和层级模式
4. **三层记忆**：短期 + 长期 + 实体，Agent 能记住和学习
5. **Flow 编排**：事件驱动的多 Crew 协调

### 类比总结

| CrewAI | 现实世界 | Java 类比 |
|--------|---------|-----------|
| Agent | 团队成员 | 一个 Service 类 |
| Task | Jira 工单 | 一个方法调用 |
| Crew | 项目组 | Spring Batch Job |
| Process.sequential | 瀑布式开发 | 顺序执行 Step |
| Process.hierarchical | 有 PM 的团队 | 有 Orchestrator 的微服务 |
| Flow | 项目管理工具 | 事件驱动架构 |
