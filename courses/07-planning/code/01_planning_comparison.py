"""
课程 7：Planning（规划能力）实现

展示两种规划方式：
1. 静态规划：预定义计划模板
2. 动态规划：让 LLM 自己规划（ReAct 模式）
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
# 模拟工具函数
# ============================================
def get_user_profile() -> dict:
    """获取用户档案"""
    return {
        "name": "张三",
        "height": 170,
        "weight": 75,
        "age": 30,         # 添加年龄
        "gender": "male",  # 添加性别
        "target_weight": 65,
        "goal": "减肥"
    }

def calculate_tdee(height: int, weight: int, age: int = 30, gender: str = "male") -> int:
    """计算每日总能量消耗"""
    if gender == "male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    return int(bmr * 1.375)

def generate_meal_plan(calorie_target: int, preferences: list) -> dict:
    """生成食谱计划"""
    return {
        "breakfast": "燕麦粥 + 鸡蛋",
        "lunch": "鸡胸肉沙拉",
        "dinner": "蔬菜汤 + 全麦面包",
        "total_calories": calorie_target
    }

def generate_exercise_plan(goal: str) -> dict:
    """生成运动计划"""
    return {
        "cardio": "跑步 30 分钟，每周 3-4 次",
        "strength": "力量训练，每周 2 次"
    }


# ============================================
# 方式 1：静态规划（预定义模板）
# ============================================
class StaticPlanner:
    """
    静态规划器

    预先定义好常见任务的步骤模板
    """

    def __init__(self):
        # 定义计划模板库
        self.templates = {
            "减肥计划": [
                {"step": 1, "action": "get_user_profile", "description": "获取用户档案"},
                {"step": 2, "action": "calculate_tdee", "description": "计算每日热量需求"},
                {"step": 3, "action": "set_calorie_target", "description": "设定热量目标"},
                {"step": 4, "action": "generate_meal_plan", "description": "生成食谱计划"},
                {"step": 5, "action": "generate_exercise_plan", "description": "生成运动计划"},
            ]
        }

        # 工具映射
        self.tools_map = {
            "get_user_profile": get_user_profile,
            "calculate_tdee": calculate_tdee,
            "generate_meal_plan": generate_meal_plan,
            "generate_exercise_plan": generate_exercise_plan,
        }

    def execute_plan(self, task_name: str):
        """
        执行计划

        参数：
            task_name: 任务名称（如"减肥计划"）
        """
        print(f"\n{'='*60}", flush=True)
        print(f"[静态规划] 执行任务：{task_name}", flush=True)
        print(f"{'='*60}\n", flush=True)

        # 获取计划模板
        plan = self.templates.get(task_name)
        if not plan:
            print(f"错误：未找到任务模板 '{task_name}'")
            return

        print(f"计划步骤：", flush=True)
        for step in plan:
            print(f"  {step['step']}. {step['description']}", flush=True)
        print(flush=True)

        # 执行计划
        context = {}  # 存储中间结果

        for step in plan:
            print(f"--- 步骤 {step['step']}: {step['description']} ---", flush=True)

            action = step["action"]

            # 特殊处理：根据上下文传参
            if action == "get_user_profile":
                result = self.tools_map[action]()
                context["profile"] = result

            elif action == "calculate_tdee":
                profile = context["profile"]
                result = self.tools_map[action](
                    height=profile["height"],
                    weight=profile["weight"]
                )
                context["tdee"] = result

            elif action == "set_calorie_target":
                # 减肥：TDEE - 500 千卡
                tdee = context["tdee"]
                result = tdee - 500
                context["calorie_target"] = result

            elif action == "generate_meal_plan":
                result = self.tools_map[action](
                    calorie_target=context["calorie_target"],
                    preferences=[]
                )
                context["meal_plan"] = result

            elif action == "generate_exercise_plan":
                result = self.tools_map[action](
                    goal=context["profile"]["goal"]
                )
                context["exercise_plan"] = result

            print(f"结果：{json.dumps(result, ensure_ascii=False)}\n", flush=True)

        # 生成最终报告
        print(f"{'='*60}", flush=True)
        print("计划执行完成！", flush=True)
        print(f"{'='*60}\n", flush=True)
        self.generate_report(context)

    def generate_report(self, context: dict):
        """生成最终报告"""
        profile = context["profile"]
        print(f"减肥计划报告：", flush=True)
        print(f"- 用户：{profile['name']}", flush=True)
        print(f"- 当前体重：{profile['weight']}kg，目标：{profile['target_weight']}kg", flush=True)
        print(f"- 每日热量需求：{context['tdee']} 千卡", flush=True)
        print(f"- 建议摄入：{context['calorie_target']} 千卡", flush=True)
        print(f"- 食谱：{context['meal_plan']}", flush=True)
        print(f"- 运动：{context['exercise_plan']}", flush=True)


# ============================================
# 方式 2：动态规划（让 LLM 自己规划）
# ============================================
class DynamicPlanner:
    """
    动态规划器（ReAct 模式）

    让 LLM 自己决定每一步做什么
    """

    def __init__(self):
        # 定义可用工具
        self.tools_definition = [
            {
                "type": "function",
                "function": {
                    "name": "get_user_profile",
                    "description": "获取用户的健康档案",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_tdee",
                    "description": "计算每日总能量消耗（TDEE）",
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
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_meal_plan",
                    "description": "生成食谱计划",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "calorie_target": {"type": "integer"},
                            "preferences": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["calorie_target"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_exercise_plan",
                    "description": "生成运动计划",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "goal": {"type": "string"}
                        },
                        "required": ["goal"]
                    }
                }
            }
        ]

        self.tools_map = {
            "get_user_profile": get_user_profile,
            "calculate_tdee": calculate_tdee,
            "generate_meal_plan": generate_meal_plan,
            "generate_exercise_plan": generate_exercise_plan,
        }

    def execute_task(self, user_message: str):
        """
        执行任务（动态规划）

        LLM 自己决定每一步做什么
        """
        print(f"\n{'='*60}", flush=True)
        print(f"[动态规划] 用户：{user_message}", flush=True)
        print(f"{'='*60}\n", flush=True)

        messages = [
            {
                "role": "system",
                "content": "你是一个健康管家 AI Agent。你可以使用工具来完成任务。请一步步思考，使用必要的工具。"
            },
            {"role": "user", "content": user_message}
        ]

        # Agent 循环
        for iteration in range(1, 11):
            print(f"--- 第 {iteration} 轮 ---", flush=True)

            # 调用 LLM
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=self.tools_definition,
                tool_choice="auto"
            )

            message = response.choices[0].message

            if message.tool_calls:
                # LLM 决定调用工具
                messages.append(message)

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"LLM 决定：调用 {tool_name}({json.dumps(tool_args, ensure_ascii=False)})", flush=True)

                    # 执行工具
                    tool_function = self.tools_map.get(tool_name)
                    result = tool_function(**tool_args) if tool_function else {"error": "未知工具"}

                    print(f"结果：{json.dumps(result, ensure_ascii=False)}\n", flush=True)

                    # 返回结果给 LLM
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            else:
                # LLM 给出最终回复
                print(f"{'='*60}", flush=True)
                print(f"最终回复：\n{message.content}", flush=True)
                print(f"{'='*60}\n", flush=True)
                print(f"总共 {iteration} 轮", flush=True)
                return


# ============================================
# 测试对比
# ============================================
if __name__ == "__main__":
    print("\n" + "="*70, flush=True)
    print("对比：静态规划 vs 动态规划", flush=True)
    print("="*70, flush=True)

    # 测试 1：静态规划
    static_planner = StaticPlanner()
    static_planner.execute_plan("减肥计划")

    print("\n\n")

    # 测试 2：动态规划
    dynamic_planner = DynamicPlanner()
    dynamic_planner.execute_task("帮我制定一个减肥计划")
