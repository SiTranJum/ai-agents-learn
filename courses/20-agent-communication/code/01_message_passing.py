"""
示例 1：消息传递模式

Agent 之间通过消息队列通信，解耦发送者和接收者。
"""

from openai import OpenAI
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import json

client = OpenAI(
    api_key="sk-a4ae611c3f9c4df89a133e621b2b7851",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


# ============ 消息定义 ============

@dataclass
class Message:
    """
    Agent 之间传递的消息。

    类比 Java：类似 Spring Event 或 MQ 消息
    """
    from_agent: str      # 发送者
    to_agent: str        # 接收者（可以是 "*" 表示广播）
    msg_type: str        # 消息类型，用于接收者判断如何处理
    data: Any            # 消息内容
    timestamp: str       # 时间戳

    def to_dict(self) -> Dict:
        """转为字典，方便序列化"""
        return {
            "from": self.from_agent,
            "to": self.to_agent,
            "type": self.msg_type,
            "data": self.data,
            "timestamp": self.timestamp
        }


# ============ 消息总线 ============

class MessageBus:
    """
    消息总线：Agent 发消息到这里，其他 Agent 从这里取消息。

    类比 Java：类似 RabbitMQ / Kafka / Spring ApplicationEventPublisher
    """
    def __init__(self):
        # 消息队列：key 是 Agent 名称，value 是该 Agent 的消息列表
        # 类比 Java：Map<String, Queue<Message>>
        self.queues: Dict[str, List[Message]] = {}

    def send(self, message: Message):
        """
        发送消息到总线。

        参数：
            message: 要发送的消息
        """
        target = message.to_agent

        # 如果目标队列不存在，创建它
        if target not in self.queues:
            self.queues[target] = []

        self.queues[target].append(message)
        print(f"[消息总线] {message.from_agent} → {message.to_agent}: {message.msg_type}")

    def receive(self, agent_name: str) -> List[Message]:
        """
        接收发给某个 Agent 的所有消息。

        参数：
            agent_name: Agent 名称
        返回：
            消息列表（取出后清空队列）
        """
        if agent_name not in self.queues:
            return []

        messages = self.queues[agent_name]
        self.queues[agent_name] = []  # 取出后清空
        return messages


# ============ 基于消息的 Agent ============

def create_message_agent(name: str, system_prompt: str, bus: MessageBus):
    """
    创建一个基于消息通信的 Agent。

    参数：
        name: Agent 名称
        system_prompt: 系统提示词
        bus: 消息总线
    """
    def process_message(message: Message) -> Message:
        """
        处理一条消息，返回响应消息。

        参数：
            message: 收到的消息
        返回：
            响应消息
        """
        print(f"\n[{name}] 处理消息：{message.msg_type}")

        # 构造 LLM 输入：把消息内容转为文本
        if isinstance(message.data, dict):
            user_input = json.dumps(message.data, ensure_ascii=False)
        else:
            user_input = str(message.data)

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

        # 构造响应消息
        return Message(
            from_agent=name,
            to_agent=message.from_agent,  # 回复给发送者
            msg_type=f"{message.msg_type}_response",
            data=result,
            timestamp=datetime.now().isoformat()
        )

    def run():
        """
        Agent 的主循环：不断从消息总线取消息并处理。

        注意：这里简化为手动调用，实际系统中会是一个后台线程。
        """
        messages = bus.receive(name)
        responses = []

        for msg in messages:
            response = process_message(msg)
            responses.append(response)

        return responses

    run.name = name
    run.process_message = process_message  # 暴露出来，方便测试
    return run


# ============ 测试 ============

if __name__ == "__main__":
    # 创建消息总线
    bus = MessageBus()

    # 创建三个 Agent
    parse_agent = create_message_agent(
        name="parse_agent",
        system_prompt="你是饮食解析专家。提取食物名称和量，输出 JSON 格式。",
        bus=bus
    )

    nutrition_agent = create_message_agent(
        name="nutrition_agent",
        system_prompt="你是营养专家。根据食物信息返回营养数据，输出 JSON 格式。",
        bus=bus
    )

    advice_agent = create_message_agent(
        name="advice_agent",
        system_prompt="你是健康顾问。根据营养数据给出建议，2-3 句话。",
        bus=bus
    )

    print("=" * 60)
    print("测试：消息传递模式")
    print("=" * 60)

    # 第 1 步：发送初始消息给解析 Agent
    initial_msg = Message(
        from_agent="user",
        to_agent="parse_agent",
        msg_type="parse_food",
        data="我今天吃了一碗牛肉面",
        timestamp=datetime.now().isoformat()
    )
    bus.send(initial_msg)

    # 第 2 步：解析 Agent 处理消息
    parse_response = parse_agent.process_message(initial_msg)

    # 第 3 步：把解析结果发给营养 Agent
    nutrition_msg = Message(
        from_agent="parse_agent",
        to_agent="nutrition_agent",
        msg_type="get_nutrition",
        data=parse_response.data,
        timestamp=datetime.now().isoformat()
    )
    bus.send(nutrition_msg)

    # 第 4 步：营养 Agent 处理消息
    nutrition_response = nutrition_agent.process_message(nutrition_msg)

    # 第 5 步：把营养数据发给建议 Agent
    advice_msg = Message(
        from_agent="nutrition_agent",
        to_agent="advice_agent",
        msg_type="generate_advice",
        data=nutrition_response.data,
        timestamp=datetime.now().isoformat()
    )
    bus.send(advice_msg)

    # 第 6 步：建议 Agent 处理消息
    advice_response = advice_agent.process_message(advice_msg)

    print("\n" + "=" * 60)
    print(f"最终建议：{advice_response.data}")
    print("=" * 60)
