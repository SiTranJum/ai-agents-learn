import os
"""
练习：探索 Chat Completions API

通过 3 个小任务，熟悉 API 的核心参数和返回值。
每个任务都可以独立运行，建议按顺序完成。
"""

from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ============================================================
# 任务一：体验 temperature 对输出的影响
# ============================================================
# 说明：同一个 prompt，不同 temperature 会产生不同风格的输出
# 操作：分别将 TEMPERATURE 改为 0、0.7、1.5，各运行一次，对比结果

TEMPERATURE = 0  # TODO: 分别改为 0, 0.7, 1.5

print(f"=== 任务一：Temperature = {TEMPERATURE} ===\n")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个创意写作助手。"},
        {"role": "user", "content": "写一句关于春天的诗。"}
    ],
    temperature=TEMPERATURE,
    max_tokens=50
)

print(response.choices[0].message.content)
print(f"Token 用量：{response.usage.total_tokens}")

# ============================================================
# 任务二：体验 max_tokens 截断效果
# ============================================================
# 说明：当 max_tokens 设得很小时，AI 的回复会被强制截断
# 操作：观察 finish_reason 的值，理解 "stop" 和 "length" 的区别

print("\n=== 任务二：max_tokens 截断测试 ===\n")

response_short = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "详细介绍一下春天的特点。"}
    ],
    temperature=0.7,
    max_tokens=10  # 故意设得很小，观察截断效果
)

print(f"回复内容：{response_short.choices[0].message.content}")
print(f"结束原因：{response_short.choices[0].finish_reason}")
# 预期：finish_reason = "length"，说明回复被截断了
# 如果是 "stop"，说明 AI 恰好在限制内说完了

# ============================================================
# 任务三：多轮对话 —— messages 列表的作用
# ============================================================
# 说明：LLM 本身没有记忆，"记忆"是通过把历史消息都传进去实现的
# 操作：观察第二轮对话中，AI 是否记得第一轮的内容

print("\n=== 任务三：多轮对话 ===\n")

# 第一轮：告诉 AI 一个信息
messages = [
    {"role": "system", "content": "你是一个健康顾问。"},
    {"role": "user", "content": "我今天早餐吃了两个鸡蛋和一杯牛奶。"}
]

response_1 = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    temperature=0.7,
    max_tokens=100
)

ai_reply_1 = response_1.choices[0].message.content
print(f"AI 第一轮回复：{ai_reply_1}")

# 关键步骤：把 AI 的回复加入 messages，这样下一轮调用时 AI 就有了上下文
# 这就是"多轮对话"的实现原理 —— 每次都把完整历史传过去
messages.append({"role": "assistant", "content": ai_reply_1})

# 第二轮：基于上下文追问
messages.append({"role": "user", "content": "那我这顿早餐大概摄入了多少蛋白质？"})

response_2 = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,  # 包含了完整的对话历史
    temperature=0.7,
    max_tokens=150
)

ai_reply_2 = response_2.choices[0].message.content
print(f"\nAI 第二轮回复：{ai_reply_2}")
# AI 能回答蛋白质问题，因为它从 messages 里看到了你吃了什么

# 查看第二轮的 token 用量（会比第一轮多，因为输入包含了历史消息）
print(f"\n第一轮 Token：{response_1.usage.total_tokens}")
print(f"第二轮 Token：{response_2.usage.total_tokens}")
# 注意：轮次越多，输入 token 越多，费用越高 —— 这就是为什么后面要学"记忆管理"
