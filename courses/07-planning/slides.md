# 课程 7：Planning（规划能力）

## 第一部分：为什么需要规划

### 简单任务 vs 复杂任务

**简单任务**：一步就能完成
```
用户："北京今天天气怎么样？"
Agent：调用 get_weather("北京") → 回答
```

**复杂任务**：需要多步才能完成
```
用户："帮我制定一个减肥计划"

需要做什么？
1. 获取用户档案（身高、体重、目标）
2. 计算每日热量需求（TDEE）
3. 制定热量摄入目标
4. 根据偏好生成食谱建议
5. 制定运动计划
6. 设置提醒
```

**问题**：Agent 怎么知道要做这 6 步？怎么知道先做哪步、后做哪步？

→ 这就需要 **Planning（规划能力）**

---

## 第二部分：规划的两种方式

### 方式 1：让 LLM 自己规划（动态规划）

**ReAct 模式**（Reasoning + Acting）

```
用户："帮我制定减肥计划"

Agent 循环：
第 1 轮：
  思考：需要先了解用户的基本信息
  行动：调用 get_user_profile()
  观察：得到身高 170cm，体重 75kg

第 2 轮：
  思考：需要计算 TDEE
  行动：调用 calculate_tdee(170, 75, 30, "male")
  观察：得到 TDEE = 2390 千卡

第 3 轮：
  思考：信息充足，可以制定计划了
  行动：生成减肥计划
  观察：计划已生成
```

**优势**：
- 灵活，能应对各种情况
- 不需要预先定义步骤

**劣势**：
- 每次都要 LLM 思考，慢
- 可能走弯路
- 成本高（每轮都调用 LLM）

---

### 方式 2：预先定义计划模板（静态规划）

**定义好步骤，按顺序执行**

```python
# 减肥计划的步骤模板
WEIGHT_LOSS_PLAN_STEPS = [
    {"step": 1, "action": "get_user_profile", "description": "获取用户档案"},
    {"step": 2, "action": "calculate_tdee", "description": "计算每日热量需求"},
    {"step": 3, "action": "generate_meal_plan", "description": "生成食谱"},
    {"step": 4, "action": "generate_exercise_plan", "description": "生成运动计划"},
    {"step": 5, "action": "set_reminders", "description": "设置提醒"},
]

# 按顺序执行
for step in WEIGHT_LOSS_PLAN_STEPS:
    execute_step(step)
```

**优势**：
- 快，不需要每次都让 LLM 思考
- 可预测，步骤固定
- 成本低

**劣势**：
- 不灵活，只能处理预定义的场景
- 需要人工设计步骤

---

## 第三部分：两种方式的对比

| | 动态规划（ReAct） | 静态规划（模板） |
|---|---|---|
| **实现方式** | LLM 自己决定每一步 | 预先定义步骤 |
| **灵活性** | 高，能应对新场景 | 低，只能处理预定义场景 |
| **速度** | 慢（每步都调用 LLM） | 快（只在需要时调用） |
| **成本** | 高 | 低 |
| **可预测性** | 低 | 高 |
| **适用场景** | 开放式任务 | 固定流程任务 |

---

## 第四部分：混合方式（推荐）

**结合两种方式的优势**

```
1. 用静态规划定义常见任务的模板
2. 用动态规划处理特殊情况

示例：
用户："帮我制定减肥计划"
→ 匹配到"减肥计划"模板 → 按模板执行（快）

用户："我想减肥，但我有糖尿病，怎么办？"
→ 没有匹配的模板 → 用 ReAct 动态规划（灵活）
```

---

## 第五部分：实现规划系统

### 核心组件

```python
class Planner:
    """规划器"""

    def __init__(self):
        self.plan_templates = {}  # 计划模板库

    def create_plan(self, task: str) -> list:
        """
        创建计划

        返回：步骤列表
        """
        # 1. 尝试匹配模板
        template = self.match_template(task)
        if template:
            return template

        # 2. 没有模板，让 LLM 生成计划
        return self.generate_plan_with_llm(task)

    def execute_plan(self, plan: list):
        """执行计划"""
        for step in plan:
            self.execute_step(step)
```

---

## 第六部分：健康管家的规划场景

### 场景 1：制定减肥计划

```python
WEIGHT_LOSS_PLAN = [
    {"action": "get_user_profile"},
    {"action": "calculate_tdee"},
    {"action": "set_calorie_target"},
    {"action": "generate_meal_suggestions"},
    {"action": "generate_exercise_plan"},
    {"action": "set_reminders"},
]
```

### 场景 2：生成周报

```python
WEEKLY_REPORT_PLAN = [
    {"action": "query_meals", "params": {"days": 7}},
    {"action": "calculate_nutrition_stats"},
    {"action": "query_weight_records"},
    {"action": "analyze_trends"},
    {"action": "generate_report"},
]
```

### 场景 3：多目标协调

```
用户："我想减肥，同时增肌"

规划：
1. 分析目标冲突（减肥 = 热量缺口，增肌 = 热量盈余）
2. 制定折中方案（小幅热量缺口 + 高蛋白）
3. 调整运动计划（有氧 + 力量训练）
4. 监控进度，动态调整
```

---

## 第七部分：规划的关键要素

### 1. 任务分解

```
大任务 → 子任务 → 具体步骤

"制定减肥计划"
  ↓
├─ 了解用户情况
│   ├─ 获取档案
│   └─ 计算 TDEE
├─ 制定饮食方案
│   ├─ 设定热量目标
│   └─ 生成食谱
└─ 制定运动方案
    ├─ 选择运动类型
    └─ 安排频率
```

### 2. 依赖关系

```
步骤 A 必须在步骤 B 之前：

calculate_tdee() 依赖 get_user_profile()
  ↓ 必须先执行
generate_meal_plan() 依赖 calculate_tdee()
```

### 3. 错误处理

```python
def execute_step(step):
    try:
        result = step.action()
        return result
    except Exception as e:
        # 步骤失败，怎么办？
        if step.is_critical:
            # 关键步骤失败 → 终止计划
            raise
        else:
            # 非关键步骤失败 → 跳过，继续
            log_error(e)
            continue
```

### 4. 进度追踪

```python
class Plan:
    def __init__(self, steps):
        self.steps = steps
        self.current_step = 0
        self.completed_steps = []

    def get_progress(self):
        return f"{self.current_step}/{len(self.steps)}"
```

---

## 第八部分：Planning vs Agent 循环

**它们的关系**：

```
Planning = 制定计划（决定做什么）
Agent 循环 = 执行计划（怎么做）

Planning：
  "我要做 A、B、C 三件事"

Agent 循环：
  第 1 轮：执行 A
  第 2 轮：执行 B
  第 3 轮：执行 C
```

**类比 Java**：

```java
// Planning = 定义业务流程
List<Step> plan = Arrays.asList(
    new Step("查询用户"),
    new Step("计算结果"),
    new Step("保存数据")
);

// Agent 循环 = 执行流程
for (Step step : plan) {
    step.execute();  // 每一步可能调用不同的 Service
}
```
