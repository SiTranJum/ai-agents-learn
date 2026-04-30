"""
课程 13：Multi-Step Agent — 复杂任务的多步编排

核心思想：
- 预先定义好步骤和依赖关系
- 按照 DAG（有向无环图）顺序执行
- 支持并行执行独立步骤
- 每个步骤可以配置不同的错误处理策略

与 ReAct 的区别：
- ReAct：LLM 每步自由决定下一步做什么（灵活但不可控）
- Multi-Step：开发者预先定义好流程（可控但不灵活）

Java 类比：
- Step = Spring Batch 的 Step
- MultiStepPlanner = Spring Batch 的 Job
- depends_on = CompletableFuture.thenCompose()
- 并行执行 = CompletableFuture.allOf()
"""

import json
import sys
import io
import time
import asyncio
from openai import OpenAI

# ========== Windows 终端中文输出修复 ==========
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# ========== DeepSeek API 客户端 ==========
client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"
)


# ========== Step 类：定义一个执行步骤 ==========

class Step:
    """
    一个执行步骤

    Java 类比：类似 Spring Batch 的 Tasklet
    - name: 步骤名称（唯一标识）
    - func: 要执行的函数，接收 context 参数，返回结果
    - depends_on: 依赖的步骤名称列表（这些步骤必须先完成）
    - on_error: 错误处理策略
        - "raise": 抛出异常，终止整个流程（默认）
        - "skip": 跳过该步骤，继续执行
        - "retry": 重试，最多 max_retries 次
        - "fallback": 执行降级函数
    """

    def __init__(self, name, func, depends_on=None,
                 on_error="raise", max_retries=3, fallback_func=None):
        self.name = name
        self.func = func
        # depends_on 默认为空列表（没有依赖）
        # Java 类比：类似 @DependsOn 注解
        self.depends_on = depends_on or []
        self.on_error = on_error
        self.max_retries = max_retries
        self.fallback_func = fallback_func


# ========== MultiStepPlanner 类：编排引擎 ==========

