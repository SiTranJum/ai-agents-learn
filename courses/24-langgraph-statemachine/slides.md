# 课程 24：LangGraph 状态机编排

---

## 开场：为什么需要 Graph？

上节课我们深入了 LangChain 的 Runnable 和 LCEL。LCEL 很强大，但它本质上是**线性的**——数据从左到右流过管道。

真实的 Agent 流程往往不是线性的：

```
ReAct Agent 的流程：
  LLM 思考 → 需要工具？ → 是 → 调用工具 → 回到 LLM 思考
                          → 否 → 输出结果

这里有循环、有条件分支——Chain 表达不了。
```

LangGraph 用**图（Graph）**来解决这个问题。

---

## 第一部分：从 Chain 到 Graph

### Chain 的局限

```
Chain（线性）：
  A → B → C → D

能表达：顺序执行
不能表达：
  - 条件分支（if-else）
  - 循环（while/for）
  - 并行执行
  - 暂停/恢复
```

### Graph 的能力

```
Graph（有向图）：
  
  ┌──→ B ──→ C ──┐
  │              │
  A              ↓
  │              E → [END]
  └──→ D ──────┘

能表达：
  - 条件分支：A 根据条件走 B 或 D
  - 循环：E 可以回到 A
  - 并行：B 和 D 可以同时执行
  - 暂停/恢复：任意节点可以中断
```

### 类比

```
如果你用过工作流引擎（Activiti、Camunda），LangGraph 的概念会很熟悉：

BPMN 流程图          LangGraph
─────────────        ──────────
流程定义              StateGraph
ServiceTask          Node（节点函数）
SequenceFlow         Edge（边）
ExclusiveGateway     Conditional Edge（条件边）
流程变量              State（状态）
流程实例快照          Checkpoint
UserTask             Human-in-the-loop
子流程               Subgraph
```

---

## 第二部分：StateGraph 核心概念

### 概念 1：State（状态）

State 是 LangGraph 的核心——所有节点共享一个状态对象，通过修改状态来传递数据。

```python
from typing import TypedDict, Annotated
from operator import add

class AgentState(TypedDict):
    """
    状态定义
    
    类比 Java：
    public class AgentState {
        private List<Message> messages;
        private String currentStep;
        private String finalAnswer;
    }
    
    关键区别：Annotated[list, add] 中的 add 是 reducer
    """
    messages: Annotated[list, add]  # 消息列表
    current_step: str               # 当前步骤
    final_answer: str               # 最终答案
```

**Reducer 是什么？**

```python
# 当多个节点更新同一个字段时，reducer 决定如何合并

# Annotated[list, add] 的含义：
# - 类型是 list
# - reducer 是 add（Python 内置的加法函数）
# - 效果：新值会追加到列表末尾

# 示例：
# 初始状态：messages = [msg1]
# 节点返回：{"messages": [msg2]}
# 合并后：messages = [msg1, msg2]  ← add([msg1], [msg2])

# 如果没有 reducer：
# 初始状态：messages = [msg1]
# 节点返回：{"messages": [msg2]}
# 合并后：messages = [msg2]  ← 直接覆盖！

# 类比 Redux：
# reducer = (state, action) => newState
# LangGraph 的 reducer 更简单：(oldValue, newValue) => mergedValue
```

### 概念 2：Node（节点）

节点就是一个普通的 Python 函数，接收 State，返回 State 的增量更新。

```python
def call_llm(state: AgentState) -> dict:
    """
    节点函数
    
    参数：state — 当前完整状态
    返回：dict — 要更新的字段（增量更新，不是全量替换）
    
    类比 Spring：
    @Service
    public class LLMService {
        public Map<String, Object> process(AgentState state) {
            // 处理逻辑
            return Map.of("messages", List.of(newMessage));
        }
    }
    """
    messages = state["messages"]
    response = llm.invoke(messages)
    # 只返回要更新的字段
    # messages 的 reducer 是 add，所以 [response] 会追加到现有列表
    return {"messages": [response]}
```

### 概念 3：Edge（边）

边定义节点之间的连接关系。

```python
# 普通边：无条件跳转
# A 执行完后，一定去 B
graph.add_edge("node_a", "node_b")

# 条件边：根据条件选择下一个节点
# A 执行完后，根据 router 函数的返回值决定去哪
def router(state: AgentState) -> str:
    """
    路由函数：返回下一个节点的名称
    
    类比 BPMN 的 ExclusiveGateway（排他网关）
    类比 Spring 的 @ConditionalOnProperty
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "call_tool"
    return "end"

graph.add_conditional_edges(
    "node_a",           # 源节点
    router,             # 路由函数
    {                   # 路由映射
        "call_tool": "call_tool",
        "end": END
    }
)
```

### 概念 4：编译与执行

