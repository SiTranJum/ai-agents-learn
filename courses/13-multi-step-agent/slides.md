# 课程 13：Multi-Step Agent — 复杂任务的多步编排

---

## 第一部分：Multi-Step Agent 是什么

### 1.1 回顾：我们学过的 Agent 模式

**课程 11：ReAct 模式**
```
用户："帮我制定减肥计划"

Thought: 需要先了解用户信息
Action: 询问用户
Observation: 得到用户信息

Thought: 现在可以计算 BMI
Action: 调用 calculate_bmi
Observation: BMI = 22.9

Thought: 可以制定方案了
Action: 生成方案
...
```

**特点**：LLM 自由推理，每一步都由 LLM 决定下一步做什么。

### 1.2 Multi-Step Agent 的不同

**Multi-Step Agent**：预先定义好步骤和编排逻辑，按照既定流程执行。

```python
# 预先定义好的步骤
steps = [
    Step("获取用户档案", get_user_profile),
    Step("计算健康指标", calculate_metrics),
    Step("生成饮食方案", create_diet_plan),
    Step("生成运动方案", create_exercise_plan),
    Step("设置提醒", setup_reminders),
    Step("返回完整方案", return_plan)
]

# 按顺序执行
planner.execute(steps)
```

### 1.3 两种模式的对比

| 维度 | ReAct 模式 | Multi-Step Agent |
|------|-----------|-----------------|
| **决策方式** | LLM 每步自由决定 | 预先定义好流程 |
| **灵活性** | 高（能应对意外情况） | 低（按固定流程） |
| **可控性** | 低（不确定 LLM 会做什么） | 高（流程可预测） |
| **成本** | 高（每步都要调用 LLM） | 低（只在需要时调用） |
| **适用场景** | 开放式任务、探索性任务 | 结构化任务、流程明确的任务 |
| **错误处理** | LLM 自己判断 | 开发者预先设计 |

**Java 类比**：
- ReAct = 递归算法（每次调用自己决定下一步）
- Multi-Step = 循环 + 状态机（按预定义流程执行）

### 1.4 为什么需要 Multi-Step Agent？

**场景 1：任务步骤明确**
```
制定减肥方案：
1. 获取用户档案 ← 必须先做
2. 计算指标 ← 依赖步骤 1
3. 生成方案 ← 依赖步骤 2
4. 设置提醒 ← 依赖步骤 3
```

这种任务用 ReAct 会浪费 token，因为每步都要 LLM 推理"下一步做什么"，但答案是固定的。

**场景 2：需要并行执行**
```
生成健康方案：
- 饮食方案（可以并行）
- 运动方案（可以并行）
- 睡眠建议（可以并行）
```

ReAct 是串行的，Multi-Step 可以并行执行独立步骤。

**场景 3：需要精确控制**
```
支付流程：
1. 验证用户身份 ← 必须成功
2. 检查余额 ← 必须成功
3. 扣款 ← 必须成功
4. 发送通知 ← 可以失败
```

Multi-Step 可以为每个步骤设置不同的错误处理策略。

---

## 第二部分：任务分解策略

### 2.1 自动分解 vs 手动分解

**手动分解**（推荐用于生产环境）
```python
# 开发者预先定义好步骤
steps = [
    Step("step1", "获取用户档案", get_user_profile),
    Step("step2", "计算指标", calculate_metrics, depends_on=["step1"]),
    Step("step3", "生成方案", create_plan, depends_on=["step2"])
]
```

优点：可控、可预测、可测试
缺点：不够灵活

**自动分解**（适合探索阶段）
```python
# 让 LLM 分析任务，生成步骤列表
task = "帮我制定一个减肥计划"
steps = llm.decompose_task(task)
# LLM 返回：
# [
#   "获取用户基本信息",
#   "计算 BMI 和 TDEE",
#   "制定饮食方案",
#   "制定运动方案",
#   "设置提醒"
# ]
```

优点：灵活、适应性强
缺点：不可控、可能出错

**混合模式**（最佳实践）
```python
# 预定义主流程，LLM 负责细节
main_steps = ["获取档案", "分析数据", "生成方案"]
for step in main_steps:
    sub_steps = llm.decompose_step(step)  # LLM 分解子步骤
    execute(sub_steps)
```

