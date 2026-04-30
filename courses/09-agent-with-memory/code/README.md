# 课程 9：给 Agent 加上记忆能力 - 代码说明

## 文件结构

```
code/
├── conversation_memory.py    # 短期记忆（对话历史管理）
├── long_term_memory.py       # 长期记忆（持久化存储）
├── agent_with_memory.py      # 完整的带记忆的 Agent
├── exercise.py               # 练习和测试
└── README.md                 # 本文件
```

## 运行前准备

### 1. 设置 API Key

```bash
# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="your-api-key"

# Windows (CMD)
set DEEPSEEK_API_KEY=your-api-key

# Linux/Mac
export DEEPSEEK_API_KEY="your-api-key"
```

### 2. 安装依赖

```bash
pip install openai
```

## 运行示例

### 1. 测试短期记忆

```bash
python conversation_memory.py
```

**预期输出**：
- 显示对话历史的添加过程
- 显示历史修剪的效果

### 2. 测试长期记忆

```bash
python long_term_memory.py
```

**预期输出**：
- 创建用户档案
- 添加饮食记录
- 查询历史记录
- 生成 `data/` 目录和 JSON 文件

### 3. 运行完整 Agent

```bash
python agent_with_memory.py
```

**测试对话**：
```
你：我今天早上吃了两个鸡蛋
AI：好的，已记录：早餐 - 鸡蛋 2个，140 卡路里

你：我的早餐热量是多少？
AI：您的早餐摄入了 140 卡路里（2 个鸡蛋）

你：我今天总共吃了什么？
AI：今天您吃了：早餐 - 鸡蛋 2个，总计 140 卡路里
```

### 4. 运行练习

```bash
python exercise.py
```

**测试内容**：
- 测试 1：短期记忆（对话历史）
- 测试 2：长期记忆（持久化存储）
- 测试 3：记忆召回（汇总统计）

## 代码说明

### ConversationMemory（短期记忆）

**核心方法**：
- `add_user_message(content)`: 添加用户消息
- `add_assistant_message(content)`: 添加 AI 回复
- `get_messages()`: 获取完整对话历史
- `_trim_history()`: 修剪历史，保持在最大长度内

**关键点**：
- 对话历史存储在 `messages` 列表中
- 每次调用 LLM 时，通过 `get_messages()` 获取历史
- 自动修剪历史，避免超出上下文窗口

### LongTermMemory（长期记忆）

**核心方法**：
- `update_profile(**kwargs)`: 更新用户档案
- `get_profile()`: 获取用户档案
- `add_record(type, data)`: 添加历史记录
- `get_recent_records(type, limit)`: 获取最近的记录
- `get_records_by_date(date, type)`: 获取指定日期的记录

**关键点**：
- 数据存储在 JSON 文件中（`data/` 目录）
- 用户档案和历史记录分开存储
- 支持按类型、日期查询记录

### HealthAgent（带记忆的 Agent）

**组件**：
- `client`: DeepSeek API 客户端
- `short_memory`: 短期记忆（ConversationMemory）
- `long_memory`: 长期记忆（LongTermMemory）
- `tools`: 工具集（Function Calling）

**核心流程**：
1. 用户输入 → 添加到短期记忆
2. 调用 LLM（带上对话历史）
3. 如果 LLM 调用工具 → 执行工具 → 保存到长期记忆
4. 返回 LLM 回复 → 添加到短期记忆

## 数据文件

运行后会在 `data/` 目录生成：

```
data/
├── user_001_profile.json    # 用户档案
└── user_001_history.json    # 历史记录
```

**profile.json 示例**：
```json
{
  "name": "张三",
  "height": 175,
  "weight": 70,
  "goal": "减肥"
}
```

**history.json 示例**：
```json
[
  {
    "type": "meal",
    "timestamp": "2024-03-27T08:30:00",
    "data": {
      "meal_time": "早餐",
      "food": "鸡蛋",
      "amount": 2,
      "unit": "个",
      "calories": 140
    }
  }
]
```

## 扩展练习

### 练习 1：添加用户偏好记忆

**任务**：
- 在 `LongTermMemory` 中添加 `add_preference()` 方法
- 在 `HealthAgent` 的 system_prompt 中加载偏好
- 测试 Agent 是否能根据偏好给出建议

**提示**：
```python
# 在 LongTermMemory 中
def add_preference(self, preference: str):
    if "preferences" not in self.profile:
        self.profile["preferences"] = []
    self.profile["preferences"].append(preference)
    self._save_json(self.profile_file, self.profile)
```

### 练习 2：实现记忆搜索

**任务**：
- 在 `LongTermMemory` 中添加 `search_records()` 方法
- 支持按关键词搜索历史记录

**提示**：
```python
def search_records(self, keyword: str) -> list:
    results = []
    for record in self.history:
        # 在 data 中搜索关键词
        if keyword in str(record["data"]):
            results.append(record)
    return results
```

### 练习 3：实现记忆压缩

**任务**：
- 当对话历史太长时，用 LLM 总结历史对话
- 将总结结果存入长期记忆

**提示**：
```python
# 在 ConversationMemory 中
def summarize(self, client, model):
    # 构建总结提示
    prompt = "请总结以下对话的关键信息：\n\n"
    for msg in self.messages[1:]:  # 跳过 system
        prompt += f"{msg['role']}: {msg['content']}\n"
    
    # 调用 LLM 生成总结
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content
```

## 常见问题

### Q1: 为什么要分短期记忆和长期记忆？

**A**: 
- **短期记忆**：当前对话的上下文，存储在内存中，会话结束就消失
- **长期记忆**：跨会话的持久化数据，存储在文件/数据库中，永久保存

类比：短期记忆 = 工作记忆（你正在思考的内容），长期记忆 = 知识库（你学过的知识）

### Q2: 为什么用 JSON 文件而不是数据库？

**A**: 
- 学习阶段，重点是理解记忆系统的逻辑，而不是数据库操作
- JSON 文件简单、直观、易于调试
- 后续课程会升级到数据库（Supabase + Milvus）

### Q3: 如何处理上下文窗口限制？

**A**: 
- **限制消息数量**：只保留最近 N 条消息（`max_messages`）
- **消息压缩**：用 LLM 总结历史对话（练习 3）
- **重要信息提取**：把关键信息存入长期记忆

### Q4: 记忆系统的性能如何优化？

**A**: 
- **向量检索**：用 Embedding + 向量数据库检索相关记忆（课程 16）
- **记忆分层**：高频记忆（热数据）+ 低频记忆（冷数据）
- **记忆遗忘**：时间衰减、重要性过滤

## 下一步

完成本课程后，你应该：
1. 理解短期记忆和长期记忆的区别
2. 掌握对话历史管理的方法
3. 掌握持久化存储的基础实现
4. 能够将记忆系统整合到 Agent 中

**下一课**：课程 10 - 基础阶段总复习
