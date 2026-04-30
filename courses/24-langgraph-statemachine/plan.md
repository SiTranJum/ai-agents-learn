# 课程 24：LangGraph 状态机编排

## 学习目标
1. 深入理解 LangGraph 的状态机设计思想
2. 掌握 StateGraph 的核心概念：节点、边、条件路由
3. 理解 Checkpoint 机制和状态持久化
4. 掌握 Human-in-the-loop 模式
5. 能用 LangGraph 实现复杂的 Agent 工作流

## 为什么这节课重要？

LangChain 的 Chain 是线性的，但真实的 Agent 流程往往是非线性的：
- **条件分支**：根据 LLM 输出走不同路径
- **循环**：ReAct 模式需要反复执行
- **并行**：多个子任务同时执行
- **人工介入**：关键决策需要人确认

LangGraph 用图（Graph）来表达这些复杂流程，是 LangChain 团队推荐的 Agent 编排方案。

## 课程内容

### 1. 从 Chain 到 Graph 的演进（20 分钟）

#### 1.1 Chain 的局限性
```
Chain（线性）：A → B → C → D
问题：
- 无法表达条件分支
- 无法表达循环
- 无法暂停和恢复
- 无法人工介入
```

#### 1.2 Graph 的优势
```
Graph（图）：
    A → B → C
    ↑       ↓
    └── D ←─┘
    
优势：
- 条件分支：B 可以根据条件走 C 或 D
- 循环：D 可以回到 A
- 暂停/恢复：任意节点可以暂停
- 人工介入：在关键节点等待人确认
```

#### 1.3 类比
```
LangGraph ≈ 工作流引擎（如 Activiti、Camunda）
- StateGraph ≈ BPMN 流程定义
- Node ≈ 流程节点（UserTask、ServiceTask）
- Edge ≈ 流程连线（SequenceFlow）
- Checkpoint ≈ 流程实例快照
- Human-in-the-loop ≈ UserTask（等待人工处理）
```

### 2. StateGraph 核心概念（35 分钟）

#### 2.1 State（状态）
```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
from operator import add

class AgentState(TypedDict):
    """
    状态定义（类比 Java 的 POJO）
    所有节点共享这个状态对象
    """
    messages: Annotated[list, add]  # 消息列表（追加模式）
    current_step: str               # 当前步骤
    tool_results: list              # 工具调用结果
    final_answer: str               # 最终答案
```

**Annotated[list, add] 的含义**：
- `add` 是 reducer 函数
- 当多个节点更新同一字段时，用 `add` 合并（追加）
- 类比 Redux 的 reducer

#### 2.2 Node（节点）
```python
def call_llm(state: AgentState) -> dict:
    """
    节点函数：接收 state，返回 state 的更新
    类比：Spring 的 Service 方法
    """
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}  # 返回要更新的字段

def call_tool(state: AgentState) -> dict:
    """工具调用节点"""
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]
    result = execute_tool(tool_call)
    return {"messages": [result], "tool_results": [result]}
```

#### 2.3 Edge（边）
```python
# 普通边：无条件跳转
graph.add_edge("node_a", "node_b")

# 条件边：根据条件选择下一个节点
def should_continue(state: AgentState) -> str:
    """
    条件函数：返回下一个节点的名称
    类比：BPMN 的 ExclusiveGateway
    """
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "call_tool"    # 有工具调用 → 执行工具
    else:
        return "end"          # 无工具调用 → 结束

graph.add_conditional_edges(
    "call_llm",
    should_continue,
    {"call_tool": "call_tool", "end": END}
)
```

#### 2.4 完整的 StateGraph 构建

```python
from langgraph.graph import StateGraph, END

# 1. 创建图
graph = StateGraph(AgentState)

# 2. 添加节点
graph.add_node("call_llm", call_llm)
graph.add_node("call_tool", call_tool)

# 3. 设置入口
graph.set_entry_point("call_llm")

# 4. 添加边
graph.add_conditional_edges(
    "call_llm",
    should_continue,
    {"call_tool": "call_tool", "end": END}
)
graph.add_edge("call_tool", "call_llm")  # 工具执行后回到 LLM

# 5. 编译
app = graph.compile()

# 6. 执行
result = app.invoke({
    "messages": [HumanMessage(content="北京天气怎么样？")]
})
```

### 3. LangGraph 内部执行机制（30 分钟）

#### 3.1 图的编译过程
```
源码级理解：
graph.compile() 做了什么？

1. 验证图的合法性（所有节点都可达、无孤立节点）
2. 构建邻接表（节点 → 下一个节点的映射）
3. 创建执行引擎（CompiledGraph）
4. 初始化 Checkpoint 存储
```

