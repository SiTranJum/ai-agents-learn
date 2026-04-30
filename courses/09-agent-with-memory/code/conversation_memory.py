"""
短期记忆：对话历史管理

作用：
- 存储当前对话的历史记录（messages 列表）
- 控制历史长度，避免超出上下文窗口
- 提供添加消息、获取历史的接口
"""

class ConversationMemory:
    """
    短期记忆类：管理对话历史

    类比 Java：类似 HttpSession，存储会话期间的数据
    """

    def __init__(self, system_prompt: str, max_messages: int = 20):
        """
        初始化对话记忆

        参数：
        - system_prompt: 系统提示词，定义 Agent 的角色和行为
        - max_messages: 最多保留多少条消息（包括 system 消息）
                       默认 20 条，避免超出上下文窗口限制

        属性：
        - self.messages: 对话历史列表，格式为 [{"role": "...", "content": "..."}]
        - self.max_messages: 最大消息数量
        """
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]
        self.max_messages = max_messages

    def add_user_message(self, content: str):
        """
        添加用户消息到历史记录

        参数：
        - content: 用户输入的文本

        作用：
        - 将用户消息添加到 messages 列表
        - 自动触发历史修剪（如果超出长度限制）
        """
        self.messages.append({"role": "user", "content": content})
        self._trim_history()

    def add_assistant_message(self, content: str):
        """
        添加 AI 助手的回复消息到历史记录

        参数：
        - content: AI 回复的文本

        作用：
        - 将 AI 回复添加到 messages 列表
        - 自动触发历史修剪
        """
        self.messages.append({"role": "assistant", "content": content})
        self._trim_history()

    def add_tool_message(self, tool_call_id: str, content: str):
        """
        添加工具调用结果消息

        参数：
        - tool_call_id: 工具调用的 ID（由 LLM 生成）
        - content: 工具执行的结果

        作用：
        - 将工具调用结果添加到历史记录
        - 用于 Function Calling 的多轮对话
        """
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })
        self._trim_history()

    def get_messages(self) -> list:
        """
        获取完整的对话历史

        返回：
        - list: 对话历史列表，可直接传递给 LLM API 的 messages 参数

        用途：
        - 每次调用 LLM API 时，通过这个方法获取历史记录
        - 让 LLM 能够"记住"之前的对话内容
        """
        return self.messages

    def _trim_history(self):
        """
        修剪历史记录，保持在最大长度内

        策略：
        - 始终保留第一条消息（system prompt）
        - 删除最旧的消息，保留最近的消息
        - 确保总消息数不超过 max_messages

        为什么需要修剪：
        - LLM 的上下文窗口有限制（如 DeepSeek 是 64K tokens）
        - 消息太多会超出限制，导致 API 调用失败
        - 保留最近的消息，因为它们通常更相关
        """
        if len(self.messages) > self.max_messages:
            # 保留第一条（system）+ 最近的 (max_messages - 1) 条
            self.messages = [self.messages[0]] + self.messages[-(self.max_messages - 1):]

    def clear(self):
        """
        清空对话历史（保留 system prompt）

        用途：
        - 开始新的对话会话
        - 重置 Agent 状态
        """
        system_message = self.messages[0]
        self.messages = [system_message]

    def get_message_count(self) -> int:
        """
        获取当前消息数量

        返回：
        - int: 消息总数（包括 system 消息）
        """
        return len(self.messages)


# 使用示例
if __name__ == "__main__":
    # 创建短期记忆实例
    memory = ConversationMemory(
        system_prompt="你是一个健康管家 AI，帮助用户记录饮食和管理健康。",
        max_messages=10  # 最多保留 10 条消息
    )

    # 模拟对话
    print("=== 对话开始 ===\n")

    # 第一轮对话
    memory.add_user_message("我今天早上吃了两个鸡蛋")
    print(f"用户：我今天早上吃了两个鸡蛋")
    print(f"当前消息数：{memory.get_message_count()}\n")

    memory.add_assistant_message("好的，已记录：早餐 - 2 个鸡蛋，约 140 卡路里")
    print(f"AI：好的，已记录：早餐 - 2 个鸡蛋，约 140 卡路里")
    print(f"当前消息数：{memory.get_message_count()}\n")

    # 第二轮对话
    memory.add_user_message("我的早餐热量是多少？")
    print(f"用户：我的早餐热量是多少？")
    print(f"当前消息数：{memory.get_message_count()}\n")

    # 查看完整历史
    print("=== 完整对话历史 ===")
    for i, msg in enumerate(memory.get_messages()):
        print(f"{i+1}. [{msg['role']}] {msg['content'][:50]}...")

    # 测试历史修剪
    print("\n=== 测试历史修剪 ===")
    for i in range(10):
        memory.add_user_message(f"测试消息 {i}")

    print(f"添加 10 条消息后，当前消息数：{memory.get_message_count()}")
    print("（应该被修剪到 max_messages=10）")
