import os
"""
MCP Client 示例 - 如何使用 db-query-mcp-server

这个脚本展示如何在你的 Agent 中集成 db-query-mcp-server。

功能：
1. 连接 MCP Server（通过 stdio）
2. 获取可用工具列表
3. 调用 query_database 工具
4. 在 Agent 循环中使用 MCP 工具

类比 Java：
    这就像一个 REST Client，连接远程服务并调用 API
    RestTemplate restTemplate = new RestTemplate();
    Result result = restTemplate.postForObject(url, request, Result.class);
"""

import asyncio
import json
from openai import OpenAI
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


# ============ 配置 ============

# 通义千问 API 配置
llm_client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


# ============ 工具转换函数 ============

def mcp_tool_to_openai_function(mcp_tool) -> dict:
    """
    将 MCP Tool 转换为 OpenAI Function Calling 格式

    MCP Tool 格式：
        Tool(
            name="query_database",
            description="查询数据库",
            inputSchema={...}
        )

    OpenAI Function 格式：
        {
            "type": "function",
            "function": {
                "name": "query_database",
                "description": "查询数据库",
                "parameters": {...}  # 就是 inputSchema
            }
        }

    参数：
        mcp_tool: MCP Tool 对象

    返回：
        OpenAI Function Calling 格式的字典

    类比 Java：
        public OpenAiFunction convertToOpenAiFunction(McpTool mcpTool) {
            return OpenAiFunction.builder()
                .name(mcpTool.getName())
                .description(mcpTool.getDescription())
                .parameters(mcpTool.getInputSchema())
                .build();
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


# ============ 示例 1：简单调用 MCP 工具 ============

async def example1_simple_call():
    """
    示例 1：简单调用 MCP 工具

    流程：
    1. 连接 MCP Server
    2. 调用 query_database 工具
    3. 打印结果
    """
    print("\n" + "="*60)
    print("示例 1：简单调用 MCP 工具")
    print("="*60)

    # 连接 MCP Server
    # stdio_client - 通过标准输入输出连接 Server
    # command: 启动 Server 的命令
    # args: 命令参数
    # env: 环境变量（数据库配置、LLM 配置）
    async with stdio_client(
        StdioServerParameters(
            command="python",
            args=["server.py"],
            env={
                "DB_HOST": "localhost",
                "DB_PORT": "3306",
                "DB_USER": "root",
                "DB_PASSWORD": "root",
                "DB_NAME": "test",
                "LLM_API_KEY": os.environ.get("DASHSCOPE_API_KEY"),
                "SKILLS_DIR": "./skills"
            }
        )
    ) as (read, write):
        # 创建 MCP Client
        async with ClientSession(read, write) as mcp_client:
            # 初始化连接（握手）
            await mcp_client.initialize()
            print("[OK] 已连接到 MCP Server\n")

            # 调用工具
            print("[调用] query_database")
            result = await mcp_client.call_tool(
                "query_database",
                {"question": "查询所有正常状态的用户"}
            )

            # 打印结果
            print(f"[结果]\n{result.content[0].text}\n")


# ============ 示例 2：在 Agent 中使用 MCP 工具 ============

async def example2_agent_with_mcp():
    """
    示例 2：在 Agent 中使用 MCP 工具

    这是完整的 Agent 循环，展示如何：
    1. 将 MCP 工具转换为 OpenAI Function Calling 格式
    2. LLM 决定调用哪个工具
    3. 调用 MCP 工具
    4. 将结果返回给 LLM
    5. LLM 生成最终回复

    这是最实用的模式！
    """
    print("\n" + "="*60)
    print("示例 2：在 Agent 中使用 MCP 工具")
    print("="*60)

    # 连接 MCP Server
    async with stdio_client(
        StdioServerParameters(
            command="python",
            args=["server.py"],
            env={
                "DB_HOST": "localhost",
                "DB_PORT": "3306",
                "DB_USER": "root",
                "DB_PASSWORD": "root",
                "DB_NAME": "test",
                "LLM_API_KEY": os.environ.get("DASHSCOPE_API_KEY"),
                "SKILLS_DIR": "./skills"
            }
        )
    ) as (read, write):
        async with ClientSession(read, write) as mcp_client:
            await mcp_client.initialize()
            print("[OK] 已连接到 MCP Server\n")

            # 获取 MCP 工具列表
            tools_result = await mcp_client.list_tools()
            mcp_tools = tools_result.tools
            print(f"[工具列表] 找到 {len(mcp_tools)} 个工具:")
            for tool in mcp_tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # 转换为 OpenAI Function Calling 格式
            openai_tools = [mcp_tool_to_openai_function(t) for t in mcp_tools]

            # Agent 循环
            print("[Agent 循环开始]\n")

            # 用户问题
            user_question = "帮我查询所有正常状态的用户，并统计数量"

            # 消息历史
            messages = [
                {
                    "role": "system",
                    "content": """你是数据库查询助手 Agent，可以帮用户：

1. **查询数据库**：使用 query_database 工具
   - 用户问："查询所有正常状态的用户"
   - 用户问："统计订单数量"

2. **查看模块信息**：使用 list_modules 和 get_module_detail 工具
   - 用户问："有哪些模块"
   - 用户问："user_module 包含哪些表"

