import os
"""
模式二：并行扇出（Fan-out / Fan-in）

场景：用户要求综合健康分析 → 同时启动营养/运动/睡眠三个 Agent → 汇总结果

多个 Agent 并行工作，最后汇总。
"""

from openai import OpenAI
import asyncio  # 用于并行执行
from typing import List

# 创建 DashScope 客户端
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def create_agent(name: str, system_prompt: str):
    """创建一个 Agent"""
    def run(user_message: str) -> str:
        print(f"\n[{name}] 开始工作...")

        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )

        result = response.choices[0].message.content
        print(f"[{name}] 完成：{result[:500]}...")
        return result

    run.name = name
    return run


# ============ 定义四个 Agent ============

# Agent 1：营养分析 Agent
nutrition_agent = create_agent(
    name="营养分析Agent",
    system_prompt="""
你是营养分析专家。
用户会告诉你今天吃了什么，你需要：
1. 估算总热量
2. 评价营养是否均衡
3. 给出 1-2 句建议

输出格式：简短的分析（2-3 句话）
"""
)

# Agent 2：运动分析 Agent
exercise_agent = create_agent(
    name="运动分析Agent",
    system_prompt="""
你是运动分析专家。
用户会告诉你今天的运动情况，你需要：
1. 估算运动消耗
2. 评价运动量是否足够
3. 给出 1-2 句建议

输出格式：简短的分析（2-3 句话）
"""
)

# Agent 3：睡眠分析 Agent
sleep_agent = create_agent(
    name="睡眠分析Agent",
    system_prompt="""
你是睡眠分析专家。
用户会告诉你今天的睡眠情况，你需要：
1. 评价睡眠时长是否充足
2. 评价睡眠质量
3. 给出 1-2 句建议

输出格式：简短的分析（2-3 句话）
"""
)

# Agent 4：汇总 Agent
summary_agent = create_agent(
    name="汇总Agent",
    system_prompt="""
你是健康管家。
你会收到三个专家的分析报告（营养、运动、睡眠），你需要：
1. 综合三方面的情况
2. 给出整体的健康评价
3. 提供 2-3 条最重要的改进建议

语气友好、鼓励为主。
输出格式：自然语言，3-5 句话。
"""
)


# ============ 并行扇出执行 ============

async def fan_out_fan_in(user_input: str) -> str:
    """
    并行扇出：同时启动三个分析 Agent，最后汇总。

    参数：
        user_input: 用户的综合健康数据描述
    返回：
        汇总后的健康建议

    注意：这里用 asyncio 模拟并行，但实际上 OpenAI SDK 的同步调用会阻塞。
    真正的并行需要用异步 SDK 或多线程。这里重点是展示架构模式。
    """
    print("=" * 60)
    print("开始并行分析")
    print("=" * 60)

    # 并行执行三个 Agent
    # asyncio.gather() — 并行执行多个协程，等待全部完成
    # 类比 Java：CompletableFuture.allOf()
    nutrition_result, exercise_result, sleep_result = await asyncio.gather(
        asyncio.to_thread(nutrition_agent, user_input),  # 在线程中运行同步函数
        asyncio.to_thread(exercise_agent, user_input),
        asyncio.to_thread(sleep_agent, user_input)
    )

    print("\n" + "=" * 60)
    print("三个 Agent 都完成了，开始汇总")
    print("=" * 60)

    # 汇总结果
    summary_input = f"""
营养分析：{nutrition_result}

运动分析：{exercise_result}

睡眠分析：{sleep_result}
"""
    final_result = summary_agent(summary_input)

    print("=" * 60)
    print("汇总完成")
    print("=" * 60)

    return final_result


# ============ 测试 ============

if __name__ == "__main__":
    # 测试用例
    user_input = """
我今天早上吃了一碗牛肉面，中午吃了沙拉，晚上吃了鸡胸肉和西兰花。
下午跑了 5 公里，用时 30 分钟。
晚上 11 点睡觉，早上 6 点起床，睡了 7 小时。
"""

    # asyncio.run() — 运行异步函数的入口
    # 类比 Java：类似于 main() 方法启动应用
    result = asyncio.run(fan_out_fan_in(user_input))

    print(f"\n最终建议：\n{result}\n")
