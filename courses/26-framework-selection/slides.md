# 课程 26：框架选型实战

---

## 开场：选框架不是选"最好的"，是选"最合适的"

前面四节课我们学了：
- 课程 22：框架设计哲学（为什么需要框架）
- 课程 23：LangChain 架构（组件组合 + LCEL）
- 课程 24：LangGraph 状态机（图编排 + Checkpoint）
- 课程 25：CrewAI 角色驱动（团队协作 + Flow）

现在你对三大框架都有了理解。但真正做项目时，最难的问题是：**我该用哪个？**

这节课不讲理论，直接用**同一个需求**在四种方式下实现，让你亲眼看到差异。

---

## 第一部分：框架评估方法论

### 评估维度

```
选框架要看两个维度：

技术维度（能不能做）：
├─ 架构适配度：框架的抽象是否匹配你的需求
├─ 性能：延迟、吞吐量、资源消耗
├─ 可扩展性：能否满足未来需求
├─ 可观测性：调试、监控、日志是否方便
└─ 生态成熟度：社区、文档、第三方集成

工程维度（好不好用）：
├─ 学习曲线：团队上手难度
├─ 开发效率：从需求到实现的速度
├─ 可维护性：代码可读性、测试友好度
├─ 社区活跃度：issue 响应、版本迭代
└─ 锁定风险：框架绑定程度
```

类比 Java 选框架：
- 你不会因为 Spring 功能最全就所有项目都用 Spring
- 小工具用 Vert.x 可能更合适，微服务用 Quarkus 可能更轻量
- **关键是需求匹配，不是功能多少**

### 一个实用的决策流程

```
你的需求是什么？
│
├─ 简单的 LLM 调用链（Prompt → LLM → 解析）
│   → 手写 或 LangChain LCEL
│
├─ 需要工具调用的单 Agent
│   → LangChain + LangGraph create_react_agent
│
├─ 复杂流程（多步骤、条件分支、循环、人工审核）
│   → LangGraph
│
├─ 多 Agent 协作（角色明确、任务可分工）
│   → CrewAI
│
└─ 以上都有
    → 混合使用（LangGraph 做主流程 + CrewAI 做局部协作）
```

---

## 第二部分：同一需求的四种实现

### 需求描述

```
健康饮食分析 Agent：
1. 接收用户的饮食描述（如"早餐吃了牛奶和面包"）
2. 分析营养摄入
3. 给出改善建议
```

这是一个简单但完整的需求，足以看出四种方式的差异。

### 实现 1：手写版本（基线）

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def analyze_diet(user_input: str) -> str:
    """手写版本：最直接，最简单"""
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {
                "role": "system",
                "content": "你是营养师。分析用户饮食，估算热量，给出2条改善建议。回答简洁。"
            },
            {"role": "user", "content": user_input}
        ],
    )
    return response.choices[0].message.content

result = analyze_diet("早餐：牛奶+面包，午餐：米饭+红烧肉+青菜")
```

**优点**：简单直接，没有任何依赖，完全可控
**缺点**：没有流式、没有重试、没有组合能力，扩展要改很多代码

### 实现 2：LangChain LCEL 版本

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# LCEL 版本：声明式，可组合
chain = (
    ChatPromptTemplate.from_messages([
        ("system", "你是营养师。分析用户饮食，估算热量，给出2条改善建议。回答简洁。"),
        ("user", "{input}"),
    ])
    | llm
    | StrOutputParser()
)

result = chain.invoke({"input": "早餐：牛奶+面包，午餐：米饭+红烧肉+青菜"})

# 自动支持流式
for chunk in chain.stream({"input": "早餐：牛奶+面包"}):
    print(chunk, end="")
```

**优点**：自动支持 stream/batch/async，可组合，可加 retry/fallback
**缺点**：对于这个简单需求，和手写差别不大

### 实现 3：LangGraph 版本

```python
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import TypedDict, Annotated
from operator import add

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

class DietState(TypedDict):
    messages: Annotated[list, add]
    analysis: str
    suggestions: str

def analyze(state: DietState) -> dict:
    """分析饮食"""
    user_msg = state["messages"][-1].content
    response = llm.invoke([
        SystemMessage(content="分析以下饮食的营养摄入，估算总热量。用2-3句话回答。"),
        HumanMessage(content=user_msg),
    ])
    return {"analysis": response.content}

def suggest(state: DietState) -> dict:
    """给出建议"""
    response = llm.invoke([
        SystemMessage(content="根据以下饮食分析，给出2条改善建议。"),
        HumanMessage(content=state["analysis"]),
    ])
    return {"suggestions": response.content}

# 构建图
graph = StateGraph(DietState)
graph.add_node("analyze", analyze)
graph.add_node("suggest", suggest)
graph.add_edge(START, "analyze")
graph.add_edge("analyze", "suggest")
graph.add_edge("suggest", END)

app = graph.compile()
result = app.invoke({
    "messages": [HumanMessage(content="早餐：牛奶+面包，午餐：米饭+红烧肉+青菜")],
    "analysis": "",
    "suggestions": "",
})
```