3. **同步表结构**：使用 sync_schema_check 和 sync_schema_apply 工具
   - 用户说："新增了 challenge 模块，包含 4 个表：challenge_config、challenge_progress、challenge_task、challenge_task_config"
   - 用户说："users 表新增了 vip_level 字段"

   流程：
   a) 如果是新增模块，直接调用 sync_schema_apply（会自动创建模块文件）
   b) 如果是更新现有模块，先调用 sync_schema_check 检查差异，再调用 sync_schema_apply
   c) 将结果用自然语言解释给用户

重要：
- 识别用户意图，选择正确的工具
- 新增模块时，直接调用 sync_schema_apply，无需先 check（因为模块不存在）
- 更新现有模块时，先 check 再 apply
- 将工具返回的结果用自然语言解释给用户
"""
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ]

            print(f"[用户] {user_question}\n")

            # 最多 5 轮交互
            for iteration in range(5):
                print(f"[迭代 {iteration + 1}]")

                # 调用 LLM
                response = llm_client.chat.completions.create(
                    model="qwen-plus",
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto"
                )

                message = response.choices[0].message

                # 检查是否调用工具
                if message.tool_calls:
                    print(f"  LLM 决定调用工具\n")

                    # 将 LLM 的决策加入历史
                    messages.append(message)

                    # 处理每个工具调用
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        print(f"  [调用工具] {tool_name}")
                        print(f"  [参数] {tool_args}\n")

                        # 调用 MCP 工具
                        result = await mcp_client.call_tool(tool_name, tool_args)
                        result_text = result.content[0].text

                        print(f"  [工具结果]\n{result_text}\n")

                        # 将工具结果返回给 LLM
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_text
                        })

                else:
                    # LLM 给出最终回复
                    print(f"[助手] {message.content}\n")
                    break

            print("[Agent 循环结束]\n")


# ============ 示例 3：列出和查看 Skills ============

async def example3_manage_skills():
    """
    示例 3：管理 Skills

    展示如何：
    1. 列出所有 skills
    2. 查看 skill 详细信息
    """
    print("\n" + "="*60)
    print("示例 3：管理 Skills")
    print("="*60)

    async with stdio_client(
        StdioServerParameters(
            command="python",
            args=["server.py"],
            env={
                "DB_HOST": "localhost",
                "DB_PORT": "3306",
                "DB_USER": "root",
                "DB_PASSWORD": "root",
                "DB_NAME": "test",
                "LLM_API_KEY": os.environ.get("DASHSCOPE_API_KEY"),
                "SKILLS_DIR": "./skills"
            }
        )
    ) as (read, write):
        async with ClientSession(read, write) as mcp_client:
            await mcp_client.initialize()
            print("[OK] 已连接到 MCP Server\n")

            # 列出所有模块
            print("[调用] list_modules")
            result = await mcp_client.call_tool("list_modules", {})
            print(f"{result.content[0].text}\n")

            # 查看模块详细信息
            print("[调用] get_module_detail")
            result = await mcp_client.call_tool(
                "get_module_detail",
                {"module_name": "user_module"}
            )
            print(f"{result.content[0].text}...\n")


# ============ 主函数 ============

async def main():
    """
    运行所有示例

    你可以注释掉不需要的示例
    """
    print("\n" + "="*60)
    print("MCP Client 示例")
    print("="*60)

    # 示例 1：简单调用
    # await example1_simple_call()

    # 示例 2：在 Agent 中使用（最实用）
    await example2_agent_with_mcp()

    # 示例 3：管理 Skills
    # await example3_manage_skills()


if __name__ == "__main__":
    asyncio.run(main())


# ============ 使用说明 ============

"""
运行方式：

1. 确保 db-query-mcp-server 已经实现完成
2. 设置环境变量（或在代码中修改）
3. 运行：python client_example.py

关键概念：

1. stdio_client - 连接 MCP Server
   - command: 启动 Server 的命令
   - args: 命令参数
   - env: 环境变量（配置）

2. mcp_client.initialize() - 握手
   - 协商协议版本
   - 交换能力信息

3. mcp_client.list_tools() - 获取工具列表
   - 返回 MCP Tool 对象列表
   - 需要转换为 OpenAI Function Calling 格式

4. mcp_client.call_tool(name, arguments) - 调用工具
   - name: 工具名称
   - arguments: 参数字典
   - 返回：ToolResult 对象

5. Agent 循环中的集成
   - 将 MCP 工具转换为 OpenAI 格式
   - LLM 决定调用工具
   - 调用 MCP 工具
   - 将结果返回给 LLM
   - LLM 生成最终回复

类比 Java：

// MCP Client 就像 RestTemplate
RestTemplate restTemplate = new RestTemplate();

// 获取工具列表 = 获取 API 文档
List<Tool> tools = restTemplate.getForObject(
    "http://server/tools/list",
    List.class
);

// 调用工具 = 调用 API
Result result = restTemplate.postForObject(
    "http://server/tools/call",
    new ToolRequest("query_database", args),
    Result.class
);

// Agent 循环 = 业务逻辑层
while (!done) {
    // 调用 LLM
    LlmResponse response = llmClient.chat(messages, tools);

    // 如果 LLM 决定调用工具
    if (response.hasToolCalls()) {
        // 调用 MCP Server
        Result result = mcpClient.callTool(toolName, args);

        // 将结果返回给 LLM
        messages.add(new ToolMessage(result));
    } else {
        // LLM 给出最终回复
        return response.getContent();
    }
}
"""
