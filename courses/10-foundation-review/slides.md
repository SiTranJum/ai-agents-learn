# 课程 10：基础阶段总复习

---

## 一、知识体系回顾

### 1.1 课程 1：LLM 基础

**核心概念**：

| 概念 | 说明 | 关键点 |
|------|------|--------|
| **Token** | LLM 处理文本的最小单位 | 1 token ≈ 0.75 个英文单词，中文 1 字 ≈ 1-2 tokens |
| **Temperature** | 控制输出的随机性 | 0 = 确定性，1 = 创造性，默认 0.7 |
| **上下文窗口** | LLM 能"看到"的文本长度 | DeepSeek: 64K tokens |
| **System Prompt** | 定义 AI 的角色和行为 | 全局指令，影响所有回复 |
| **多轮对话** | 通过 messages 数组实现 | 每次调用带上历史记录 |

**关键代码**：
```python
from openai import OpenAI

client = OpenAI(
    api_key="your-key",
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是健康管家"},
        {"role": "user", "content": "我今天吃了什么？"}
    ],
    temperature=0.7
)
```

**Java 类比**：
- `OpenAI` 客户端 = `RestTemplate`（HTTP 客户端）
- `messages` = `List<Message>`
- `response` = `ResponseEntity<ChatResponse>`

---

### 1.2 课程 2：Prompt Engineering

**五大原则**：

1. **清晰具体**：明确任务，避免模糊
   ```
   ❌ "帮我分析一下"
   ✅ "分析这段代码的时间复杂度，并给出优化建议"
   ```

2. **提供上下文**：给足背景信息
   ```
   ❌ "这个 bug 怎么修？"
   ✅ "Spring Boot 项目，用户登录时报 NullPointerException，
       堆栈信息：[...]，相关代码：[...]"
   ```

3. **指定输出格式**：结构化输出
   ```
   ✅ "以 JSON 格式返回，包含 food、calories、protein 字段"
   ```

4. **Few-shot 示例**：给出示例
   ```
   示例 1：输入 "鸡蛋 2 个" → 输出 {"food": "鸡蛋", "amount": 2}
   示例 2：输入 "一碗米饭" → 输出 {"food": "米饭", "amount": 1}
   ```

5. **Chain of Thought**：引导思考过程
   ```
   ✅ "请一步步分析：1) 识别食物 2) 估算份量 3) 计算热量"
   ```

**Prompt 组成**：
```
System Prompt（角色定义）
  + User Prompt（具体任务）
  + Context（上下文信息）
  + Examples（示例）
  + Output Format（输出格式）
  = 高质量 Prompt
```

---

### 1.3 课程 3：Tool Use（Function Calling）

**核心流程**：

```
1. 定义工具（JSON Schema）
   ↓
2. 用户输入 → LLM 判断是否需要调用工具
   ↓
3. LLM 返回 tool_calls（工具名 + 参数）
   ↓
4. 执行工具，获取结果
   ↓
5. 将结果返回给 LLM
   ↓
6. LLM 生成最终回复
```

**工具定义示例**：
```python
{
    "type": "function",
    "function": {
        "name": "record_meal",
        "description": "记录用户的饮食",
        "parameters": {
            "type": "object",
            "properties": {
                "food": {"type": "string", "description": "食物名称"},
                "amount": {"type": "number", "description": "数量"},
                "calories": {"type": "number", "description": "热量"}
            },
            "required": ["food", "amount", "calories"]
        }
    }
}
```

**关键点**：
- 工具定义要清晰：`description` 决定 LLM 是否调用
- 参数类型要准确：`type`、`required` 要正确
- 多轮对话：工具结果要加入 messages 历史

**Java 类比**：
- 工具定义 = 接口定义（`@FunctionalInterface`）
- 工具调用 = 反射调用（`Method.invoke()`）
- `tool_calls` = 方法调用列表

---

### 1.4 课程 4：什么是 Agent？

**Agent vs 普通 LLM 调用**：

| 维度 | 普通 LLM 调用 | Agent |
|------|--------------|-------|
| **交互方式** | 一问一答 | 自主循环 |
| **能力** | 只能回答 | 能调用工具、执行任务 |
| **记忆** | 无记忆（除非手动传历史） | 有记忆系统 |
| **规划** | 无规划能力 | 能拆解复杂任务 |
| **自主性** | 被动响应 | 主动行动 |

**Agent 的核心特征**：
1. **自主性**：能自己决定下一步做什么
2. **工具使用**：能调用外部工具完成任务
3. **记忆能力**：能记住历史信息
4. **规划能力**：能拆解复杂任务