**优点**：状态清晰，可加 Checkpoint、条件分支、Human-in-the-loop
**缺点**：对于这个简单需求，明显过度设计（杀鸡用牛刀）

### 实现 4：CrewAI 版本

```python
from crewai import Agent, Task, Crew, LLM

llm = LLM(
    model="openai/qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
)

analyst = Agent(
    role="营养分析师",
    goal="分析饮食，估算热量，给出建议",
    backstory="你是注册营养师，擅长饮食分析。回答简洁。",
    llm=llm,
)

task = Task(
    description="分析这份饮食记录：早餐：牛奶+面包，午餐：米饭+红烧肉+青菜。估算热量并给出2条建议。",
    expected_output="热量估算 + 2条改善建议",
    agent=analyst,
)

crew = Crew(agents=[analyst], tasks=[task])
result = crew.kickoff()
```

**优点**：角色定义清晰，Multi-Agent 扩展方便
**缺点**：单 Agent 场景下，比手写和 LCEL 都重；调试不如 LangGraph 透明

---

## 第三部分：四种实现的对比分析

### 代码量和复杂度

| 维度 | 手写 | LangChain | LangGraph | CrewAI |
|------|------|-----------|-----------|--------|
| 核心代码量 | ~15 行 | ~15 行 | ~40 行 | ~20 行 |
| 依赖包 | openai | langchain-openai, langchain-core | + langgraph | crewai |
| 学习成本 | 最低 | 低 | 中 | 中 |
| 可读性 | 高 | 高 | 中（需理解状态机） | 高 |

### 扩展能力

| 需求变化 | 手写 | LangChain | LangGraph | CrewAI |
|---------|------|-----------|-----------|--------|
| 加流式输出 | 改代码 | 自动支持 | 自动支持 | 支持 |
| 加工具调用 | 改很多 | 简单 | 简单 | 简单 |
| 加多步骤流程 | 改很多 | 用 LCEL 组合 | 加节点和边 | 加 Task |
| 加 Multi-Agent | 重写 | 需要自己编排 | 需要自己编排 | 原生支持 |
| 加人工审核 | 自己实现 | 自己实现 | Checkpoint + interrupt | human_input=True |
| 加记忆 | 自己实现 | 自己实现 | Checkpoint | 内置三层记忆 |

### 核心结论

```
简单需求（单 LLM 调用）→ 手写 或 LangChain LCEL
  理由：框架带来的收益不足以抵消学习成本

中等需求（多步骤 + 工具调用）→ LangChain LCEL + LangGraph
  理由：LCEL 处理简单链，LangGraph 处理复杂流程

复杂需求（Multi-Agent + 状态管理）→ LangGraph + CrewAI
  理由：LangGraph 做精确流程控制，CrewAI 做角色协作
```

---

## 第四部分：健康管家项目技术选型

### 回顾产品需求

```
健康管家的核心功能：
1. 自然语言饮食记录 → 意图识别 + 实体提取
2. 拍照识别食物 → 工具调用
3. 营养分析 + 个性化建议 → 多步骤推理
4. AI 记忆系统 → 短期/长期记忆
5. 主动提醒 → 定时任务
6. 多轮对话 → 上下文管理
```

### 需求 → 框架映射

| 功能 | 技术需求 | 推荐框架 |
|------|---------|---------|
| 对话主循环 | 意图识别 → 路由 → 执行 → 回复 | LangGraph（需要精确的状态控制） |
| 饮食记录 | 实体提取 + 工具调用 | LangChain LCEL（简单链） |
| 营养分析 | 多步骤推理 + 知识检索 | LangGraph（多步骤 + RAG） |
| 记忆系统 | 短期/长期/实体记忆 | 自己实现（更灵活）或 LangGraph Checkpoint |
| 健康报告 | 多 Agent 协作生成 | CrewAI（营养师 + 运动教练 + 报告员） |
| 主动提醒 | 定时触发 | 后端定时任务（不需要框架） |

### 推荐方案

```
健康管家的技术架构：

┌─────────────────────────────────────────────┐
│  对话主循环（LangGraph）                      │
│  意图识别 → 路由 → 执行 → 回复               │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │ 饮食记录  │  │ 营养分析  │  │ 健康报告   │ │
│  │ LCEL 链   │  │ LangGraph │  │ CrewAI    │ │
│  └──────────┘  └──────────┘  └───────────┘ │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ 记忆系统（自己实现 + LangGraph 状态）  │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**为什么是混合方案？**

1. **LangGraph 做主循环**：对话流程需要精确的状态控制（意图识别 → 路由 → 不同处理分支），LangGraph 的图模型最合适
2. **LangChain LCEL 做简单链**：饮食记录这种"提取 → 查询 → 存储"的线性流程，LCEL 最简洁
3. **CrewAI 做报告生成**：健康报告需要多个"专家"协作（营养师分析 + 运动教练建议 + 报告员汇总），CrewAI 的角色模型最自然
4. **记忆系统自己实现**：我们的记忆需求（短期/中期/长期分层 + 向量检索）比较定制化，框架内置的记忆不够灵活

---

## 第五部分：框架混合使用策略

### LangChain + LangGraph 组合（最常见）

```python
# LangChain 提供组件（LLM、Prompt、Parser）
# LangGraph 提供编排（图、状态、Checkpoint）

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph

