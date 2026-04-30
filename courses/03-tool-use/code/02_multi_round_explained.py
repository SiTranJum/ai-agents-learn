"""
Tool Use 的"多轮请求"详解

对比：
1. 普通对话：1 轮请求
2. Tool Use：2+ 轮请求
"""

from openai import OpenAI
import json

client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"
)

print("=" * 70)
print("示例 1：普通对话（1 轮请求）")
print("=" * 70)

# 普通对话：只需要 1 次 API 调用
print("\n【第 1 轮】你 → LLM：发送用户消息")
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
)

print("【第 1 轮】LLM → 你：直接返回最终回复")
print(f"回复：{response.choices[0].message.content}")
print("\n✅ 完成！只用了 1 轮请求\n")


print("\n" + "=" * 70)
print("示例 2：Tool Use（多轮请求）")
print("=" * 70)

# 定义工具
tools = [{
    "name": "get_weather",
    "description": "获取指定城市的天气",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"}
        },
        "required": ["city"]
    }
}]

# 构建 System Prompt（告诉 LLM 有哪些工具）
system_prompt = f"""你是一个智能助手，可以调用外部工具。

可用工具：
{json.dumps(tools, ensure_ascii=False, indent=2)}

当需要调用工具时，返回 JSON 格式：
{{
    "tool_call": true,
    "tool_name": "工具名",
    "parameters": {{"参数": "值"}}
}}
"""

# ============================================
# 第 1 轮请求
# ============================================
print("\n【第 1 轮】你 → LLM：发送用户消息 + 工具定义")
print("  用户消息：'北京今天天气怎么样？'")
print("  工具定义：get_weather(city)")

response_1 = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "北京今天天气怎么样？"}
    ]
)

content_1 = response_1.choices[0].message.content
print("\n【第 1 轮】LLM → 你：返回工具调用请求")
print(f"  LLM 说：{content_1}")

# 解析工具调用请求
try:
    # 提取 JSON（可能在代码块中）
    if "```json" in content_1:
        json_start = content_1.find("```json") + 7
        json_end = content_1.find("```", json_start)
        json_str = content_1[json_start:json_end].strip()
    else:
        json_str = content_1.strip()

    tool_request = json.loads(json_str)

    if tool_request.get("tool_call"):
        print("\n  ✅ 检测到工具调用请求：")
        print(f"     工具名：{tool_request['tool_name']}")
        print(f"     参数：{tool_request['parameters']}")

        # ============================================
        # 你的代码执行工具（这不是 API 调用）
        # ============================================
        print("\n【你的代码】执行工具函数（本地执行，不是 API 调用）")
        # 模拟工具执行
        tool_result = {"temperature": 15, "condition": "晴天"}
        print(f"  工具返回：{tool_result}")

        # ============================================
        # 第 2 轮请求
        # ============================================
        print("\n【第 2 轮】你 → LLM：发送工具执行结果")
        print(f"  工具结果：{tool_result}")

        response_2 = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "北京今天天气怎么样？"},
                {"role": "assistant", "content": content_1},
                {
                    "role": "user",
                    "content": f"工具执行结果：{json.dumps(tool_result, ensure_ascii=False)}\n\n请基于这个结果回答用户的问题。"
                }
            ]
        )

        content_2 = response_2.choices[0].message.content
        print("\n【第 2 轮】LLM → 你：返回最终回复")
        print(f"  LLM 说：{content_2}")

        print("\n✅ 完成！用了 2 轮请求")

except Exception as e:
    print(f"\n❌ 解析失败：{e}")


print("\n" + "=" * 70)
print("总结：为什么需要多轮？")
print("=" * 70)
print("""
1. LLM 不能直接执行代码，只能"建议"调用工具
2. 你的代码负责实际执行工具（查数据库、调 API 等）
3. 执行结果需要再发给 LLM，让它生成用户友好的回复

类比 Java：
- 第 1 轮：Controller 收到请求，决定调用哪个 Service
- 中间：实际执行 Service 方法（不是 HTTP 请求）
- 第 2 轮：Controller 拿到 Service 结果，返回给前端

Tool Use 就是把 LLM 当作"决策者"，你的代码是"执行者"
""")
