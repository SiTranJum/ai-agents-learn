"""
练习 2：在 Agent 中集成 MCP Server

目标：
    创建一个简单的 Agent，使用 MCP Client 连接 health-mcp-server，
    实现一个健康咨询对话系统

任务：

1. 实现 MCP Client 连接逻辑
   - 使用 stdio_client 启动 server.py
   - 初始化连接并获取工具列表

2. 实现 Agent 主循环
   - 接收用户输入
   - 调用 LLM 决定是否需要使用工具
   - 如果需要，调用 MCP 工具
   - 将工具结果返回给 LLM
   - 输出最终回复

3. 测试场景
   - 用户问："苹果的热量是多少？"
   - 用户问："我身高 175cm，体重 70kg，BMI 是多少？"
   - 用户问："今天天气怎么样？"（测试 Agent 不调用工具的情况）

提示：
    - 使用通义千问 API（qwen-plus）
    - 使用 OpenAI SDK 的 Function Calling 格式
    - 将 MCP 工具转换为 OpenAI Function Calling 的 tools 格式
    - 参考课件中的集成示例

完成后：
    运行 Agent，测试以上三个场景是否正常工作
"""

import asyncio
import json
from openai import OpenAI
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# ============ 配置 ============

# 通义千问 API 配置
client = OpenAI(
    api_key="sk-non",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# ============ 调试：打印完整上下文 ============

DEBUG = True  # 设为 False 关闭调试输出

def debug_print_raw_request(messages, tools, iteration):
    """
    打印发送给 LLM 的原始请求内容

    这是实际发送给 OpenAI API 的 JSON 格式
    """
    if not DEBUG:
        return

    print(f"\n{'='*80}")
    print(f"  [DEBUG] 第 {iteration} 次调用 LLM - 原始请求内容")
    print(f"{'='*80}\n")

    # 构造完整的请求体（和实际发送的一样）
    request_body = {
        "model": "qwen-plus",
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto"
    }

    # 打印为格式化的 JSON
    import json
    print(json.dumps(request_body, ensure_ascii=False, indent=2))

    print(f"\n{'='*80}\n")


# ============ MCP 工具转换 ============

def mcp_tool_to_openai_function(mcp_tool) -> dict:
    """
    将 MCP Tool 转换为 OpenAI Function Calling 格式

    MCP Tool 格式：
        Tool(
            name="query_nutrition",
            description="查询食物营养",
            inputSchema={...}
        )

    OpenAI Function 格式：
        {
            "type": "function",
            "function": {
                "name": "query_nutrition",
                "description": "查询食物营养",
                "parameters": {...}
            }
        }
    """
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema
        }
    }


# ============ Agent 实现 ============

async def run_agent():
    """
    运行健康咨询 Agent

    流程：
    1. 连接 MCP Server
    2. 获取工具列表并转换为 OpenAI 格式
    3. 进入对话循环
    4. 根据 LLM 的决策调用工具
    5. 返回最终回复
    """
    # TODO 1: 连接 MCP Server
    # 提示：使用 stdio_client 启动 server.py
    server_params = StdioServerParameters(
        command="python",
        args=["exercise_1.py"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_client:
            # 初始化连接
            await mcp_client.initialize()
            print("✓ 已连接 health-mcp-server\n")
            # TODO 2: 获取工具列表
            # 提示：使用 mcp_client.list_tools()
            mcp_tools = await mcp_client.list_tools()

            # TODO 3: 转换为 OpenAI Function Calling 格式
            openai_tools = [mcp_tool_to_openai_function(t) for t in mcp_tools.tools]

            print("健康咨询 Agent 已启动！")
            print(f"可用工具：{[t.name for t in mcp_tools.tools]}")
            print("输入 'quit' 退出\n")

            # 对话历史
            messages = [
                {
                    "role": "system",
                    "content": "你是一个健康咨询助手，可以查询食物营养、计算 BMI 等。"
                }
            ]

            # TODO 4: 实现对话循环
            while True:
                # 获取用户输入
                user_input = input("用户: ")
                if user_input.lower() == "quit":
                    break

                # 添加用户消息
                messages.append({"role": "user", "content": user_input})

                call_count = 0
                for _ in range(3):
                    call_count += 1

                    # 打印原始请求内容
                    debug_print_raw_request(messages, openai_tools, call_count)

                    # TODO 5: 调用 LLM（带工具）
                    response = client.chat.completions.create(
                        model="qwen-plus",
                        messages=messages,
                        tools=openai_tools,
                        tool_choice="auto"
                    )
                    assistant_message = response.choices[0].message

                    # TODO 6: 处理 LLM 响应
                    if assistant_message.tool_calls:
                        # 将 assistant 消息加入历史
                        messages.append({
                            "role": "assistant",
                            "content": assistant_message.content,
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": tc.type,
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments
                                    }
                                }
                                for tc in assistant_message.tool_calls
                            ]
                        })

                        # TODO 7: 调用 MCP 工具
                        for tool_call in assistant_message.tool_calls:
                            print(f"LLM 决定调用工具: {tool_call.function.name}，参数: {tool_call.function.arguments}")
                            result = await mcp_client.call_tool(
                                tool_call.function.name,
                                json.loads(tool_call.function.arguments)
                            )
                            result_text = result.content[0].text
                            print(f"工具调用结果: {result_text}")

                            # 将工具结果添加到消息历史
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result_text
                            })
                    else:
                        # 直接回复
                        print(f"助手: {assistant_message.content}\n")
                        messages.append({
                            "role": "assistant",
                            "content": assistant_message.content
                        })
                        break


# ============ 主函数 ============

if __name__ == "__main__":
    asyncio.run(run_agent())

# ============ 参考：完整的工具调用流程 ============

"""
完整流程示例：

1. 用户输入："苹果的热量是多少？"

2. 调用 LLM（带工具）
   response = client.chat.completions.create(
       model="qwen-plus",
       messages=[...],
       tools=openai_tools
   )

3. LLM 决定调用工具
   assistant_message.tool_calls = [
       {
           "id": "call_123",
           "type": "function",
           "function": {
               "name": "query_nutrition",
               "arguments": '{"food_name": "苹果"}'
           }
       }
   ]

4. 调用 MCP 工具
   result = await mcp_client.call_tool(
       "query_nutrition",
       {"food_name": "苹果"}
   )
   # result.content[0].text = "苹果：热量 52kcal/100g..."

5. 将工具结果添加到 messages
   messages.append({
       "role": "assistant",
       "content": None,
       "tool_calls": assistant_message.tool_calls
   })
   messages.append({
       "role": "tool",
       "tool_call_id": "call_123",
       "content": result.content[0].text
   })

6. 再次调用 LLM 生成最终回复
   final_response = client.chat.completions.create(
       model="qwen-plus",
       messages=messages,
       tools=openai_tools
   )
   # final_response: "苹果的热量是 52kcal/100g，是一种低热量水果..."

7. 输出最终回复
"""