# LangChain 的组件
llm = ChatOpenAI(model="qwen-plus", ...)
prompt = ChatPromptTemplate.from_messages([...])

# 在 LangGraph 的节点中使用 LangChain 组件
def my_node(state):
    chain = prompt | llm  # LCEL 链
    result = chain.invoke({"input": state["user_input"]})
    return {"output": result.content}

# LangGraph 编排
graph = StateGraph(...)
graph.add_node("process", my_node)
```

**这是最推荐的组合**：LangChain 负责"怎么调用 LLM"，LangGraph 负责"什么时候调用"。

### LangGraph + CrewAI 组合

```python
# LangGraph 做主流程，某个节点内部用 CrewAI

def generate_report_node(state):
    """LangGraph 的一个节点，内部用 CrewAI 生成报告"""
    crew = Crew(
        agents=[nutrition_agent, exercise_agent, report_agent],
        tasks=[...],
        process=Process.sequential,
    )
    result = crew.kickoff(inputs={"data": state["analysis"]})
    return {"report": result.raw}

# LangGraph 图中的一个节点
graph.add_node("generate_report", generate_report_node)
```

### 渐进式迁移策略

```
不要一开始就用框架！推荐的路径：

阶段 1：手写 Agent（验证需求）
  → 先用最简单的方式跑通核心功能
  → 确认需求是对的

阶段 2：引入 LangChain（提升开发效率）
  → 用 LCEL 替代手写的 LLM 调用链
  → 获得 stream/batch/retry 等能力

阶段 3：引入 LangGraph（处理复杂流程）
  → 当流程变复杂（条件分支、循环、人工审核）时引入
  → 用 Checkpoint 实现状态持久化

阶段 4：引入 CrewAI（Multi-Agent 场景）
  → 当需要多 Agent 协作时引入
  → 用 CrewAI 处理角色明确的协作场景
```

**核心原则：不要为了用框架而用框架。先手写，遇到痛点再引入框架解决。**

---

## 第六部分：避免过度依赖框架

### 框架的风险

```
1. 版本不稳定
   LangChain 从 0.1 到 1.0 经历了大量 breaking changes
   CrewAI 也在快速迭代中
   → 核心业务逻辑不要和框架深度耦合

2. 黑盒问题
   框架封装了很多细节，出问题时难以调试
   → 理解框架原理（这就是前几节课的价值）

3. 锁定风险
   深度使用一个框架后，迁移成本很高
   → 在框架和业务之间加一层抽象
```

### 防锁定的架构建议

```python
# ❌ 业务代码直接依赖框架
class HealthService:
    def analyze(self, input):
        chain = ChatPromptTemplate(...) | ChatOpenAI(...) | StrOutputParser()
        return chain.invoke(input)

# ✅ 加一层抽象，业务代码不直接依赖框架
class LLMService:
    """抽象层：隔离框架依赖"""
    def chat(self, system_prompt: str, user_input: str) -> str:
        # 内部用 LangChain，但接口不暴露框架细节
        chain = ChatPromptTemplate(...) | self.llm | StrOutputParser()
        return chain.invoke({"input": user_input})

class HealthService:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def analyze(self, input):
        return self.llm.chat("你是营养师...", input)
        # 如果以后换框架，只改 LLMService，不改 HealthService
```

类比 Java：
- `LLMService` ≈ Repository 接口
- LangChain 实现 ≈ JPA 实现
- 如果以后换框架 ≈ 换成 MyBatis 实现
- 业务层不受影响

---

## 小结

### 框架选型的核心原则

1. **需求驱动**：先明确需求，再选框架，不要反过来
2. **最简方案**：能手写解决的不用框架，能用 LCEL 的不用 LangGraph
3. **渐进引入**：先手写验证 → 再引入框架优化
4. **混合使用**：不同模块用不同框架，各取所长
5. **防锁定**：核心业务和框架之间加抽象层

### 健康管家项目的最终选型

| 模块 | 框架 | 原因 |
|------|------|------|
| 对话主循环 | LangGraph | 需要精确的状态控制和流程编排 |
| 简单 LLM 链 | LangChain LCEL | 简洁、可组合、自动支持流式 |
| 健康报告 | CrewAI | 多角色协作，角色模型自然 |
| 记忆系统 | 自己实现 | 定制化需求，框架内置的不够灵活 |
| RAG | LangChain | 生态丰富，向量数据库集成齐全 |

### 框架全景速查

| | 手写 | LangChain | LangGraph | CrewAI |
|---|---|---|---|---|
| 核心能力 | 完全可控 | 组件组合 | 图编排 | 角色协作 |
| 适合场景 | 简单/学习 | 通用 | 复杂流程 | Multi-Agent |
| 学习曲线 | 最低 | 低 | 中 | 中 |
| 灵活性 | 最高 | 高 | 高 | 中 |
| 生产就绪 | 需要自己补 | 是 | 是 | 基本是 |
