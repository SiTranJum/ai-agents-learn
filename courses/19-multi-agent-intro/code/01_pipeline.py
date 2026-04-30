"""
模式一：串行管道（Pipeline）

场景：用户输入饮食记录 → 解析 Agent → 营养 Agent → 建议 Agent

每个 Agent 的输出是下一个 Agent 的输入，像流水线一样。
"""

from openai import OpenAI

# 创建 DashScope 客户端（通义千问）
client = OpenAI(
    api_key="sk-non",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def create_agent(name: str, system_prompt: str):
    """
    创建一个 Agent。

    参数：
        name: Agent 名称
        system_prompt: 系统提示词，定义 Agent 的职责和行为

    返回：
        一个函数，接收输入字符串，返回输出字符串
    """
    def run(user_message: str) -> str:
        print(f"\n[{name}] 收到输入：{user_message[:50]}...")

        # chat.completions.create() — 调用 LLM API
        # model: 使用的模型名称
        # messages: 对话消息列表，system 定义角色，user 是输入
        # temperature: 0-1，控制输出随机性，0=确定性强，1=创造性强
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )

        # choices[0].message.content — 提取 LLM 返回的文本内容
        result = response.choices[0].message.content
        print(f"[{name}] 输出：{result[:500]}...")
        return result

    run.name = name
    return run


# ============ 定义三个 Agent ============

# Agent 1：解析 Agent
# 职责：从用户的自然语言中提取结构化的食物信息
parse_agent = create_agent(
    name="解析Agent",
    system_prompt="""
你是一个饮食记录解析专家。
用户会用自然语言描述吃了什么，你需要提取出：
1. 食物名称
2. 大概的量（如果有）

输出格式（JSON）：
{
  "foods": [
    {"name": "食物名", "amount": "量"}
  ]
}

只输出 JSON，不要其他解释。
"""
)

# Agent 2：营养 Agent
# 职责：根据食物信息查询营养数据（这里简化为模拟数据）
nutrition_agent = create_agent(
    name="营养Agent",
    system_prompt="""
你是一个营养数据专家。
用户会给你一个食物列表（JSON 格式），你需要返回每个食物的营养信息。

输出格式（JSON）：
{
  "foods": [
    {
      "name": "食物名",
      "amount": "量",
      "calories": 热量（千卡）,
      "protein": 蛋白质（克）,
      "carbs": 碳水化合物（克）,
      "fat": 脂肪（克）
    }
  ],
  "total": {
    "calories": 总热量,
    "protein": 总蛋白质,
    "carbs": 总碳水,
    "fat": 总脂肪
  }
}

只输出 JSON，不要其他解释。
"""
)

# Agent 3：建议 Agent
# 职责：根据营养数据生成个性化建议
advice_agent = create_agent(
    name="建议Agent",
    system_prompt="""
你是一个健康顾问。
用户会给你营养数据（JSON 格式），你需要：
1. 评价这顿饭的营养是否均衡
2. 给出具体的改进建议
3. 语气友好、鼓励为主

输出格式：自然语言，2-3 句话。
"""
)


# ============ 串行管道执行 ============

def pipeline(user_input: str) -> str:
    """
    串行管道：解析 → 营养 → 建议

    参数：
        user_input: 用户的原始输入
    返回：
        最终的建议文本
    """
    print("=" * 60)
    print("开始执行串行管道")
    print("=" * 60)

    # 第 1 步：解析用户输入
    parsed = parse_agent(user_input)

    # 第 2 步：查询营养信息
    nutrition = nutrition_agent(parsed)

    # 第 3 步：生成建议
    advice = advice_agent(nutrition)

    print("=" * 60)
    print("管道执行完成")
    print("=" * 60)

    return advice


# ============ 测试 ============

if __name__ == "__main__":
    # 测试用例 1
    user_input_1 = "我今天早上吃了一碗牛肉面，加了一个鸡蛋"
    result_1 = pipeline(user_input_1)
    print(f"\n最终建议：{result_1}\n")

    # 测试用例 2
    user_input_2 = "中午吃了一份沙拉，有生菜、番茄、鸡胸肉"
    result_2 = pipeline(user_input_2)
    print(f"\n最终建议：{result_2}\n")
