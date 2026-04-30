"""
健康管家 Multi-Agent 系统

整合课程 19-21 的所有概念：
- 路由分发（Router）
- 串行管道（Pipeline）
- 并行扇出（Fan-out）
- 编排器（Orchestrator）
- 共享上下文（AgentContext）
- 执行追踪（Tracer）
"""

from openai import OpenAI
from dataclasses import dataclass, field
from typing import Dict, Any, Callable, List, Optional
import json
import time
import uuid
import asyncio

client = OpenAI(
    api_key="sk-non",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


# ============================================================
# 1. 基础设施层
# ============================================================

@dataclass
class TraceStep:
    """追踪的一个步骤"""
    agent: str
    input_preview: str
    output_preview: str
    duration_ms: int
    success: bool
    error: Optional[str] = None


class Tracer:
    """
    执行追踪器：记录每个 Agent 的执行情况。

    类比 Java：类似 Zipkin / Sleuth 的 Span
    """
    def __init__(self):
        self.trace_id = str(uuid.uuid4())[:8]
        self.steps: List[TraceStep] = []

    def record(self, agent: str, input_data: str, output_data: str,
               duration_ms: int, success: bool, error: str = None):
        """记录一个步骤"""
        self.steps.append(TraceStep(
            agent=agent,
            input_preview=input_data[:80],
            output_preview=output_data[:80],
            duration_ms=duration_ms,
            success=success,
            error=error
        ))

    def print_trace(self):
        """打印完整的执行追踪"""
        print(f"\n{'=' * 60}")
        print(f"Trace ID: {self.trace_id}")
        print(f"{'=' * 60}")
        total_ms = sum(s.duration_ms for s in self.steps)
        for i, step in enumerate(self.steps):
            status = "OK" if step.success else "FAIL"
            print(f"  [{i+1}] {step.agent} ({step.duration_ms}ms) [{status}]")
            print(f"      输入: {step.input_preview}")
            print(f"      输出: {step.output_preview}")
            if step.error:
                print(f"      错误: {step.error}")
        print(f"  总耗时: {total_ms}ms")
        print(f"{'=' * 60}")


class AgentContext:
    """共享上下文：所有 Agent 读写的黑板"""
    def __init__(self):
        self._data: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._data[key] = value

    def get(self, key: str, default=None) -> Any:
        return self._data.get(key, default)


def call_llm(system_prompt: str, user_input: str) -> str:
    """封装 LLM 调用，统一错误处理和重试"""
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.5
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < 2:
                print(f"  [重试] 第 {attempt + 1} 次失败: {e}")
                time.sleep(1)
            else:
                raise


# ============================================================
# 2. Agent 定义
# ============================================================

def router_agent(user_input: str) -> str:
    """路由 Agent：判断用户意图"""
    return call_llm(
        system_prompt="""你是意图识别专家。判断用户意图并返回 JSON。
可能的意图：
- diet: 饮食记录（吃了什么）
- analysis: 综合健康分析（分析今天的整体情况）
- knowledge: 健康知识问答
- chat: 日常闲聊
输出格式：{"intent": "类型"}
只输出 JSON。""",
        user_input=user_input
    )


def parse_agent(user_input: str) -> str:
    """解析 Agent：提取食物信息"""
    return call_llm(
        system_prompt="""你是饮食解析专家。提取食物名称和量。
输出 JSON：{"foods": [{"name": "食物名", "amount": "量"}]}
只输出 JSON。""",
        user_input=user_input
    )


def nutrition_agent(user_input: str) -> str:
    """营养 Agent：查询营养数据"""
    return call_llm(
        system_prompt="""你是营养专家。根据食物信息返回营养数据。
输出 JSON：{"total": {"calories": 总热量, "protein": 蛋白质克}}
只输出 JSON。""",
        user_input=user_input
    )


def advice_agent(user_input: str) -> str:
    """建议 Agent：生成个性化建议"""
    return call_llm(
        system_prompt="你是健康顾问。根据营养数据给出 2-3 句建议，语气友好。",
        user_input=user_input
    )


def exercise_analysis_agent(user_input: str) -> str:
    """运动分析 Agent"""
    return call_llm(
        system_prompt="你是运动分析专家。分析运动情况，估算消耗，给出 2 句建议。",
        user_input=user_input
    )


def sleep_analysis_agent(user_input: str) -> str:
    """睡眠分析 Agent"""
    return call_llm(
        system_prompt="你是睡眠分析专家。评价睡眠时长和质量，给出 2 句建议。",
        user_input=user_input
    )


def nutrition_analysis_agent(user_input: str) -> str:
    """营养分析 Agent（用于综合分析）"""
    return call_llm(
        system_prompt="你是营养分析专家。分析今天的饮食情况，给出 2 句评价。",
        user_input=user_input
    )


def summary_agent(user_input: str) -> str:
    """汇总 Agent：综合多方分析"""
    return call_llm(
        system_prompt="你是健康管家。综合营养、运动、睡眠三方面分析，给出 3-5 句整体建议。",
        user_input=user_input
    )


def knowledge_agent(user_input: str) -> str:
    """知识问答 Agent"""
    return call_llm(
        system_prompt="你是健康知识专家。给出准确、通俗的回答，必要时提醒咨询医生。",
        user_input=user_input
    )


def chat_agent(user_input: str) -> str:
    """闲聊 Agent"""
    return call_llm(
        system_prompt="你是友好的健康管家。自然回应，适当引导到健康话题。",
        user_input=user_input
    )


# ============================================================
# 3. 编排器
# ============================================================

class HealthOrchestrator:
    """
    健康管家编排器：路由 + 管道 + 并行 + 追踪。

    类比 Java：DispatcherServlet + 工作流引擎
    """
    def __init__(self):
        self.tracer: Optional[Tracer] = None

    def _traced_call(self, name: str, agent_fn: Callable, input_data: str) -> str:
        """带追踪的 Agent 调用"""
        start = time.time()
        try:
            result = agent_fn(input_data)
            duration = int((time.time() - start) * 1000)
            if self.tracer:
                self.tracer.record(name, input_data, result, duration, True)
            return result
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            if self.tracer:
                self.tracer.record(name, input_data, "", duration, False, str(e))
            return f"抱歉，{name}处理时出了点问题。"

    def _diet_pipeline(self, user_input: str) -> str:
        """饮食记录：串行管道"""
        parsed = self._traced_call("解析Agent", parse_agent, user_input)
        nutrition = self._traced_call("营养Agent", nutrition_agent, parsed)
        advice = self._traced_call("建议Agent", advice_agent, nutrition)
        return advice

    def _analysis_fanout(self, user_input: str) -> str:
        """综合分析：并行扇出"""
        # 用 asyncio 并行执行三个分析 Agent
        async def _parallel():
            return await asyncio.gather(
                asyncio.to_thread(
                    self._traced_call, "营养分析", nutrition_analysis_agent, user_input),
                asyncio.to_thread(
                    self._traced_call, "运动分析", exercise_analysis_agent, user_input),
                asyncio.to_thread(
                    self._traced_call, "睡眠分析", sleep_analysis_agent, user_input),
            )

        nutrition_r, exercise_r, sleep_r = asyncio.run(_parallel())

        # 汇总
        combined = f"营养分析：{nutrition_r}\n运动分析：{exercise_r}\n睡眠分析：{sleep_r}"
        return self._traced_call("汇总Agent", summary_agent, combined)

    def handle(self, user_input: str) -> str:
        """
        处理用户输入的入口。

        参数：
            user_input: 用户的原始输入
        返回：
            系统的回复
        """
        self.tracer = Tracer()

        print(f"\n用户：{user_input}")
        print("-" * 40)

        # 第 1 步：路由
        route_result = self._traced_call("路由Agent", router_agent, user_input)

        try:
            intent = json.loads(route_result).get("intent", "chat")
        except json.JSONDecodeError:
            intent = "chat"

        print(f"[意图] {intent}")

        # 第 2 步：根据意图分发
        if intent == "diet":
            result = self._diet_pipeline(user_input)
        elif intent == "analysis":
            result = self._analysis_fanout(user_input)
        elif intent == "knowledge":
            result = self._traced_call("知识Agent", knowledge_agent, user_input)
        else:
            result = self._traced_call("闲聊Agent", chat_agent, user_input)

        # 打印追踪信息
        self.tracer.print_trace()

        return result


# ============================================================
# 4. 测试
# ============================================================

if __name__ == "__main__":
    orchestrator = HealthOrchestrator()

    tests = [
        "我中午吃了一碗番茄鸡蛋面和一杯豆浆",
        "高血压患者能吃咸鸭蛋吗",
        "今天心情不错",
    ]

    for test_input in tests:
        print("\n" + "=" * 60)
        result = orchestrator.handle(test_input)
        print(f"\n回复：{result}")
        print("=" * 60)