**类比**：
- 普通 LLM = 咨询顾问（只给建议）
- Agent = 执行助理（能帮你做事）

---

### 1.5 课程 5：Agent Loop（核心循环）

**Agent 循环**：

```
┌─────────────────────────────────┐
│   1. 感知（Perception）          │
│   - 接收用户输入                 │
│   - 读取环境状态                 │
└──────────┬──────────────────────┘
           ↓
┌─────────────────────────────────┐
│   2. 思考（Reasoning）           │
│   - 理解任务                     │
│   - 制定计划                     │
│   - 决定行动                     │
└──────────┬──────────────────────┘
           ↓
┌─────────────────────────────────┐
│   3. 行动（Action）              │
│   - 调用工具                     │
│   - 执行任务                     │
│   - 返回结果                     │
└──────────┬──────────────────────┘
           ↓
┌─────────────────────────────────┐
│   4. 更新记忆                    │
│   - 保存结果                     │
│   - 更新状态                     │
└──────────┬──────────────────────┘
           ↓
        是否完成？
         ↓ 否
    回到步骤 1
```

**Java 类比**：
- Agent Loop = Spring MVC 的请求处理流程
  - 感知 = `DispatcherServlet` 接收请求
  - 思考 = `Controller` 处理逻辑
  - 行动 = `Service` 执行业务
  - 更新 = 更新数据库

---

### 1.6 课程 6：Memory（记忆系统）

**三种记忆类型**：

| 类型 | 作用范围 | 存储位置 | 生命周期 | 例子 |
|------|---------|---------|---------|------|
| **短期记忆** | 当前对话 | 内存（messages） | 本次会话 | "我刚才说的早餐" |
| **中期记忆** | 最近几天 | 内存/缓存 | 几天 | "这周的饮食记录" |
| **长期记忆** | 跨会话 | 数据库 | 永久 | "用户的身高体重目标" |

**实现方式**：
- **短期记忆**：`messages` 数组（对话历史）
- **中期记忆**：内存缓存 + 定期清理
- **长期记忆**：JSON 文件 / 数据库

**记忆召回**：
- 短期记忆：每次调用 LLM 时自动带上
- 长期记忆：根据当前对话，检索相关记忆

**Java 类比**：
- 短期记忆 = `HttpSession`（会话数据）
- 中期记忆 = `Redis`（缓存）
- 长期记忆 = `MySQL`（持久化）

---

### 1.7 课程 7：Planning（规划能力）

**为什么需要规划？**

复杂任务需要拆解：
```
任务："帮我制定一个减肥计划"

拆解：
1. 了解用户基本信息（身高、体重、目标）
2. 计算 BMI 和目标体重
3. 制定饮食方案（每日热量、营养配比）
4. 制定运动方案（类型、频率、时长）
5. 生成完整计划文档
```

**规划策略**：

1. **ReAct 模式**：推理 + 行动交替
   ```
   Thought: 我需要先了解用户的基本信息
   Action: 询问用户身高、体重、目标
   Observation: 用户回复了信息
   Thought: 现在可以计算 BMI 了
   Action: 调用 calculate_bmi 工具
   ...
   ```

2. **Chain of Thought**：展示思考过程
   ```
   让我一步步分析：
   1. 首先，用户的 BMI = 70 / (1.75^2) = 22.9（正常范围）
   2. 目标体重 65kg，需要减 5kg
   3. 每减 1kg 需要消耗 7700 卡路里
   4. 因此总共需要消耗 38500 卡路里
   5. 如果每天减少 500 卡路里，需要 77 天
   ```

3. **分步执行**：拆解成子任务
   ```python
   plan = [
       {"step": 1, "action": "get_user_info"},
       {"step": 2, "action": "calculate_bmi"},
       {"step": 3, "action": "create_diet_plan"},
       {"step": 4, "action": "create_exercise_plan"},
       {"step": 5, "action": "generate_report"}
   ]
   ```

---

### 1.8 课程 8：构建完整 Agent

**Agent 架构**：

```python
class HealthAgent:
    def __init__(self):
        self.client = OpenAI(...)        # LLM 客户端
        self.memory = Memory(...)        # 记忆系统
        self.tools = [...]               # 工具集
        self.planner = Planner(...)      # 规划器
    
    def run(self, user_input):
        # 1. 感知：接收输入
        # 2. 思考：调用 LLM，决定行动
        # 3. 行动：执行工具
        # 4. 更新：保存记忆
        # 5. 循环：直到任务完成
```

**组件整合**：
- **LLM**：大脑（思考和决策）
- **Memory**：记忆（上下文和历史）
- **Tools**：手脚（执行任务）
- **Planner**：规划（拆解复杂任务）

---