### 2.2 任务依赖关系（DAG）

**DAG = Directed Acyclic Graph（有向无环图）**

```
获取档案 (A)
    ↓
计算指标 (B)
    ↓
    ├─→ 饮食方案 (C)
    └─→ 运动方案 (D)
         ↓
    设置提醒 (E) ← 依赖 C 和 D
    ↓
返回方案 (F)
```

**依赖关系定义**：
```python
steps = [
    Step("A", get_profile),
    Step("B", calculate_metrics, depends_on=["A"]),
    Step("C", diet_plan, depends_on=["B"]),
    Step("D", exercise_plan, depends_on=["B"]),
    Step("E", setup_reminders, depends_on=["C", "D"]),
    Step("F", return_plan, depends_on=["E"])
]
```

**执行顺序**：
1. A 先执行
2. B 等 A 完成后执行
3. C 和 D 等 B 完成后并行执行
4. E 等 C 和 D 都完成后执行
5. F 等 E 完成后执行

**Java 类比**：
- 类似 Spring Batch 的 Job Flow
- 类似 CompletableFuture 的依赖链

### 2.3 步骤粒度的选择

**太细碎**：
```python
steps = [
    Step("获取身高"),
    Step("获取体重"),
    Step("获取年龄"),
    Step("获取性别"),
    Step("计算 BMI"),
    Step("计算 BMR"),
    Step("计算 TDEE"),
    ...
]
```
问题：步骤太多，管理复杂

**太粗糙**：
```python
steps = [
    Step("获取所有数据并生成方案")
]
```
问题：失去了分步的意义

**合适的粒度**：
```python
steps = [
    Step("获取用户档案"),  # 内部包含身高、体重等
    Step("计算健康指标"),  # 内部包含 BMI、TDEE 等
    Step("生成方案"),      # 内部包含饮食、运动等
]
```

**原则**：
- 每个步骤是一个有意义的业务单元
- 步骤之间有清晰的输入输出
- 步骤可以独立测试

---

## 第三部分：编排模式

### 3.1 Sequential（顺序执行）

最简单的模式，步骤按顺序一个接一个执行。

```python
class SequentialPlanner:
    def execute(self, steps):
        context = {}  # 共享上下文
        for step in steps:
            result = step.run(context)
            context[step.name] = result  # 保存结果供后续步骤使用
        return context
```

**示例**：
```python
steps = [
    Step("step1", lambda ctx: {"user_id": 123}),
    Step("step2", lambda ctx: {"bmi": 22.9}),
    Step("step3", lambda ctx: {"plan": "减肥方案"})
]

planner = SequentialPlanner()
result = planner.execute(steps)
# result = {
#   "step1": {"user_id": 123},
#   "step2": {"bmi": 22.9},
#   "step3": {"plan": "减肥方案"}
# }
```

### 3.2 Conditional（条件分支）

根据前一步的结果决定下一步。

```python
class ConditionalPlanner:
    def execute(self, steps, conditions):
        context = {}
        for step in steps:
            # 检查条件
            if self.should_execute(step, context, conditions):
                result = step.run(context)
                context[step.name] = result
        return context
```

**示例**：
```python
steps = [
    Step("get_bmi", calculate_bmi),
    Step("weight_loss_plan", create_loss_plan, 
         condition=lambda ctx: ctx["get_bmi"]["bmi"] > 24),
    Step("weight_gain_plan", create_gain_plan,
         condition=lambda ctx: ctx["get_bmi"]["bmi"] < 18.5),
    Step("maintain_plan", create_maintain_plan,
         condition=lambda ctx: 18.5 <= ctx["get_bmi"]["bmi"] <= 24)
]
```

**Java 类比**：
```java
if (bmi > 24) {
    createWeightLossPlan();
} else if (bmi < 18.5) {
    createWeightGainPlan();
} else {
    createMaintainPlan();
}
```

### 3.3 Parallel（并行执行）

多个独立步骤同时执行，提高效率。

```python
import asyncio

class ParallelPlanner:
    async def execute(self, steps):
        # 找出可以并行的步骤
        parallel_groups = self.group_by_dependencies(steps)
        
        context = {}
        for group in parallel_groups:
            # 并行执行同一组的步骤
            tasks = [step.run_async(context) for step in group]
            results = await asyncio.gather(*tasks)
            
            # 保存结果
            for step, result in zip(group, results):
                context[step.name] = result
        
        return context
```

