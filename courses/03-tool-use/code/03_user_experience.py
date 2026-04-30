"""
Tool Use 的用户体验设计

关键：用户只看到最终结果，不看到中间的工具调用过程

实现方式：
1. 后端用循环完成所有工具调用
2. 只向前端返回最终的 AI 回复
3. 可选：通过 WebSocket 或 SSE 实时展示工具调用状态
"""

from openai import OpenAI
import json
import time

client = OpenAI(
    api_key="sk-539707f4724a4e39a213e9b51e3f9c12",
    base_url="https://api.deepseek.com"
)

# ============================================
# 工具定义和函数
# ============================================
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

def get_weather(city: str) -> dict:
    """模拟天气查询（实际会调用真实 API）"""
    time.sleep(0.5)  # 模拟 API 延迟
    weather_data = {
        "北京": {"temperature": 15, "condition": "晴天"},
        "上海": {"temperature": 20, "condition": "多云"},
        "深圳": {"temperature": 25, "condition": "小雨"},
    }
    return weather_data.get(city, {"temperature": 0, "condition": "未知城市"})

tools_map = {
    "get_weather": get_weather
}

# ============================================
# System Prompt
# ============================================
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
# 核心函数：在后端完成所有工具调用
# ============================================
def chat_with_tools(user_message: str, show_process: bool = False):
    """
    带工具调用的对话函数

    参数：
        user_message: 用户消息
        show_process: 是否展示中间过程（调试用）

    返回：
        最终的 AI 回复（字符串）
    """
    # 初始化消息历史
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    # 最多循环 5 次（防止无限循环）
    max_iterations = 5

    for iteration in range(max_iterations):
        if show_process:
            print(f"\n{'='*50}")
            print(f"第 {iteration + 1} 轮 API 调用")
            print(f"{'='*50}")

        # 调用 LLM
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7
        )

        content = response.choices[0].message.content

        # 尝试解析是否是工具调用
        try:
            # 提取 JSON
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()

            parsed = json.loads(json_str)

            if parsed.get("tool_call"):
                # 是工具调用
                tool_name = parsed["tool_name"]
                parameters = parsed["parameters"]

                if show_process:
                    print(f"🔧 LLM 请求调用工具：{tool_name}")
                    print(f"   参数：{parameters}")

                # 执行工具
                tool_function = tools_map.get(tool_name)
                if tool_function:
                    result = tool_function(**parameters)
                    if show_process:
                        print(f"   工具返回：{result}")
                else:
                    result = {"error": f"未找到工具：{tool_name}"}

                # 将工具调用和结果添加到消息历史
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": f"工具执行结果：{json.dumps(result, ensure_ascii=False)}\n\n请基于这个结果回答用户的问题。"
                })

                # 继续循环，让 LLM 处理工具结果
                continue

        except:
            pass

        # 不是工具调用，说明是最终回复
        if show_process:
            print(f"\n✅ 得到最终回复")

        return content

    # 超过最大循环次数
    return "抱歉，处理超时了。"


# ============================================
# 模拟用户体验
# ============================================
print("=" * 70)
print("模拟用户视角（看不到中间过程）")
print("=" * 70)

print("\n用户：北京今天天气怎么样？")
print("[AI 思考中...]")

# 后端完成所有工具调用
final_answer = chat_with_tools("北京今天天气怎么样？", show_process=False)

print(f"AI：{final_answer}")


print("\n\n" + "=" * 70)
print("开发者视角（展示中间过程）")
print("=" * 70)

print("\n用户：北京今天天气怎么样？")

# 展示中间过程（调试用）
final_answer = chat_with_tools("北京今天天气怎么样？", show_process=True)

print(f"\n最终返回给用户：{final_answer}")


# ============================================
# 实际产品中的实现方式
# ============================================
print("\n\n" + "=" * 70)
print("实际产品中的实现方式")
print("=" * 70)

print("""
方案 1：简单方式（适合小项目）
- 后端用循环完成所有工具调用
- 前端显示 loading 状态
- 完成后一次性返回最终结果

方案 2：流式展示（更好的用户体验）
- 使用 WebSocket 或 Server-Sent Events (SSE)
- 实时推送工具调用状态：

  前端显示：
  ┌─────────────────────────────┐
  │ 用户：北京天气怎么样？        │
  │                             │
  │ AI：                        │
  │ 🔧 正在查询天气...          │  ← 实时状态
  │ ✅ 查询完成                 │
  │                             │
  │ 北京今天晴天，15°C          │  ← 最终回复
  └─────────────────────────────┘

方案 3：后台任务（适合耗时操作）
- 工具调用放到后台任务队列（Celery、RQ 等）
- 前端轮询或 WebSocket 获取进度
- 适合需要调用多个慢速 API 的场景

推荐：
- 简单对话：方案 1
- 健康管家这种产品：方案 2（用户体验更好）
""")


# ============================================
# 方案 2 的伪代码示例
# ============================================
print("\n" + "=" * 70)
print("方案 2 的伪代码（SSE 流式推送）")
print("=" * 70)

print("""
# 后端（FastAPI 示例）
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

@app.post("/chat")
async def chat(message: str):
    async def event_stream():
        messages = [...]

        for iteration in range(max_iterations):
            # 调用 LLM
            response = client.chat.completions.create(...)

            # 检查是否是工具调用
            if is_tool_call(response):
                tool_name = extract_tool_name(response)

                # 推送状态：开始调用工具
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name})}\\n\\n"

                # 执行工具
                result = execute_tool(tool_name, parameters)

                # 推送状态：工具完成
                yield f"data: {json.dumps({'type': 'tool_done', 'tool': tool_name})}\\n\\n"

                # 继续循环
                continue

            # 推送最终回复
            yield f"data: {json.dumps({'type': 'message', 'content': response})}\\n\\n"
            break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# 前端（React 示例）
const [status, setStatus] = useState('');
const [message, setMessage] = useState('');

const eventSource = new EventSource('/chat?message=' + userMessage);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'tool_start') {
        setStatus(`🔧 正在调用 ${data.tool}...`);
    } else if (data.type === 'tool_done') {
        setStatus(`✅ ${data.tool} 完成`);
    } else if (data.type === 'message') {
        setMessage(data.content);
        setStatus('');
        eventSource.close();
    }
};
""")
