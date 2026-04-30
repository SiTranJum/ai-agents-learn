# 课程 6：Memory（记忆系统）

## 第一部分：为什么 Agent 需要记忆

### LLM 本身无记忆

还记得课程 1 讲的吗？**LLM 是无状态的**。

```python
# 第一次对话
response1 = client.chat.completions.create(
    messages=[{"role": "user", "content": "我叫张三"}]
)

# 第二次对话（LLM 不记得之前说了什么）
response2 = client.chat.completions.create(
    messages=[{"role": "user", "content": "我叫什么？"}]
)
# LLM 回答："抱歉，我不知道你的名字"
```

### 对话历史 ≠ 真正的记忆

你可能会说："我们可以把历史消息都传给 LLM 啊"

```python
messages = [
    {"role": "user", "content": "我叫张三"},
    {"role": "assistant", "content": "你好，张三！"},
    {"role": "user", "content": "我叫什么？"}
]
response = client.chat.completions.create(messages=messages)
# LLM 回答："你叫张三"
```

这确实能工作，但有问题：

**问题 1：上下文窗口有限**
```
对话 1 天后：messages 有 20 条，还能全部传入
对话 1 周后：messages 有 200 条，开始变慢
对话 1 月后：messages 有 1000 条，超出上下文窗口限制
```

**问题 2：成本高**
```
每次调用都传入全部历史 = 每次都付费处理所有 token
1000 条消息 × 每条 100 token = 每次调用 100,000 token
```

**问题 3：效率低**
```
LLM 需要重新阅读所有历史才能理解上下文
就像每次对话都要从头读一遍聊天记录
```

**问题 4：无法跨会话**
```
用户今天说："我在减肥"
用户明天打开 App，新会话开始
Agent 不记得用户在减肥
```

---

## 第二部分：三种记忆类型

### 类比人类记忆

```
短期记忆（工作记忆）：
- 你刚才说了什么
- 当前对话的上下文
- 类比：你记得刚才聊天说了什么

中期记忆（情景记忆）：
- 最近几天发生的事
- 最近的活动和行为
- 类比：你记得这周吃了什么

长期记忆（语义记忆）：
- 用户的基本信息
- 习惯和偏好
- 目标和计划
- 类比：你记得自己的名字、喜好、目标
```

### 在健康管家中的应用

#### 1. 短期记忆（当前对话）

```
用户："我今天中午吃了红烧肉"
Agent："好的，已记录。红烧肉热量较高..."

用户："那我晚上应该吃什么？"
Agent："考虑到你中午吃了红烧肉（高热量），晚上建议清淡些..."
         ↑ 记得刚才说的"红烧肉"
```

**实现方式**：对话历史（messages 列表）

#### 2. 中期记忆（最近活动）

```
用户："我这周吃得怎么样？"

Agent 需要记住：
- 周一：早餐燕麦，午餐鸡胸肉，晚餐沙拉
- 周二：早餐鸡蛋，午餐红烧肉，晚餐面条
- 周三：...
```

**实现方式**：数据库查询（最近 7 天的记录）

#### 3. 长期记忆（用户画像）

```
用户："给我推荐早餐"

Agent 需要记住：
- 用户目标：减肥，目标体重 65kg
- 饮食偏好：不吃辣、喜欢清淡
- 过敏信息：对海鲜过敏
- 作息习惯：早上 7 点起床
- 运动习惯：每周跑步 3 次
```

**实现方式**：结构化存储（用户档案表）

---

## 第三部分：记忆的存储方式

### 1. 短期记忆：对话历史

```python
class Agent:
    def __init__(self):
        self.messages = []  # 对话历史

    def chat(self, user_message: str):
        # 添加用户消息
        self.messages.append({
            "role": "user",
            "content": user_message
        })

        # 调用 LLM
        response = client.chat.completions.create(
            messages=self.messages  # 传入完整历史
        )

        # 添加 AI 回复
        self.messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content
        })
```

**优化：历史压缩**
```python
def compress_history(self, max_messages: int = 20):
    """保留最近 N 条消息"""
    if len(self.messages) > max_messages:
        # 保留 system prompt + 最近 N 条
        self.messages = [self.messages[0]] + self.messages[-max_messages:]
```

### 2. 中期记忆：数据库查询

```python
def get_recent_meals(days: int = 7) -> list:
    """查询最近 N 天的饮食记录"""
    # 从数据库查询
    query = """
        SELECT date, food, calories
        FROM meals
        WHERE user_id = ? AND date >= date('now', '-7 days')
        ORDER BY date DESC
    """
    return db.execute(query, user_id)
```

### 3. 长期记忆：结构化存储

```python
# 用户档案表
user_profile = {
    "user_id": "123",
    "name": "张三",
    "height": 170,
    "weight": 75,
    "target_weight": 65,
    "goal": "减肥",
    "preferences": {
        "diet": ["清淡", "不吃辣"],
        "allergies": ["海鲜"],
        "exercise": ["跑步", "游泳"]
    },
    "created_at": "2026-01-01",
    "updated_at": "2026-03-31"
}
```

---

## 第四部分：记忆召回机制

### 什么时候召回记忆？

```
用户："给我推荐早餐"

Agent 思考：
1. 需要知道用户的目标 → 召回长期记忆（用户档案）
2. 需要知道最近吃了什么 → 召回中期记忆（最近饮食）
3. 需要知道刚才聊了什么 → 召回短期记忆（对话历史）
```

### 召回策略

```python
def recall_memory(user_message: str) -> dict:
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
    memory["short_term"] = self.messages[-10:]  # 最近 10 条

    # 2. 中期记忆：根据关键词判断
    if "最近" in user_message or "这周" in user_message:
        memory["mid_term"] = get_recent_meals(days=7)

    # 3. 长期记忆：总是包含基本信息
    memory["long_term"] = get_user_profile()

    return memory
```

---

## 第五部分：记忆与 Prompt 的结合

### 将记忆注入 System Prompt

```python
def build_system_prompt(memory: dict) -> str:
    """
    根据记忆构建 System Prompt
    """
    profile = memory["long_term"]

    prompt = f"""你是一个健康管家 AI Agent。

用户信息：
- 姓名：{profile['name']}
- 目标：{profile['goal']}（目标体重 {profile['target_weight']}kg）
- 饮食偏好：{', '.join(profile['preferences']['diet'])}
- 过敏信息：{', '.join(profile['preferences']['allergies'])}

请基于用户的目标和偏好，提供个性化的建议。
"""

    return prompt
```

### 完整示例

```python
# 用户："给我推荐早餐"

# 1. 召回记忆
memory = recall_memory("给我推荐早餐")

# 2. 构建 System Prompt
system_prompt = build_system_prompt(memory)

# 3. 调用 LLM
messages = [
    {"role": "system", "content": system_prompt},
    *memory["short_term"],  # 对话历史
    {"role": "user", "content": "给我推荐早餐"}
]

response = client.chat.completions.create(messages=messages)
```

LLM 现在知道：
- 用户在减肥
- 用户喜欢清淡
- 用户对海鲜过敏
- 用户最近吃了什么

能给出个性化的建议。
