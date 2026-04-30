import os
"""
模式三：路由分发（Router）

场景：用户输入 → Router Agent 判断意图 → 分发到对应的专业 Agent

类似 Spring MVC 的 DispatcherServlet，根据请求类型路由到不同 Controller。
"""

from openai import OpenAI
import json

# 创建 DashScope 客户端
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def create_agent(name: str, system_prompt: str):
    """创建一个 Agent"""
    def run(user_message: str) -> str:
        print(f"\n[{name}] 处理中...")

        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )

        result = response.choices[0].message.content
        return result

    run.name = name
    return run


# ============ 定义 Router 和专业 Agent ============

# Router Agent：判断用户意图
router_agent = create_agent(
    name="路由Agent",
    system_prompt="""
你是一个意图识别专家。
用户会发送各种消息，你需要判断用户的意图，并返回对应的类型。

可能的意图类型：
- diet: 饮食相关（记录吃了什么、查询食物营养）
- exercise: 运动相关（记录运动、查询运动消耗）
- knowledge: 健康知识问答（问疾病、营养知识）
- chat: 日常闲聊（打招呼、聊天）

输出格式（JSON）：
{
  "intent": "类型",
  "confidence": 0.0-1.0
}

只输出 JSON，不要其他内容。
"""
)

# 饮食 Agent
diet_agent = create_agent(
    name="饮食Agent",
    system_prompt="""
你是饮食记录助手。
用户会告诉你吃了什么，你需要：
1. 确认记录的食物
2. 简单评价营养
3. 鼓励用户继续记录

语气友好、简洁。
"""
)

# 运动 Agent
exercise_agent = create_agent(
    name="运动Agent",
    system_prompt="""
你是运动记录助手。
用户会告诉你做了什么运动，你需要：
1. 确认记录的运动
2. 估算消耗
3. 鼓励用户坚持

语气友好、简洁。
"""
)

# 知识问答 Agent
knowledge_agent = create_agent(
    name="知识问答Agent",
    system_prompt="""
你是健康知识专家。
用户会问健康相关的问题，你需要：
1. 给出准确、科学的回答
2. 语言通俗易懂
3. 必要时提醒用户咨询医生

语气专业但友好。
"""
)

# 闲聊 Agent
chat_agent = create_agent(
    name="闲聊Agent",
    system_prompt="""
你是一个友好的健康管家。
用户在和你闲聊，你需要：
1. 自然地回应
2. 适当引导到健康话题
3. 保持轻松愉快的氛围

语气轻松、亲切。
"""
)


# ============ 路由系统 ============

# Agent 注册表：类似 Spring 的 Bean 容器
AGENT_REGISTRY = {
    "diet": diet_agent,
    "exercise": exercise_agent,
    "knowledge": knowledge_agent,
    "chat": chat_agent
}


def route_and_execute(user_input: str) -> str:
    """
    路由并执行：判断意图 → 分发到对应 Agent

    参数：
        user_input: 用户输入
    返回：
        对应 Agent 的回复
    """
    print("=" * 60)
    print(f"用户输入：{user_input}")
    print("=" * 60)

    # 第 1 步：Router 判断意图
    router_result = router_agent(user_input)
    print(f"\n[路由结果] {router_result}")

    # 解析 JSON
    try:
        # json.loads() — 将 JSON 字符串解析为 Python 字典
        # 类比 Java：类似 ObjectMapper.readValue()
        intent_data = json.loads(router_result)
        intent = intent_data["intent"]
        confidence = intent_data.get("confidence", 0.0)

        print(f"[意图识别] 类型={intent}, 置信度={confidence}")

    except json.JSONDecodeError:
        print("[错误] Router 返回的不是有效 JSON，默认使用闲聊 Agent")
        intent = "chat"

    # 第 2 步：从注册表中获取对应的 Agent
    # dict.get(key, default) — 获取字典值，如果 key 不存在返回 default
    # 类比 Java：类似 Map.getOrDefault()
    target_agent = AGENT_REGISTRY.get(intent, chat_agent)

    print(f"\n[分发] 路由到 {target_agent.name}")
    print("=" * 60)

    # 第 3 步：执行目标 Agent
    result = target_agent(user_input)

    return result


# ============ 测试 ============

if __name__ == "__main__":
    # 测试用例 1：饮食记录
    print("\n" + "=" * 60)
    print("测试 1：饮食记录")
    print("=" * 60)
    result1 = route_and_execute("我今天早上吃了一碗牛肉面")
    print(f"\n回复：{result1}\n")

    # 测试用例 2：运动记录
    print("\n" + "=" * 60)
    print("测试 2：运动记录")
    print("=" * 60)
    result2 = route_and_execute("我刚跑了 5 公里")
    print(f"\n回复：{result2}\n")

    # 测试用例 3：知识问答
    print("\n" + "=" * 60)
    print("测试 3：知识问答")
    print("=" * 60)
    result3 = route_and_execute("痛风能吃豆腐吗")
    print(f"\n回复：{result3}\n")

    # 测试用例 4：闲聊
    print("\n" + "=" * 60)
    print("测试 4：闲聊")
    print("=" * 60)
    result4 = route_and_execute("今天天气真好")
    print(f"\n回复：{result4}\n")
