import os
"""
课程 8：构建完整的健康管家 Agent

整合所有组件：
- Memory（记忆系统）
- Planning（规划能力）
- Tool Use（工具调用）
- Agent Loop（Agent 循环）
"""

from openai import OpenAI
import json
import sys
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


# ============================================
# 模拟数据库
# ============================================

# 用户档案
USER_PROFILES = {
    "user_001": {
        "name": "张三",
        "height": 170,
        "weight": 75,
        "age": 30,
        "gender": "male",
        "target_weight": 65,
        "goal": "减肥",
        "preferences": {
            "diet": ["清淡", "不吃辣"],
            "allergies": ["海鲜"],
        }
    }
}

# 饮食记录
MEAL_RECORDS = []

# 食物数据库
FOOD_DATABASE = {
    "红烧肉": {"calories": 500, "protein": 20, "fat": 40, "carbs": 10},
    "米饭": {"calories": 230, "protein": 5, "fat": 1, "carbs": 50},
    "鸡胸肉": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0},
    "燕麦粥": {"calories": 150, "protein": 5, "fat": 3, "carbs": 27},
    "苹果": {"calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14},
}


# ============================================
# 工具函数
# ============================================

def get_user_profile(user_id: str = "user_001") -> dict:
    """获取用户档案"""
    return USER_PROFILES.get(user_id, {})


def search_food(name: str) -> dict:
    """搜索食物营养信息"""
    food = FOOD_DATABASE.get(name)
    if food:
        return {"name": name, **food, "found": True}
    return {"name": name, "found": False, "message": "未找到该食物"}


def log_meal(food: str, meal_type: str = "午餐", weight: int = 100) -> dict:
    """记录饮食"""
    # 查询食物信息
    food_info = search_food(food)

    if not food_info["found"]:
        return {"success": False, "message": f"未找到食物：{food}"}

    # 保存记录
    record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "meal_type": meal_type,
        "food": food,
        "weight": weight,
        "calories": food_info["calories"],
        "protein": food_info["protein"],
        "fat": food_info["fat"],
        "carbs": food_info["carbs"]
    }
    MEAL_RECORDS.append(record)

    return {
        "success": True,
        "message": f"已记录：{food}（{food_info['calories']} 千卡）",
        "record": record
    }


def get_daily_summary(date: str = None) -> dict:
    """获取每日摘要"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # 筛选当天的记录
    daily_records = [r for r in MEAL_RECORDS if r["date"] == date]

    if not daily_records:
        return {
            "date": date,
            "total_calories": 0,
            "total_protein": 0,
            "total_fat": 0,
            "total_carbs": 0,
            "meals": []
        }

    # 统计
    total_calories = sum(r["calories"] for r in daily_records)
    total_protein = sum(r["protein"] for r in daily_records)
    total_fat = sum(r["fat"] for r in daily_records)
    total_carbs = sum(r["carbs"] for r in daily_records)

    return {
        "date": date,
        "total_calories": total_calories,
        "total_protein": total_protein,
        "total_fat": total_fat,
        "total_carbs": total_carbs,
        "meals": daily_records
    }


def calculate_tdee(height: int, weight: int, age: int, gender: str) -> int:
    """计算每日总能量消耗"""
    if gender == "male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    return int(bmr * 1.375)


# ============================================
# 组件 1：MemoryManager（记忆管理器）
# ============================================

class MemoryManager:
    """记忆管理器"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.messages = []  # 短期记忆：对话历史
        self.max_history = 10  # 最多保留 10 条

    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.messages.append({"role": role, "content": content})

        # 压缩历史
        if len(self.messages) > self.max_history:
            system_messages = [m for m in self.messages if m["role"] == "system"]
            recent_messages = self.messages[-self.max_history:]
            self.messages = system_messages + recent_messages

    def get_short_term_memory(self) -> list:
        """获取短期记忆（对话历史）"""
        return [m for m in self.messages if m["role"] != "system"]

    def get_long_term_memory(self) -> dict:
        """获取长期记忆（用户档案）"""
        return get_user_profile(self.user_id)

    def recall_memory(self, user_message: str) -> dict:
        """召回相关记忆"""
        memory = {
            "short_term": self.get_short_term_memory(),
            "long_term": self.get_long_term_memory()
        }
        return memory

    def build_system_prompt(self, memory: dict) -> str:
        """根据记忆构建 System Prompt"""
        profile = memory["long_term"]

        prompt = f"""你是一个健康管家 AI Agent。

用户信息：
- 姓名：{profile.get('name', '未知')}
- 身高：{profile.get('height', 0)}cm，体重：{profile.get('weight', 0)}kg
- 目标：{profile.get('goal', '未设定')}（目标体重 {profile.get('target_weight', 0)}kg）
- 饮食偏好：{', '.join(profile.get('preferences', {}).get('diet', []))}
- 过敏信息：{', '.join(profile.get('preferences', {}).get('allergies', []))}

请基于用户的目标和偏好，提供个性化的建议。
"""
        return prompt


