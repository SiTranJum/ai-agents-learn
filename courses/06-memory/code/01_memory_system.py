"""
课程 6：Memory（记忆系统）实现

展示三种记忆类型的实现：
1. 短期记忆：对话历史
2. 中期记忆：最近活动（模拟数据库）
3. 长期记忆：用户档案
"""

from openai import OpenAI
import json
import sys
import io
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = OpenAI(
    api_key="sk-ds-non",
    base_url="https://api.deepseek.com"
)


# ============================================
# 模拟数据库
# ============================================

# 用户档案（长期记忆）
USER_PROFILE = {
    "user_id": "user_001",
    "name": "张三",
    "height": 170,
    "weight": 75,
    "target_weight": 65,
    "goal": "减肥",
    "preferences": {
        "diet": ["清淡", "不吃辣"],
        "allergies": ["海鲜"],
        "exercise": ["跑步", "游泳"]
    }
}

# 最近饮食记录（中期记忆）
RECENT_MEALS = [
    {"date": "2026-03-31", "meal_type": "早餐", "food": "燕麦粥", "calories": 150},
    {"date": "2026-03-31", "meal_type": "午餐", "food": "鸡胸肉沙拉", "calories": 350},
    {"date": "2026-03-30", "meal_type": "早餐", "food": "鸡蛋三明治", "calories": 300},
    {"date": "2026-03-30", "meal_type": "午餐", "food": "红烧肉", "calories": 500},
    {"date": "2026-03-30", "meal_type": "晚餐", "food": "蔬菜面", "calories": 400},
]


# ============================================
# 记忆管理类
# ============================================
class MemoryManager:
    """
    记忆管理器

    管理三种类型的记忆：
    - 短期记忆：对话历史（messages）
    - 中期记忆：最近活动（数据库查询）
    - 长期记忆：用户档案（结构化存储）
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.messages = []  # 短期记忆：对话历史
        self.max_history = 20  # 最多保留 20 条消息

    # ========================================
    # 短期记忆：对话历史
    # ========================================
    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.messages.append({
            "role": role,
            "content": content
        })

        # 压缩历史（保留最近 N 条）
        if len(self.messages) > self.max_history:
            # 保留 system prompt（如果有）+ 最近 N 条
            system_messages = [m for m in self.messages if m["role"] == "system"]
            recent_messages = self.messages[-self.max_history:]
            self.messages = system_messages + recent_messages

    def get_short_term_memory(self) -> list:
        """获取短期记忆（对话历史）"""
        return self.messages.copy()

    # ========================================
    # 中期记忆：最近活动
    # ========================================
    def get_mid_term_memory(self, days: int = 7) -> list:
        """
        获取中期记忆（最近 N 天的活动）

        实际项目中，这里会查询数据库：
        SELECT * FROM meals WHERE user_id = ? AND date >= date('now', '-7 days')
        """
        # 模拟数据库查询
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        recent = [m for m in RECENT_MEALS if m["date"] >= cutoff_date]
        return recent

    # ========================================
    # 长期记忆：用户档案
    # ========================================
    def get_long_term_memory(self) -> dict:
        """
        获取长期记忆（用户档案）

        实际项目中，这里会查询数据库：
        SELECT * FROM user_profiles WHERE user_id = ?
        """
        return USER_PROFILE.copy()

    # ========================================
    # 记忆召回：根据上下文决定召回哪些记忆
    # ========================================
    def recall_memory(self, user_message: str) -> dict:
        """
        根据用户消息召回相关记忆

        返回：
            {
                "short_term": [...],  # 对话历史
                "mid_term": [...],    # 最近活动
                "long_term": {...}    # 用户档案
            }
        """
        memory = {}

        # 1. 短期记忆：总是包含
        memory["short_term"] = self.get_short_term_memory()

        # 2. 中期记忆：根据关键词判断是否需要
        keywords = ["最近", "这周", "今天", "昨天", "吃了什么"]
        if any(kw in user_message for kw in keywords):
            memory["mid_term"] = self.get_mid_term_memory(days=7)
        else:
            memory["mid_term"] = []

        # 3. 长期记忆：总是包含基本信息
        memory["long_term"] = self.get_long_term_memory()

        return memory

    # ========================================
    # 构建 System Prompt（注入记忆）
    # ========================================
    def build_system_prompt(self, memory: dict) -> str:
        """
        根据记忆构建 System Prompt
        """
        profile = memory["long_term"]

        prompt = f"""你是一个健康管家 AI Agent。

