# 课程 11：ReAct 模式

---

## 一、什么是 ReAct？

### 1.1 ReAct 的全称

**ReAct = Reasoning（推理）+ Acting（行动）**

这是一种让 Agent 交替进行"思考"和"行动"的模式。

### 1.2 为什么需要 ReAct？

**普通 Agent 的问题**：

```
用户：帮我制定一个减肥计划

Agent：[内部思考，我们看不到]
      ↓
      调用工具 A
      ↓
      调用工具 B
      ↓
      返回结果
```

我们看不到 Agent 为什么调用这些工具，思考过程是"黑盒"。

**ReAct 的改进**：

```
用户：帮我制定一个减肥计划

Thought: 我需要先了解用户的基本信息
Action: 询问用户身高、体重、目标
Observation: 用户回复了信息

Thought: 现在可以计算 BMI 了
Action: 调用 calculate_bmi 工具
Observation: BMI = 22.9（正常范围）

Thought: 根据 BMI 和目标，制定饮食方案
Action: 调用 create_diet_plan 工具
Observation: 生成了饮食方案

Thought: 任务完成，返回结果
Answer: [完整的减肥计划]
```

**优势**：
1. **可解释性**：能看到 Agent 的思考过程
2. **可调试性**：出错时能定位问题
3. **可控性**：可以干预 Agent 的决策

### 1.3 ReAct 的核心循环

```
┌─────────────────────────────────┐
│   Thought（思考）                │
│   - 分析当前状态                 │
│   - 决定下一步做什么             │
└──────────┬──────────────────────┘
           ↓
┌─────────────────────────────────┐
│   Action（行动）                 │
│   - 调用工具                     │
│   - 或直接回答                   │
└──────────┬──────────────────────┘
           ↓
┌─────────────────────────────────┐
│   Observation（观察）            │
│   - 工具执行结果                 │
│   - 环境反馈                     │
└──────────┬──────────────────────┘
           ↓
        是否完成？
         ↓ 否
    回到 Thought
```

---

## 二、ReAct 的工作流程

### 2.1 Thought（思考）

Agent 分析当前状态，决定下一步做什么。

**示例**：
```
Thought: 用户想记录饮食，但没有说明食物的热量。
我需要先查询这个食物的营养信息。
```

**关键点**：
- 思考要清晰、具体
- 说明为什么要这样做
- 基于当前的观察结果

### 2.2 Action（行动）

执行具体的操作。

**两种类型**：

1. **调用工具**：
   ```
   Action: query_nutrition(food="鸡蛋")
   ```

2. **直接回答**：
   ```
   Action: Answer
   已记录：早餐 - 鸡蛋 2个，140 卡路里
   ```

### 2.3 Observation（观察）

工具执行的结果或环境反馈。

**示例**：
```
Observation: {"food": "鸡蛋", "calories": 70, "protein": 6}
```

**关键点**：
- Observation 是客观的事实
- 不包含 Agent 的主观判断
- 作为下一轮 Thought 的输入

### 2.4 完整示例

```
用户：我今天早上吃了两个鸡蛋

Thought: 用户想记录早餐，但没有说明热量。
我需要先查询鸡蛋的营养信息。

Action: query_nutrition(food="鸡蛋")

Observation: {"food": "鸡蛋", "calories": 70, "protein": 6}

Thought: 查询到鸡蛋的热量是 70 卡/个，用户吃了 2 个，
总热量是 140 卡。现在可以记录了。

Action: record_meal(meal_time="早餐", food="鸡蛋", amount=2, calories=140)

Observation: {"success": true, "message": "已记录"}

Thought: 记录成功，可以回复用户了。

Action: Answer
已记录：早餐 - 鸡蛋 2个，140 卡路里。鸡蛋富含蛋白质，是很好的早餐选择！
```

---

## 三、ReAct vs 普通 Agent