```python
from langgraph.graph import StateGraph, START, END

# 1. 创建图
graph = StateGraph(AgentState)

# 2. 添加节点
graph.add_node("call_llm", call_llm)
graph.add_node("call_tool", call_tool)

# 3. 添加边
graph.add_edge(START, "call_llm")
graph.add_conditional_edges("call_llm", router, {...})
graph.add_edge("call_tool", "call_llm")

# 4. 编译
#    compile() 做了什么？
#    - 验证图的合法性（所有节点可达、无孤立节点）
#    - 构建邻接表
#    - 创建执行引擎
app = graph.compile()

# 5. 执行
#    invoke() 的内部流程：
#    a. 初始化 State
#    b. 从 START 开始
#    c. 执行当前节点 → 用 reducer 合并输出到 State
#    d. 评估边 → 确定下一个节点
#    e. 如果是 END → 返回最终 State
#    f. 否则 → 回到 c
result = app.invoke({"messages": [HumanMessage(content="...")]})
```

---

## 第三部分：LangGraph 内部执行机制

### 图的执行流程（源码级理解）

```
app.invoke(input) 的完整执行过程：

┌─────────────────────────────────────────┐
│ 1. 初始化 State                          │
│    state = AgentState(**input)           │
├─────────────────────────────────────────┤
│ 2. current_node = START                  │
├─────────────────────────────────────────┤
│ 3. 查找 START 的下一个节点               │
│    next_node = edges[START]              │
├─────────────────────────────────────────┤
│ 4. 执行节点函数                          │
│    update = next_node.func(state)        │
├─────────────────────────────────────────┤
│ 5. 用 reducer 合并更新到 State           │
│    for key, value in update.items():     │
│        state[key] = reducer(state[key],  │
│                             value)       │
├─────────────────────────────────────────┤
│ 6. 保存 Checkpoint（如果配置了）          │
├─────────────────────────────────────────┤
│ 7. 评估条件边，确定下一个节点             │
│    next = conditional_edge_func(state)   │
├─────────────────────────────────────────┤
│ 8. next == END ?                         │
│    → 是：返回 state                      │
│    → 否：回到步骤 4                      │
└─────────────────────────────────────────┘
```

### State 更新的 Reducer 机制

```python
# 理解 Reducer 是理解 LangGraph 的关键

# 场景：两个节点都更新 messages 字段

# 节点 A 返回：
{"messages": [AIMessage(content="让我查一下")]}

# 节点 B 返回：
{"messages": [ToolMessage(content="查询结果...")]}

# 如果 messages 的 reducer 是 add：
# 最终 messages = 原始消息 + [AIMessage] + [ToolMessage]
# 消息按顺序追加，保持完整的对话历史

# 如果没有 reducer（直接覆盖）：
# 最终 messages = [ToolMessage]
# 之前的消息全丢了！

# 这就是为什么 messages 字段几乎总是用 Annotated[list, add]
```

---

## 第四部分：Checkpoint — 状态持久化

### 为什么需要 Checkpoint？

```
场景 1：长时间任务
  用户开始一个健康分析 → 中途关闭浏览器 → 下次打开继续

场景 2：错误恢复
  Agent 执行到第 3 步出错 → 修复后从第 3 步继续，不用重头来

场景 3：人工介入
  Agent 生成了一个医疗建议 → 暂停等医生审核 → 审核通过后继续

场景 4：调试
  查看 Agent 每一步的状态变化，定位问题
```

### Checkpoint 的实现

```python
from langgraph.checkpoint.memory import MemorySaver

# MemorySaver：内存存储（开发调试用）
# 生产环境可以用 SqliteSaver、PostgresSaver 等
checkpointer = MemorySaver()

# 编译时传入 checkpointer
app = graph.compile(checkpointer=checkpointer)

# 执行时指定 thread_id
# thread_id 类比 HTTP Session ID
# 同一个 thread_id 的多次调用共享状态
config = {"configurable": {"thread_id": "user-123"}}

# 第一次调用
result1 = app.invoke(
    {"messages": [HumanMessage(content="我今天吃了什么？")]},
    config
)

# 第二次调用（自动加载上次的状态）
# 不需要重新传入之前的消息，Checkpoint 已经保存了
result2 = app.invoke(
    {"messages": [HumanMessage(content="帮我算一下总热量")]},
    config
)
```

### 查看 Checkpoint 历史

```python
# 获取所有 Checkpoint
for state in app.get_state_history(config):
    print(f"步骤: {state.metadata.get('step', '?')}")
    print(f"节点: {state.metadata.get('source', '?')}")
    print(f"消息数: {len(state.values.get('messages', []))}")
    print("---")
```

---

## 第五部分：Human-in-the-loop

### 设计思想

```
有些决策不能完全交给 AI：
- 医疗建议需要医生确认
- 大额操作需要用户确认
- 敏感操作需要管理员审批

Human-in-the-loop = 在关键节点暂停，等待人工确认后继续

类比 BPMN 的 UserTask：
  流程执行到 UserTask → 暂停 → 等待人处理 → 继续
```

### 实现方式

