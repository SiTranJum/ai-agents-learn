import os
"""
练习 1：对比不同 prompt 的效果

任务：用同一个问题，尝试 3 种不同质量的 prompt，观察输出差异
"""

from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ============================================================
# 场景：让 AI 分析"红烧肉"的营养
# ============================================================

print("=== 练习 1：Prompt 质量对比 ===\n")

# 差的 prompt：模糊、没有明确要求
print("【差的 prompt】")
response_bad = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "红烧肉"}
    ],
    temperature=0.7
)
print(response_bad.choices[0].message.content)
print("\n" + "="*50 + "\n")

# 中等的 prompt：有明确任务，但不够具体
print("【中等的 prompt】")
response_medium = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "分析红烧肉的营养"}
    ],
    temperature=0.7
)
print(response_medium.choices[0].message.content)
print("\n" + "="*50 + "\n")

# 好的 prompt：清晰、具体、有格式要求
print("【好的 prompt】")
response_good = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "system",
            "content": "你是营养师，分析食物营养时要给出具体数值。"
        },
        {
            "role": "user",
            "content": """
分析"红烧肉 100g"的营养成分，包括：
- 热量（千卡）
- 蛋白质（克）
- 脂肪（克）
- 碳水化合物（克）

用简洁的列表格式返回。
"""
        }
    ],
    temperature=0.7
)
print(response_good.choices[0].message.content)
