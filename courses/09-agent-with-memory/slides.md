# 课程 9：给 Agent 加上记忆能力

---

## 一、为什么 Agent 需要记忆？

### 1.1 没有记忆的 Agent 有什么问题？

回顾课程 8 的 Agent，每次对话都是"全新的"：

```python
# 第一轮对话
用户：我今天早上吃了两个鸡蛋
Agent：好的，记录了早餐：2 个鸡蛋，约 140 卡路里

# 第二轮对话（新的 API 调用）
用户：我的早餐热量是多少？
Agent：抱歉，我不知道你今天吃了什么早餐  # ❌ 忘记了！
```

**问题根源**：每次调用 LLM API 时，都是独立的请求，LLM 不会自动记住之前的对话。

### 1.2 记忆的两种类型

| 类型 | 作用范围 | 存储位置 | 生命周期 | 例子 |
|------|---------|---------|---------|------|
| **短期记忆** | 当前对话 | 内存（对话历史） | 本次会话 | "我刚才说的早餐" |
| **长期记忆** | 跨会话 | 持久化存储 | 永久 | "用户的身高体重目标" |

**类比 Java**：
- 短期记忆 = 方法内的局部变量（方法结束就消失）
- 长期记忆 = 数据库中的数据（持久化保存）

### 1.3 健康管家需要记住什么？

**短期记忆（对话历史）**：
- 用户刚才记录的饮食
- 用户刚才问的问题
- Agent 刚才给的建议

**长期记忆（用户档案）**：
- 用户基本信息：身高、体重、年龄、性别
- 用户目标：减肥、增肌、保持
- 用户偏好：不吃辣、素食、过敏食物
- 历史数据：过去的饮食记录、体重变化

---

## 二、短期记忆：对话历史管理

### 2.1 对话历史的结构

LLM API 的 `messages` 参数就是短期记忆：

```python
messages = [
    {"role": "system", "content": "你是健康管家 AI"},
    {"role": "user", "content": "我今天早上吃了两个鸡蛋"},
    {"role": "assistant", "content": "好的，记录了早餐：2 个鸡蛋，约 140 卡路里"},
    {"role": "user", "content": "我的早餐热量是多少？"},  # 新问题
]
```

**关键**：每次调用 API 时，把之前的对话历史都带上，LLM 就能"记住"之前的内容。

### 2.2 对话历史管理类

```python
class ConversationMemory:
    """
    短期记忆：管理当前对话的历史记录
    
    作用：
    - 存储对话历史（messages 列表）
    - 添加新消息
    - 获取完整历史（用于 API 调用）
    - 控制历史长度（避免超出上下文窗口）
    """
    
    def __init__(self, system_prompt: str, max_messages: int = 20):
        """
        初始化对话记忆
        
        参数：
        - system_prompt: 系统提示词（定义 Agent 角色）
        - max_messages: 最多保留多少条消息（避免超出上下文限制）
        """
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]
        self.max_messages = max_messages
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.messages.append({"role": "user", "content": content})
        self._trim_history()  # 控制历史长度
    
    def add_assistant_message(self, content: str):
        """添加 AI 回复消息"""
        self.messages.append({"role": "assistant", "content": content})
        self._trim_history()
    
    def get_messages(self) -> list:
        """获取完整对话历史（用于 API 调用）"""
        return self.messages
    
    def _trim_history(self):
        """
        修剪历史记录，保持在最大长度内
        
        策略：保留 system 消息 + 最近的 N 条消息
        """
        if len(self.messages) > self.max_messages:
            # 保留第一条（system）+ 最近的消息
            self.messages = [self.messages[0]] + self.messages[-(self.max_messages-1):]
```

**Java 类比**：
- `ConversationMemory` 类似 `HttpSession`（存储会话数据）
- `messages` 列表类似 `List<Message>`
- `_trim_history()` 类似 LRU 缓存的淘汰策略

### 2.3 上下文窗口限制

**问题**：LLM 的上下文窗口有限制（如 DeepSeek 是 64K tokens）

**解决方案**：
1. **限制消息数量**：只保留最近 N 条消息
2. **消息压缩**：用 LLM 总结历史对话（高级技巧）
3. **重要信息提取**：把关键信息存入长期记忆

---

## 三、长期记忆：持久化存储

### 3.1 什么需要长期记忆？

**用户档案**：
- 基本信息：身高、体重、年龄、性别
- 目标：减肥目标、目标体重、目标日期
- 偏好：饮食偏好、运动习惯

**历史数据**：
- 饮食记录：日期、食物、热量
- 体重记录：日期、体重、BMI
- 运动记录：日期、类型、时长

### 3.2 简单的持久化方案：JSON 文件

在课程 9，我们先用最简单的方案：**JSON 文件存储**。