class MultiStepPlanner:
    """
    多步编排引擎

    职责：
    1. 解析步骤之间的依赖关系
    2. 按正确顺序执行步骤（拓扑排序）
    3. 并行执行没有依赖关系的步骤
    4. 处理每个步骤的错误

    Java 类比：类似 Spring Batch 的 JobLauncher + Flow
    """

    def __init__(self, steps):
        """
        初始化编排引擎

        参数：
        - steps: Step 对象列表
        """
        self.steps = {s.name: s for s in steps}  # 用字典存储，方便按名称查找
        self.context = {}  # 共享上下文，所有步骤的结果都存在这里

    def _topological_sort(self):
        """
        拓扑排序：计算步骤的执行顺序

        原理：
        - 把步骤看成图的节点，依赖关系看成边
        - 没有依赖的步骤先执行
        - 依赖已完成的步骤接着执行

        Java 类比：类似编译器解析 Bean 依赖顺序（Spring IoC 容器启动时做的事）

        返回：
        - 二维列表，每个子列表是可以并行执行的一组步骤
        - 例如：[["A"], ["B"], ["C", "D"], ["E"]]
        -   表示 A 先执行，然后 B，然后 C 和 D 并行，最后 E
        """
        # 计算每个步骤的入度（有多少个依赖）
        in_degree = {}
        for name, step in self.steps.items():
            in_degree[name] = len(step.depends_on)

        result = []  # 最终的执行顺序（分层）

        while in_degree:
            # 找出所有入度为 0 的步骤（没有未完成的依赖）
            # 这些步骤可以并行执行
            ready = [name for name, degree in in_degree.items() if degree == 0]

            if not ready:
                # 如果没有入度为 0 的步骤，说明存在循环依赖
                raise ValueError(f"检测到循环依赖！剩余步骤：{list(in_degree.keys())}")

            result.append(ready)

            # 移除已就绪的步骤，并更新其他步骤的入度
            for name in ready:
                del in_degree[name]
                # 减少依赖该步骤的其他步骤的入度
                for other_name, other_step in self.steps.items():
                    if name in other_step.depends_on and other_name in in_degree:
                        in_degree[other_name] -= 1

        return result

    def _execute_step(self, step):
        """
        执行单个步骤，根据 on_error 策略处理错误

        参数：
        - step: Step 对象

        返回：
        - 步骤执行结果
        """
        print(f"\n  ▶ 执行步骤：{step.name}")

        # ---- 策略 1：直接执行，失败就抛异常 ----
        if step.on_error == "raise":
            result = step.func(self.context)
            print(f"  ✓ 步骤 {step.name} 完成")
            return result

        # ---- 策略 2：失败就跳过 ----
        if step.on_error == "skip":
            try:
                result = step.func(self.context)
                print(f"  ✓ 步骤 {step.name} 完成")
                return result
            except Exception as e:
                print(f"  ⚠ 步骤 {step.name} 失败，已跳过（原因：{e}）")
                return None

        # ---- 策略 3：失败就重试 ----
        if step.on_error == "retry":
            for attempt in range(step.max_retries):
                try:
                    result = step.func(self.context)
                    print(f"  ✓ 步骤 {step.name} 完成（第 {attempt + 1} 次尝试）")
                    return result
                except Exception as e:
                    # 指数退避：每次等待时间翻倍
                    # 第 1 次失败等 1 秒，第 2 次等 2 秒，第 3 次等 4 秒
                    wait_time = 2 ** attempt
                    print(f"  ⚠ 步骤 {step.name} 第 {attempt + 1} 次失败，"
                          f"{wait_time}秒后重试（原因：{e}）")
                    time.sleep(wait_time)
            raise RuntimeError(f"步骤 {step.name} 重试 {step.max_retries} 次后仍然失败")

        # ---- 策略 4：失败就执行降级方案 ----
        if step.on_error == "fallback":
            try:
                result = step.func(self.context)
                print(f"  ✓ 步骤 {step.name} 完成")
                return result
            except Exception as e:
                print(f"  ⚠ 步骤 {step.name} 失败，执行降级方案（原因：{e}）")
                if step.fallback_func:
                    result = step.fallback_func(self.context)
                    print(f"  ✓ 步骤 {step.name} 降级方案完成")
                    return result
                return None

    def execute(self):
        """
        执行所有步骤

        流程：
        1. 拓扑排序，确定执行顺序
        2. 按层执行（同一层的步骤可以并行）
        3. 每个步骤的结果存入 context

        返回：
        - context 字典，包含所有步骤的结果
        """
        # 第 1 步：拓扑排序
        execution_order = self._topological_sort()

        print("=" * 60)
        print("Multi-Step Agent 执行计划")
        print("=" * 60)
        for i, group in enumerate(execution_order):
            parallel_hint = "（并行）" if len(group) > 1 else ""
            print(f"  第 {i + 1} 轮{parallel_hint}：{', '.join(group)}")
        print("=" * 60)

        # 第 2 步：按层执行
        for i, group in enumerate(execution_order):
            print(f"\n--- 第 {i + 1} 轮 ---")

            if len(group) == 1:
                # 只有一个步骤，直接执行
                step = self.steps[group[0]]
                result = self._execute_step(step)
                self.context[step.name] = result
            else:
                # 多个步骤，用 asyncio 并行执行
                # 注意：这里用同步模拟并行，后面会讲真正的异步
                print(f"  （并行执行 {len(group)} 个步骤）")
                for name in group:
                    step = self.steps[name]
                    result = self._execute_step(step)
                    self.context[name] = result

        print("\n" + "=" * 60)
        print("所有步骤执行完成！")
        print("=" * 60)

        return self.context


# ========== 健康场景的工具函数 ==========

