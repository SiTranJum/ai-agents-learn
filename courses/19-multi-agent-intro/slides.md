# 课程 19：Multi-Agent 入门 — 为什么需要多个 Agent？

---

## 第一部分：单 Agent 的天花板

### 1.1 回顾：我们做过的 Agent

课程 8 做了一个健康管家 Agent，它能：
- 记录饮食
- 查询营养
- 制定计划
- 生成周报

**一个 Agent 干所有事情。** 这在功能简单时没问题。

### 1.2 问题来了

想象健康管家上线后，用户说：

```
"我今天早上吃了一碗牛肉面，中午吃了沙拉，
 下午跑了 5 公里，晚上睡了 6 小时。
 帮我分析一下今天的整体健康状况。"
```

一个 Agent 要做什么？

```
1. 解析饮食信息（牛肉面、沙拉）
2. 查询营养数据库
3. 计算总热量和营养素
4. 分析运动消耗
5. 评估睡眠质量
6. 综合所有信息给出建议
```

### 1.3 单 Agent 的三个瓶颈

```
瓶颈 1：Prompt 膨胀
  一个 System Prompt 要塞进所有领域知识
  → 饮食知识 + 运动知识 + 睡眠知识 + 心理知识...
  → Prompt 越长，LLM 注意力越分散，效果越差

瓶颈 2：工具爆炸
  一个 Agent 挂载所有工具
  → 查食物、算热量、查运动、算消耗、查睡眠标准...
  → 工具越多，LLM 选错工具的概率越大

瓶颈 3：串行瓶颈
  所有任务排队执行
  → 查营养要等，算运动要等，评估睡眠要等
  → 用户等半天才拿到结果
```

**类比 Java 开发**：这就像一个 God Class，什么都干，几千行代码。你一定重构过这种类 —— 拆成多个 Service，各司其职。Multi-Agent 就是 Agent 世界的微服务拆分。

---

## 第二部分：Multi-Agent 的核心思想

### 2.1 一句话总结

```
Multi-Agent = 多个专精 Agent + 协作机制
```

每个 Agent：
- 有自己的 System Prompt（专注一个领域）
- 有自己的工具集（只挂载需要的工具）
- 有自己的职责边界（只做自己擅长的事）

### 2.2 和微服务的对比

```
微服务世界                    Multi-Agent 世界
─────────────────────────────────────────────
Service                       Agent
API 接口                      Agent 的输入/输出格式
服务注册/发现                  Agent 注册表
API Gateway / 路由             Router Agent / Orchestrator
HTTP/gRPC 调用                 Agent 之间传递消息
服务编排                       Agent 编排
```

你做过微服务，这套思路你很熟。区别在于：Agent 之间传递的不是结构化 API 请求，而是**自然语言消息**（或结构化 JSON）。

### 2.3 什么时候该用 Multi-Agent

```
✅ 适合 Multi-Agent：
  - 任务涉及多个专业领域（饮食 + 运动 + 睡眠）
  - 子任务之间相对独立，可以并行
  - 需要不同的 Prompt 策略（严谨的医学建议 vs 轻松的鼓励）
  - 系统需要灵活扩展（随时加新能力）

❌ 不需要 Multi-Agent：
  - 单一领域的简单任务
  - 子任务强耦合，必须串行
  - 团队小、迭代快，单 Agent 够用
```

---

## 第三部分：三种协作模式

### 3.1 模式一：串行管道（Pipeline）

```
用户输入 → Agent A → Agent B → Agent C → 最终输出

例子：饮食记录流程
用户："我吃了一碗牛肉面"
  → 解析 Agent：提取食物信息 {"food": "牛肉面", "amount": "一碗"}
  → 营养 Agent：查询营养数据 {"calories": 580, "protein": 25}
  → 建议 Agent：生成个性化建议 "热量适中，蛋白质不错..."
```

**特点**：
- 上一个 Agent 的输出是下一个的输入
- 每个 Agent 只关注自己的环节
- 类比 Java：`Stream` 的 `map().filter().collect()` 或 Spring 的 `Filter Chain`

**适用场景**：任务有明确的先后顺序，后一步依赖前一步的结果。

