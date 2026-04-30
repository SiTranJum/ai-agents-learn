"""
示例 2：编排器 + 共享上下文

编排器（Orchestrator）管理整个流程，所有 Agent 共享一个 Context。
这是课程 21 完整系统的基础。
"""

from openai import OpenAI
from typing import Dict, Any, Callable
import json

client = OpenAI(
    api_key="sk-non",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


# ============ 共享上下文 ============

class AgentContext:
    """
    共享上下文：所有 Agent 都能读写的"黑板"。

    类比 Java：
      - 类似 Spring 的 ApplicationContext
      - 或者 Servlet 的 HttpServletRequest.setAttribute()
      - 或者 ThreadLocal + Map
    """
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._history: list = []  # 记录每个 Agent 的操作

    def set(self, key: str, value: Any, agent_name: str = "system"):
        """
        写入数据到上下文。

        参数：
            key: 数据键名
            value: 数据值
            agent_name: 写入者（用于追踪）
        """
        self._data[key] = value
        self._history.append({
            "agent": agent_name,
            "action": "set",
            "key": key,
            "preview": str(value)[:100]
        })
        print(f"  [Context] {agent_name} 写入 {key}")

    def get(self, key: str, default=None) -> Any:
        """
        从上下文读取数据。

        参数：
            key: 数据键名
            default: 默认值
        """
        return self._data.get(key, default)

    def get_history(self) -> list:
        """获取操作历史"""
        return self._history

    def summary(self) -> str:
        """返回上下文摘要，方便传给 LLM"""
        return json.dumps(self._data, ensure_ascii=False, default=str)


# ============ 基于上下文的 Agent ============

def create_context_agent(name: str, system_prompt: str):
    """
    创建一个基于共享上下文的 Agent。

    与课程 19 的区别：Agent 读写 Context 而不是直接传参。
    """
    def run(ctx: AgentContext, input_key: str, output_key: str) -> str:
        """
        运行 Agent：从 Context 读取输入，处理后写回 Context。

        参数：
            ctx: 共享上下文
            input_key: 从 Context 中读取哪个 key 作为输入
            output_key: 把结果写入 Context 的哪个 key
        返回：
            Agent 的输出文本
        """
        print(f"\n[{name}] 开始工作...")

        # 从上下文读取输入
        input_data = ctx.get(input_key)
        if input_data is None:
            print(f"[{name}] 错误：{input_key} 不存在")
            return ""

        # 构造 LLM 输入
        if isinstance(input_data, dict):
            user_input = json.dumps(input_data, ensure_ascii=False)
        else:
            user_input = str(input_data)

        # 调用 LLM
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.5
        )

        result = response.choices[0].message.content
        print(f"[{name}] 完成：{result[:100]}...")

        # 写回上下文
        ctx.set(output_key, result, agent_name=name)

        return result

    run.name = name
    return run


# ============ 编排器 ============

class Orchestrator:
    """
    编排器：管理 Agent 的执行流程。

    类比 Java：
      - 类似工作流引擎（Camunda / Activiti）
      - 或者 Spring Batch 的 Step 编排
    """
    def __init__(self):
        self.agents: Dict[str, Callable] = {}  # Agent 注册表
        self.workflows: Dict[str, list] = {}   # 工作流定义

    def register_agent(self, name: str, agent: Callable):
        """注册一个 Agent"""
        self.agents[name] = agent
        print(f"[编排器] 注册 Agent: {name}")

    def define_workflow(self, name: str, steps: list):
        """
        定义一个工作流。

        参数：
            name: 工作流名称
            steps: 步骤列表，每个步骤是 (agent_name, input_key, output_key)
        """
        self.workflows[name] = steps
        print(f"[编排器] 定义工作流: {name}，共 {len(steps)} 步")

    def execute(self, workflow_name: str, ctx: AgentContext) -> AgentContext:
        """
        执行一个工作流。

        参数：
            workflow_name: 工作流名称
            ctx: 共享上下文（已包含初始数据）
        返回：
            执行完成后的上下文
        """
        steps = self.workflows.get(workflow_name)
        if not steps:
            print(f"[编排器] 错误：工作流 {workflow_name} 不存在")
            return ctx

        print(f"\n{'=' * 60}")
        print(f"[编排器] 开始执行工作流: {workflow_name}")
        print(f"{'=' * 60}")

        for i, (agent_name, input_key, output_key) in enumerate(steps):
            print(f"\n--- 步骤 {i + 1}/{len(steps)}: {agent_name} ---")

            agent = self.agents.get(agent_name)
            if not agent:
                print(f"[编排器] 错误：Agent {agent_name} 未注册")
                continue

            agent(ctx, input_key, output_key)

        print(f"\n{'=' * 60}")
        print(f"[编排器] 工作流 {workflow_name} 执行完成")
        print(f"{'=' * 60}")

        return ctx


# ============ 测试 ============

if __name__ == "__main__":
    # 1. 创建 Agent
    parse_agent = create_context_agent(
        name="解析Agent",
        system_prompt="""你是饮食解析专家。提取食物名称和量。
输出 JSON：{"foods": [{"name": "食物名", "amount": "量"}]}
只输出 JSON。"""
    )

    nutrition_agent = create_context_agent(
        name="营养Agent",
        system_prompt="""你是营养专家。根据食物信息返回营养数据。
输出 JSON：{"foods": [...], "total": {"calories": 总热量, "protein": 总蛋白质}}
只输出 JSON。"""
    )

    advice_agent = create_context_agent(
        name="建议Agent",
        system_prompt="""你是健康顾问。
你会收到营养数据，请结合用户的健康目标给出建议。
输出 2-3 句话。"""
    )

    # 2. 创建编排器并注册 Agent
    orchestrator = Orchestrator()
    orchestrator.register_agent("parse", parse_agent)
    orchestrator.register_agent("nutrition", nutrition_agent)
    orchestrator.register_agent("advice", advice_agent)

    # 3. 定义工作流：(agent_name, input_key, output_key)
    orchestrator.define_workflow("diet_record", [
        ("parse", "user_input", "parsed_foods"),
        ("nutrition", "parsed_foods", "nutrition_data"),
        ("advice", "nutrition_data", "final_advice"),
    ])

    # 4. 创建上下文并执行
    ctx = AgentContext()
    ctx.set("user_input", "我今天早上吃了一碗牛肉面，加了一个鸡蛋")
    ctx.set("user_profile", {"name": "张三", "goal": "减肥", "daily_calories": 1800})

    result_ctx = orchestrator.execute("diet_record", ctx)

    # 5. 查看结果
    print(f"\n最终建议：{result_ctx.get('final_advice')}")
    print(f"\n执行历史：")
    for record in result_ctx.get_history():
        print(f"  {record['agent']}: {record['action']} {record['key']}")