用户信息：
- 姓名：{profile['name']}
- 身高：{profile['height']}cm，体重：{profile['weight']}kg
- 目标：{profile['goal']}（目标体重 {profile['target_weight']}kg）
- 饮食偏好：{', '.join(profile['preferences']['diet'])}
- 过敏信息：{', '.join(profile['preferences']['allergies'])}
- 运动偏好：{', '.join(profile['preferences']['exercise'])}
"""

        # 如果有中期记忆，添加到 prompt
        if memory["mid_term"]:
            prompt += f"\n最近饮食记录：\n"
            for meal in memory["mid_term"]:
                prompt += f"- {meal['date']} {meal['meal_type']}：{meal['food']}（{meal['calories']}千卡）\n"

        prompt += "\n请基于用户的目标、偏好和历史记录，提供个性化的建议。"

        return prompt


# ============================================
# 带记忆的 Agent
# ============================================
class AgentWithMemory:
    """带记忆系统的 Agent"""

    def __init__(self, user_id: str):
        self.memory = MemoryManager(user_id)

    def chat(self, user_message: str) -> str:
        """
        与用户对话

        参数：
            user_message: 用户消息

        返回：
            Agent 的回复
        """
        print(f"\n{'='*60}")
        print(f"用户：{user_message}")
        print(f"{'='*60}\n")

        # 1. 召回相关记忆
        print("[记忆召回]")
        recalled_memory = self.memory.recall_memory(user_message)

        print(f"  短期记忆：{len(recalled_memory['short_term'])} 条对话")
        print(f"  中期记忆：{len(recalled_memory['mid_term'])} 条饮食记录")
        print(f"  长期记忆：用户档案已加载")

        # 2. 构建 System Prompt（注入记忆）
        system_prompt = self.memory.build_system_prompt(recalled_memory)

        # 3. 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # 添加对话历史（短期记忆）
        # 注意：跳过之前的 system prompt，只保留用户和助手的对话
        for msg in recalled_memory["short_term"]:
            if msg["role"] != "system":
                messages.append(msg)

        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})

        # 4. 调用 LLM
        print("\n[LLM 思考中...]\n", flush=True)  # flush=True 立即输出
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7
        )

        assistant_message = response.choices[0].message.content

        # 5. 更新短期记忆
        self.memory.add_message("user", user_message)
        self.memory.add_message("assistant", assistant_message)

        # 6. 返回回复
        print(f"{'='*60}")
        print(f"Agent：\n{assistant_message}")
        print(f"{'='*60}\n")

        return assistant_message


# ============================================
# 对比测试：有记忆 vs 无记忆
# ============================================
def test_with_memory():
    """测试带记忆的 Agent"""
    print("\n" + "="*60)
    print("测试：带记忆的 Agent")
    print("="*60)

    agent = AgentWithMemory("user_001")

    # 第 1 轮对话
    agent.chat("你好，我想了解一下我的健康目标")

    # 第 2 轮对话（Agent 应该记得第 1 轮说了什么）
    agent.chat("那我今天应该吃什么？")

    # 第 3 轮对话（测试中期记忆召回）
    agent.chat("我最近吃得怎么样？")


def test_without_memory():
    """测试无记忆的 Agent（每次都是新对话）"""
    print("\n" + "="*60)
    print("对比：无记忆的 Agent")
    print("="*60)

    # 每次都是新的对话，没有历史
    messages1 = [{"role": "user", "content": "你好，我想了解一下我的健康目标"}]
    response1 = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages1
    )
    print(f"\n第 1 轮：\n{response1.choices[0].message.content}\n")

    # 第 2 轮：Agent 不记得第 1 轮说了什么
    messages2 = [{"role": "user", "content": "那我今天应该吃什么？"}]
    response2 = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages2
    )
    print(f"\n第 2 轮（不记得之前的对话）：\n{response2.choices[0].message.content}\n")


# ============================================
# 运行测试
# ============================================
if __name__ == "__main__":
    # 测试带记忆的 Agent
    # test_with_memory()

    # 对比：无记忆的 Agent
    test_without_memory()