**示例**：
```python
steps = [
    Step("A", get_profile),
    Step("B", calculate_metrics, depends_on=["A"]),
    Step("C", diet_plan, depends_on=["B"]),      # 可以并行
    Step("D", exercise_plan, depends_on=["B"]),  # 可以并行
    Step("E", sleep_advice, depends_on=["B"]),   # 可以并行
    Step("F", combine_plans, depends_on=["C", "D", "E"])
]

# 执行顺序：
# 第 1 轮：A
# 第 2 轮：B
# 第 3 轮：C、D、E 并行执行
# 第 4 轮：F
```

**性能对比**：
```
串行执行：A(1s) → B(1s) → C(2s) → D(2s) → E(2s) → F(1s) = 9s
并行执行：A(1s) → B(1s) → [C,D,E 并行](2s) → F(1s) = 5s
```

### 3.4 Loop（循环重试）

失败后重试，设置最大重试次数。

```python
class RetryPlanner:
    def execute_with_retry(self, step, max_retries=3):
        for attempt in range(max_retries):
            try:
                result = step.run()
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise  # 最后一次重试失败，抛出异常
                print(f"步骤 {step.name} 失败，重试 {attempt + 1}/{max_retries}")
                time.sleep(2 ** attempt)  # 指数退避：2s, 4s, 8s
```

**指数退避**（Exponential Backoff）：
```
第 1 次失败 → 等待 2^0 = 1 秒
第 2 次失败 → 等待 2^1 = 2 秒
第 3 次失败 → 等待 2^2 = 4 秒
```

**Java 类比**：
```java
@Retryable(maxAttempts = 3, backoff = @Backoff(delay = 1000, multiplier = 2))
public Result executeStep() {
    // ...
}
```

---

## 第四部分：错误处理

### 4.1 单步失败的处理策略

**策略 1：立即终止**（默认）
```python
try:
    result = step.run()
except Exception as e:
    print(f"步骤 {step.name} 失败，终止流程")
    raise
```

适用场景：关键步骤，失败后无法继续

**策略 2：跳过继续**
```python
try:
    result = step.run()
except Exception as e:
    print(f"步骤 {step.name} 失败，跳过")
    result = None  # 或默认值
```

适用场景：非关键步骤，失败不影响主流程

**策略 3：重试**
```python
result = self.retry(step, max_retries=3)
```

适用场景：网络请求、外部 API 调用

**策略 4：降级方案**
```python
try:
    result = step.run()
except Exception as e:
    print(f"步骤 {step.name} 失败，执行降级方案")
    result = step.fallback()
```

适用场景：有备选方案的步骤

### 4.2 错误处理配置

```python
class Step:
    def __init__(self, name, func, 
                 on_error="raise",  # raise | skip | retry | fallback
                 max_retries=3,
                 fallback_func=None):
        self.name = name
        self.func = func
        self.on_error = on_error
        self.max_retries = max_retries
        self.fallback_func = fallback_func
```

**示例**：
```python
steps = [
    Step("获取档案", get_profile, on_error="raise"),  # 必须成功
    Step("调用外部API", call_api, on_error="retry", max_retries=3),
    Step("发送通知", send_notification, on_error="skip"),  # 可以失败
    Step("生成方案", create_plan, on_error="fallback", 
         fallback_func=create_simple_plan)  # 有备选方案
]
```

### 4.3 健康场景的错误处理示例

```python
# 制定减肥方案的步骤
steps = [
    # 关键步骤：必须成功
    Step("get_profile", get_user_profile, on_error="raise"),
    
    # 外部 API：重试
    Step("get_food_data", fetch_food_database, 
         on_error="retry", max_retries=3),
    
    # 有降级方案：API 失败就用 LLM 估算
    Step("calculate_nutrition", calculate_with_api,
         on_error="fallback", 
         fallback_func=lambda: llm_estimate_nutrition()),
    
    # 非关键步骤：可以跳过
    Step("send_email", send_welcome_email, on_error="skip")
]
```

---

## 第五部分：实践案例

### 5.1 任务：制定完整的减肥方案

