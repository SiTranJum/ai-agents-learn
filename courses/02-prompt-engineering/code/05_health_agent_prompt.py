"""
练习 5：设计健康管家的 System Prompt

任务：为健康管家产品设计一个完整的 System Prompt
"""

from openai import OpenAI

client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"
)

# ============================================================
# 健康管家的 System Prompt 设计
# ============================================================

system_prompt = """
你是"健康管家"AI 助手，一个专业且友好的营养顾问。

## 你的能力
- 分析食物的营养成分（热量、蛋白质、脂肪、碳水化合物等）
- 提供个性化的饮食建议
- 帮助用户记录和追踪饮食习惯
- 解答健康饮食相关问题

## 你的原则
1. 回答要科学准确，基于营养学知识
2. 语气友好亲切，像朋友聊天，不要过于正式
3. 不提供医疗诊断，不推荐药物
4. 遇到严重健康问题（如疾病、过敏），建议咨询医生
5. 数据不确定时，说明是估算值

## 输出格式
- 营养数据：用 JSON 格式
- 建议：用简洁的要点
- 必要时展示计算过程

## 处理模糊输入
- 数量不明确：询问具体数量，或给出常见份量的估算
- 食物不明确：列出可能的选项
- 烹饪方式不明确：询问（煎/炸/蒸/煮会影响热量）
"""

# ============================================================
# 测试对话
# ============================================================

print("=== 健康管家对话测试 ===\n")

# 用户画像（可以动态更新）
user_profile = "用户信息：30 岁男性，身高 175cm，体重 70kg，目标减脂，每日热量目标 1800 千卡"

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "system", "content": user_profile}
]

# 第一轮对话
user_input_1 = "我今天早餐吃了两个鸡蛋和一杯牛奶"
messages.append({"role": "user", "content": user_input_1})

response_1 = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    temperature=0.7
)

ai_reply_1 = response_1.choices[0].message.content
print(f"用户：{user_input_1}")
print(f"AI：{ai_reply_1}\n")
print("="*50 + "\n")

# 把 AI 的回复加入对话历史
messages.append({"role": "assistant", "content": ai_reply_1})

# 第二轮对话（基于上下文追问）
user_input_2 = "那我午餐吃什么比较好？"
messages.append({"role": "user", "content": user_input_2})

response_2 = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    temperature=0.7
)

ai_reply_2 = response_2.choices[0].message.content
print(f"用户：{user_input_2}")
print(f"AI：{ai_reply_2}")
