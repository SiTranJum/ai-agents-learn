"""
课程 25：CrewAI 角色驱动架构 — 代码实践

本文件演示 CrewAI 的核心机制：
1. Agent/Task/Crew 三层模型
2. Sequential 和 Hierarchical 两种执行模式
3. 任务间的数据传递（context）
4. 结构化输出（output_pydantic）

运行前安装依赖：
pip install crewai crewai-tools
"""

from crewai import Agent, Task, Crew, Process, LLM

# ============================================================
# 初始化 LLM（通义千问 DashScope API）
# ============================================================

# CrewAI 用自己的 LLM 类封装模型配置
# 底层使用 litellm 路由，支持 "provider/model" 格式
# 因为通义千问兼容 OpenAI 格式，所以 provider 用 "openai"
llm = LLM(
    model="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="sk-a4ae611c3f9c4df89a133e621b2b7851",
)


# ============================================================
# 示例 1：最简单的 Crew — 单 Agent 单 Task
# ============================================================

def demo_basic_crew():
    """
    最简单的 CrewAI 示例：一个 Agent 完成一个 Task

    类比：一个人的"团队"，只有一个任务
    """
    print("=" * 60)
    print("示例 1：最简单的 Crew")
    print("=" * 60)

    # 定义 Agent
    analyst = Agent(
        role="健康顾问",
        goal="用通俗易懂的语言回答健康问题",
        backstory="你是一位社区健康顾问，擅长用简单的语言解释健康知识。",
        llm=llm,
        verbose=True,  # 输出详细日志，可以看到 ReAct 过程
    )

    # 定义 Task
    task = Task(
        description="用 3 句话解释：为什么每天要喝 8 杯水？",
        expected_output="3 句简洁的解释",
        agent=analyst,
    )

    # 组建 Crew 并执行
    crew = Crew(
        agents=[analyst],
        tasks=[task],
        verbose=True,
    )

    # kickoff() 启动执行，返回最终结果
    # 类比 Java：executorService.submit(task).get()
    result = crew.kickoff()
    print(f"\n最终结果：{result}")


# ============================================================
# 示例 2：多 Agent 协作 — Sequential 模式
# ============================================================

def demo_sequential_crew():
    """
    多 Agent 协作：营养分析师 → 运动教练 → 报告员

    Sequential 模式：任务按顺序执行，前一个的输出传给下一个
    类比：流水线生产，每个工位完成自己的工作后传给下一个
    """
    print("\n" + "=" * 60)
    print("示例 2：多 Agent 协作（Sequential）")
    print("=" * 60)

    # --- 定义三个 Agent ---

    nutrition_agent = Agent(
        role="营养分析师",
        goal="分析用户饮食，计算营养摄入",
        backstory="你是注册营养师，擅长分析饮食结构和营养成分。回答要简洁，用数据说话。",
        llm=llm,
        verbose=True,
    )

    exercise_agent = Agent(
        role="运动教练",
        goal="根据用户情况制定运动建议",
        backstory="你是健身教练，擅长为不同体质的人制定运动方案。建议要具体可执行。",
        llm=llm,
        verbose=True,
    )

    report_agent = Agent(
        role="健康报告员",
        goal="汇总分析结果，生成简洁的健康报告",
        backstory="你是健康管理师，擅长将专业分析转化为用户易懂的报告。",
        llm=llm,
        verbose=True,
    )

    # --- 定义三个 Task（注意 context 的使用）---

    # Task 1：饮食分析（无前置依赖）
    analyze_task = Task(
        description="""分析以下饮食记录的营养摄入：
        早餐：牛奶250ml + 全麦面包2片
        午餐：米饭1碗 + 红烧肉 + 炒青菜
        晚餐：面条1碗 + 煎蛋1个

        请估算总热量和三大营养素（蛋白质、碳水、脂肪）的大致摄入量。""",
        expected_output="每餐的热量估算和总营养摄入概览（2-3句话）",
        agent=nutrition_agent,
    )

    # Task 2：运动建议（依赖 Task 1 的输出）
    exercise_task = Task(
        description="根据饮食分析结果，为一个久坐办公的上班族推荐今天的运动方案。",
        expected_output="2-3 条具体的运动建议（包含运动类型、时长）",
        agent=exercise_agent,
        context=[analyze_task],
        # context 的作用：
        # analyze_task 的输出会自动注入到 exercise_task 的 Prompt 中
        # exercise_agent 能看到营养分析的结果，据此给出运动建议
    )

    # Task 3：生成报告（依赖 Task 1 和 Task 2）
    report_task = Task(
        description="汇总饮食分析和运动建议，生成一份简洁的每日健康报告。",
        expected_output="一份包含饮食总结和运动建议的简短报告（不超过 200 字）",
        agent=report_agent,
        context=[analyze_task, exercise_task],
        # 同时依赖两个前置任务的输出
    )

    # --- 组建 Crew ---
    crew = Crew(
        agents=[nutrition_agent, exercise_agent, report_agent],
        tasks=[analyze_task, exercise_task, report_task],
        process=Process.sequential,  # 串行执行
        verbose=True,
    )

    result = crew.kickoff()
    print(f"\n{'=' * 40}")
    print(f"最终健康报告：\n{result}")


# ============================================================
# 示例 3：结构化输出
# ============================================================

def demo_structured_output():
    """
    演示 CrewAI 的结构化输出功能

    用 Pydantic 模型定义输出格式，框架自动解析
    类比 Java：指定 ResponseEntity<T> 的泛型类型
    """
    print("\n" + "=" * 60)
    print("示例 3：结构化输出")
    print("=" * 60)

    from pydantic import BaseModel

    # 定义输出结构（Pydantic 模型）
    # 类比 Java：定义一个 DTO 类
    class HealthTip(BaseModel):
        category: str       # 类别（饮食/运动/睡眠）
        tip: str            # 建议内容
        difficulty: str     # 难度（简单/中等/困难）
        reason: str         # 原因

    agent = Agent(
        role="健康建议生成器",
        goal="生成结构化的健康建议",
        backstory="你是健康管理专家，擅长给出具体可执行的建议。",
        llm=llm,
    )

    task = Task(
        description="给一个经常熬夜的程序员一条最重要的健康建议。",
        expected_output="一条结构化的健康建议",
        agent=agent,
        output_pydantic=HealthTip,
        # output_pydantic: 指定输出类型
        # 框架会自动让 LLM 输出 JSON 并解析为 HealthTip 对象
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()

    # result.pydantic 是解析后的 Pydantic 对象
    if result.pydantic:
        tip = result.pydantic
        print(f"\n结构化结果：")
        print(f"  类别: {tip.category}")
        print(f"  建议: {tip.tip}")
        print(f"  难度: {tip.difficulty}")
        print(f"  原因: {tip.reason}")
    else:
        print(f"\n原始结果：{result.raw}")


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("CrewAI 角色驱动架构 — 代码实践\n")

    demo_basic_crew()
    demo_sequential_crew()
    demo_structured_output()

    print("\n" + "=" * 60)
    print("练习任务")
    print("=" * 60)
    print("""
    练习 1：设计一个 3 Agent 的健康咨询 Crew
    - 营养师 Agent：分析饮食
    - 心理咨询师 Agent：分析压力和情绪
    - 综合顾问 Agent：汇总两方面建议
    - 使用 Sequential 模式

    练习 2：用 output_pydantic 实现结构化的饮食分析报告
    - 定义 Pydantic 模型：DietReport
    - 包含字段：meals(list), total_calories(int), suggestions(list)
    - 让 Agent 输出结构化数据
    """)