```python
import json
from pathlib import Path
from datetime import datetime

class LongTermMemory:
    """
    长期记忆：持久化存储用户数据
    
    作用：
    - 存储用户档案（基本信息、目标、偏好）
    - 存储历史数据（饮食记录、体重记录）
    - 跨会话保持数据
    """
    
    def __init__(self, user_id: str, storage_dir: str = "./data"):
        """
        初始化长期记忆
        
        参数：
        - user_id: 用户 ID（用于区分不同用户）
        - storage_dir: 数据存储目录
        """
        self.user_id = user_id
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)  # 创建目录（如果不存在）
        
        # 用户数据文件路径
        self.profile_file = self.storage_dir / f"{user_id}_profile.json"
        self.history_file = self.storage_dir / f"{user_id}_history.json"
        
        # 加载数据
        self.profile = self._load_json(self.profile_file, default={})
        self.history = self._load_json(self.history_file, default=[])
    
    def _load_json(self, file_path: Path, default):
        """
        从 JSON 文件加载数据
        
        参数：
        - file_path: 文件路径
        - default: 文件不存在时的默认值
        
        返回：加载的数据
        """
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    
    def _save_json(self, file_path: Path, data):
        """保存数据到 JSON 文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def update_profile(self, **kwargs):
        """
        更新用户档案
        
        示例：
        memory.update_profile(height=170, weight=70, goal="减肥")
        """
        self.profile.update(kwargs)
        self._save_json(self.profile_file, self.profile)
    
    def get_profile(self) -> dict:
        """获取用户档案"""
        return self.profile
    
    def add_record(self, record_type: str, data: dict):
        """
        添加历史记录
        
        参数：
        - record_type: 记录类型（"meal", "weight", "exercise"）
        - data: 记录数据
        """
        record = {
            "type": record_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.history.append(record)
        self._save_json(self.history_file, self.history)
    
    def get_recent_records(self, record_type: str = None, limit: int = 10) -> list:
        """
        获取最近的记录
        
        参数：
        - record_type: 记录类型（None 表示所有类型）
        - limit: 返回数量
        """
        records = self.history
        if record_type:
            records = [r for r in records if r["type"] == record_type]
        return records[-limit:]  # 返回最近的 N 条
```

**Java 类比**：
- `LongTermMemory` 类似 DAO 层（数据访问对象）
- `_load_json` / `_save_json` 类似 JDBC 的 `select` / `insert`
- JSON 文件类似简单的数据库表

### 3.3 为什么不直接用数据库？

**现阶段用 JSON 文件的原因**：
1. **简单**：不需要安装数据库
2. **学习重点**：理解记忆系统的逻辑，而不是数据库操作
3. **够用**：单用户场景下，JSON 文件完全够用

**后续会升级**：
- 课程 16：引入向量数据库（Milvus）
- 课程 28：引入关系型数据库（Supabase）

---

## 四、整合记忆系统到 Agent

### 4.1 Agent 架构调整

```
原来的 Agent（课程 8）：
┌─────────────┐
│   Agent     │
│  - tools    │  ← 只有工具
│  - run()    │
└─────────────┘

加上记忆的 Agent（课程 9）：
┌──────────────────────┐
│       Agent          │
│  - tools             │
│  - short_memory      │  ← 短期记忆
│  - long_memory       │  ← 长期记忆
│  - run()             │
└──────────────────────┘
```

### 4.2 记忆召回的时机

**短期记忆**：
- 每次调用 LLM 时，自动带上对话历史

**长期记忆**：
- Agent 启动时，加载用户档案
- 用户提问时，检索相关历史数据
- 用户记录数据时，保存到长期记忆

### 4.3 完整代码示例

见 `code/agent_with_memory.py`

---

## 五、记忆系统的优化方向

### 5.1 记忆的优先级

不是所有信息都同等重要：
- **高优先级**：用户目标、过敏信息、重要偏好
- **中优先级**：最近的饮食记录、体重变化
- **低优先级**：很久以前的对话、不重要的闲聊

### 5.2 记忆的遗忘机制

人类会遗忘，Agent 也应该：
- **时间衰减**：越久远的记忆，权重越低
- **重要性过滤**：不重要的信息可以删除
- **容量限制**：存储空间有限，需要淘汰旧数据

### 5.3 向量检索（预告）

当前的长期记忆是"全量加载"，效率低。

**更好的方案**：向量检索
- 把记忆转换成向量（Embedding）
- 根据当前对话，检索最相关的记忆
- 只加载相关记忆，节省上下文

**课程 16 会深入讲解**。

---

## 六、小结

### 6.1 关键概念

1. **短期记忆 = 对话历史**：通过 `messages` 参数传递给 LLM
2. **长期记忆 = 持久化存储**：用户档案 + 历史数据
3. **记忆召回**：在合适的时机，把记忆加载到上下文中

### 6.2 实现要点

1. **ConversationMemory**：管理对话历史，控制长度
2. **LongTermMemory**：持久化存储，JSON 文件方案
3. **整合到 Agent**：在 `run()` 方法中使用记忆

### 6.3 下一步

- 课程 10：基础阶段总复习
- 课程 16：向量数据库与高级记忆检索
