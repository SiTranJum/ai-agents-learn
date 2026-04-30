# 课程 10：基础阶段小测验

> **说明**：这是一个开卷测验，可以查阅课程资料。重点是检验理解和动手能力，不是死记硬背。

---

## 第一部分：理论题（50 分）

### 一、选择题（每题 5 分，共 25 分）

**1. 关于 Temperature 参数，以下说法正确的是？**

A. Temperature 越高，AI 越聪明  
B. Temperature 控制输出的随机性，0 表示确定性输出  
C. Temperature 应该始终设置为 1.0  
D. Temperature 只影响输出速度，不影响内容

<details>
<summary>点击查看答案</summary>

**答案：B**

解析：
- Temperature 控制输出的随机性（采样温度）
- 0 = 确定性输出（每次结果相同）
- 1 = 高随机性（创造性输出）
- 不影响"智能程度"，只影响输出的多样性
</details>

---

**2. 以下哪个 Prompt 更符合"清晰具体"原则？**

A. "帮我分析一下"  
B. "分析这段代码"  
C. "分析这段 Python 代码的时间复杂度，并给出优化建议"  
D. "看看这个"

<details>
<summary>点击查看答案</summary>

**答案：C**

解析：
- A、B、D 都太模糊，没有明确任务
- C 明确了：分析对象（Python 代码）、分析维度（时间复杂度）、期望输出（优化建议）
</details>

---

**3. Function Calling 的核心流程是？**

A. 用户输入 → LLM 直接返回结果  
B. 用户输入 → LLM 返回 tool_calls → 执行工具 → 返回结果给 LLM → LLM 生成回复  
C. 用户输入 → 执行所有工具 → LLM 选择结果  
D. 用户输入 → LLM 生成代码 → 执行代码

<details>
<summary>点击查看答案</summary>

**答案：B**

解析：
- Function Calling 是多轮对话流程
- LLM 先判断是否需要调用工具，返回 tool_calls
- 我们执行工具，将结果返回给 LLM
- LLM 根据工具结果生成最终回复
</details>

---

**4. Agent 与普通 LLM 调用的本质区别是？**

A. Agent 使用更大的模型  
B. Agent 能自主循环，调用工具完成任务  
C. Agent 的回复更长  
D. Agent 只能用于聊天

<details>
<summary>点击查看答案</summary>

**答案：B**

解析：
- Agent 的核心特征是"自主性"
- 能自己决定下一步做什么（循环）
- 能调用工具执行任务（不只是回答）
- 有记忆和规划能力
</details>

---

**5. 关于记忆系统，以下说法错误的是？**

A. 短期记忆存储在 messages 数组中  
B. 长期记忆需要持久化存储  
C. 记忆越多越好，应该把所有历史都加载  
D. 记忆召回要按需进行，只加载相关记忆

<details>
<summary>点击查看答案</summary>

**答案：C**

解析：
- 记忆不是越多越好
- 过多记忆会浪费上下文窗口
- 应该按需加载，只加载相关的记忆
- 可以用向量检索等技术优化记忆召回
</details>

---

### 二、判断题（每题 5 分，共 15 分）

**6. System Prompt 只在第一次调用时有效，后续调用会被忽略。**

<details>
<summary>点击查看答案</summary>

**答案：错误**

解析：
- System Prompt 在每次调用时都有效
- 它是 messages 数组的第一条消息
- 每次调用 LLM 时，都会带上完整的 messages（包括 System Prompt）
</details>

---

**7. 工具定义中的 description 字段决定了 LLM 是否会调用该工具。**

<details>
<summary>点击查看答案</summary>

**答案：正确**

解析：
- description 是 LLM 判断是否调用工具的关键
- 要清晰描述工具的功能和使用场景
- 如果 description 不清晰，LLM 可能不会调用或调用错误
</details>

---

**8. Agent Loop 中，"思考"阶段是由我们编写的代码完成的，不需要 LLM。**

<details>
<summary>点击查看答案</summary>

**答案：错误**

解析：
- "思考"阶段是由 LLM 完成的
- LLM 负责理解任务、制定计划、决定行动
- 我们的代码负责"感知"（接收输入）和"行动"（执行工具）
</details>

---

### 三、简答题（10 分）

