"""
带记忆的健康管家 Agent

整合：
- 短期记忆（对话历史）
- 长期记忆（用户档案 + 历史数据）
- 工具调用（Function Calling）

这是课程 8 的 Agent 的升级版，加入了记忆能力。
"""

import os
import json
from openai import OpenAI
from conversation_memory import ConversationMemory
from long_term_memory import LongTermMemory


class HealthAgent:
    """
    健康管家 Agent（带记忆）

    组件：
    - LLM 客户端（DeepSeek API）
    - 短期记忆（对话历史）
    - 长期记忆（用户档案 + 历史数据）
    - 工具集（饮食记录、营养查询等）
    """

    def __init__(self, user_id: str, api_key: str):
        """
        初始化 Agent

        参数：
        - user_id: 用户 ID（用于区分不同用户）
        - api_key: DeepSeek API Key
        """
        # 1. 初始化 LLM 客户端
        # OpenAI SDK 兼容 DeepSeek API，只需修改 base_url
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"  # DeepSeek API 地址
        )
        self.model = "deepseek-chat"  # 使用 deepseek-chat 模型

        # 2. 初始化短期记忆（对话历史）
        system_prompt = self._build_system_prompt()
        self.short_memory = ConversationMemory(
            system_prompt=system_prompt,
            max_messages=20  # 最多保留 20 条消息
        )

        # 3. 初始化长期记忆（持久化存储）
        self.long_memory = LongTermMemory(
            user_id=user_id,
            storage_dir="./data"
        )

        # 4. 定义工具集
        self.tools = self._define_tools()

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词

        作用：
        - 定义 Agent 的角色和行为
        - 加载用户档案信息（如果有）

        返回：
        - str: 系统提示词
        """
        # 基础角色定义
        prompt = """你是一个健康管家 AI，帮助用户记录饮食、管理健康。

你的能力：
1. 记录饮食：用户说吃了什么，你帮他记录并计算热量
2. 查询营养：用户问某个食物的营养信息，你帮他查询
3. 数据统计：用户问今天吃了什么、摄入了多少热量，你帮他统计
4. 健康建议：根据用户的目标和数据，给出建议