## 二、知识图谱

```
AI Agent 知识体系
│
├─ 基础层：LLM
│   ├─ Token、Temperature、上下文窗口
│   ├─ OpenAI SDK 使用
│   └─ 多轮对话实现
│
├─ 交互层：Prompt Engineering
│   ├─ 五大原则（清晰、上下文、格式、示例、CoT）
│   └─ System Prompt + User Prompt
│
├─ 能力层：Tool Use
│   ├─ Function Calling 原理
│   ├─ 工具定义（JSON Schema）
│   └─ 多轮调用流程
│
└─ Agent 层：自主智能体
    ├─ Agent Loop（感知 → 思考 → 行动）
    ├─ Memory（短期、中期、长期）
    ├─ Planning（ReAct、CoT、分步执行）
    └─ 完整实现（整合所有组件）
```

**学习路径**：
```
LLM 基础 → Prompt → Tool Use → Agent 概念 → Agent Loop → Memory → Planning → 完整 Agent
```

---

## 三、关键要点总结

### 3.1 LLM 使用要点

1. **Temperature 选择**：
   - 事实性任务（数据分析、代码生成）：0-0.3
   - 创造性任务（写作、头脑风暴）：0.7-1.0

2. **上下文管理**：
   - 控制 messages 长度，避免超出窗口
   - 重要信息放在前面（System Prompt）
   - 最近的对话更重要

3. **多轮对话**：
   - 每次调用带上完整历史
   - 工具调用结果也要加入历史

### 3.2 Prompt 编写要点

1. **角色定义要清晰**：
   ```
   ✅ "你是一个专业的健康管家 AI，擅长饮食分析和健康建议"
   ❌ "你是一个 AI"
   ```

2. **任务描述要具体**：
   ```
   ✅ "分析用户今天的饮食，计算总热量，判断是否超标，给出改进建议"
   ❌ "分析饮食"
   ```

3. **输出格式要明确**：
   ```
   ✅ "以 JSON 格式返回：{food, amount, calories}"
   ❌ "返回食物信息"
   ```

### 3.3 Tool Use 要点

1. **工具定义要准确**：
   - `description` 决定 LLM 是否调用
   - `parameters` 决定调用是否成功

2. **工具粒度要合适**：
   - 太细：LLM 需要多次调用，效率低
   - 太粗：参数复杂，LLM 难以正确调用

3. **错误处理要完善**：
   - 工具执行失败时，返回清晰的错误信息
   - LLM 会根据错误信息重试或调整策略

### 3.4 Agent 设计要点

1. **循环控制**：
   - 设置最大迭代次数，避免死循环
   - 明确终止条件

2. **记忆管理**：
   - 短期记忆：自动管理，控制长度
   - 长期记忆：按需加载，避免浪费上下文

3. **规划策略**：
   - 简单任务：直接执行
   - 复杂任务：先规划，再执行

---

## 四、常见误区

### 误区 1：Temperature 越高越好
❌ **错误**：认为 Temperature 高能让 AI 更"聪明"  
✅ **正确**：Temperature 控制随机性，不是智能程度。事实性任务用低 Temperature。

### 误区 2：Prompt 越长越好
❌ **错误**：写很长的 Prompt，堆砌各种指令  
✅ **正确**：Prompt 要清晰简洁，重点突出。过长的 Prompt 反而会稀释关键信息。

### 误区 3：工具越多越好
❌ **错误**：定义很多工具，让 LLM 选择  
✅ **正确**：工具要精简，每个工具职责明确。工具太多会增加 LLM 的选择难度。

### 误区 4：Agent 能解决所有问题
❌ **错误**：认为 Agent 是万能的  
✅ **正确**：Agent 有能力边界，复杂推理、精确计算、实时性要求高的任务不适合。

### 误区 5：记忆越多越好
❌ **错误**：把所有历史数据都加载到上下文  
✅ **正确**：记忆要按需加载，只加载相关的记忆。过多记忆会浪费上下文窗口。

---

## 五、下一步学习

完成基础阶段后，你已经掌握：
- ✅ LLM 的基本使用
- ✅ Prompt 编写技巧
- ✅ Tool Use 实现
- ✅ Agent 的核心概念和实现

**阶段三：进阶能力课程**

接下来将学习：
1. **高级 Agent 模式**：ReAct、CoT、Multi-Step
2. **RAG**：检索增强生成，让 Agent 拥有外部知识
3. **Multi-Agent**：多个 Agent 协作
4. **框架选型**：LangChain、CrewAI 等

**阶段四：健康管家项目实战**

综合运用所学，完成完整的健康管家产品。

---

准备好了吗？接下来进入**小测验**环节！
