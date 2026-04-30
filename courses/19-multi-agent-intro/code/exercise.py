"""
练习：实现一个混合模式的健康管家

架构：
  用户输入
    → Router Agent（判断意图）
        ├→ diet:      串行管道（解析 → 营养 → 建议）
        ├→ analysis:  并行扇出（营养 + 运动 + 睡眠 → 汇总）
        ├→ exercise:  运动 Agent
        ├→ knowledge: 知识问答 Agent
        └→ chat:      闲聊 Agent
"""
from openai import OpenAI
import json
import asyncio

client = OpenAI(
    api_key="sk-non",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def create_agent(name: str, sys_prompt: str):
    def run(user_message: str) -> str:
        print(f"\n[{name}] 开始工作...")
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5
        )
        result = response.choices[0].message.content
        print(f"[{name}] 完成：{result[:200]}")
        return result

    run.name = name
    return run  # 原来漏了这行，闭包必须返回内部函数


# ============ 定义所有 Agent ============

router_agent = create_agent(
    name="路由Agent",
    sys_prompt="""
你是一个意图识别专家。
用户会发送各种消息，你需要判断用户的意图，并返回对应的类型。

可能的意图类型：
- diet: 饮食相关（记录吃了什么、查询食物营养）
- analysis: 综合健康分析（分析今天的整体健康状况，涉及多方面）
- exercise: 运动相关（记录运动、查询运动消耗）
- knowledge: 健康知识问答（问疾病、营养知识）
- chat: 日常闲聊（打招呼、聊天）

输出格式（JSON）：
{"intent": "类型", "confidence": 0.0-1.0}

只输出 JSON，不要其他内容。
"""
)

# 串行管道用的三个 Agent
parse_agent = create_agent(
    name="解析Agent",
    sys_prompt="""
你是一个饮食记录解析专家。
用户会用自然语言描述吃了什么，你需要提取出食物名称和大概的量。

输出格式（JSON）：
{"foods": [{"name": "食物名", "amount": "量"}]}

只输出 JSON，不要其他解释。
"""
)

nutrition_agent = create_agent(
    name="营养Agent",
    sys_prompt="""
你是一个营养数据专家。
用户会给你一个食物列表（JSON 格式），你需要返回每个食物的营养信息。

输出格式（JSON）：
{
  "foods": [{"name": "食物名", "calories": 热量, "protein": 蛋白质克, "carbs": 碳水克, "fat": 脂肪克}],
  "total": {"calories": 总热量, "protein": 总蛋白质, "carbs": 总碳水, "fat": 总脂肪}
}

只输出 JSON，不要其他解释。
"""
)

advice_agent = create_agent(
    name="建议Agent",
    sys_prompt="""
你是一个健康顾问。
用户会给你营养数据（JSON 格式），你需要：
1. 评价这顿饭的营养是否均衡
2. 给出具体的改进建议
3. 语气友好、鼓励为主

输出格式：自然语言，2-3 句话。
"""
)

# 单独处理的 Agent
exercise_agent = create_agent(
    name="运动Agent",
    sys_prompt="你是运动记录助手。确认用户的运动，估算消耗，给出鼓励。语气友好、简洁。"
)

knowledge_agent = create_agent(
    name="知识问答Agent",
    sys_prompt="你是健康知识专家。给出准确、通俗的回答，必要时提醒咨询医生。"
)

chat_agent = create_agent(
    name="闲聊Agent",
    sys_prompt="你是友好的健康管家。自然回应，适当引导到健康话题。语气轻松、亲切。"
)

# 并行扇出用的 Agent
nutrition_analysis_agent = create_agent(
    name="营养分析Agent",
    sys_prompt="你是营养分析专家。分析用户今天的饮食情况，给出 2 句简短评价。"
)

exercise_analysis_agent = create_agent(
    name="运动分析Agent",
    sys_prompt="你是运动分析专家。分析用户今天的运动情况，估算消耗，给出 2 句简短评价。"
)

sleep_analysis_agent = create_agent(
    name="睡眠分析Agent",
    sys_prompt="你是睡眠分析专家。评价用户的睡眠时长和质量，给出 2 句简短评价。"
)

summary_agent = create_agent(
    name="汇总Agent",
    sys_prompt="你是健康管家。综合营养、运动、睡眠三方面的分析报告，给出 3-5 句整体建议。语气友好。"
)


# ============ 串行管道 ============

def diet_pipeline(user_input: str) -> str:
    """饮食记录走串行管道：解析 → 营养 → 建议"""
    parsed = parse_agent(user_input)
    nutrition = nutrition_agent(parsed)
    advice = advice_agent(nutrition)
    return advice


# ============ 并行扇出 ============

def analysis_fanout(user_input: str) -> str:
    """综合健康分析走并行扇出：营养 + 运动 + 睡眠同时分析 → 汇总"""

    # asyncio.gather() — 并行执行多个任务，等待全部完成
    # asyncio.to_thread() — 把同步函数放到线程中执行，避免阻塞
    # 类比 Java：CompletableFuture.allOf()
    async def _parallel():
        return await asyncio.gather(
            asyncio.to_thread(nutrition_analysis_agent, user_input),
            asyncio.to_thread(exercise_analysis_agent, user_input),
            asyncio.to_thread(sleep_analysis_agent, user_input),
        )

    nutrition_r, exercise_r, sleep_r = asyncio.run(_parallel())

    # 汇总三方结果
    combined = f"营养分析：{nutrition_r}\n运动分析：{exercise_r}\n睡眠分析：{sleep_r}"
    return summary_agent(combined)


# ============ 路由 + 分发 ============

# Agent 注册表：key 要和 Router 返回的 intent 一致
AGENT_REGISTRY = {
    "diet": diet_pipeline,          # 饮食走串行管道
    "analysis": analysis_fanout,    # 综合分析走并行扇出
    "exercise": exercise_agent,
    "knowledge": knowledge_agent,
    "chat": chat_agent
}


def health_assistant(user_input: str) -> str:
    """混合模式健康管家入口"""
    print("=" * 60)
    print(f"用户：{user_input}")
    print("=" * 60)

    # 第 1 步：路由
    router_result = router_agent(user_input)
    print(f"\n[路由结果] {router_result}")

    try:
        intent_data = json.loads(router_result)
        intent = intent_data["intent"]
    except (json.JSONDecodeError, KeyError):
        intent = "chat"

    # 第 2 步：分发执行
    handler = AGENT_REGISTRY.get(intent, chat_agent)
    print(f"[分发] → {intent}")

    result = handler(user_input)
    return result


# ============ 测试 ============

if __name__ == "__main__":
    tests = [
        "我中午吃了一碗番茄鸡蛋面",                              # → diet 管道
        "我今天吃了沙拉，跑了5公里，睡了7小时，帮我分析一下",       # → analysis 扇出
        "我刚跑了 3 公里",                                       # → exercise
        "高血压不能吃什么",                                       # → knowledge
        "你好呀，今天天气不错",                                    # → chat
    ]

    for test in tests:
        result = health_assistant(test)
        print(f"\n回复：{result}")
        print("\n" + "=" * 60 + "\n")