#### 3.2 图的执行流程
```
app.invoke(input) 的执行过程：

1. 初始化 State（合并 input 到初始状态）
2. 从 entry_point 开始
3. 执行当前节点函数
4. 用 reducer 合并节点输出到 State
5. 评估条件边，确定下一个节点
6. 如果下一个节点是 END，返回最终 State
7. 否则，回到步骤 3
8. 每一步都保存 Checkpoint
```

#### 3.3 State 的更新机制
```python
# 节点返回的是 State 的"增量更新"
def my_node(state):
    return {"messages": [new_message]}  # 只返回要更新的字段

# 框架用 reducer 合并更新
# messages 字段的 reducer 是 add（追加）
# 所以 new_message 会追加到 messages 列表末尾
# 其他字段保持不变
```

### 4. Checkpoint 与状态持久化（25 分钟）

#### 4.1 Checkpoint 的作用
```
Checkpoint = 状态快照

用途：
1. 暂停/恢复：长时间任务可以中断后继续
2. 回溯：出错时可以回到之前的状态
3. 分支：从某个状态点创建多个分支
4. 调试：查看每一步的状态变化
```

#### 4.2 Checkpoint 的实现
```python
from langgraph.checkpoint.memory import MemorySaver

# 内存存储（开发用）
checkpointer = MemorySaver()

# 编译时传入 checkpointer
app = graph.compile(checkpointer=checkpointer)

# 执行时指定 thread_id
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke(input, config)

# 恢复执行（从上次的状态继续）
result = app.invoke(new_input, config)
```

#### 4.3 Human-in-the-loop
```python
from langgraph.graph import StateGraph, END

# 在关键节点设置中断
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["execute_action"]  # 在执行动作前暂停
)

# 第一次执行（会在 execute_action 前暂停）
result = app.invoke(input, config)

# 人工审核后继续
app.invoke(None, config)  # 传 None 表示继续执行
```

### 5. 实战：用 LangGraph 实现 ReAct Agent（35 分钟）

#### 5.1 ReAct Agent 的图结构
```
┌─────────┐     有工具调用     ┌───────────┐
│ call_llm │ ──────────────→ │ call_tool  │
│          │ ←────────────── │            │
└─────────┘   工具结果返回    └───────────┘
     │
     │ 无工具调用
     ↓
   [END]
```

#### 5.2 完整实现代码
（代码示例使用通义千问 API，包含详细注释）

#### 5.3 进阶：带 Human-in-the-loop 的健康建议 Agent
```
用户提问 → LLM 分析 → 生成建议
                         ↓
                    [人工审核]  ← 医疗建议需要人确认
                         ↓
                    返回给用户
```

### 6. LangGraph 高级模式（20 分钟）

#### 6.1 子图（Subgraph）
```python
# 子图：将复杂流程拆分为子流程
# 类比：Spring 的子容器
sub_graph = StateGraph(SubState)
# ... 定义子图 ...

main_graph.add_node("sub_process", sub_graph.compile())
```

#### 6.2 并行节点
```python
# 多个节点并行执行
graph.add_node("search_web", search_web)
graph.add_node("search_db", search_db)

# 两个搜索并行执行，结果合并
graph.add_edge(START, "search_web")
graph.add_edge(START, "search_db")
graph.add_edge("search_web", "merge_results")
graph.add_edge("search_db", "merge_results")
```

#### 6.3 动态路由
```python
# 根据 LLM 输出动态选择路由
def route_by_intent(state):
    intent = state["intent"]
    if intent == "diet":
        return "diet_agent"
    elif intent == "exercise":
        return "exercise_agent"
    else:
        return "general_agent"
```

### 7. 练习（30 分钟）

#### 练习 1：实现一个多步骤健康咨询 Agent
```
用户描述症状 → 意图识别 → 分支路由
                           ├─ 饮食建议流程
                           ├─ 运动建议流程
                           └─ 通用健康建议
```

#### 练习 2：给 Agent 加上 Checkpoint
要求：支持对话中断后恢复

## 预计时长
- 概念讲解：约 110 分钟
- 实战练习：约 65 分钟
- 总计：约 3 小时

## 完成标准
- 理解 StateGraph 的设计思想
- 能用 LangGraph 实现带条件分支和循环的 Agent
- 理解 Checkpoint 机制
- 能实现 Human-in-the-loop 模式

## 下节预告
课程 25：CrewAI 角色驱动架构 — 用角色和任务模型实现 Multi-Agent 协作