```python
# 方式 1：interrupt_before — 在指定节点执行前暂停
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["execute_action"]  # 在 execute_action 节点前暂停
)

# 第一次调用：执行到 execute_action 前暂停
result = app.invoke(input, config)
# result 包含 Agent 准备执行的动作

# 人工审核...
print(f"Agent 准备执行: {result}")
# 用户确认后继续
approved = input("是否批准？(y/n): ")

if approved == "y":
    # 继续执行（传 None 表示继续）
    result = app.invoke(None, config)
else:
    # 修改状态后继续
    app.update_state(config, {"messages": [HumanMessage(content="请换一个方案")]})
    result = app.invoke(None, config)
```

```python
# 方式 2：interrupt_after — 在指定节点执行后暂停
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_after=["generate_advice"]  # 生成建议后暂停
)
```

---

## 第六部分：实战模式

### 模式 1：ReAct Agent（最常用）

```
┌──────────┐    有工具调用    ┌───────────┐
│ call_llm  │ ──────────────→ │ call_tool  │
│           │ ←────────────── │            │
└──────────┘   工具结果返回    └───────────┘
      │
      │ 无工具调用（最终回答）
      ↓
    [END]
```

这就是我们之前手写的 Agent Loop，用 LangGraph 表达更清晰。

### 模式 2：多步骤流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ 意图识别  │ ──→ │ 信息收集  │ ──→ │ 生成建议  │ ──→ [END]
└──────────┘     └──────────┘     └──────────┘
                       │
                       │ 信息不足
                       ↓
                 ┌──────────┐
                 │ 追问用户  │ ──→ 回到信息收集
                 └──────────┘
```

### 模式 3：并行处理

```
                 ┌──────────────┐
            ┌──→ │ 饮食分析      │ ──┐
            │    └──────────────┘    │
┌────────┐  │    ┌──────────────┐    │    ┌──────────┐
│ 数据收集 │──┼──→ │ 运动分析      │ ──┼──→ │ 汇总报告  │ → [END]
└────────┘  │    └──────────────┘    │    └──────────┘
            │    ┌──────────────┐    │
            └──→ │ 睡眠分析      │ ──┘
                 └──────────────┘
```

### 模式 4：带审核的流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ 分析症状  │ ──→ │ 生成建议  │ ──→ │ [人工审核] │
└──────────┘     └──────────┘     └──────────┘
                                        │
                                   ┌────┴────┐
                                   │         │
                                 通过       驳回
                                   │         │
                                   ↓         ↓
                              ┌────────┐ ┌────────┐
                              │ 发送给  │ │ 重新生  │
                              │ 用户   │ │ 成建议  │
                              └────────┘ └────────┘
```

---

## 第七部分：LangGraph 高级特性

### 子图（Subgraph）

```python
# 复杂流程可以拆分为子图
# 类比：Spring 的子容器、微服务的服务拆分

# 定义子图
diet_subgraph = StateGraph(DietState)
diet_subgraph.add_node("analyze", analyze_diet)
diet_subgraph.add_node("suggest", suggest_diet)
diet_subgraph.add_edge(START, "analyze")
diet_subgraph.add_edge("analyze", "suggest")
diet_subgraph.add_edge("suggest", END)

# 在主图中使用子图
main_graph = StateGraph(MainState)
main_graph.add_node("diet", diet_subgraph.compile())
main_graph.add_node("exercise", exercise_subgraph.compile())
```

### 动态路由

```python
# 根据 LLM 的输出动态选择路由
def intent_router(state):
    """
    意图路由：LLM 判断用户意图，动态选择处理流程
    """
    # 用 LLM 判断意图
    intent = classify_intent(state["messages"][-1].content)
    
    route_map = {
        "diet_query": "diet_agent",
        "exercise_plan": "exercise_agent",
        "health_report": "report_agent",
        "general_chat": "chat_agent",
    }
    
    return route_map.get(intent, "chat_agent")
```

---

## 小结

### LangGraph 的核心设计

1. **State**：共享状态对象，Reducer 控制合并策略
2. **Node**：普通函数，接收 State 返回增量更新
3. **Edge**：定义流程走向，支持条件路由
4. **Checkpoint**：状态快照，支持暂停/恢复/回溯
5. **Human-in-the-loop**：关键节点人工介入

### 与 LangChain 的关系

```
LangGraph 不是 LangChain 的替代品，而是补充：

LangChain：提供组件（LLM、Tool、Memory、VectorStore）
LangGraph：提供编排（Graph、State、Checkpoint）

实际使用：LangGraph 编排流程 + LangChain 组件做具体工作
```

### 类比总结

| LangGraph | Java/工作流 |
|-----------|------------|
| StateGraph | BPMN 流程定义 |
| State | 流程变量 |
| Node | ServiceTask |
| Conditional Edge | ExclusiveGateway |
| Checkpoint | 流程实例快照 |
| Human-in-the-loop | UserTask |
| Subgraph | 子流程 |
| compile() | 流程部署 |
| invoke() | 启动流程实例 |