def get_user_profile(context):
    """
    获取用户档案（模拟数据）

    实际项目中，这里会从数据库读取
    """
    profile = {
        "name": "张三",
        "age": 30,
        "gender": "male",
        "height_cm": 175,
        "weight_kg": 80,
        "target_weight_kg": 70,
        "allergies": ["海鲜"],
        "preferences": ["不吃辣", "喜欢面食"]
    }
    print(f"    用户：{profile['name']}，{profile['height_cm']}cm，{profile['weight_kg']}kg")
    return profile


def calculate_health_metrics(context):
    """
    计算健康指标

    依赖 get_profile 的结果（从 context 中读取）
    """
    # 从 context 中获取上一步的结果
    profile = context["get_profile"]

    height_m = profile["height_cm"] / 100
    weight = profile["weight_kg"]
    age = profile["age"]

    # BMI = 体重(kg) / 身高(m)²
    bmi = round(weight / (height_m ** 2), 1)

    # BMR（基础代谢率）- Mifflin-St Jeor 公式
    # 男性：10 × 体重(kg) + 6.25 × 身高(cm) - 5 × 年龄 + 5
    # 女性：10 × 体重(kg) + 6.25 × 身高(cm) - 5 × 年龄 - 161
    if profile["gender"] == "male":
        bmr = round(10 * weight + 6.25 * profile["height_cm"] - 5 * age + 5)
    else:
        bmr = round(10 * weight + 6.25 * profile["height_cm"] - 5 * age - 161)

    # TDEE（每日总消耗）= BMR × 活动系数（假设轻度活动 1.375）
    tdee = round(bmr * 1.375)

    # 减肥建议热量 = TDEE - 500（每天少吃 500 卡，每周减约 0.5kg）
    target_calories = tdee - 500

    metrics = {
        "bmi": bmi,
        "bmi_status": "偏胖" if bmi > 24 else "正常" if bmi > 18.5 else "偏瘦",
        "bmr": bmr,
        "tdee": tdee,
        "target_calories": target_calories
    }

    print(f"    BMI: {bmi}（{metrics['bmi_status']}），TDEE: {tdee}，目标热量: {target_calories}")
    return metrics


def create_diet_plan(context):
    """
    用 LLM 生成饮食方案

    依赖 calculate_metrics 的结果
    """
    profile = context["get_profile"]
    metrics = context["calculate_metrics"]

    # 调用 DeepSeek 生成饮食方案
    # client.chat.completions.create() 是 OpenAI SDK 的核心方法
    # 参数说明：
    #   model: 使用的模型名称
    #   messages: 对话消息列表
    #   temperature: 0.7 表示适度创造性（0=确定性，1=最大随机性）
    #   max_tokens: 限制输出长度，避免生成过长内容
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是营养师，给出简洁的每日饮食方案。只输出方案，不要多余解释。"},
            {"role": "user", "content": (
                f"用户信息：{profile['height_cm']}cm，{profile['weight_kg']}kg，"
                f"目标 {profile['target_weight_kg']}kg\n"
                f"每日目标热量：{metrics['target_calories']} 卡\n"
                f"忌口：{', '.join(profile['allergies'])}\n"
                f"偏好：{', '.join(profile['preferences'])}\n"
                f"请给出一天的三餐方案（早/中/晚），每餐标注热量。"
            )}
        ],
        temperature=0.7,
        max_tokens=500
    )

    # response.choices[0].message.content 是 LLM 返回的文本
    plan = response.choices[0].message.content
    print(f"    饮食方案已生成（{len(plan)} 字）")
    return plan