# ============================================
# 组件 2：ToolManager（工具管理器）
# ============================================

class ToolManager:
    """工具管理器"""

    def __init__(self):
        # 工具定义
        self.tools_definition = [
            {
                "type": "function",
                "function": {
                    "name": "search_food",
                    "description": "搜索食物的营养信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "食物名称"}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "log_meal",
                    "description": "记录一餐饮食",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "food": {"type": "string", "description": "食物名称"},
                            "meal_type": {
                                "type": "string",
                                "enum": ["早餐", "午餐", "晚餐", "加餐"],
                                "description": "餐次类型"
                            },
                            "weight": {"type": "integer", "description": "重量（克）"}
                        },
                        "required": ["food"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_daily_summary",
                    "description": "获取每日饮食摘要",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "日期（YYYY-MM-DD）"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_tdee",
                    "description": "计算每日总能量消耗",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "height": {"type": "integer"},
                            "weight": {"type": "integer"},
                            "age": {"type": "integer"},
                            "gender": {"type": "string", "enum": ["male", "female"]}
                        },
                        "required": ["height", "weight", "age", "gender"]
                    }
                }
            }
        ]

        # 工具映射
        self.tools_map = {
            "search_food": search_food,
            "log_meal": log_meal,
            "get_daily_summary": get_daily_summary,
            "calculate_tdee": calculate_tdee,
        }

    def get_tools_definition(self) -> list:
        """获取工具定义"""
        return self.tools_definition

    def execute(self, tool_name: str, tool_args: dict) -> dict:
        """执行工具"""
        tool_function = self.tools_map.get(tool_name)
        if tool_function:
            return tool_function(**tool_args)
        return {"error": f"未找到工具：{tool_name}"}


# ============================================
# 组件 3：HealthAgent（完整 Agent）
# ============================================

class HealthAgent:
    """健康管家 Agent"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.memory = MemoryManager(user_id)
        self.tool_manager = ToolManager()
        self.max_iterations = 10

    def chat(self, user_message: str) -> str:
        """
        与用户对话

        流程：
        1. 召回记忆
        2. 执行 Agent 循环
        3. 保存记忆
        """
        print(f"\n{'='*60}", flush=True)
        print(f"用户：{user_message}", flush=True)
        print(f"{'='*60}\n", flush=True)

        # 1. 召回记忆
        print("[记忆召回]", flush=True)
        memory = self.memory.recall_memory(user_message)
        print(f"  短期记忆：{len(memory['short_term'])} 条对话", flush=True)
        print(f"  长期记忆：用户档案已加载\n", flush=True)

        # 2. 执行 Agent 循环
        response = self.agent_loop(user_message, memory)

        # 3. 保存记忆
        self.memory.add_message("user", user_message)
        self.memory.add_message("assistant", response)

        return response

    def agent_loop(self, user_message: str, memory: dict) -> str:
        """
        Agent 循环：感知 → 思考 → 行动 → 观察
        """
        # 构建 System Prompt（注入记忆）
        system_prompt = self.memory.build_system_prompt(memory)

        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # 添加对话历史（短期记忆）
        messages.extend(memory["short_term"])

        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})

        # 开始循环
        for iteration in range(1, self.max_iterations + 1):
            print(f"--- 第 {iteration} 轮 ---", flush=True)

            # 调用 LLM（感知 + 思考）
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=self.tool_manager.get_tools_definition(),
                tool_choice="auto"
            )

            message = response.choices[0].message

            # 行动
            if message.tool_calls:
                # LLM 决定调用工具
                messages.append(message)

                # 观察：执行工具并收集结果
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"LLM 决定：调用 {tool_name}({json.dumps(tool_args, ensure_ascii=False)})", flush=True)

                    # 执行工具
                    result = self.tool_manager.execute(tool_name, tool_args)
                    print(f"结果：{json.dumps(result, ensure_ascii=False)}\n", flush=True)

                    # 将结果返回给 LLM
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            else:
                # LLM 给出最终回复
                print(f"{'='*60}", flush=True)
                print(f"Agent 回复：\n{message.content}", flush=True)
                print(f"{'='*60}\n", flush=True)
                print(f"总共 {iteration} 轮\n", flush=True)
                return message.content

        return "抱歉，处理超时了。"


# ============================================
# 测试
# ============================================

if __name__ == "__main__":
    # 创建 Agent
    agent = HealthAgent("user_001")

    # 测试 1：记录饮食
    agent.chat("我今天中午吃了红烧肉")

    # 测试 2：查询今日摄入（有记忆）
    agent.chat("我今天还能吃多少？")

    # 测试 3：查询食物信息
    agent.chat("苹果的热量是多少？")
