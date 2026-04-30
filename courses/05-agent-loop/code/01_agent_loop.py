"""
课程 5：Agent 核心循环实现

实现一个基础的 Agent 循环框架
展示感知 → 思考 → 行动 → 观察的完整流程
"""

from openai import OpenAI
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = OpenAI(
    api_key="sk-539707f4724a4e39a213e9b51e3f9c12",
    base_url="https://api.deepseek.com"
)


# ============================================
# 模拟工具
# ============================================
def get_user_profile() -> dict:
    """获取用户档案"""
    return {
        "height": 170,
        "weight": 75,
        "age": 30,
        "gender": "male",
        "goal": "减肥",
        "target_weight": 65
    }

def calculate_tdee(height: int, weight: int, age: int, gender: str) -> int:
    """计算每日总能量消耗（TDEE）"""
    # 简化的 Harris-Benedict 公式
    if gender == "male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

    tdee = int(bmr * 1.375)  # 假设轻度活动
    return tdee


# ============================================
# Agent 类
# ============================================
class SimpleAgent:
    """
    简单的 Agent 实现

    核心循环：感知 → 思考 → 行动 → 观察
    """

    def __init__(self, tools_definition: list, tools_map: dict):
        """
        初始化 Agent

        参数：
            tools_definition: 工具定义列表（JSON Schema 格式）
            tools_map: 工具名到函数的映射
        """
        self.tools_definition = tools_definition
        self.tools_map = tools_map
        self.max_iterations = 10  # 最大循环次数

    def run(self, user_message: str) -> str:
        """
        运行 Agent

        参数：
            user_message: 用户消息

        返回：
            Agent 的最终回复
        """
        print(f"\n{'='*60}")
        print(f"用户：{user_message}")
        print(f"{'='*60}\n")

        # 初始化消息历史
        messages = [
            {
                "role": "system",
                "content": "你是一个健康管家 AI Agent。你可以使用工具获取信息。请一步步思考，使用必要的工具来完成任务。"
            },
            {"role": "user", "content": user_message}
        ]

        # 开始循环
        for iteration in range(1, self.max_iterations + 1):
            print(f"--- 第 {iteration} 轮循环 ---\n")

            # 1. 感知 + 思考（调用 LLM）
            print("[感知 + 思考] 调用 LLM 分析当前状态...")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=self.tools_definition,
                tool_choice="auto"
            )

            message = response.choices[0].message

            # 2. 行动（执行 LLM 的决策）
            if message.tool_calls:
                # LLM 决定调用工具
                print(f"[行动] LLM 决定调用 {len(message.tool_calls)} 个工具\n")

                # 将 LLM 的决策加入历史
                messages.append(message)

                # 3. 观察（执行工具并收集结果）
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"  工具：{tool_name}")
                    print(f"  参数：{json.dumps(tool_args, ensure_ascii=False)}")

                    # 执行工具
                    tool_function = self.tools_map.get(tool_name)
                    if tool_function:
                        result = tool_function(**tool_args)
                        print(f"  结果：{json.dumps(result, ensure_ascii=False)}\n")
                    else:
                        result = {"error": f"未找到工具：{tool_name}"}
                        print(f"  错误：{result}\n")

                    # 将工具结果加入历史
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

                print("[观察] 工具执行完成，进入下一轮循环\n")

            else:
                # LLM 决定不调用工具，给出最终回复
                print("[行动] LLM 决定给出最终回复\n")
                print(f"{'='*60}")
                print(f"Agent 回复：\n{message.content}")
                print(f"{'='*60}\n")
                print(f"总共循环了 {iteration} 轮")
                return message.content

        # 达到最大循环次数
        print(f"\n[警告] 达到最大循环次数（{self.max_iterations}），强制结束")
        return "抱歉，处理超时了。"


# ============================================
# 工具定义
# ============================================
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "获取用户的健康档案，包括身高、体重、年龄、性别、目标等",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_tdee",
            "description": "计算用户的每日总能量消耗（TDEE），需要身高、体重、年龄、性别",
            "parameters": {
                "type": "object",
                "properties": {
                    "height": {"type": "integer", "description": "身高（厘米）"},
                    "weight": {"type": "integer", "description": "体重（公斤）"},
                    "age": {"type": "integer", "description": "年龄"},
                    "gender": {"type": "string", "enum": ["male", "female"], "description": "性别"}
                },
                "required": ["height", "weight", "age", "gender"]
            }
        }
    }
]

tools_map = {
    "get_user_profile": get_user_profile,
    "calculate_tdee": calculate_tdee
}


# ============================================
# 测试
# ============================================
if __name__ == "__main__":
    # 创建 Agent
    agent = SimpleAgent(tools_definition, tools_map)

    # 测试 1：需要多步调用的任务
    agent.run("帮我制定一个减肥计划，需要考虑我的基本情况")

    print("\n\n")

    # 测试 2：简单任务
    agent.run("我的目标体重是多少？")
