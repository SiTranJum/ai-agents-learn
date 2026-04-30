"""
健康管家 MCP Server
提供食物营养查询、BMI 计算等工具

运行方式：
    python server.py

测试方式：
    1. 使用 MCP Inspector: mcp-inspector python server.py
    2. 在 Claude Desktop 中配置
    3. 使用 MCP Client SDK 连接
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

# ============ 创建 MCP Server 实例 ============

# Server(name: str) - 创建一个 MCP Server
# 参数：
#   name: Server 的唯一标识符，用于在 Host 中区分不同的 Server
server = Server("health-assistant")


# ============ 1. 定义工具列表 ============

@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    返回 Server 提供的所有工具列表

    这个方法会在以下时机被调用：
    1. Client 首次连接时（能力协商阶段）
    2. Client 请求刷新工具列表时

    返回值：
        list[Tool]: 工具列表，每个 Tool 包含：
            - name: 工具名称（唯一标识）
            - description: 工具描述（LLM 会根据这个决定是否调用）
            - inputSchema: 参数 Schema（JSON Schema 格式）

    类比：
        类似 Spring Boot 的 @RequestMapping 扫描
        或者 OpenAPI 的 /swagger.json 端点
    """
    return [
        Tool(
            name="query_nutrition",
            description="查询食物的营养成分，包括热量、蛋白质、脂肪、碳水化合物。支持常见食物如水果、主食、肉类等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "food_name": {
                        "type": "string",
                        "description": "食物名称，例如：苹果、米饭、鸡胸肉"
                    }
                },
                "required": ["food_name"]
            }
        ),
        Tool(
            name="calculate_bmi",
            description="根据身高和体重计算 BMI 指数，并给出健康评估（偏瘦/正常/偏胖/肥胖）",
            inputSchema={
                "type": "object",
                "properties": {
                    "height": {
                        "type": "number",
                        "description": "身高，单位：厘米（cm），例如：175"
                    },
                    "weight": {
                        "type": "number",
                        "description": "体重，单位：公斤（kg），例如：70"
                    }
                },
                "required": ["height", "weight"]
            }
        )
    ]


# ============ 2. 处理工具调用 ============

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    处理工具调用请求

    当 Agent 决定调用工具时，会发送 "tools/call" 请求到 Server，
    这个方法负责路由到具体的工具实现逻辑。

    参数：
        name: 工具名称（对应 list_tools 返回的 Tool.name）
        arguments: 工具参数（dict 格式，对应 Tool.inputSchema）

    返回值：
        list[TextContent]: 工具执行结果
            - TextContent.type: "text"（文本类型）
            - TextContent.text: 结果文本

    异常：
        ValueError: 当工具名称不存在时抛出

    类比：
        类似 Spring Boot 的 Controller 方法：
        @PostMapping("/tools/call")
        public ToolResult callTool(@RequestParam String name, @RequestBody Map arguments)
    """
    if name == "query_nutrition":
        # 调用营养查询逻辑
        food_name = arguments["food_name"]
        result = query_nutrition_logic(food_name)
        return [TextContent(type="text", text=result)]

    elif name == "calculate_bmi":
        # 调用 BMI 计算逻辑
        height = arguments["height"]
        weight = arguments["weight"]
        result = calculate_bmi_logic(height, weight)
        return [TextContent(type="text", text=result)]

    else:
        # 未知工具，抛出异常
        raise ValueError(f"Unknown tool: {name}")


# ============ 3. 工具实现逻辑 ============

def query_nutrition_logic(food_name: str) -> str:
    """
    查询食物营养成分

    实际项目中应该：
    1. 查询数据库（Supabase）
    2. 调用第三方营养 API
    3. 使用 RAG 从知识库检索

    这里为了演示，使用硬编码的数据
    """
    # 模拟营养数据库
    nutrition_db = {
        "苹果": {"热量": 52, "蛋白质": 0.3, "脂肪": 0.2, "碳水": 13.8},
        "香蕉": {"热量": 89, "蛋白质": 1.1, "脂肪": 0.3, "碳水": 22.8},
        "米饭": {"热量": 116, "蛋白质": 2.6, "脂肪": 0.3, "碳水": 25.9},
        "鸡胸肉": {"热量": 133, "蛋白质": 24.6, "脂肪": 5.0, "碳水": 0.0},
        "鸡蛋": {"热量": 147, "蛋白质": 12.8, "脂肪": 10.6, "碳水": 1.3},
    }

    if food_name in nutrition_db:
        data = nutrition_db[food_name]
        return f"""{food_name}的营养成分（每100g）：
- 热量：{data['热量']} kcal
- 蛋白质：{data['蛋白质']} g
- 脂肪：{data['脂肪']} g
- 碳水化合物：{data['碳水']} g"""
    else:
        return f"抱歉，暂无 {food_name} 的营养数据。当前支持的食物：苹果、香蕉、米饭、鸡胸肉、鸡蛋"


def calculate_bmi_logic(height: float, weight: float) -> str:
    """
    计算 BMI 指数

    BMI 计算公式：
        BMI = 体重(kg) / 身高(m)^2

    健康标准（中国标准）：
        < 18.5: 偏瘦
        18.5 - 23.9: 正常
        24.0 - 27.9: 偏胖
        >= 28.0: 肥胖
    """
    # 身高转换为米
    height_m = height / 100

    # 计算 BMI
    bmi = weight / (height_m ** 2)

    # 健康评估
    if bmi < 18.5:
        status = "偏瘦"
        advice = "建议增加营养摄入，适当增重"
    elif bmi < 24:
        status = "正常"
        advice = "保持当前体重，继续健康饮食"
    elif bmi < 28:
        status = "偏胖"
        advice = "建议控制饮食，增加运动"
    else:
        status = "肥胖"
        advice = "建议咨询医生，制定减重计划"

    return f"""BMI 计算结果：
- 身高：{height} cm
- 体重：{weight} kg
- BMI：{bmi:.1f}
- 评估：{status}
- 建议：{advice}"""


# ============ 4. 启动 Server ============

async def main():
    """
    启动 MCP Server

    使用 stdio 传输方式（标准输入输出）：
    - Host 会启动这个 Python 进程
    - 通过 stdin 发送请求（JSON-RPC 2.0 格式）
    - 通过 stdout 接收响应

    类比：
        类似 Unix 管道通信：
        Host 进程 | Python Server 进程
    """
    from mcp.server.stdio import stdio_server

    # stdio_server() 返回一个异步上下文管理器
    # read_stream: 从 stdin 读取 Client 请求
    # write_stream: 向 stdout 写入响应
    async with stdio_server() as (read_stream, write_stream):
        # server.run() 启动消息循环
        # 参数：
        #   read_stream: 输入流
        #   write_stream: 输出流
        #   initialization_options: 初始化选项
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
