# 课程 8：动手做一个完整的 Agent

## 第一部分：回顾组件

### Agent 的四大组件

```
课程 4：Agent 概念
  ↓ Agent = LLM + 感知 + 记忆 + 工具 + 规划

课程 5：Agent 循环
  ↓ 感知 → 思考 → 行动 → 观察 → 循环

课程 6：Memory（记忆系统）
  ↓ 短期记忆 + 中期记忆 + 长期记忆

课程 7：Planning（规划能力）
  ↓ 静态规划 + 动态规划
```

---

## 第二部分：整体架构设计

### 完整 Agent 的架构

```
┌─────────────────────────────────────────┐
│           HealthAgent                   │
│  (健康管家 Agent - 核心类)               │
└─────────────────────────────────────────┘
           │
           ├─── MemoryManager (记忆管理器)
           │      ├─ 短期记忆：对话历史
           │      ├─ 中期记忆：最近活动
           │      └─ 长期记忆：用户档案
           │
           ├─── Planner (规划器)
           │      ├─ 静态规划：预定义模板
           │      └─ 动态规划：LLM 决策
           │
           ├─── ToolManager (工具管理器)
           │      ├─ 工具注册
           │      ├─ 工具执行
           │      └─ 结果处理
           │
           └─── AgentLoop (Agent 循环)
                  └─ 感知 → 思考 → 行动 → 观察
```

### 数据流向

```
用户消息
  ↓
MemoryManager.recall_memory()  # 召回相关记忆
  ↓
Planner.create_plan()          # 创建计划（可选）
  ↓
AgentLoop.run()                # 执行循环
  ├─ LLM 思考
  ├─ ToolManager.execute()     # 执行工具
  └─ MemoryManager.save()      # 保存记忆
  ↓
最终回复
```

---

## 第三部分：组件协同工作

### 场景：用户说"我今天吃了红烧肉"

```
1. MemoryManager 召回记忆
   - 短期：最近对话
   - 长期：用户目标（减肥）、偏好

2. AgentLoop 开始循环
   第 1 轮：
     LLM 思考：需要记录饮食
     行动：调用 log_meal("红烧肉")
     观察：记录成功

   第 2 轮：
     LLM 思考：红烧肉热量高，用户在减肥，应该提醒
     行动：生成建议
     观察：完成

3. MemoryManager 保存记忆
   - 短期：更新对话历史
   - 中期：保存饮食记录
```

---

## 第四部分：实现要点

### 1. Agent 核心类

```python
class HealthAgent:
    """健康管家 Agent"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.memory = MemoryManager(user_id)
        self.planner = Planner()
        self.tool_manager = ToolManager()

    def chat(self, user_message: str) -> str:
        """
        与用户对话

        流程：
        1. 召回记忆
        2. 执行 Agent 循环
        3. 保存记忆
        """
        # 1. 召回记忆
        memory = self.memory.recall_memory(user_message)

        # 2. 执行 Agent 循环
        response = self.agent_loop(user_message, memory)

        # 3. 保存记忆
        self.memory.save_message("user", user_message)
        self.memory.save_message("assistant", response)

        return response
```

### 2. 整合 Memory

```python
# 构建 System Prompt（注入记忆）
system_prompt = self.memory.build_system_prompt(memory)

messages = [
    {"role": "system", "content": system_prompt},
    *memory["short_term"],  # 对话历史
    {"role": "user", "content": user_message}
]
```

### 3. 整合 Planning

```python
# 检查是否需要规划
if self.planner.need_planning(user_message):
    plan = self.planner.create_plan(user_message)
    # 按计划执行
    return self.execute_plan(plan)
else:
    # 直接执行 Agent 循环
    return self.agent_loop(user_message, memory)
```

### 4. 整合 Tool Use

```python
# Agent 循环中
if message.tool_calls:
    for tool_call in message.tool_calls:
        # 使用 ToolManager 执行工具
        result = self.tool_manager.execute(
            tool_call.function.name,
            tool_call.function.arguments
        )
```

---

## 第五部分：健康管家的核心功能

### 功能 1：记录饮食

