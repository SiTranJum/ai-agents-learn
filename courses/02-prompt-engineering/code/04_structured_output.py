"""
练习 4：结构化输出（JSON 格式）

任务：让 AI 返回程序可以直接处理的 JSON 数据
"""

from openai import OpenAI
import json

client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"
)

print("=== 练习 4：结构化输出 ===\n")

# ============================================================
# 要求 AI 返回 JSON 格式的营养数据
# ============================================================

system_prompt = """
你是营养数据库 API，返回食物的营养信息。
只返回 JSON，不要其他解释。

格式：
{
  "food": "食物名称",
  "amount": 数量,
  "unit": "单位",
  "nutrition": {
    "calories": 热量(千卡),
    "protein": 蛋白质(克),
    "fat": 脂肪(克),
    "carbs": 碳水化合物(克)
  }
}
"""

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "鸡胸肉 150g"}
    ],
    temperature=0.3  # 低温度，输出更稳定
)

# 获取 AI 的回复
ai_output = response.choices[0].message.content
print("AI 返回的内容：")
print(ai_output)
print()

# 尝试解析 JSON
try:
    data = json.loads(ai_output)
    print("✅ JSON 解析成功！")
    print(f"食物：{data['food']}")
    print(f"热量：{data['nutrition']['calories']} 千卡")
    print(f"蛋白质：{data['nutrition']['protein']} 克")
except json.JSONDecodeError:
    print("❌ JSON 解析失败，AI 可能返回了额外的文字")