你的特点：
- 友好、耐心、专业
- 主动询问缺失的信息（如食物份量）
- 记住用户的偏好和目标
"""

        # 加载用户档案（如果有）
        profile = self.long_memory.get_profile()
        if profile:
            prompt += "\n\n用户档案：\n"
            for key, value in profile.items():
                prompt += f"- {key}: {value}\n"

        return prompt

    def _define_tools(self) -> list:
        """
        定义工具集

        返回：
        - list: 工具定义列表（JSON Schema 格式）

        工具说明：
        - record_meal: 记录饮食
        - query_nutrition: 查询食物营养信息
        - get_today_summary: 获取今日饮食汇总
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "record_meal",
                    "description": "记录用户的饮食，包括食物名称、数量、热量等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "meal_time": {
                                "type": "string",
                                "description": "用餐时间，如：早餐、午餐、晚餐、加餐"
                            },
                            "food": {
                                "type": "string",
                                "description": "食物名称"
                            },
                            "amount": {
                                "type": "number",
                                "description": "食物数量"
                            },
                            "unit": {
                                "type": "string",
                                "description": "单位，如：个、碗、克"
                            },
                            "calories": {
                                "type": "number",
                                "description": "热量（卡路里）"
                            }
                        },
                        "required": ["meal_time", "food", "amount", "calories"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_nutrition",
                    "description": "查询食物的营养信息（热量、蛋白质、脂肪、碳水化合物等）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "food": {
                                "type": "string",
                                "description": "食物名称"
                            }
                        },
                        "required": ["food"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_today_summary",
                    "description": "获取今日饮食汇总（总热量、各餐详情）",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    # ========== 工具实现 ==========

    def _record_meal(self, meal_time: str, food: str, amount: float,
                     calories: float, unit: str = "份") -> str:
        """
        工具实现：记录饮食

        参数：
        - meal_time: 用餐时间
        - food: 食物名称
        - amount: 数量
        - calories: 热量
        - unit: 单位

        返回：
        - str: 执行结果（JSON 字符串）
        """
        # 保存到长期记忆
        self.long_memory.add_record("meal", {
            "meal_time": meal_time,
            "food": food,
            "amount": amount,
            "unit": unit,
            "calories": calories
        })

        return json.dumps({
            "success": True,
            "message": f"已记录：{meal_time} - {food} {amount}{unit}，{calories} 卡路里"
        }, ensure_ascii=False)

    def _query_nutrition(self, food: str) -> str:
        """
        工具实现：查询食物营养信息

        参数：
        - food: 食物名称

        返回：
        - str: 营养信息（JSON 字符串）

        注意：这里是模拟数据，实际应该调用营养数据库 API
        """
        # 模拟营养数据库
        nutrition_db = {
            "鸡蛋": {"calories": 70, "protein": 6, "fat": 5, "carbs": 0.5, "unit": "个"},
            "米饭": {"calories": 200, "protein": 4, "fat": 0.5, "carbs": 45, "unit": "碗"},
            "苹果": {"calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14, "unit": "个"},
            "鸡胸肉": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0, "unit": "100克"}
        }

        if food in nutrition_db:
            data = nutrition_db[food]
            return json.dumps({
                "success": True,
                "food": food,
                "nutrition": data
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "success": False,
                "message": f"未找到 {food} 的营养信息"
            }, ensure_ascii=False)

    def _get_today_summary(self) -> str:
        """
        工具实现：获取今日饮食汇总

        返回：
        - str: 汇总信息（JSON 字符串）
        """
        from datetime import datetime

        # 获取今天的日期
        today = datetime.now().strftime("%Y-%m-%d")

        # 从长期记忆中获取今天的饮食记录
        today_meals = self.long_memory.get_records_by_date(today, "meal")

        # 计算总热量
        total_calories = sum(meal["data"]["calories"] for meal in today_meals)

        # 按餐次分组
        meals_by_time = {}
        for meal in today_meals:
            meal_time = meal["data"]["meal_time"]
            if meal_time not in meals_by_time:
                meals_by_time[meal_time] = []
            meals_by_time[meal_time].append(meal["data"])

        return json.dumps({
            "success": True,
            "date": today,
            "total_calories": total_calories,
            "meals": meals_by_time,
            "meal_count": len(today_meals)
        }, ensure_ascii=False)

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """
        执行工具调用

        参数：
        - tool_name: 工具名称
        - arguments: 工具参数（dict）

        返回：
        - str: 工具执行结果
        """
        if tool_name == "record_meal":
            return self._record_meal(**arguments)
        elif tool_name == "query_nutrition":
            return self._query_nutrition(**arguments)
        elif tool_name == "get_today_summary":
            return self._get_today_summary()
        else:
            return json.dumps({"error": f"未知工具：{tool_name}"})

    # ========== Agent 主循环 ==========

    def run(self, user_input: str) -> str:
        """
        Agent 主循环：处理用户输入，返回回复

        参数：
        - user_input: 用户输入

        返回：
        - str: Agent 回复

        流程：
        1. 将用户输入添加到短期记忆
        2. 调用 LLM（带上对话历史）
        3. 如果 LLM 要调用工具，执行工具并继续对话
        4. 返回最终回复
        """
        # 1. 添加用户消息到短期记忆
        self.short_memory.add_user_message(user_input)

        # 2. Agent 循环（最多 5 轮）
        max_iterations = 5
        for i in range(max_iterations):
            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.short_memory.get_messages(),
                tools=self.tools,
                temperature=0.7
            )

            message = response.choices[0].message

            # 3. 判断 LLM 的响应类型
            if message.tool_calls:
                # LLM 要调用工具
                # 将 LLM 的消息添加到历史（包含 tool_calls）
                self.short_memory.messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })

                # 执行所有工具调用
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    # 执行工具
                    result = self._execute_tool(tool_name, arguments)

                    # 将工具结果添加到历史
                    self.short_memory.add_tool_message(tool_call.id, result)

                # 继续循环，让 LLM 根据工具结果生成回复
                continue

            else:
                # LLM 直接回复（不调用工具）
                reply = message.content

                # 将回复添加到短期记忆
                self.short_memory.add_assistant_message(reply)

                return reply

        # 超过最大迭代次数
        return "抱歉，处理超时了，请重试。"


# 使用示例
if __name__ == "__main__":
    # 从环境变量获取 API Key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误：请设置环境变量 DEEPSEEK_API_KEY")
        exit(1)

    # 创建 Agent
    agent = HealthAgent(user_id="user_001", api_key=api_key)

    print("=== 健康管家 Agent（带记忆）===")
    print("输入 'quit' 退出\n")

    # 对话循环
    while True:
        user_input = input("你：")
        if user_input.lower() in ["quit", "exit", "退出"]:
            break

        reply = agent.run(user_input)
        print(f"AI：{reply}\n")
