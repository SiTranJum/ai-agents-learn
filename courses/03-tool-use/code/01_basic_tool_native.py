import os
"""
Tool Use 基础示例：天气查询（使用 DeepSeek 原生 Function Calling）

DeepSeek API 支持原生的 Function Calling（工具调用）
使用方式与 OpenAI 的 Function Calling 完全一致
"""

from openai import OpenAI
import json

# 初始化 DeepSeek 客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ============================================
# 第一步：定义工具
# ============================================
# 工具定义使用 JSON Schema 格式
# 类比 Java：这就像定义一个接口方法的签名和文档
tools = [
    {
        "type": "function",  # 固定值，表示这是一个函数工具
        "function": {
            "name": "get_weather",  # 工具名称（函数名）
            "description": "获取指定城市的实时天气信息，包括温度和天气状况",  # 描述
            "parameters": {  # 参数定义（JSON Schema 格式）
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'、'深圳'"
                    }
                },
                "required": ["city"]  # 必填参数
            }
        }
    }
]

# ============================================
# 第二步：定义实际的工具函数
# ============================================
def get_weather(city: str) -> dict:
    """
    获取天气信息（这里用模拟数据）

    实际项目中，这里会调用真实的天气 API，如：
    - 和风天气 API
    - OpenWeatherMap API
    - 高德天气 API

    参数：
        city: 城市名称

    返回：
        包含温度和天气状况的字典
    """
    # 模拟数据
    weather_data = {
        "北京": {"temperature": 15, "condition": "晴天"},
        "上海": {"temperature": 20, "condition": "多云"},
        "深圳": {"temperature": 25, "condition": "小雨"},
    }
    return weather_data.get(city, {"temperature": 0, "condition": "未知城市"})


# ============================================
# 第三步：发送消息给 LLM（带工具定义）
# ============================================
def chat_with_tool(user_message: str):
    """
    带工具调用的对话函数

    参数：
        user_message: 用户消息
    """
    print(f"\n用户：{user_message}")
    print("-" * 50)

    # 调用 DeepSeek API
    # 注意：这里传入了 tools 参数
    response = client.chat.completions.create(
        model="deepseek-chat",  # 模型名称
        messages=[
            {"role": "user", "content": user_message}
        ],
        tools=tools,  # 传递工具定义列表
        tool_choice="auto"  # 让 LLM 自动决定是否调用工具
        # tool_choice 可选值：
        # - "auto": 自动决定（推荐）
        # - "none": 不调用工具
        # - {"type": "function", "function": {"name": "get_weather"}}: 强制调用指定工具
    )

    print(f"LLM 响应类型：{response.choices[0].finish_reason}")
    # finish_reason 可能的值：
    # - "stop": 正常结束，没有工具调用
    # - "tool_calls": 需要调用工具
    # - "length": 达到最大 token 限制

    # ============================================
    # 第四步：解析 LLM 的响应
    # ============================================
    message = response.choices[0].message

    # 检查是否有工具调用
    if message.tool_calls:
        # 有工具调用请求
        print(f"\n🔧 LLM 请求调用 {len(message.tool_calls)} 个工具：")

        # 遍历所有工具调用（可能有多个）
        for tool_call in message.tool_calls:
            # tool_call 的结构：
            # - id: 工具调用 ID（用于返回结果时匹配）
            # - type: 固定为 "function"
            # - function.name: 工具名称
            # - function.arguments: 工具参数（JSON 字符串）

            tool_call_id = tool_call.id
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)  # 解析 JSON 字符串为字典

            print(f"\n   工具 ID: {tool_call_id}")
            print(f"   工具名称: {tool_name}")
            print(f"   参数: {json.dumps(tool_args, ensure_ascii=False)}")

            # ============================================
            # 第五步：执行工具函数
            # ============================================
            if tool_name == "get_weather":
                # 执行工具函数
                # ** 是 Python 的解包操作符，将字典解包为关键字参数
                # 类比 Java：类似于反射调用 method.invoke(obj, args)
                result = get_weather(**tool_args)
                print(f"   工具返回: {json.dumps(result, ensure_ascii=False)}")

                # ============================================
                # 第六步：将工具结果返回给 LLM
                # ============================================
                # 构建包含工具结果的消息历史
                messages = [
                    {"role": "user", "content": user_message},
                    message,  # LLM 的工具调用请求（包含 tool_calls）
                    {
                        "role": "tool",  # 角色是 "tool"
                        "tool_call_id": tool_call_id,  # 必须匹配之前的 tool_call_id
                        "content": json.dumps(result, ensure_ascii=False)  # 工具结果（字符串格式）
                    }
                ]

                # 再次调用 LLM，让它基于工具结果生成回复
                final_response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    tools=tools
                )

                # 输出最终回复
                print("\n" + "=" * 50)
                final_message = final_response.choices[0].message
                print(f"LLM 最终回复：{final_message.content}")

    else:
        # 没有工具调用，直接输出文本
        print(f"\nLLM 直接回复：{message.content}")


# ============================================
# 测试
# ============================================
if __name__ == "__main__":
    # 测试 1：需要调用工具的问题
    chat_with_tool("北京今天天气怎么样？")

    # 测试 2：不需要调用工具的问题
    print("\n\n" + "=" * 70 + "\n")
    chat_with_tool("你好，请介绍一下自己")
