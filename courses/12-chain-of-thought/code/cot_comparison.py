"""
课程 12：Chain of Thought 三种用法对比

对比：
1. 无 CoT：直接回答
2. Zero-shot CoT：加一句"请一步步推理"
3. Few-shot CoT：给出推理示例

通过同一个问题，观察三种方式的回答质量差异。
"""

import sys
import io
import json
from openai import OpenAI

# 解决 Windows 终端中文输出问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# DeepSeek API 客户端
client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"
)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    调用 LLM

    参数：
    - system_prompt: 系统提示词
    - user_prompt: 用户输入

    返回：
    - str: LLM 回复
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3  # 低温度，让结果更确定，方便对比
    )
    return response.choices[0].message.content


# ============================================
# 测试问题
# ============================================

test_question = """我今天的饮食如下：
- 早餐：2 个鸡蛋（每个 70 卡）、1 杯牛奶（150 卡）
- 午餐：一碗米饭（200 卡）、鸡胸肉 150g（约 250 卡）、炒青菜（50 卡）
- 下午茶：一个苹果（52 卡）
- 晚餐：一碗面条（300 卡）、一个煎蛋（90 卡）

我的目标是每天 1800 卡。请分析我今天的饮食情况。"""


# ============================================
# 方式 1：无 CoT（直接回答）
# ============================================

def test_no_cot():
    """无 CoT：直接回答"""
    system_prompt = "你是健康管家 AI，帮助用户分析饮食。请简洁回答。"

    print("=" * 60)
    print("方式 1：无 CoT（直接回答）")
    print("=" * 60)

    result = call_llm(system_prompt, test_question)
    print(result)
    print()


# ============================================
# 方式 2：Zero-shot CoT
# ============================================

def test_zero_shot_cot():
    """
    Zero-shot CoT：在 system_prompt 中要求逐步推理

    关键：只需要加一句"请一步步分析"
    """
    system_prompt = """你是健康管家 AI，帮助用户分析饮食。

回答时请一步步分析：先计算每餐热量，再算总热量，最后给出建议。"""

    print("=" * 60)
    print("方式 2：Zero-shot CoT（一步步思考）")
    print("=" * 60)

    result = call_llm(system_prompt, test_question)
    print(result)
    print()


# ============================================
# 方式 3：Few-shot CoT
# ============================================

def test_few_shot_cot():
    """
    Few-shot CoT：给出推理示例，让 LLM 模仿

    关键：提供一个完整的推理示例，包括每一步的计算过程
    """
    system_prompt = """你是健康管家 AI，帮助用户分析饮食。

请严格按照以下格式逐步分析：

【示例】
用户饮食：早餐 3 个苹果（每个 52 卡），午餐一碗米饭（200 卡）
用户目标：1500 卡

分析：
1. 各餐热量计算：
   - 早餐：3 × 52 = 156 卡
   - 午餐：200 卡
2. 今日总摄入：156 + 200 = 356 卡
3. 与目标对比：目标 1500 卡，已摄入 356 卡，剩余 1144 卡
4. 营养评估：
   - 热量：远低于目标（仅 23.7%）
   - 蛋白质：不足，缺乏肉类/蛋类
   - 建议：晚餐需要大量补充，建议摄入高蛋白食物

请按此格式分析用户的饮食。
"""

    print("=" * 60)
    print("方式 3：Few-shot CoT（给出推理示例）")
    print("=" * 60)

    result = call_llm(system_prompt, test_question)
    print(result)
    print()


# ============================================
# 主函数
# ============================================

if __name__ == "__main__":
    print("课程 12：Chain of Thought 三种用法对比\n")
    print(f"测试问题：{test_question}\n")

    test_no_cot()
    test_zero_shot_cot()
    test_few_shot_cot()

    print("=" * 60)
    print("对比总结")
    print("=" * 60)
    print("""
1. 无 CoT：回答可能不够精确，缺少推理过程
2. Zero-shot CoT：加一句话就能改善，但格式不可控
3. Few-shot CoT：格式最可控，推理最严谨，但占用更多上下文

建议：
- 简单任务 → 无 CoT
- 一般推理 → Zero-shot CoT
- 重要计算 → Few-shot CoT
""")
