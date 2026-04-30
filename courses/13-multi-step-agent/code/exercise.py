"""
课程 13 练习：

练习目标：
1. 理解步骤依赖关系和执行顺序
2. 体验不同的错误处理策略
3. 自己设计一个 Multi-Step 流程

运行方式：python exercise.py
"""

import json
import sys
import io
import time

# 注意：sys.stdout 的重新包装只需要做一次
# multi_step_agent.py 的顶层代码已经做了，这里不要重复做
# 否则会导致 stdout 被关闭，报 "I/O operation on closed file" 错误

# 复用主代码中的 Step 和 MultiStepPlanner
# import 时会执行 multi_step_agent.py 的顶层代码（包括 sys.stdout 设置）
from multi_step_agent import Step, MultiStepPlanner, client


# ========== 练习 1：观察执行顺序 ==========

def exercise_1():
    """
    练习 1：观察拓扑排序的执行顺序

    任务：看下面的依赖关系，先在脑中推算执行顺序，然后运行验证

    依赖关系：
      A（无依赖）
      B 依赖 A
      C 依赖 A
      D 依赖 B 和 C
      E 依赖 D

    问题：哪些步骤可以并行执行？
    """
    print("\n" + "=" * 50)
    print("练习 1：观察执行顺序")
    print("=" * 50)

    steps = [
        Step("A", lambda ctx: print("    执行 A") or "A done"),
        Step("B", lambda ctx: print("    执行 B") or "B done", depends_on=["A"]),
        Step("C", lambda ctx: print("    执行 C") or "C done", depends_on=["A"]),
        Step("D", lambda ctx: print("    执行 D") or "D done", depends_on=["B", "C"]),
        Step("E", lambda ctx: print("    执行 E") or "E done", depends_on=["D"]),
    ]

    planner = MultiStepPlanner(steps)
    planner.execute()

    # 思考题：
    # 1. B 和 C 是并行执行的吗？为什么？
    # 2. 如果把 E 的依赖改成 ["B"]，执行顺序会怎么变？
    # 3. 如果加一个步骤 F 依赖 ["A"]，它会和谁并行？


# ========== 练习 2：体验错误处理策略 ==========

def exercise_2():
    """
    练习 2：体验不同的错误处理策略

    任务：运行代码，观察每种策略的行为差异
    """
    print("\n" + "=" * 50)
    print("练习 2：错误处理策略")
    print("=" * 50)

    call_count = {"api": 0}  # 用字典模拟计数器（闭包需要可变对象）

    def always_fail(ctx):
        """一个总是失败的函数"""
        raise Exception("模拟 API 超时")

    def fail_twice_then_succeed(ctx):
        """前两次失败，第三次成功（模拟网络抖动）"""
        call_count["api"] += 1
        if call_count["api"] <= 2:
            raise Exception(f"第 {call_count['api']} 次调用失败")
        return "第 3 次调用成功！"

    def simple_fallback(ctx):
        """降级方案"""
        return "使用本地缓存数据"

    # --- 测试 skip 策略 ---
    print("\n--- 测试 skip 策略 ---")
    steps = [
        Step("step1", lambda ctx: "步骤1完成"),
        Step("step2_skip", always_fail,
             depends_on=["step1"],
             on_error="skip"),  # 失败就跳过
        Step("step3", lambda ctx: f"步骤3完成（step2结果：{ctx.get('step2_skip', '无')}）",
             depends_on=["step2_skip"]),
    ]
    planner = MultiStepPlanner(steps)
    result = planner.execute()
    print(f"\n  step3 的结果：{result['step3']}")

    # --- 测试 retry 策略 ---
    print("\n--- 测试 retry 策略 ---")
    call_count["api"] = 0  # 重置计数器
    steps = [
        Step("call_api", fail_twice_then_succeed,
             on_error="retry",  # 失败就重试
             max_retries=3),
    ]
    planner = MultiStepPlanner(steps)
    result = planner.execute()
    print(f"\n  最终结果：{result['call_api']}")

    # --- 测试 fallback 策略 ---
    print("\n--- 测试 fallback 策略 ---")
    steps = [
        Step("fetch_data", always_fail,
             on_error="fallback",  # 失败就降级
             fallback_func=simple_fallback),
    ]
    planner = MultiStepPlanner(steps)
    result = planner.execute()
    print(f"\n  最终结果：{result['fetch_data']}")

    # 思考题：
    # 1. skip 策略下，step3 拿到的 step2 结果是什么？
    # 2. retry 策略中，指数退避的等待时间分别是多少？
    # 3. 什么场景适合用 fallback？什么场景必须用 raise？


# ========== 练习 3：自己设计一个 Multi-Step 流程 ==========