**9. 请简述 ReAct 模式的核心思想，并举例说明。（10 分）**

<details>
<summary>点击查看答案</summary>

**答案要点**：

1. **核心思想**（5 分）：
   - ReAct = Reasoning（推理）+ Acting（行动）
   - 推理和行动交替进行
   - 每次行动后，根据观察结果继续推理

2. **示例**（5 分）：
   ```
   任务：查询北京今天的天气

   Thought: 我需要调用天气查询工具
   Action: call_weather_api(city="北京")
   Observation: 今天北京晴天，温度 15-25°C

   Thought: 用户可能还想知道是否适合出行
   Action: 无需进一步行动
   Answer: 北京今天晴天，温度 15-25°C，适合出行
   ```

**评分标准**：
- 说明核心思想（推理+行动交替）：5 分
- 给出合理示例：5 分
</details>

---

## 第二部分：实践题（50 分）

### 实践题 1：编写 Prompt（15 分）

**任务**：为健康管家 Agent 编写一个 System Prompt，要求：

1. 定义 Agent 的角色和能力
2. 说明 Agent 的行为准则
3. 包含用户档案信息（假设用户是 25 岁男性，身高 175cm，体重 70kg，目标是减肥）

**要求**：
- 清晰具体
- 结构化
- 长度适中（200-300 字）

<details>
<summary>点击查看参考答案</summary>

**参考答案**：

```
你是一个专业的健康管家 AI，帮助用户管理饮食和健康。

你的能力：
1. 记录饮食：用户说吃了什么，你帮他记录并计算热量
2. 查询营养：用户问某个食物的营养信息，你帮他查询
3. 数据分析：统计每日/每周的饮食数据，分析趋势
4. 健康建议：根据用户的目标和数据，给出个性化建议

你的行为准则：
- 友好、耐心、专业
- 主动询问缺失的信息（如食物份量）
- 记住用户的偏好和目标
- 给出的建议要科学、可行

用户档案：
- 姓名：张三
- 年龄：25 岁
- 性别：男
- 身高：175 cm
- 体重：70 kg
- 目标：减肥（目标体重 65 kg）
- BMI：22.9（正常范围）

请根据用户的目标，提供针对性的建议。
```

**评分标准**：
- 角色定义清晰（5 分）
- 能力和行为准则明确（5 分）
- 包含用户档案信息（5 分）
</details>

---

### 实践题 2：定义工具（15 分）

**任务**：为健康管家 Agent 定义一个工具：`calculate_bmi`，用于计算用户的 BMI 并判断健康状况。

**要求**：
1. 使用 JSON Schema 格式
2. 参数：height（身高，cm）、weight（体重，kg）
3. description 要清晰，说明工具的功能和使用场景

<details>
<summary>点击查看参考答案</summary>

**参考答案**：

```python
{
    "type": "function",
    "function": {
        "name": "calculate_bmi",
        "description": "计算用户的 BMI（身体质量指数）并判断健康状况。BMI = 体重(kg) / 身高(m)^2。根据 BMI 值判断：<18.5 偏瘦，18.5-24 正常，24-28 偏胖，>28 肥胖。当用户询问自己的 BMI 或健康状况时调用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "height": {
                    "type": "number",
                    "description": "身高，单位：厘米（cm）"
                },
                "weight": {
                    "type": "number",
                    "description": "体重，单位：千克（kg）"
                }
            },
            "required": ["height", "weight"]
        }
    }
}
```

**评分标准**：
- JSON Schema 格式正确（5 分）
- description 清晰，说明功能和使用场景（5 分）
- 参数定义准确（type、description、required）（5 分）
</details>

---

### 实践题 3：实现简单 Agent（20 分）

**任务**：实现一个简单的健康管家 Agent，支持以下功能：

1. 记录饮食（调用 `record_meal` 工具）
2. 查询今日总热量（调用 `get_today_calories` 工具）

**要求**：
1. 使用 DeepSeek API
2. 实现 Agent 的 `run()` 方法
3. 支持多轮对话（工具调用）
4. 代码要有详细注释

**提示**：
- 可以参考课程 8 的代码
- 工具实现可以简化（模拟数据）

<details>
<summary>点击查看参考答案</summary>

**参考答案**：