```python
def log_meal(food: str, meal_type: str = "午餐") -> dict:
    """记录饮食"""
    # 1. 查询食物营养信息
    nutrition = search_food(food)

    # 2. 保存到数据库
    save_meal_record(user_id, food, nutrition, meal_type)

    # 3. 返回结果
    return {
        "food": food,
        "calories": nutrition["calories"],
        "saved": True
    }
```

### 功能 2：查询营养信息

```python
def search_food(name: str) -> dict:
    """搜索食物营养信息"""
    # 模拟食物数据库
    food_db = {
        "红烧肉": {"calories": 500, "protein": 20, "fat": 40},
        "米饭": {"calories": 230, "protein": 5, "fat": 1},
    }
    return food_db.get(name, {"calories": 0})
```

### 功能 3：制定减肥计划

```python
# 使用静态规划
WEIGHT_LOSS_PLAN = [
    {"action": "get_user_profile"},
    {"action": "calculate_tdee"},
    {"action": "generate_meal_plan"},
    {"action": "generate_exercise_plan"},
]
```

### 功能 4：生成周报

```python
def generate_weekly_report() -> dict:
    """生成周报"""
    # 1. 查询最近 7 天的数据
    meals = query_meals(days=7)
    weights = query_weight_records(days=7)

    # 2. 统计分析
    stats = calculate_nutrition_stats(meals)

    # 3. 生成报告
    return {
        "total_calories": stats["total"],
        "avg_daily": stats["avg"],
        "weight_change": weights[-1] - weights[0]
    }
```

---

## 第六部分：完整流程示例

### 用户："我今天吃了红烧肉，还能吃多少？"

```
1. MemoryManager.recall_memory()
   召回：
   - 用户目标：减肥，目标体重 65kg
   - 今日已吃：早餐燕麦粥（150 千卡）
   - 每日目标：1800 千卡

2. AgentLoop.run()
   第 1 轮：
     LLM 决定：调用 log_meal("红烧肉", "午餐")
     结果：已记录，500 千卡

   第 2 轮：
     LLM 决定：调用 get_daily_summary()
     结果：今日已摄入 650 千卡

   第 3 轮：
     LLM 思考：650 千卡，目标 1800，剩余 1150
     LLM 决定：生成回复

3. 最终回复：
   "已记录红烧肉（500 千卡）。
    今日已摄入 650 千卡，还可以摄入 1150 千卡。
    考虑到你的减肥目标，建议晚餐选择清淡食物。"

4. MemoryManager.save()
   保存：
   - 对话历史
   - 饮食记录
```

---

## 第七部分：关键设计原则

### 1. 模块化

```python
# 每个组件独立，职责单一
class MemoryManager:  # 只负责记忆
class Planner:        # 只负责规划
class ToolManager:    # 只负责工具
class HealthAgent:    # 组装所有组件
```

### 2. 可扩展

```python
# 添加新工具很简单
tool_manager.register("new_tool", new_tool_function)

# 添加新计划模板很简单
planner.add_template("新计划", steps)
```

### 3. 可测试

```python
# 每个组件可以独立测试
def test_memory():
    memory = MemoryManager("test_user")
    memory.add_message("user", "你好")
    assert len(memory.get_short_term_memory()) == 1

def test_planner():
    planner = Planner()
    plan = planner.create_plan("减肥计划")
    assert len(plan) == 5
```

---

## 第八部分：与健康管家产品的关系

这个完整 Agent 就是健康管家产品的**核心引擎**：

```
健康管家产品
  ├─ 前端（Web/App）
  │    └─ 聊天界面、数据展示
  │
  ├─ 后端 API
  │    └─ FastAPI / Flask
  │
  └─ Agent 引擎 ← 这就是我们这节课要做的
       ├─ HealthAgent
       ├─ MemoryManager
       ├─ Planner
       └─ ToolManager
```

后续课程会逐步完善：
- 课程 9：给 Agent 加上更强的记忆能力（向量数据库）
- 课程 10：基础阶段总复习
- 课程 11+：进阶能力（ReAct、RAG、Multi-Agent）
