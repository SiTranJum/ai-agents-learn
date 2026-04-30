"""
ReAct Agent 实现

核心思想：
- Thought（思考）→ Action（行动）→ Observation（观察）
- 循环执行，直到任务完成
"""

import re
import json
import sys
import io
from openai import OpenAI

# 解决 Windows 终端中文输出问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# DeepSeek API 客户端（全局复用，和前面课程一样）
client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"  # DeepSeek API 地址
)


class ReactAgent:
    """ReAct 模式的 Agent"""

    def __init__(self):
        self.client = client  # 复用全局客户端
        self.model = "deepseek-chat"

        # 模拟数据存储
        self.meals = []

    def _get_system_prompt(self) -> str:
        """构建 System Prompt"""
        # 核心改进：
        # 1. 明确区分两种输出格式：调用工具 vs 最终回答
        # 2. 用 FINISH 替代 Answer，避免和 Action 混淆
        # 3. 给出清晰的示例，让 LLM 严格遵循格式
        return """你是一个健康管家 AI，使用 ReAct 模式工作。

每次回复严格遵循以下格式之一：

【格式 1：需要调用工具时】
Thought: 你的思考过程
Action: 工具调用

【格式 2：任务完成、直接回答用户时】
Thought: 你的思考过程
FINISH: 最终回答内容

可用工具：
- query_nutrition(food="食物名") - 查询食物营养信息
- record_meal(food="食物名", amount=数量, calories=热量) - 记录饮食
- get_summary() - 获取今日饮食汇总

规则：
1. 每次只输出一个 Thought 和一个 Action（或 FINISH），不要多输出
2. 需要调用工具时用 Action，不需要调用工具时用 FINISH
3. 不要同时输出 Action 和 FINISH

示例 1（调用工具）：
Thought: 用户想记录饮食，我需要先查询鸡蛋的热量
Action: query_nutrition(food="鸡蛋")

示例 2（最终回答）：
Thought: 已经记录成功，可以回复用户了
FINISH: 已记录：早餐 - 鸡蛋 2个，140 卡路里
"""

    def _parse_output(self, text: str) -> tuple:
        """
        解析 LLM 输出，提取 Thought 和 Action/FINISH

        返回：(thought, action)
        - action 以 "FINISH:" 开头表示最终回答
        - 否则是工具调用
        """
        # 提取 Thought
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|FINISH:|$)', text, re.DOTALL | re.IGNORECASE)
        thought = thought_match.group(1).strip() if thought_match else ""

        # 优先检测 FINISH（最终回答）
        finish_match = re.search(r'FINISH:\s*(.+?)$', text, re.DOTALL | re.IGNORECASE)
        if finish_match:
            return thought, "FINISH:" + finish_match.group(1).strip()

        # 其次检测 Action（工具调用）
        action_match = re.search(r'Action:\s*(.+?)$', text, re.DOTALL | re.IGNORECASE)
        action = action_match.group(1).strip() if action_match else ""

        return thought, action

    def _execute_tool(self, action: str) -> str:
        """执行工具调用"""
        # 解析工具名和参数
        tool_match = re.match(r'(\w+)\((.*?)\)', action)
        if not tool_match:
            return "错误：无法解析工具调用"

        tool_name = tool_match.group(1)
        params_str = tool_match.group(2)

        # 简单解析参数（实际应该用更健壮的方法）
        params = {}
        for param in params_str.split(','):
            if '=' in param:
                key, value = param.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                try:
                    value = float(value) if '.' in value else int(value)
                except:
                    pass
                params[key] = value

        # 执行工具
        if tool_name == "query_nutrition":
            return self._query_nutrition(params.get('food', ''))
        elif tool_name == "record_meal":
            return self._record_meal(
                params.get('food', ''),
                params.get('amount', 0),
                params.get('calories', 0)
            )
        elif tool_name == "get_summary":
            return self._get_summary()
        else:
            return f"错误：未知工具 {tool_name}"

    def _query_nutrition(self, food: str) -> str:
        """工具：查询营养信息"""
        nutrition_db = {
            "鸡蛋": {"calories": 70, "protein": 6},
            "米饭": {"calories": 200, "protein": 4},
            "苹果": {"calories": 52, "protein": 0.3}
        }

        if food in nutrition_db:
            data = nutrition_db[food]
            return json.dumps(data, ensure_ascii=False)
        return f"未找到 {food} 的营养信息"

    def _record_meal(self, food: str, amount: float, calories: float) -> str:
        """工具：记录饮食"""
        self.meals.append({
            "food": food,
            "amount": amount,
            "calories": calories
        })
        return f"已记录：{food} {amount}份，{calories} 卡路里"

    def _get_summary(self) -> str:
        """工具：获取汇总"""
        if not self.meals:
            return "今天还没有记录"

        total = sum(m['calories'] for m in self.meals)
        return json.dumps({
            "meals": self.meals,
            "total_calories": total
        }, ensure_ascii=False)

    def run(self, user_input: str, max_iterations: int = 5) -> str:
        """运行 ReAct Agent"""
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": user_input}
        ]

        print(f"\n{'='*50}")
        print(f"用户：{user_input}")
        print(f"{'='*50}\n")

        for i in range(max_iterations):
            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )

            output = response.choices[0].message.content
            thought, action = self._parse_output(output)

            print(f"【第 {i+1} 轮】")
            print(f"Thought: {thought}")
            print(f"Action: {action}")

            # 判断是否完成（FINISH: 表示最终回答）
            if action.startswith("FINISH:"):
                answer = action.replace("FINISH:", "").strip()
                print(f"\n最终回答：{answer}\n")
                return answer

            # 执行工具
            observation = self._execute_tool(action)
            print(f"Observation: {observation}\n")

            # 添加到历史
            messages.append({"role": "assistant", "content": output})
            messages.append({"role": "user", "content": f"Observation: {observation}"})

        return "任务超时"


# 测试
if __name__ == "__main__":
    agent = ReactAgent()

    # 测试 1：记录饮食
    agent.run("我今天早上吃了两个鸡蛋")

    # 测试 2：查询汇总
    agent.run("我今天吃了什么？")
