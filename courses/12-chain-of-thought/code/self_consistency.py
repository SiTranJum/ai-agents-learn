"""
课程 12：Self-Consistency CoT 实现

核心思想：
- 同一个问题，让 LLM 用较高的 temperature 推理多次
- 提取每次推理的最终结果
- 取出现次数最多的结果（多数投票）

类比 Java：
- 类似分布式系统的 Quorum（多数投票）
- 多个副本计算同一个结果，取一致性最高的
"""

import sys
import io
import re
from collections import Counter
from openai import OpenAI

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"
)


def self_consistency_cot(question: str, num_samples: int = 3) -> str:
    """
    Self-Consistency CoT：多次推理取一致结果

    参数：
    - question: 用户问题
    - num_samples: 推理次数（默认 3 次）

    返回：
    - str: 最终回答（包含所有推理过程）

    原理：
    1. 用较高的 temperature（0.7）调用 LLM 多次
    2. 每次都会得到稍微不同的推理路径
    3. 提取每次推理的最终数字结果
    4. 取出现次数最多的结果作为最终答案
    """

    system_prompt = """你是健康管家 AI。请逐步计算用户的饮食热量。

要求：
1. 逐步计算每种食物的热量
2. 计算总热量
3. 最后一行必须用这个格式：【总热量：XXX 卡】
"""

    results = []     # 存储每次推理的完整回复
    numbers = []     # 存储每次推理提取的数字

    for i in range(num_samples):
        # 调用 LLM（temperature=0.7，让每次结果略有不同）
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7
        )
        reply = response.choices[0].message.content
        results.append(reply)

        # 提取最终数字（匹配"总热量：XXX"）
        match = re.search(r'总热量[：:]\s*(\d+)', reply)
        if match:
            numbers.append(int(match.group(1)))

        print(f"--- 第 {i+1} 次推理 ---")
        print(reply)
        print()

    # 多数投票：取出现次数最多的数字
    if numbers:
        # Counter 统计每个数字出现的次数
        # most_common(1) 返回出现次数最多的 1 个元素
        counter = Counter(numbers)
        most_common = counter.most_common(1)[0]  # (数字, 出现次数)
        best_answer = most_common[0]
        count = most_common[1]

        print(f"{'='*40}")
        print(f"所有推理结果：{numbers}")
        print(f"投票结果：{best_answer} 卡（{count}/{num_samples} 次一致）")
        print(f"{'='*40}")

        return f"经过 {num_samples} 次独立推理，您的总热量为 {best_answer} 卡（{count}/{num_samples} 次结果一致）"
    else:
        return "无法提取推理结果"


# ============================================
# 测试
# ============================================

if __name__ == "__main__":
    print("课程 12：Self-Consistency CoT\n")

    question = """请计算我今天的总热量：
- 早餐：2 个鸡蛋、1 杯牛奶
- 午餐：一碗米饭、鸡胸肉 150g、炒青菜
- 晚餐：一碗面条、一个煎蛋"""

    print(f"问题：{question}\n")

    result = self_consistency_cot(question, num_samples=3)
    print(f"\n最终结论：{result}")