**需求**：
用户说"我想减肥"，Agent 需要：
1. 获取用户档案（身高、体重、年龄、性别、目标体重）
2. 计算健康指标（BMI、BMR、TDEE）
3. 生成饮食方案（每日热量、营养素分配）
4. 生成运动方案（运动类型、频率、时长）
5. 设置提醒（饮食记录提醒、运动提醒）
6. 返回完整方案

### 5.2 步骤分解

```python
steps = [
    # 第 1 步：获取用户档案
    Step(
        name="get_profile",
        func=get_user_profile,
        on_error="raise"  # 必须成功
    ),
    
    # 第 2 步：计算健康指标
    Step(
        name="calculate_metrics",
        func=calculate_health_metrics,
        depends_on=["get_profile"],
        on_error="raise"
    ),
    
    # 第 3 步：生成饮食方案（可以并行）
    Step(
        name="diet_plan",
        func=create_diet_plan,
        depends_on=["calculate_metrics"],
        on_error="fallback",
        fallback_func=create_simple_diet_plan
    ),
    
    # 第 4 步：生成运动方案（可以并行）
    Step(
        name="exercise_plan",
        func=create_exercise_plan,
        depends_on=["calculate_metrics"],
        on_error="fallback",
        fallback_func=create_simple_exercise_plan
    ),
    
    # 第 5 步：设置提醒
    Step(
        name="setup_reminders",
        func=setup_reminders,
        depends_on=["diet_plan", "exercise_plan"],
        on_error="skip"  # 提醒失败不影响主流程
    ),
    
    # 第 6 步：返回完整方案
    Step(
        name="return_plan",
        func=format_final_plan,
        depends_on=["diet_plan", "exercise_plan", "setup_reminders"]
    )
]
```

### 5.3 依赖关系图

```
get_profile (A)
    ↓
calculate_metrics (B)
    ↓
    ├─→ diet_plan (C) ────┐
    └─→ exercise_plan (D) ┤
                          ↓
                    setup_reminders (E)
                          ↓
                    return_plan (F)
```

**执行顺序**：
1. A 先执行
2. B 等 A 完成
3. C 和 D 并行执行（都依赖 B）
4. E 等 C 和 D 都完成
5. F 等 E 完成

### 5.4 完整代码实现

下一节我们会写完整的代码，包括：
- `Step` 类
- `MultiStepPlanner` 类
- 依赖解析
- 并行执行
- 错误处理

---

## 第六部分：Multi-Step vs ReAct 的选择

### 何时用 Multi-Step？

✅ 任务步骤明确且固定
✅ 需要精确控制流程
✅ 需要并行执行
✅ 需要复杂的错误处理
✅ 成本敏感（减少 LLM 调用）

**例子**：
- 制定健康方案（步骤固定）
- 支付流程（必须精确控制）
- 数据处理 Pipeline（需要并行）

### 何时用 ReAct？

✅ 任务开放、不确定
✅ 需要灵活应对意外情况
✅ 探索性任务
✅ 用户需求不明确

**例子**：
- "帮我分析这个健康报告"（不知道会发现什么问题）
- "我想改善睡眠"（需要先了解具体情况）
- 调试问题（需要根据现象逐步排查）

### 混合使用

**最佳实践**：主流程用 Multi-Step，细节用 ReAct

```python
# 主流程：Multi-Step
steps = [
    Step("分析用户情况", analyze_user),  # 内部用 ReAct
    Step("生成方案", create_plan),       # 固定逻辑
    Step("执行方案", execute_plan)       # 内部用 ReAct
]
```

---

## 小结

### 核心概念

1. **Multi-Step Agent**：预先定义步骤和编排逻辑，按既定流程执行
2. **与 ReAct 的区别**：Multi-Step 更可控，ReAct 更灵活
3. **任务分解**：手动分解（可控）vs 自动分解（灵活）
4. **依赖关系**：用 DAG 表示步骤之间的依赖
5. **编排模式**：Sequential、Conditional、Parallel、Loop
6. **错误处理**：raise、skip、retry、fallback

### 下一步

下一节课我们会：
1. 实现完整的 `MultiStepPlanner` 类
2. 完成"制定减肥方案"的实践案例
3. 测试并行执行和错误处理

准备好了吗？我们开始写代码！
