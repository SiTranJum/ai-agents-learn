"""
练习 3：Chain of Thought（思维链）

任务：让 AI 展示推理过程，而不是直接给结论
"""

from openai import OpenAI

client = OpenAI(
    api_key="sk-539707f4724a4e39a213e9b51e3f9c12",
    base_url="https://api.deepseek.com"
)

print("=== 练习 3：Chain of Thought ===\n")

# ============================================================
# 不使用 CoT：直接问，AI 直接给结论
# ============================================================
print("【不使用 CoT】\n")

response_no_cot = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "system",
            "content": "你是营养师。"
        },
        {
            "role": "user",
            "content": "我今天吃了一份炸鸡（约 200g），热量超标了吗？我是 30 岁男性，轻度运动。"
        }
    ],
    temperature=0.7
)

print(response_no_cot.choices[0].message.content)
print("\n" + "="*50 + "\n")

# ============================================================
# 使用 CoT：引导 AI 分步思考
# ============================================================
print("【使用 CoT（分步思考）】\n")

response_cot = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "system",
            "content": "你是营养师，分析问题时要展示推理过程。"
        },
        {
            "role": "user",
            "content": """
我今天吃了一份炸鸡（约 200g），热量超标了吗？我是 30 岁男性，轻度运动。

请按以下步骤分析：
1. 估算 200g 炸鸡的热量
2. 计算我的每日热量需求
3. 判断这一餐占每日需求的比例
4. 得出结论
"""
        }
    ],
    temperature=0.7
)

print(response_cot.choices[0].message.content)
print("\n观察：CoT 让推理过程透明，结论更可信")