### 3.2 模式二：并行扇出（Fan-out / Fan-in）

```
                ┌→ Agent A（营养分析）─┐
用户输入 → 分发 ├→ Agent B（运动分析）─┤→ 汇总 → 最终输出
                └→ Agent C（睡眠分析）─┘

例子：综合健康分析
用户："分析我今天的健康状况"
  → 同时启动三个 Agent
  → 营养 Agent：分析饮食 → "热量 1800 卡，蛋白质偏低"
  → 运动 Agent：分析运动 → "跑步 5km，消耗 400 卡"
  → 睡眠 Agent：分析睡眠 → "6 小时偏少，建议 7-8 小时"
  → 汇总 Agent：综合三方结果，给出整体建议
```

**特点**：
- 多个 Agent 同时工作，互不依赖
- 最后有一个汇总环节
- 类比 Java：`CompletableFuture.allOf()` 或 `ForkJoinPool`

**适用场景**：多个子任务相互独立，可以并行处理。

### 3.3 模式三：路由分发（Router）

```
                ┌→ 饮食 Agent（记录/查询饮食）
用户输入 → 路由 ├→ 运动 Agent（记录/查询运动）
                ├→ 问答 Agent（健康知识问答）
                └→ 闲聊 Agent（日常聊天）

例子：
用户："我中午吃了沙拉" → 路由到饮食 Agent
用户："痛风能吃豆腐吗" → 路由到问答 Agent
用户："今天心情不好"   → 路由到闲聊 Agent
```

**特点**：
- 一个 Router 判断用户意图，分发到对应 Agent
- 每次只有一个 Agent 工作
- 类比 Java：`Spring MVC` 的 `DispatcherServlet`，根据 URL 路由到不同 Controller

**适用场景**：用户请求类型多样，不同类型需要不同处理逻辑。

### 3.4 实际项目中：混合使用

```
健康管家的真实架构（预览）：

用户输入
  → Router Agent（判断意图）
      ├→ 饮食记录：串行管道（解析 → 营养查询 → 记录 → 反馈）
      ├→ 健康分析：并行扇出（营养 + 运动 + 睡眠 → 汇总）
      ├→ 知识问答：RAG Agent（检索 → 生成）
      └→ 日常闲聊：通用对话 Agent
```

这就是我们最终要做的健康管家架构。今天先把每种模式单独实现。

---

## 第四部分：动手实现

接下来我们用代码实现这三种模式。每个 Agent 就是一个函数，接收输入、调用 LLM、返回输出。

### 4.1 基础结构：Agent 就是一个函数

```python
# 最简单的 Agent 定义
# 每个 Agent 本质上就是：System Prompt + LLM 调用
# 类比 Java：一个 Agent 就像一个 @Service，有自己的职责

def create_agent(name: str, system_prompt: str, tools: list = None):
    """
    创建一个 Agent。
    
    参数：
        name: Agent 名称，用于日志和调试
        system_prompt: 这个 Agent 的系统提示词，定义它的专业领域和行为
        tools: 这个 Agent 可用的工具列表（本课先不用，下节课加）
    
    返回：
        一个函数，接收用户消息，返回 Agent 的回复
    """
    from openai import OpenAI
    
    # 创建 DashScope 客户端
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    def run(user_message: str) -> str:
        """
        运行这个 Agent。
        
        参数：
            user_message: 用户输入（或上一个 Agent 的输出）
        返回：
            Agent 的回复文本
        """
        # chat.completions.create() — 调用 LLM 生成回复
        # messages 列表定义对话上下文：system 定义角色，user 是输入
        response = client.chat.completions.create(
            model="qwen-plus",          # 通义千问 Plus 模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7             # 控制回复的随机性，0=确定，1=随机
        )
        # choices[0].message.content — 取第一个回复的文本内容
        return response.choices[0].message.content
    
    # 把名称挂在函数上，方便调试时知道是哪个 Agent
    run.name = name
    return run
```

这就是最简单的 Agent 工厂。每个 Agent 的区别只在于 `system_prompt` 不同。

---

接下来的代码示例在 `code/` 目录中，我们一个一个来实现。

准备好了吗？我们从串行管道开始。
