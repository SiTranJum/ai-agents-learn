"""
练习：给 Agent 加上记忆能力

目标：
1. 理解短期记忆和长期记忆的区别
2. 实践记忆系统的使用
3. 测试记忆召回的效果

练习任务：
1. 运行示例代码，观察记忆系统的工作方式
2. 测试多轮对话，验证短期记忆
3. 重启程序，验证长期记忆
4. 扩展：添加新的记忆功能
"""

import os
from agent_with_memory import HealthAgent


def test_short_term_memory():
    """
    测试 1：短期记忆（对话历史）

    目标：验证 Agent 能记住当前对话中的信息
    """
    print("=== 测试 1：短期记忆 ===\n")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    agent = HealthAgent(user_id="test_user", api_key=api_key)

    # 第一轮：记录饮食
    print("第一轮对话：")
    print("你：我今天早上吃了两个鸡蛋")
    reply1 = agent.run("我今天早上吃了两个鸡蛋")
    print(f"AI：{reply1}\n")

    # 第二轮：询问刚才记录的内容
    print("第二轮对话：")
    print("你：我的早餐热量是多少？")
    reply2 = agent.run("我的早餐热量是多少？")
    print(f"AI：{reply2}\n")

    # 观察：AI 应该能回答出早餐的热量（因为有短期记忆）

    print("✅ 如果 AI 能回答出早餐热量，说明短期记忆工作正常\n")


def test_long_term_memory():
    """
    测试 2：长期记忆（持久化存储）

    目标：验证 Agent 能记住跨会话的信息
    """
    print("=== 测试 2：长期记忆 ===\n")

    api_key = os.getenv("DEEPSEEK_API_KEY")

    # 第一次会话：设置用户档案
    print("第一次会话：")
    agent1 = HealthAgent(user_id="test_user", api_key=api_key)

    # 更新用户档案
    agent1.long_memory.update_profile(
        name="张三",
        height=175,
        weight=70,
        goal="减肥"
    )
    print("已设置用户档案：张三，175cm，70kg，目标：减肥\n")

    # 记录一些饮食
    print("你：我今天早上吃了两个鸡蛋")
    reply1 = agent1.run("我今天早上吃了两个鸡蛋")
    print(f"AI：{reply1}\n")

    # 模拟程序重启（创建新的 Agent 实例）
    print("--- 模拟程序重启 ---\n")

    # 第二次会话：验证数据是否保留
    print("第二次会话：")
    agent2 = HealthAgent(user_id="test_user", api_key=api_key)

    # 查看用户档案
    profile = agent2.long_memory.get_profile()
    print(f"用户档案：{profile}")

    # 查看今日饮食
    print("\n你：我今天吃了什么？")
    reply2 = agent2.run("我今天吃了什么？")
    print(f"AI：{reply2}\n")

    # 观察：AI 应该能回答出之前记录的饮食（因为有长期记忆）

    print("✅ 如果 AI 能回答出之前记录的饮食，说明长期记忆工作正常\n")


def test_memory_recall():
    """
    测试 3：记忆召回

    目标：验证 Agent 能在合适的时机调用记忆
    """
    print("=== 测试 3：记忆召回 ===\n")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    agent = HealthAgent(user_id="test_user", api_key=api_key)

    # 记录多条饮食
    meals = [
        "我早上吃了两个鸡蛋",
        "中午吃了一碗米饭和鸡胸肉",
        "下午吃了一个苹果"
    ]

    for meal in meals:
        print(f"你：{meal}")
        reply = agent.run(meal)
        print(f"AI：{reply}\n")

    # 询问汇总信息
    print("你：我今天总共摄入了多少热量？")
    reply = agent.run("我今天总共摄入了多少热量？")
    print(f"AI：{reply}\n")

    print("✅ 如果 AI 能正确汇总所有饮食的热量，说明记忆召回工作正常\n")


# ========== 扩展练习 ==========

def exercise_1():
    """
    练习 1：添加用户偏好记忆

    任务：
    1. 在 LongTermMemory 中添加 add_preference() 方法
    2. 在 Agent 中使用用户偏好（如：不吃辣、素食）
    3. 测试 Agent 是否能根据偏好给出建议

    提示：
    - 偏好可以存储在 profile 中
    - 在 system_prompt 中加载偏好信息
    """
    print("=== 练习 1：添加用户偏好记忆 ===\n")
    print("TODO: 实现用户偏好功能\n")


def exercise_2():
    """
    练习 2：实现记忆搜索

    任务：
    1. 在 LongTermMemory 中添加 search_records() 方法
    2. 支持按关键词搜索历史记录
    3. 测试搜索功能

    提示：
    - 可以用简单的字符串匹配
    - 后续课程会学习向量检索（更高级的搜索）
    """
    print("=== 练习 2：实现记忆搜索 ===\n")
    print("TODO: 实现记忆搜索功能\n")


def exercise_3():
    """
    练习 3：实现记忆压缩

    任务：
    1. 当对话历史太长时，用 LLM 总结历史对话
    2. 将总结结果存入长期记忆
    3. 测试压缩后的对话是否仍然连贯

    提示：
    - 可以在 ConversationMemory 中添加 summarize() 方法
    - 调用 LLM 生成总结："请总结以下对话的关键信息..."
    """
    print("=== 练习 3：实现记忆压缩 ===\n")
    print("TODO: 实现记忆压缩功能\n")


# ========== 主函数 ==========

if __name__ == "__main__":
    # 检查 API Key
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("错误：请设置环境变量 DEEPSEEK_API_KEY")
        exit(1)

    print("=== 课程 9：给 Agent 加上记忆能力 - 练习 ===\n")

    # 运行测试
    try:
        test_short_term_memory()
        input("按回车继续下一个测试...")

        test_long_term_memory()
        input("按回车继续下一个测试...")

        test_memory_recall()

        print("\n=== 基础测试完成 ===")
        print("\n接下来可以尝试扩展练习：")
        print("1. 添加用户偏好记忆")
        print("2. 实现记忆搜索")
        print("3. 实现记忆压缩")

    except Exception as e:
        print(f"错误：{e}")
        import traceback
        traceback.print_exc()