def exercise_3():
    """
    练习 3：设计"每日健康报告"的 Multi-Step 流程

    需求：生成一份每日健康报告，包含：
    1. 获取今日饮食记录
    2. 获取今日运动记录
    3. 计算营养摄入汇总
    4. 用 LLM 生成健康评价
    5. 格式化输出报告

    TODO：请你完成下面的代码
    """
    print("\n" + "=" * 50)
    print("练习 3：设计每日健康报告")
    print("=" * 50)

    # 模拟数据
    def get_meals(ctx):
        """获取今日饮食记录"""
        return [
            {"meal": "早餐", "food": "鸡蛋2个+牛奶", "calories": 280},
            {"meal": "午餐", "food": "牛肉面", "calories": 550},
            {"meal": "晚餐", "food": "鸡胸肉沙拉", "calories": 350},
        ]

    def get_exercises(ctx):
        """获取今日运动记录"""
        return [
            {"type": "跑步", "duration_min": 30, "calories_burned": 300},
        ]

    def calculate_summary(ctx):
        """计算营养摄入汇总"""
        meals = ctx["get_meals"]
        exercises = ctx["get_exercises"]

        total_intake = sum(m["calories"] for m in meals)
        total_burned = sum(e["calories_burned"] for e in exercises)

        return {
            "total_intake": total_intake,
            "total_burned": total_burned,
            "net_calories": total_intake - total_burned,
            "meal_count": len(meals)
        }

    def generate_evaluation(ctx):
        """用 LLM 生成健康评价"""
        summary = ctx["calculate_summary"]
        meals = ctx["get_meals"]

        # TODO: 调用 DeepSeek API，让 LLM 根据今日数据给出评价
        # 提示：
        #   1. 用 client.chat.completions.create() 调用 API
        #   2. system prompt 设定为"你是健康顾问"
        #   3. user prompt 传入今日的饮食和运动数据
        #   4. 让 LLM 给出 2-3 句话的简短评价

        # ↓↓↓ 在这里写你的代码 ↓↓↓
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是健康顾问，给出简短的每日健康评价（2-3句话）。"},
                {"role": "user", "content": (
                    f"今日饮食：{json.dumps(meals, ensure_ascii=False)}\n"
                    f"总摄入：{summary['total_intake']} 卡\n"
                    f"运动消耗：{summary['total_burned']} 卡\n"
                    f"净摄入：{summary['net_calories']} 卡\n"
                    f"请给出简短评价。"
                )}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
        # ↑↑↑ 在这里写你的代码 ↑↑↑

    def format_report(ctx):
        """格式化输出报告"""
        meals = ctx["get_meals"]
        exercises = ctx["get_exercises"]
        summary = ctx["calculate_summary"]
        evaluation = ctx.get("generate_evaluation", "（评价生成失败）")

        report = f"""
{'='*40}
        今日健康报告
{'='*40}

【饮食记录】
"""
        for m in meals:
            report += f"  {m['meal']}：{m['food']}（{m['calories']} 卡）\n"

        report += f"\n【运动记录】\n"
        for e in exercises:
            report += f"  {e['type']}：{e['duration_min']}分钟（消耗 {e['calories_burned']} 卡）\n"

        report += f"""
【汇总】
  总摄入：{summary['total_intake']} 卡
  总消耗：{summary['total_burned']} 卡
  净摄入：{summary['net_calories']} 卡

【AI 评价】
  {evaluation}

{'='*40}"""
        return report

    # TODO: 定义步骤和依赖关系
    # 提示：
    #   - get_meals 和 get_exercises 没有依赖，可以并行
    #   - calculate_summary 依赖 get_meals 和 get_exercises
    #   - generate_evaluation 依赖 calculate_summary
    #   - format_report 依赖所有步骤

    # ↓↓↓ 在这里定义你的 steps ↓↓↓
    steps = [
        Step("get_meals", get_meals),
        Step("get_exercises", get_exercises),
        Step("calculate_summary", calculate_summary,
             depends_on=["get_meals", "get_exercises"]),
        Step("generate_evaluation", generate_evaluation,
             depends_on=["calculate_summary"],
             on_error="fallback",
             fallback_func=lambda ctx: "今日数据不足，无法生成评价"),
        Step("format_report", format_report,
             depends_on=["get_meals", "get_exercises",
                         "calculate_summary", "generate_evaluation"]),
    ]
    # ↑↑↑ 在这里定义你的 steps ↑↑↑

    planner = MultiStepPlanner(steps)
    result = planner.execute()
    print(result["format_report"])


# ========== 运行练习 ==========

if __name__ == "__main__":
    print("课程 13 练习\n")
    print("选择练习：")
    print("  1 - 观察执行顺序")
    print("  2 - 体验错误处理策略")
    print("  3 - 设计每日健康报告")
    print("  a - 运行全部")

    choice = input("\n请输入选择：").strip()

    if choice == "1":
        exercise_1()
    elif choice == "2":
        exercise_2()
    elif choice == "3":
        exercise_3()
    elif choice == "a":
        exercise_1()
        exercise_2()
        exercise_3()
    else:
        print("无效选择")