```python
"""
简单的健康管家 Agent

功能：
1. 记录饮食
2. 查询今日总热量
"""

import os
import json
from openai import OpenAI


class SimpleHealthAgent:
    """简单的健康管家 Agent"""

    def __init__(self, api_key: str):
        """
        初始化 Agent

        参数：
        - api_key: DeepSeek API Key
        """
        # 初始化 LLM 客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"

        # 对话历史（短期记忆）
        self.messages = [
            {
                "role": "system",
                "content": "你是健康管家 AI，帮助用户记录饮食和管理健康。"
            }
        ]

        # 今日饮食记录（模拟长期记忆）
        self.today_meals = []

        # 定义工具
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "record_meal",
                    "description": "记录用户的饮食",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "food": {"type": "string", "description": "食物名称"},
                            "calories": {"type": "number", "description": "热量（卡路里）"}
                        },
                        "required": ["food", "calories"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_today_calories",
                    "description": "获取今日总热量",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    def _record_meal(self, food: str, calories: float) -> str:
        """
        工具实现：记录饮食

        参数：
        - food: 食物名称
        - calories: 热量

        返回：
        - str: 执行结果（JSON 字符串）
        """
        self.today_meals.append({"food": food, "calories": calories})
        return json.dumps({
            "success": True,
            "message": f"已记录：{food}，{calories} 卡路里"
        }, ensure_ascii=False)

    def _get_today_calories(self) -> str:
        """
        工具实现：获取今日总热量

        返回：
        - str: 总热量（JSON 字符串）
        """
        total = sum(meal["calories"] for meal in self.today_meals)
        return json.dumps({
            "success": True,
            "total_calories": total,
            "meals": self.today_meals
        }, ensure_ascii=False)

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """
        执行工具调用

        参数：
        - tool_name: 工具名称
        - arguments: 工具参数

        返回：
        - str: 工具执行结果
        """
        if tool_name == "record_meal":
            return self._record_meal(**arguments)
        elif tool_name == "get_today_calories":
            return self._get_today_calories()
        else:
            return json.dumps({"error": f"未知工具：{tool_name}"})

    def run(self, user_input: str) -> str:
        """
        Agent 主循环

        参数：
        - user_input: 用户输入

        返回：
        - str: Agent 回复
        """
        # 1. 添加用户消息到历史
        self.messages.append({"role": "user", "content": user_input})

        # 2. Agent 循环（最多 5 轮）
        for i in range(5):
            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
                temperature=0.7
            )

            message = response.choices[0].message

            # 3. 判断响应类型
            if message.tool_calls:
                # LLM 要调用工具
                # 将 LLM 的消息添加到历史
                self.messages.append({
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

                # 执行工具
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    result = self._execute_tool(tool_name, arguments)

                    # 将工具结果添加到历史
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

                # 继续循环
                continue

            else:
                # LLM 直接回复
                reply = message.content
                self.messages.append({"role": "assistant", "content": reply})
                return reply

        return "抱歉，处理超时了。"


# 测试
if __name__ == "__main__":
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误：请设置环境变量 DEEPSEEK_API_KEY")
        exit(1)

    agent = SimpleHealthAgent(api_key)

    print("=== 简单健康管家 Agent ===")
    print("输入 'quit' 退出\n")

    while True:
        user_input = input("你：")
        if user_input.lower() in ["quit", "exit"]:
            break

        reply = agent.run(user_input)
        print(f"AI：{reply}\n")
```

**评分标准**：
- Agent 结构正确（初始化、工具定义、run 方法）（8 分）
- 工具调用流程正确（判断 tool_calls、执行工具、返回结果）（8 分）
- 代码有详细注释（4 分）
</details>

---

## 测验完成

恭喜你完成了基础阶段的测验！

**下一步**：
1. 对照答案，检查自己的答案
2. 理解错误的题目，查阅相关课程资料
3. 完成实践题的代码，运行测试
4. 准备进入阶段三：进阶能力课程

**评分参考**：
- 90-100 分：优秀，基础扎实
- 75-89 分：良好，部分知识需要巩固
- 60-74 分：及格，建议复习薄弱环节
- <60 分：需要重新学习基础课程

无论分数如何，重要的是理解知识点，能够动手实践。加油！
