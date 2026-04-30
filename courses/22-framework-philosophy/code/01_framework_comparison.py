"""
课程 22：框架对比实战 — 同一个需求的三种实现

需求：实现一个简单的健康助手 Agent
- 能查询食物热量
- 能根据查询结果给出建议

我们用三种方式实现：手写、LangChain、LangGraph
直观感受框架带来的差异

运行前安装依赖：
pip install openai langchain langchain-openai langgraph
"""

import sys
import os

# Windows 控制台默认 GBK 编码，遇到 emoji 等 Unicode 字符会崩溃
# 强制设置为 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')
os.environ["PYTHONIOENCODING"] = "utf-8"

from openai import OpenAI
import json

# ============================================================
# 公共部分：食物数据和工具函数
# ============================================================

# 模拟食物数据库
FOOD_DB = {
    "苹果": {"calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14, "unit": "100g"},
    "鸡胸肉": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0, "unit": "100g"},
    "米饭": {"calories": 116, "protein": 2.6, "fat": 0.3, "carbs": 25.6, "unit": "100g"},
    "西兰花": {"calories": 34, "protein": 2.8, "fat": 0.4, "carbs": 7, "unit": "100g"},
    "全麦面包": {"calories": 247, "protein": 13, "fat": 3.4, "carbs": 41, "unit": "100g"},
}

def query_food_nutrition(food_name: str) -> str:
    """查询食物营养信息（三种实现共用）"""
    if food_name in FOOD_DB:
        info = FOOD_DB[food_name]
        return (
            f"{food_name}（每{info['unit']}）：\n"
            f"  热量: {info['calories']} kcal\n"
            f"  蛋白质: {info['protein']}g\n"
            f"  脂肪: {info['fat']}g\n"
            f"  碳水: {info['carbs']}g"
        )
    return f"未找到 {food_name} 的营养信息"


# ============================================================
# 实现一：手写版本（我们之前的方式）
# ============================================================

def run_handwritten_agent(user_input: str) -> str:
    """
    手写 Agent：直接调用 OpenAI SDK

    优点：完全控制，无额外依赖
    缺点：代码量大，扩展困难
    """
    # --- 初始化 LLM 客户端 ---
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # --- 定义工具（JSON Schema，手动编写） ---
    tools = [
        {
            "type": "function",
            "function": {
                "name": "query_food_nutrition",
                "description": "查询食物的营养成分信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "food_name": {
                            "type": "string",
                            "description": "食物名称，如：苹果、鸡胸肉"
                        }
                    },
                    "required": ["food_name"]
                }
            }
        }
    ]

    # --- 构造消息 ---
    messages = [
        {
            "role": "system",
            "content": "你是一个健康饮食助手。用户询问食物信息时，使用工具查询，然后给出简短的健康建议。"
        },
        {"role": "user", "content": user_input}
    ]

    # --- Agent 循环（手动实现） ---
    max_iterations = 5  # 防止无限循环
    for _ in range(max_iterations):
        # 调用 LLM
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            tools=tools
        )

        choice = response.choices[0]
        assistant_msg = choice.message

        # 将 LLM 回复加入消息历史
        messages.append(assistant_msg.model_dump())

        # 判断是否需要调用工具
        if choice.finish_reason == "tool_calls" or (assistant_msg.tool_calls and len(assistant_msg.tool_calls) > 0):
            # 手动处理每个工具调用
            for tool_call in assistant_msg.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                # 手动路由到对应函数
                if func_name == "query_food_nutrition":
                    result = query_food_nutrition(func_args["food_name"])
                else:
                    result = f"未知工具: {func_name}"

                # 手动构造工具结果消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            # 没有工具调用，返回最终回答
            return assistant_msg.content

    return "达到最大迭代次数"


# ============================================================
# 实现二：LangChain 版本
# ============================================================

