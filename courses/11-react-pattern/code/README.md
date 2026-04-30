# 课程 11：ReAct 模式 - 代码说明

## 什么是 ReAct？

**ReAct = Reasoning（推理）+ Acting（行动）**

让 Agent 交替进行"思考"和"行动"，使决策过程透明可见。

## 核心流程

```
Thought（思考）→ Action（行动）→ Observation（观察）→ 循环
```

## 运行示例

### 1. 设置 API Key

```bash
export DEEPSEEK_API_KEY="your-api-key"
```

### 2. 运行代码

```bash
cd courses/11-react-pattern/code
python react_agent.py
```

### 3. 预期输出

```
==================================================
用户：我今天早上吃了两个鸡蛋
==================================================

【第 1 轮】
Thought: 用户想记录早餐，但没有说明热量。我需要先查询鸡蛋的营养信息。
Action: query_nutrition(food="鸡蛋")
Observation: {"calories": 70, "protein": 6}

【第 2 轮】
Thought: 查询到鸡蛋的热量是 70 卡/个，用户吃了 2 个，总热量是 140 卡。现在可以记录了。
Action: record_meal(food="鸡蛋", amount=2, calories=140)
Observation: 已记录：鸡蛋 2份，140 卡路里

【第 3 轮】
Thought: 记录成功，可以回复用户了。
Action: Answer: 已记录：早餐 - 鸡蛋 2个，140 卡路里。鸡蛋富含蛋白质，是很好的早餐选择！

最终回答：已记录：早餐 - 鸡蛋 2个，140 卡路里。鸡蛋富含蛋白质，是很好的早餐选择！
```

## 代码结构

```python
class ReactAgent:
    def _get_system_prompt()  # 构建 ReAct 格式的 System Prompt
    def _parse_output()       # 解析 Thought 和 Action
    def _execute_tool()       # 执行工具调用
    def run()                 # 主循环
```

## 关键实现

### 1. System Prompt 设计

```python
"""你是一个健康管家 AI，使用 ReAct 模式工作。

工作流程：
1. Thought: 分析当前状态，决定下一步做什么
2. Action: 执行操作（调用工具或回答用户）

输出格式：
Thought: [你的思考过程]
Action: [工具调用] 或 Answer: [最终回答]
"""
```

### 2. 输出解析

```python
def _parse_output(self, text: str) -> tuple:
    # 提取 Thought
    thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|$)', text)
    
    # 提取 Action
    action_match = re.search(r'Action:\s*(.+?)$', text)
    
    return thought, action
```

### 3. 循环执行

```python
for i in range(max_iterations):
    # 1. 调用 LLM
    response = llm.chat(messages)
    
    # 2. 解析输出
    thought, action = parse_output(response)
    
    # 3. 判断是否完成
    if action.startswith("Answer"):
        return answer
    
    # 4. 执行工具
    observation = execute_tool(action)
    
    # 5. 添加到历史
    messages.append(observation)
```

## ReAct vs 普通 Agent

| 维度 | 普通 Agent | ReAct Agent |
|------|-----------|-------------|
| 思考过程 | 黑盒 | 透明 |
| 可解释性 | 低 | 高 |
| 调试难度 | 难 | 易 |
| 性能 | 快 | 稍慢 |

## 练习

1. **添加新工具**：添加 `calculate_bmi` 工具
2. **优化 Prompt**：让思考过程更清晰
3. **错误处理**：处理工具调用失败的情况

## 下一步

- 课程 12：Chain of Thought（CoT）
- 课程 13：Multi-Step Agent