def create_exercise_plan(context):
    """
    用 LLM 生成运动方案

    依赖 calculate_metrics 的结果
    可以和 create_diet_plan 并行执行（两者互不依赖）
    """
    profile = context["get_profile"]
    metrics = context["calculate_metrics"]

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是健身教练，给出简洁的每周运动方案。只输出方案，不要多余解释。"},
            {"role": "user", "content": (
                f"用户信息：{profile['height_cm']}cm，{profile['weight_kg']}kg，"
                f"BMI {metrics['bmi']}（{metrics['bmi_status']}）\n"
                f"目标：减到 {profile['target_weight_kg']}kg\n"
                f"请给出每周运动方案（周一到周日），标注运动类型和时长。"
            )}
        ],
        temperature=0.7,
        max_tokens=500
    )

    plan = response.choices[0].message.content
    print(f"    运动方案已生成（{len(plan)} 字）")
    return plan


def setup_reminders(context):
    """
    设置提醒（模拟）

    依赖 diet_plan 和 exercise_plan
    on_error="skip"：提醒失败不影响主流程
    """
    reminders = [
        "每天 8:00 - 记录早餐",
        "每天 12:00 - 记录午餐",
        "每天 19:00 - 记录晚餐",
        "每天 21:00 - 记录体重",
    ]

    # 如果有运动方案，加上运动提醒
    if context.get("exercise_plan"):
        reminders.append("每周一/三/五 18:00 - 运动提醒")

    print(f"    已设置 {len(reminders)} 个提醒")
    return reminders


def format_final_plan(context):
    """
    汇总所有结果，生成最终方案

    依赖所有前面的步骤
    """
    profile = context["get_profile"]
    metrics = context["calculate_metrics"]
    diet = context.get("diet_plan", "（生成失败）")
    exercise = context.get("exercise_plan", "（生成失败）")
    reminders = context.get("setup_reminders", [])

    plan = f"""
{'='*60}
           {profile['name']} 的减肥方案
{'='*60}

【基本信息】
  身高：{profile['height_cm']}cm
  当前体重：{profile['weight_kg']}kg → 目标：{profile['target_weight_kg']}kg
  BMI：{metrics['bmi']}（{metrics['bmi_status']}）
  每日目标热量：{metrics['target_calories']} 卡

【饮食方案】
{diet}

【运动方案】
{exercise}

【提醒设置】
"""
    for r in reminders:
        plan += f"  - {r}\n"

    plan += f"\n{'='*60}"
    return plan


# ========== 主程序 ==========

if __name__ == "__main__":
    print("\n课程 13：Multi-Step Agent 演示\n")

    # 定义步骤和依赖关系
    # 注意看 depends_on 参数，它定义了步骤之间的依赖
    steps = [
        Step(
            name="get_profile",
            func=get_user_profile,
            on_error="raise"  # 获取档案必须成功
        ),
        Step(
            name="calculate_metrics",
            func=calculate_health_metrics,
            depends_on=["get_profile"],  # 依赖 get_profile
            on_error="raise"
        ),
        Step(
            name="diet_plan",
            func=create_diet_plan,
            depends_on=["calculate_metrics"],  # 依赖 calculate_metrics
            on_error="fallback",  # 失败就用降级方案
            fallback_func=lambda ctx: "降级方案：每日三餐，每餐 500 卡，少油少盐"
        ),
        Step(
            name="exercise_plan",
            func=create_exercise_plan,
            depends_on=["calculate_metrics"],  # 也依赖 calculate_metrics
            on_error="fallback",  # 和 diet_plan 可以并行！
            fallback_func=lambda ctx: "降级方案：每周 3 次有氧运动，每次 30 分钟"
        ),
        Step(
            name="setup_reminders",
            func=setup_reminders,
            depends_on=["diet_plan", "exercise_plan"],  # 依赖两个方案
            on_error="skip"  # 提醒失败不影响主流程
        ),
        Step(
            name="format_plan",
            func=format_final_plan,
            depends_on=["diet_plan", "exercise_plan", "setup_reminders"]
        ),
    ]

    # 创建编排引擎并执行
    planner = MultiStepPlanner(steps)
    result = planner.execute()

    # 输出最终方案
    print(result["format_plan"])