def run_langchain_agent(user_input: str) -> str:
    """
    LangChain Agent：用框架的组件化方式实现

    优点：代码简洁，组件可复用，易于扩展
    缺点：需要学习框架 API，有一定抽象开销
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, SystemMessage
    # LangChain v1 新 API：create_agent 替代了旧的 create_react_agent
    # 内部基于 LangGraph 构建，支持 Checkpoint、中断、流式等能力
    from langchain.agents import create_agent

    # --- 初始化 LLM（一行代码，切换模型只改这里） ---
    # ChatOpenAI 是 LangChain 对 OpenAI 兼容 API 的封装
    # 它实现了 Runnable 协议，可以用 | 操作符组合
    llm = ChatOpenAI(
        model="qwen-plus",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # --- 定义工具（用 @tool 装饰器，自动生成 JSON Schema） ---
    # 对比手写版本：不需要手动写 JSON Schema
    # 框架从函数签名和 docstring 自动推断
    @tool
    def query_food(food_name: str) -> str:
        """查询食物的营养成分信息。参数 food_name: 食物名称，如苹果、鸡胸肉"""
        return query_food_nutrition(food_name)

    # --- 创建 Agent ---
    # create_agent 是 LangChain v1 的统一入口，内部实现了：
    # 1. 构造带工具的 Prompt
    # 2. Agent Loop（调用 LLM → 判断是否需要工具 → 执行工具 → 循环）
    # 3. 错误处理和重试
    #
    # 参数说明：
    # - model: LLM 实例或字符串（如 "openai:gpt-4o"），这里传 ChatOpenAI 实例
    # - tools: 工具列表
    # - system_prompt: 系统提示词，定义 Agent 行为
    agent = create_agent(
        llm,
        tools=[query_food],
        system_prompt="你是一个健康饮食助手。用户询问食物信息时，使用工具查询，然后给出简短的健康建议。"
    )

    # --- 执行（一行调用） ---
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]}
    )

    # 返回最后一条 AI 消息
    return result["messages"][-1].content


# ============================================================
# 实现三：LangGraph 版本（显式状态机）
# ============================================================

def run_langgraph_agent(user_input: str) -> str:
    """
    LangGraph Agent：用状态机方式实现

    优点：流程可视化，状态可追踪，支持复杂分支
    缺点：对简单场景略显繁琐

    注意：这里展示的是手动构建 Graph 的方式
    上面 LangChain 版本用的 create_react_agent 内部其实也是 LangGraph
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
    from langgraph.graph import StateGraph, END, START
    from typing import TypedDict, Annotated
    from operator import add

    # --- 定义状态（State）---
    # 类比 Java 的 POJO / DTO
    # 所有节点共享这个状态对象
    class AgentState(TypedDict):
        messages: Annotated[list, add]  # 消息列表，用 add 作为 reducer（追加模式）

    # --- 初始化 LLM 和工具 ---
    llm = ChatOpenAI(
        model="qwen-plus",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    @tool
    def query_food(food_name: str) -> str:
        """查询食物的营养成分信息。参数 food_name: 食物名称，如苹果、鸡胸肉"""
        return query_food_nutrition(food_name)

    # 绑定工具到 LLM（让 LLM 知道有哪些工具可用）
    llm_with_tools = llm.bind_tools([query_food])

    # --- 定义节点函数 ---

    def call_llm(state: AgentState) -> dict:
        """
        节点 1：调用 LLM
        接收当前状态，返回状态的增量更新
        """
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}  # 返回新消息（会追加到 messages）

    def call_tool(state: AgentState) -> dict:
        """
        节点 2：执行工具调用
        从最后一条消息中提取工具调用，执行并返回结果
        """
        last_message = state["messages"][-1]
        tool_results = []

        for tool_call in last_message.tool_calls:
            # 框架自动匹配工具名称并执行
            if tool_call["name"] == "query_food":
                result = query_food_nutrition(tool_call["args"]["food_name"])
            else:
                result = f"未知工具: {tool_call['name']}"

            tool_results.append(
                ToolMessage(content=result, tool_call_id=tool_call["id"])
            )

        return {"messages": tool_results}

    # --- 定义条件路由 ---
    def should_continue(state: AgentState) -> str:
        """
        条件函数：决定下一步去哪个节点
        类比 BPMN 的 ExclusiveGateway（排他网关）
        """
        last_message = state["messages"][-1]
        # 如果 LLM 输出包含工具调用 → 去执行工具
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "call_tool"
        # 否则 → 结束
        return END

    # --- 构建状态图 ---
    # 这就是 LangGraph 的核心：用图来描述流程
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("call_llm", call_llm)
    graph.add_node("call_tool", call_tool)

    # 添加边
    graph.add_edge(START, "call_llm")           # 入口 → call_llm
    graph.add_conditional_edges(                 # call_llm → 条件路由
        "call_llm",
        should_continue,
        {"call_tool": "call_tool", END: END}
    )
    graph.add_edge("call_tool", "call_llm")     # call_tool → 回到 call_llm

    # 编译图
    app = graph.compile()

    # --- 执行 ---
    result = app.invoke({
        "messages": [
            SystemMessage(content="你是一个健康饮食助手。用户询问食物信息时，使用工具查询，然后给出简短的健康建议。"),
            HumanMessage(content=user_input)
        ]
    })

    return result["messages"][-1].content


# ============================================================
# 主程序：运行三种实现并对比
# ============================================================

if __name__ == "__main__":
    test_input = "苹果和鸡胸肉哪个更适合减肥？"

    print("=" * 60)
    print(f"测试输入: {test_input}")
    print("=" * 60)

    # --- 手写版本 ---
    print("\n【实现一：手写版本】")
    print("-" * 40)
    try:
        result1 = run_handwritten_agent(test_input)
        print(result1)
    except Exception as e:
        print(f"错误: {e}")

    # --- LangChain 版本 ---
    print("\n【实现二：LangChain 版本】")
    print("-" * 40)
    try:
        result2 = run_langchain_agent(test_input)
        print(result2)
    except Exception as e:
        print(f"错误: {e}")

    # --- LangGraph 版本 ---
    print("\n【实现三：LangGraph 版本】")
    print("-" * 40)
    try:
        result3 = run_langgraph_agent(test_input)
        print(result3)
    except Exception as e:
        print(f"错误: {e}")

    # --- 对比总结 ---
    print("\n" + "=" * 60)
    print("对比总结")
    print("=" * 60)
    print("""
    | 维度       | 手写          | LangChain      | LangGraph       |
    |-----------|--------------|----------------|-----------------|
    | 代码量     | ~60 行        | ~20 行          | ~50 行           |
    | 工具定义   | 手写 JSON     | @tool 自动生成   | @tool 自动生成    |
    | 循环控制   | while + if   | 框架自动处理     | 图 + 条件边       |
    | 可扩展性   | 低（改代码）   | 高（加组件）     | 高（加节点/边）    |
    | 可观测性   | print        | Callbacks      | 状态追踪          |
    | 学习成本   | 低           | 中             | 中高              |
    """)
