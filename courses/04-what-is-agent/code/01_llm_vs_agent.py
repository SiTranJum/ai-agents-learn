"""
课程 4：普通 LLM 调用 vs Agent 对比

场景：健康管家 — 用户询问饮食情况
通过同一个场景，对比两种实现方式的区别
"""

from openai import OpenAI
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"
)


# ============================================
# 模拟数据（假装是数据库和 API）
# ============================================
def query_meals(date: str) -> list:
    """查询某天的饮食记录"""
    db = {
        "today": [
            {"food": "红烧肉", "weight": 150, "calories": 500},
            {"food": "米饭", "weight": 200, "calories": 230},
            {"food": "苹果", "weight": 200, "calories": 100},
        ]
    }
    return db.get(date, [])

def get_user_target() -> dict:
    """查询用户的每日热量目标"""
    return {"daily_calories_target": 1800, "goal": "减肥"}

def calculate_total_calories(meals: list) -> int:
    """计算总热量"""
    return sum(m["calories"] for m in meals)


# ============================================
# 方式 1：普通 LLM 调用（你是大脑，LLM 是工具）
# ============================================
def normal_llm_approach(user_message: str):
    """
    普通 LLM 调用：程序员控制每一步

    问题：
    1. 流程写死了，不管用户问什么都执行同样的步骤
    2. LLM 只负责最后生成文案，不参与决策
    3. 换个需求就要改代码
    """
    print("=" * 60)
    print("[方式 1] 普通 LLM 调用")
    print("=" * 60)

    # 第 1 步：你决定查询饮食记录
    print("\n[程序员写死] 第 1 步：查询饮食记录")
    meals = query_meals("today")
    print(f"  结果：{json.dumps(meals, ensure_ascii=False)}")

    # 第 2 步：你决定计算热量
    print("[程序员写死] 第 2 步：计算总热量")
    total = calculate_total_calories(meals)
    print(f"  结果：{total} 千卡")

    # 第 3 步：你决定查用户目标
    print("[程序员写死] 第 3 步：查询用户目标")
    target = get_user_target()
    print(f"  结果：{json.dumps(target, ensure_ascii=False)}")

    # 第 4 步：你算剩余
    remaining = target["daily_calories_target"] - total
    print(f"[程序员写死] 第 4 步：计算剩余 = {remaining} 千卡")

    # 最后：LLM 只负责"把数据说成人话"
    print("\n[最后] LLM 只是文案生成器：")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{
            "role": "user",
            "content": f"""用户问：{user_message}

数据如下：
- 今日饮食：{json.dumps(meals, ensure_ascii=False)}
- 已摄入：{total} 千卡
- 每日目标：{target['daily_calories_target']} 千卡
- 剩余：{remaining} 千卡
- 用户目标：{target['goal']}

请用友好的语气回答用户。"""
        }]
    )
    print(f"\n{response.choices[0].message.content}")


# ============================================
# 方式 2：Agent（LLM 是大脑，你提供工具）
# ============================================

# Agent 可用的工具定义
agent_tools = [
    {
        "type": "function",
        "function": {
            "name": "query_meals",
            "description": "查询指定日期的饮食记录，返回食物列表（含名称、重量、热量）",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "日期，如 'today'、'yesterday'、'2026-03-30'"
                    }
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_target",
            "description": "查询用户的每日热量目标和健康目标",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# 工具映射
agent_tools_map = {
    "query_meals": query_meals,
    "get_user_target": get_user_target,
}


def agent_approach(user_message: str):
    """
    Agent 方式：LLM 自主决策

    优势：
    1. LLM 自己决定调用什么工具、调用几次
    2. 换个问题不用改代码
    3. LLM 参与整个决策过程
    """
    print("=" * 60)
    print("[方式 2] Agent（LLM 自主决策）")
    print("=" * 60)

    # 初始化消息
    messages = [
        {
            "role": "system",
            "content": "你是一个健康管家 AI Agent。你可以使用工具查询用户的饮食记录和健康目标。根据数据给出专业、友好的建议。"
        },
        {"role": "user", "content": user_message}
    ]

    # Agent 循环：让 LLM 自主决策
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Agent 第 {iteration} 轮思考 ---")

        # 调用 LLM（LLM 自己决定要不要调用工具）
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=agent_tools,
            tool_choice="auto"  # 让 LLM 自己决定
        )

        message = response.choices[0].message

        # 检查 LLM 的决策
        if message.tool_calls:
            # LLM 决定调用工具
            print(f"[Agent 决策] 需要调用工具：")

            # 把 LLM 的决策加入消息历史
            messages.append(message)

            # 执行所有工具调用
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"  -> 调用 {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")

                # 执行工具
                tool_function = agent_tools_map.get(tool_name)
                result = tool_function(**tool_args) if tool_function else {"error": "未知工具"}

                print(f"  <- 结果：{json.dumps(result, ensure_ascii=False)}")

                # 把工具结果返回给 LLM
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

            # 继续循环，让 LLM 决定下一步
        else:
            # LLM 决定不再调用工具，给出最终回复
            print(f"\n[Agent 决策] 信息充足，给出最终回复：")
            print(f"\n{message.content}")
            return

    print("\n[警告] 达到最大循环次数")


# ============================================
# 运行对比
# ============================================
if __name__ == "__main__":
    user_question = "我今天吃了什么，还能吃多少？"

    print(f"\n用户：{user_question}\n")

    # 方式 1：普通 LLM 调用
    normal_llm_approach(user_question)

    print("\n\n")

    # 方式 2：Agent
    agent_approach(user_question)

    # 试试换个问题 — Agent 不用改代码
    print("\n\n" + "=" * 60)
    print("换个问题试试（Agent 不需要改代码）")
    print("=" * 60)

    agent_approach("我的减肥目标是什么？")