| 维度 | 普通 Agent | ReAct Agent |
|------|-----------|-------------|
| **思考过程** | 黑盒，看不到 | 透明，每步都展示 |
| **可解释性** | 低 | 高 |
| **可调试性** | 难 | 易 |
| **实现复杂度** | 简单 | 中等 |
| **性能** | 快（直接调用） | 稍慢（多轮对话） |
| **适用场景** | 简单任务 | 复杂任务、需要解释的场景 |

**什么时候用 ReAct？**

✅ **适合**：
- 复杂的多步任务
- 需要解释决策过程
- 需要调试和优化
- 用户关心"为什么"

❌ **不适合**：
- 简单的单步任务
- 对性能要求极高
- 不需要解释的场景

---

## 四、实现 ReAct Agent

### 4.1 Prompt 设计

ReAct 的关键是 Prompt 设计，要让 LLM 按照 Thought → Action → Observation 的格式输出。

**System Prompt 示例**：

```
你是一个健康管家 AI，使用 ReAct 模式工作。

工作流程：
1. Thought: 分析当前状态，决定下一步做什么
2. Action: 执行操作（调用工具或回答用户）
3. Observation: 观察结果
4. 重复 1-3，直到任务完成

输出格式：
Thought: [你的思考过程]
Action: [工具名称(参数)] 或 Answer: [回答内容]

可用工具：
- query_nutrition(food): 查询食物营养信息
- record_meal(meal_time, food, amount, calories): 记录饮食
- get_today_summary(): 获取今日饮食汇总

示例：
用户：我今天早上吃了两个鸡蛋
Thought: 用户想记录早餐，需要先查询鸡蛋的热量
Action: query_nutrition(food="鸡蛋")
```

**关键点**：
1. 明确说明 ReAct 流程
2. 定义输出格式
3. 提供工具列表
4. 给出示例

### 4.2 解析输出

LLM 的输出需要解析，提取 Thought 和 Action。

**输出示例**：
```
Thought: 用户想记录早餐，需要先查询鸡蛋的热量
Action: query_nutrition(food="鸡蛋")
```

**解析逻辑**：
```python
import re

def parse_react_output(text):
    """
    解析 ReAct 格式的输出
    
    返回：
    - thought: 思考内容
    - action: 行动（工具调用或回答）
    """
    # 提取 Thought
    thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|$)', text, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else ""
    
    # 提取 Action
    action_match = re.search(r'Action:\s*(.+?)(?=Observation:|$)', text, re.DOTALL)
    action = action_match.group(1).strip() if action_match else ""
    
    return thought, action
```

### 4.3 执行循环

ReAct Agent 的核心是循环执行 Thought → Action → Observation。

**伪代码**：
```python
def run_react_agent(user_input):
    messages = [system_prompt, user_input]
    
    for i in range(max_iterations):
        # 1. 调用 LLM
        response = llm.chat(messages)
        
        # 2. 解析输出
        thought, action = parse_react_output(response)
        
        # 3. 判断是否完成
        if action.startswith("Answer:"):
            return action.replace("Answer:", "").strip()
        
        # 4. 执行工具
        observation = execute_tool(action)
        
        # 5. 添加到历史
        messages.append({
            "role": "assistant",
            "content": f"Thought: {thought}\nAction: {action}"
        })
        messages.append({
            "role": "user",
            "content": f"Observation: {observation}"
        })
    
    return "任务超时"
```

---

## 五、小结

### 5.1 关键概念

1. **ReAct = Reasoning + Acting**：推理和行动交替进行
2. **核心循环**：Thought → Action → Observation
3. **优势**：可解释、可调试、可控
4. **实现关键**：Prompt 设计 + 输出解析 + 循环执行

### 5.2 实现要点

1. **Prompt 要清晰**：明确说明 ReAct 流程和输出格式
2. **解析要准确**：正确提取 Thought 和 Action
3. **循环要控制**：设置最大迭代次数，避免死循环
4. **观察要客观**：Observation 是事实，不是判断

### 5.3 下一步

- 课程 12：Chain of Thought（CoT）
- 课程 13：Multi-Step Agent
- 课程 14：错误处理与自我修正

接下来我们会看完整的代码实现！
