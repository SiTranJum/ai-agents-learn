"""
练习 2：Few-shot Learning（少样本学习）

任务：让 AI 从自然语言中提取食物和数量，用 Few-shot 提升准确率
"""

from openai import OpenAI

client = OpenAI(
    api_key="sk-539707f4724a4e39a213e9b51e3f9c12",
    base_url="https://api.deepseek.com"
)

print("=== 练习 2：Few-shot Learning ===\n")

# ============================================================
# Zero-shot：不给示例，直接让 AI 做
# ============================================================
print("【Zero-shot（不给示例）】\n")

response_zero = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "system",
            "content": "从用户输入中提取食物名称和数量，用 JSON 格式返回。"
        },
        {
            "role": "user",
            "content": "我早上吃了两个鸡蛋和一杯牛奶"
        }
    ],
    temperature=0.3
)

print(response_zero.choices[0].message.content)
print("\n" + "="*50 + "\n")

# ============================================================
# Few-shot：给 3 个示例，让 AI 学会模式
# ============================================================
print("【Few-shot（给 3 个示例）】\n")

system_prompt_few_shot = """
从用户输入中提取食物名称和数量，用 JSON 数组格式返回。

示例 1：
输入：我早上吃了两个鸡蛋
输出：[{"food": "鸡蛋", "amount": 2, "unit": "个"}]

示例 2：
输入：喝了一大杯牛奶
输出：[{"food": "牛奶", "amount": 1, "unit": "大杯"}]

示例 3：
输入：午饭吃了一碗米饭和一些青菜
输出：[
  {"food": "米饭", "amount": 1, "unit": "碗"},
  {"food": "青菜", "amount": null, "unit": "一些"}
]

现在处理用户输入，只返回 JSON，不要其他解释。
"""

response_few = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt_few_shot},
        {"role": "user", "content": "我早上吃了两个鸡蛋和一杯牛奶"}
    ],
    temperature=0.3
)

print(response_few.choices[0].message.content)
print("\n观察：Few-shot 的输出格式更统一、更符合预期")
