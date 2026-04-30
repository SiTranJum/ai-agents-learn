"""
示例：第一个 LLM API 调用

这个示例展示如何调用 DeepSeek API（兼容 OpenAI 格式）
DeepSeek 使用 OpenAI 的 SDK，所以学会这套 API，以后切换到 GPT、通义千问等都是一样的用法。
"""

from openai import OpenAI

# ============================================================
# 第一步：创建客户端（类比 Java 的 new RestTemplate() 或 new HttpClient()）
# ============================================================
# OpenAI 类是 SDK 的入口，所有 API 调用都通过它发起
# 参数说明：
#   api_key  - 你的 API 密钥，用于身份认证（类比 Java 的 Authorization Header）
#   base_url - API 的基础地址，不同厂商地址不同：
#              DeepSeek: https://api.deepseek.com
#              OpenAI:   https://api.openai.com/v1
#              通义千问:  https://dashscope.aliyuncs.com/compatible-mode/v1
client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"
)

# ============================================================
# 第二步：调用 Chat Completions API（最核心的方法）
# ============================================================
# client.chat.completions.create() —— 发送对话请求，让 LLM 生成回复
# 这是你用得最多的方法，几乎所有对话场景都用它
#
# 类比 Java：
#   相当于调用一个 POST /v1/chat/completions 接口
#   SDK 帮你封装了 HTTP 请求、序列化、错误处理等
response = client.chat.completions.create(
    # model - 指定使用哪个模型（类比选择数据库实例）
    #   "deepseek-chat"     - DeepSeek 的通用对话模型
    #   "deepseek-reasoner" - DeepSeek 的推理模型（更强但更贵）
    #   "gpt-4o"            - 如果用 OpenAI 的话
    model="deepseek-chat",

    # messages - 对话历史，是一个列表（类比 Java 的 List<Message>）
    # 每条消息有两个字段：
    #   role    - 角色，三种取值：
    #             "system"    → 系统指令，设定 AI 的行为和角色（AI 不会回复这条）
    #             "user"      → 用户说的话
    #             "assistant" → AI 之前的回复（用于多轮对话时提供上下文）
    #   content - 消息内容，就是具体的文本
    messages=[
        {
            "role": "system",
            "content": "你是一个友好的助手。"
        },
        {
            "role": "user",
            "content": "请用一句话解释什么是 AI？"
        }
    ],

    # temperature - 控制输出随机性，范围 0~2
    #   0   → 每次输出几乎相同（适合提取数据、分类）
    #   0.7 → 平衡稳定性和创造性（通用场景推荐值）
    #   1.5 → 非常随机（适合创意写作）
    temperature=0.7,

    # max_tokens - 限制 AI 回复的最大 token 数
    #   注意：这只限制输出，不包括输入
    #   如果回复在 max_tokens 处被截断，finish_reason 会是 "length"
    max_tokens=100
)

# ============================================================
# 第三步：解析响应（类比 Java 解析 JSON Response）
# ============================================================
# response 的类型是 ChatCompletion，结构如下：
#
# ChatCompletion(
#   id="chatcmpl-xxx",           # 本次请求的唯一 ID
#   choices=[                     # 生成的回复列表（通常只有 1 个）
#     Choice(
#       index=0,
#       message=ChatCompletionMessage(
#         role="assistant",       # 固定是 "assistant"
#         content="AI 是..."      # ← 这就是 AI 的回复文本
#       ),
#       finish_reason="stop"      # 结束原因："stop"=正常结束，"length"=被截断
#     )
#   ],
#   usage=CompletionUsage(        # token 用量统计（关系到计费）
#     prompt_tokens=25,           # 输入消耗的 token 数
#     completion_tokens=18,       # 输出消耗的 token 数
#     total_tokens=43             # 总计
#   )
# )

# 取出 AI 的回复文本
# choices[0] → 第一个（通常唯一的）回复
# .message   → 消息对象
# .content   → 文本内容
answer = response.choices[0].message.content
print(f"AI 的回答：{answer}")

# 查看 token 用量（直接影响你的 API 费用）
print(f"\n输入 Token：{response.usage.prompt_tokens}")
print(f"输出 Token：{response.usage.completion_tokens}")
print(f"总计 Token：{response.usage.total_tokens}")

# 查看结束原因
print(f"结束原因：{response.choices[0].finish_reason}")
# "stop"   → 正常说完了
# "length" → 被 max_tokens 截断了，可能需要增大 max_tokens
