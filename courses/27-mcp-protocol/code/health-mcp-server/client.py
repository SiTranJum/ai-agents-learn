"""
MCP Client - 连接 health-mcp-server 并使用工具

展示如何：
1. 启动并连接 MCP Server
2. 获取工具列表
3. 将 MCP 工具转换为 OpenAI Function Calling 格式
4. 在 Agent 循环中调用 MCP 工具

类比 Java：
    类似用 RestTemplate 调用远程 API
    RestTemplate restTemplate = new RestTemplate();
    Result result = restTemplate.postForObject(url, request, Result.class);
"""

import asyncio
import json
from openai import OpenAI
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import Tool


# ============ LLM 配置 ============

# 通义千问 API（OpenAI SDK 兼容模式）
llm = OpenAI(
    api_key="sk-non",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


# ============ 工具转换 ============

def mcp_tool_to_openai(mcp_tool) -> dict:
    """
    将 MCP Tool 转换为 OpenAI Function Calling 格式

    MCP 的工具定义和 OpenAI 的几乎一样，只是外层包装不同：
    - MCP: Tool(name, description, inputSchema)
    - OpenAI: {"type": "function", "function": {"name", "description", "parameters"}}

    参数：
        mcp_tool: MCP Tool 对象
            mcp_tool.name         → 工具名称
            mcp_tool.description  → 工具描述
            mcp_tool.inputSchema  → 参数 Schema（JSON Schema 格式）

    返回：
        OpenAI Function Calling 格式的字典

    类比 Java：
        // 就是一个 DTO 转换
        public OpenAiTool convert(McpTool mcpTool) {
            return new OpenAiTool("function", new Function(
                mcpTool.getName(),
                mcpTool.getDescription(),
                mcpTool.getInputSchema()  // 直接复用，格式一样
            ));
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


# ============ 主逻辑 ============

async def main():
    """
    完整的 Agent + MCP 集成示例

    流程：
    1. 启动 MCP Server 进程并连接
    2. 获取工具列表，转换为 OpenAI 格式
    3. 进入对话循环
    4. LLM 决定是否调用工具 → 调用 MCP → 结果返回 LLM → 最终回复
    """

    # ============ 1. 连接 MCP Server ============

    # StdioServerParameters - Server 启动参数
    # command: 启动命令（python）
    # args: 命令参数（server.py 的路径）
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )

    # stdio_client() - 启动 Server 进程并通过 stdin/stdout 通信
    #
    # 类比 Java：
    #   ProcessBuilder pb = new ProcessBuilder("python", "server.py");
    #   Process process = pb.start();
    #   InputStream in = process.getInputStream();   // 读 Server 响应
    #   OutputStream out = process.getOutputStream(); // 发请求给 Server
    async with stdio_client(server_params) as (read, write):

        # ClientSession - 创建 MCP Client 会话
        # read: 从 Server 读取响应的流
        # write: 向 Server 发送请求的流
        async with ClientSession(read, write) as session:

            # initialize() - 握手（能力协商）
            # Client 和 Server 交换各自支持的能力
            # 类比：TCP 三次握手 / TLS 握手
            await session.initialize()
            print("✓ 已连接 health-mcp-server\n")

            # ============ 2. 获取工具列表 ============

            # list_tools() - 获取 Server 提供的所有工具
            # 返回：ListToolsResult，包含 tools 列表
            #
            # 类比 Java：
            #   List<Tool> tools = restTemplate.getForObject(
            #       "http://server/tools/list", List.class
            #   );
            result = await session.list_tools()
            mcp_tools = result.tools

            print(f"可用工具（{len(mcp_tools)} 个）：")
            for tool in mcp_tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # 转换为 OpenAI Function Calling 格式
            openai_tools = [mcp_tool_to_openai(t) for t in mcp_tools]

            # ============ 3. 对话循环 ============

            # 系统提示词
            messages = [
                {
                    "role": "system",
                    "content": "你是健康管理助手，可以查询食物营养、计算 BMI。根据用户问题调用合适的工具。"
                }
            ]

            print("健康管家 Agent 已启动（输入 quit 退出）\n")

            while True:
                # 获取用户输入
                user_input = input("你: ")
                if user_input.lower() == "quit":
                    break

                messages.append({"role": "user", "content": user_input})

                # ============ 4. Agent 循环 ============

                # 最多 3 轮工具调用
                for _ in range(3):

                    # 调用 LLM（带工具定义）
                    # LLM 会根据 tools 中的 description 决定是否调用工具
                    #
                    # 类比 Java：
                    #   ChatCompletionRequest request = ChatCompletionRequest.builder()
                    #       .model("qwen-plus")
                    #       .messages(messages)
                    #       .tools(openaiTools)
                    #       .toolChoice("auto")
                    #       .build();
                    #   ChatCompletionResponse response = openAiService.createChatCompletion(request);
                    response = llm.chat.completions.create(
                        model="qwen-plus",
                        messages=messages,
                        tools=openai_tools,
                        tool_choice="auto"
                    )

                    assistant_msg = response.choices[0].message

                    # ---- 情况 1：LLM 决定调用工具 ----
                    if assistant_msg.tool_calls:
                        # 将 LLM 的决策加入消息历史
                        messages.append(assistant_msg)

                        for tool_call in assistant_msg.tool_calls:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)

                            print(f"  [调用工具] {tool_name}({tool_args})")

                            # 调用 MCP Server 的工具
                            # call_tool(name, arguments) - 发送 tools/call 请求
                            #
                            # 类比 Java：
                            #   ToolResult result = restTemplate.postForObject(
                            #       "http://server/tools/call",
                            #       new ToolCallRequest(toolName, toolArgs),
                            #       ToolResult.class
                            #   );
                            result = await session.call_tool(tool_name, tool_args)

                            # result.content 是一个列表，每个元素是 TextContent
                            # result.content[0].text 就是工具返回的文本结果
                            result_text = result.content[0].text
                            print(f"  [结果] {result_text}")

                            # 将工具结果加入消息历史
                            # role="tool" 表示这是工具的返回值
                            # tool_call_id 必须和 LLM 返回的 tool_call.id 匹配
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result_text
                            })

                        # 继续循环，让 LLM 根据工具结果生成回复

                    # ---- 情况 2：LLM 直接回复（不调用工具） ----
                    else:
                        print(f"\n助手: {assistant_msg.content}\n")
                        messages.append({
                            "role": "assistant",
                            "content": assistant_msg.content
                        })
                        break


# ============ 入口 ============

if __name__ == "__main__":
    asyncio.run(main())
