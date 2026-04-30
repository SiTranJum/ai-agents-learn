"""
课程 24：LangGraph 状态机编排 — 代码实践

本文件通过四个递进的示例，从简单到复杂地演示 LangGraph：
1. 最简 StateGraph — 理解基本概念
2. ReAct Agent — 带工具调用的循环
3. 多步骤健康分析流程 — 条件路由 + 多节点
4. Checkpoint + Human-in-the-loop — 状态持久化和人工介入

运行前安装依赖：
pip install langchain langchain-openai langgraph
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Literal
from operator import add
import json

# ============================================================
# 初始化 LLM（通义千问 DashScope API）
# ============================================================

llm = ChatOpenAI(
    model="qwen-plus",
    api_key="sk-a4ae611c3f9c4df89a133e621b2b7851",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ============================================================
# 示例 1：最简 StateGraph — 理解基本概念
# ============================================================

def demo_basic_graph():
    """
    最简单的 StateGraph 示例

    流程：greeting → farewell → END

    目的：理解 State、Node、Edge 的基本概念
    """
    print("=" * 60)
    print("示例 1：最简 StateGraph")
    print("=" * 60)

    # --- 1. 定义状态 ---
    # TypedDict 定义状态的结构（类比 Java 的 POJO）
    # Annotated[list, add] 表示 messages 字段的 reducer 是 add（追加模式）
    class SimpleState(TypedDict):
        messages: Annotated[list, add]  # 消息列表，新消息追加到末尾

    # --- 2. 定义节点函数 ---
    # 节点函数接收完整的 state，返回要更新的字段（增量更新）
    def greeting_node(state: SimpleState) -> dict:
        """问候节点：生成欢迎消息"""
        user_msg = state["messages"][-1]  # 获取最后一条消息
        print(f"  [greeting_node] 收到: {user_msg}")

        # 返回要更新的字段
        # 因为 messages 的 reducer 是 add，所以这条消息会追加到列表末尾
        return {"messages": [f"你好！收到你的消息：'{user_msg}'"]}

    def farewell_node(state: SimpleState) -> dict:
        """告别节点：生成告别消息"""
        print(f"  [farewell_node] 当前消息数: {len(state['messages'])}")
        return {"messages": ["再见！祝你健康！"]}

    # --- 3. 构建图 ---
    graph = StateGraph(SimpleState)

    # 添加节点（名称 → 函数）
    graph.add_node("greeting", greeting_node)
    graph.add_node("farewell", farewell_node)

    # 添加边（定义执行顺序）
    graph.add_edge(START, "greeting")       # 入口 → greeting
    graph.add_edge("greeting", "farewell")  # greeting → farewell
    graph.add_edge("farewell", END)         # farewell → 结束

    # --- 4. 编译 ---
    # compile() 验证图的合法性，构建执行引擎
    app = graph.compile()

    # --- 5. 执行 ---
    result = app.invoke({"messages": ["你好，我想了解健康饮食"]})

    print(f"\n最终状态的 messages：")
    for i, msg in enumerate(result["messages"]):
        print(f"  [{i}] {msg}")

    # 输出：
    # [0] 你好，我想了解健康饮食     ← 初始输入
    # [1] 你好！收到你的消息...       ← greeting 节点追加
    # [2] 再见！祝你健康！            ← farewell 节点追加


# ============================================================
# 示例 2：ReAct Agent — 带工具调用的循环
# ============================================================

def demo_react_agent():
    """
    用 LangGraph 实现 ReAct Agent

    流程：
    ┌──────────┐    有工具调用    ┌───────────┐
    │ call_llm  │ ──────────────→ │ call_tool  │
    │           │ ←────────────── │            │
    └──────────┘   工具结果返回    └───────────┘
          │
          │ 无工具调用
          ↓
        [END]

    这就是我们之前手写的 Agent Loop，用 LangGraph 表达
    """
    print("\n" + "=" * 60)
    print("示例 2：ReAct Agent（工具调用循环）")
    print("=" * 60)

    # --- 状态定义 ---
    class AgentState(TypedDict):
        messages: Annotated[list, add]

    # --- 定义工具 ---
    # @tool 装饰器自动生成 JSON Schema
    # LangGraph 可以直接使用 LangChain 的工具
    @tool
    def query_food_nutrition(food_name: str) -> str:
        """查询食物的营养成分信息。参数 food_name: 食物名称，如苹果、鸡胸肉"""
        food_db = {
            "苹果": "苹果(100g): 热量52kcal, 蛋白质0.3g, 脂肪0.2g, 碳水14g",
            "鸡胸肉": "鸡胸肉(100g): 热量165kcal, 蛋白质31g, 脂肪3.6g, 碳水0g",
            "米饭": "米饭(100g): 热量116kcal, 蛋白质2.6g, 脂肪0.3g, 碳水25.6g",
            "西兰花": "西兰花(100g): 热量34kcal, 蛋白质2.8g, 脂肪0.4g, 碳水7g",
        }
        return food_db.get(food_name, f"未找到 {food_name} 的营养信息")

    @tool
    def calculate_bmi(height_cm: float, weight_kg: float) -> str:
        """计算BMI指数。参数 height_cm: 身高(厘米), weight_kg: 体重(公斤)"""
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        if bmi < 18.5:
            category = "偏瘦"
        elif bmi < 24:
            category = "正常"
        elif bmi < 28:
            category = "偏胖"
        else:
            category = "肥胖"
        return f"BMI = {bmi:.1f}（{category}）"

    tools = [query_food_nutrition, calculate_bmi]

    # bind_tools：把工具信息绑定到 LLM
    # 内部原理：在发给 LLM 的请求中附带 tools 参数
    llm_with_tools = llm.bind_tools(tools)

    # --- 工具名称到函数的映射 ---
    tool_map = {t.name: t for t in tools}

    # --- 定义节点 ---

    def call_llm_node(state: AgentState) -> dict:
        """
        LLM 节点：调用 LLM，可能返回工具调用或最终回答

        内部流程：
        1. 从 state 获取消息历史
        2. 调用 LLM（带工具绑定）
        3. 返回 LLM 的回复（追加到 messages）
        """
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        print(f"  [LLM] {'调用工具' if response.tool_calls else '最终回答'}")
        return {"messages": [response]}

    def call_tool_node(state: AgentState) -> dict:
        """
        工具节点：执行 LLM 请求的工具调用

        内部流程：
        1. 从最后一条 AI 消息中提取 tool_calls
        2. 逐个执行工具
        3. 构造 ToolMessage 返回结果
        """
        last_message = state["messages"][-1]
        tool_results = []

        for tc in last_message.tool_calls:
            print(f"  [Tool] 调用 {tc['name']}({tc['args']})")
            # 通过 tool_map 找到对应的工具函数并执行
            tool_func = tool_map[tc["name"]]
            result = tool_func.invoke(tc["args"])
            # 构造 ToolMessage（必须包含 tool_call_id，LLM 需要它来匹配）
            tool_results.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"])
            )

        return {"messages": tool_results}

    # --- 定义条件路由 ---
    def should_continue(state: AgentState) -> Literal["call_tool", "__end__"]:
        """
        路由函数：决定下一步去工具节点还是结束

        返回值必须是下一个节点的名称或 END
        Literal 类型注解帮助 IDE 提示和类型检查
        """
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "call_tool"
        return "__end__"  # END 的字符串值就是 "__end__"

    # --- 构建图 ---
    graph = StateGraph(AgentState)

    graph.add_node("call_llm", call_llm_node)
    graph.add_node("call_tool", call_tool_node)

    graph.add_edge(START, "call_llm")
    graph.add_conditional_edges(
        "call_llm",
        should_continue,
        {"call_tool": "call_tool", "__end__": END}
    )
    graph.add_edge("call_tool", "call_llm")  # 工具结果返回 LLM

    app = graph.compile()

    # --- 执行 ---
    print("\n测试：查询食物营养")
    result = app.invoke({
        "messages": [
            SystemMessage(content="你是一个健康饮食助手。使用工具查询信息后给出建议。"),
            HumanMessage(content="鸡胸肉和西兰花搭配怎么样？帮我分析一下营养。")
        ]
    })

    print(f"\n最终回答：")
    print(result["messages"][-1].content)


# ============================================================
# 示例 3：多步骤健康分析流程
# ============================================================

def demo_multi_step_flow():
    """
    多步骤流程：条件路由 + 多节点

    流程：
    ┌──────────┐     ┌──────────┐
    │ 意图识别  │ ──→ │ 路由      │
    └──────────┘     └──────────┘
                          │
                    ┌─────┼─────┐
                    ↓     ↓     ↓
               ┌────┐ ┌────┐ ┌────┐
               │饮食│ │运动│ │通用│
               │分析│ │建议│ │问答│
               └────┘ └────┘ └────┘
                    │     │     │
                    └─────┼─────┘
                          ↓
                    ┌──────────┐
                    │ 输出格式化 │ → [END]
                    └──────────┘
    """
    print("\n" + "=" * 60)
    print("示例 3：多步骤健康分析流程")
    print("=" * 60)

    # --- 状态定义 ---
    class HealthState(TypedDict):
        messages: Annotated[list, add]
        intent: str         # 识别出的意图
        analysis: str       # 分析结果

    # --- 节点函数 ---

    def classify_intent(state: HealthState) -> dict:
        """意图识别节点：用 LLM 判断用户意图"""
        user_msg = state["messages"][-1]

        response = llm.invoke([
            SystemMessage(content=(
                "判断用户消息的意图，只返回以下之一：diet（饮食相关）、exercise（运动相关）、general（其他）。"
                "只返回一个英文单词，不要返回其他内容。"
            )),
            user_msg
        ])

        intent = response.content.strip().lower()
        # 确保 intent 是合法值
        if intent not in ("diet", "exercise", "general"):
            intent = "general"

        print(f"  [意图识别] {intent}")
        return {"intent": intent}

    def diet_analysis(state: HealthState) -> dict:
        """饮食分析节点"""
        user_msg = state["messages"][-1]
        response = llm.invoke([
            SystemMessage(content="你是营养师。简要分析用户描述的饮食情况，给出改善建议。回答控制在100字以内。"),
            user_msg
        ])
        print(f"  [饮食分析] 完成")
        return {"analysis": response.content}

    def exercise_advice(state: HealthState) -> dict:
        """运动建议节点"""
        user_msg = state["messages"][-1]
        response = llm.invoke([
            SystemMessage(content="你是健身教练。根据用户描述给出简要的运动建议。回答控制在100字以内。"),
            user_msg
        ])
        print(f"  [运动建议] 完成")
        return {"analysis": response.content}

    def general_answer(state: HealthState) -> dict:
        """通用问答节点"""
        user_msg = state["messages"][-1]
        response = llm.invoke([
            SystemMessage(content="你是健康顾问。简要回答用户的健康问题。回答控制在100字以内。"),
            user_msg
        ])
        print(f"  [通用问答] 完成")
        return {"analysis": response.content}

    def format_output(state: HealthState) -> dict:
        """输出格式化节点：整理最终输出"""
        intent_label = {
            "diet": "饮食分析",
            "exercise": "运动建议",
            "general": "健康问答"
        }
        label = intent_label.get(state["intent"], "回答")

        formatted = f"【{label}】\n{state['analysis']}"
        print(f"  [格式化] 完成")
        return {"messages": [AIMessage(content=formatted)]}

    # --- 路由函数 ---
    def route_by_intent(state: HealthState) -> str:
        """
        根据意图路由到不同的处理节点

        这就是 LangGraph 的条件边
        类比 BPMN 的排他网关（ExclusiveGateway）
        """
        intent = state["intent"]
        return intent  # 返回节点名称

    # --- 构建图 ---
    graph = StateGraph(HealthState)

    # 添加节点
    graph.add_node("classify", classify_intent)
    graph.add_node("diet", diet_analysis)
    graph.add_node("exercise", exercise_advice)
    graph.add_node("general", general_answer)
    graph.add_node("format", format_output)

    # 添加边
    graph.add_edge(START, "classify")

    # 条件路由：根据意图走不同分支
    graph.add_conditional_edges(
        "classify",
        route_by_intent,
        {
            "diet": "diet",
            "exercise": "exercise",
            "general": "general"
        }
    )

    # 三个分支最终都汇聚到 format 节点
    graph.add_edge("diet", "format")
    graph.add_edge("exercise", "format")
    graph.add_edge("general", "format")
    graph.add_edge("format", END)

    app = graph.compile()

    # --- 测试三种意图 ---
    test_cases = [
        "我今天早上吃了两个鸡蛋和一杯牛奶，中午吃了炸鸡，这样合理吗？",
        "我想减肥，应该做什么运动？",
        "晚上总是失眠怎么办？"
    ]

    for question in test_cases:
        print(f"\n问题: {question}")
        result = app.invoke({
            "messages": [HumanMessage(content=question)],
            "intent": "",
            "analysis": ""
        })
        print(f"\n{result['messages'][-1].content}")
        print("-" * 40)


# ============================================================
# 示例 4：Checkpoint + Human-in-the-loop
# ============================================================

def demo_checkpoint_and_hitl():
    """
    演示 Checkpoint 和 Human-in-the-loop

    场景：健康建议生成流程
    - 分析用户情况 → 生成建议 → [人工审核] → 发送给用户

    Checkpoint 保存每一步的状态
    Human-in-the-loop 在生成建议后暂停等待审核
    """
    print("\n" + "=" * 60)
    print("示例 4：Checkpoint + Human-in-the-loop")
    print("=" * 60)

    from langgraph.checkpoint.memory import MemorySaver

    # --- 状态定义 ---
    class AdviceState(TypedDict):
        messages: Annotated[list, add]
        user_situation: str    # 用户情况描述
        advice: str            # 生成的建议
        approved: bool         # 是否通过审核

    # --- 节点函数 ---

    def analyze_situation(state: AdviceState) -> dict:
        """分析用户情况"""
        user_msg = state["messages"][-1].content
        response = llm.invoke([
            SystemMessage(content="简要分析用户描述的健康情况，提取关键信息。用2-3句话总结。"),
            HumanMessage(content=user_msg)
        ])
        print(f"  [分析] {response.content[:50]}...")
        return {"user_situation": response.content}

    def generate_advice(state: AdviceState) -> dict:
        """生成健康建议"""
        response = llm.invoke([
            SystemMessage(content="根据以下情况分析，给出具体的健康建议（3条，每条一句话）。"),
            HumanMessage(content=state["user_situation"])
        ])
        print(f"  [生成建议] {response.content[:50]}...")
        return {"advice": response.content}

    def deliver_advice(state: AdviceState) -> dict:
        """发送建议给用户"""
        final_msg = f"【健康建议】\n{state['advice']}"
        print(f"  [发送] 建议已发送给用户")
        return {"messages": [AIMessage(content=final_msg)], "approved": True}

    # --- 构建图 ---
    graph = StateGraph(AdviceState)

    graph.add_node("analyze", analyze_situation)
    graph.add_node("generate", generate_advice)
    graph.add_node("deliver", deliver_advice)

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "generate")
    graph.add_edge("generate", "deliver")  # 我们会在 deliver 之前设置中断
    graph.add_edge("deliver", END)

    # --- Checkpoint ---
    # MemorySaver：将状态保存在内存中
    # 生产环境可以用 SqliteSaver（持久化到数据库）
    checkpointer = MemorySaver()

    # 编译时配置：
    # - checkpointer: 状态持久化
    # - interrupt_before: 在 deliver 节点执行前暂停
    app = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["deliver"]  # 关键！在发送建议前暂停
    )

    # --- 执行 ---
    # thread_id 类比 HTTP Session ID
    config = {"configurable": {"thread_id": "user-001"}}

    print("\n--- 第一次执行：分析 + 生成建议（在 deliver 前暂停）---")
    result = app.invoke(
        {
            "messages": [HumanMessage(content="我170cm，80kg，每天久坐办公，晚上经常吃夜宵")],
            "user_situation": "",
            "advice": "",
            "approved": False,
        },
        config
    )

    # 此时流程暂停在 deliver 之前
    # 我们可以查看生成的建议
    print(f"\n生成的建议（等待审核）：")
    print(f"  {result.get('advice', '暂无')}")

    # 查看当前状态
    current_state = app.get_state(config)
    print(f"\n当前暂停在节点: {current_state.next}")  # ('deliver',)

    # --- 人工审核 ---
    # input() 会暂停程序，等待你在终端输入
    # 类比 Java：Scanner scanner = new Scanner(System.in); scanner.nextLine();
    approval = input("\n请审核以上建议，输入 'y' 通过，输入 'n' 拒绝: ").strip().lower()

    if approval == "y":
        print("\n--- 审核通过，继续执行 ---")
        # 传入 None 表示"继续执行"（不修改状态）
        final_result = app.invoke(None, config)
        print(f"\n最终结果：")
        print(final_result["messages"][-1].content)
    else:
        print("\n--- 审核拒绝，流程终止 ---")
        print("建议已被驳回，不会发送给用户。")
        return

    # --- 查看 Checkpoint 历史 ---
    print("\n--- Checkpoint 历史 ---")
    for i, state in enumerate(app.get_state_history(config)):
        node = state.metadata.get("source", "unknown")
        step = state.metadata.get("step", "?")
        msg_count = len(state.values.get("messages", []))
        print(f"  步骤 {step}: 节点={node}, 消息数={msg_count}")


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("LangGraph 状态机编排 — 代码实践\n")

    # 四个递进的示例
    demo_basic_graph()
    demo_react_agent()
    demo_multi_step_flow()
    demo_checkpoint_and_hitl()

    print("\n" + "=" * 60)
    print("练习任务")
    print("=" * 60)
    print("""
    练习 1：修改 ReAct Agent，添加一个新工具
    - 添加一个"记录饮食"工具（接收食物名称和份量，返回确认信息）
    - 测试 Agent 是否能在对话中同时查询和记录

    练习 2：给多步骤流程添加"信息不足"分支
    - 如果意图识别后发现信息不足，路由到"追问用户"节点
    - 追问用户后回到意图识别（形成循环）

    练习 3：实现一个带审核的饮食计划生成器
    - 流程：收集信息 → 生成计划 → [人工审核] → 修改/通过
    - 使用 Checkpoint 实现暂停/恢复
    - 如果审核不通过，回到"生成计划"重新生成
    """)
