# 课程 3：Tool Use（工具调用）

## 第一部分：Tool Use 基础概念

### 什么是 Tool Use？

Tool Use（也叫 Function Calling）是让 LLM 能够调用外部工具和函数的能力。

**类比理解**（用 Java 开发者熟悉的概念）：
- **普通 LLM**：像一个只能返回 String 的方法
- **带 Tool Use 的 LLM**：像一个能调用其他服务的 Controller，可以调用 Service 层、访问数据库、调用外部 API

```
普通对话：
用户："北京今天天气怎么样？"
LLM："抱歉，我无法获取实时天气信息..."

带 Tool Use：
用户："北京今天天气怎么样？"
LLM：[决定调用 get_weather 工具]
系统：[执行工具，返回 "晴天，15°C"]
LLM："北京今天天气晴朗，气温 15°C"
```

### Tool Use 的工作流程

```
1. 用户发送消息
   ↓
2. 你定义可用的工具列表，连同消息一起发给 LLM
   ↓
3. LLM 分析消息，决定是否需要调用工具
   ↓
4. 如果需要，LLM 返回工具调用请求（包含工具名和参数）
   ↓
5. 你的代码执行实际的工具函数
   ↓
6. 将工具执行结果返回给 LLM
   ↓
7. LLM 基于工具结果生成最终回复
```

**关键点**：
- LLM 不会真的执行工具，它只是"建议"调用哪个工具
- 你的代码负责实际执行工具
- 这是一个多轮对话过程

### 工具定义的结构

工具定义使用 JSON Schema 格式，包含三个核心部分：

```python
{
    "name": "get_weather",              # 工具名称（函数名）
    "description": "获取指定城市的天气信息",  # 工具描述（帮助 LLM 理解何时使用）
    "input_schema": {                   # 参数定义（JSON Schema 格式）
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称，如'北京'、'上海'"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "温度单位"
            }
        },
        "required": ["city"]            # 必填参数
    }
}
```

**类比 Java**：
```java
// 这就像定义一个接口方法
public interface WeatherService {
    /**
     * 获取指定城市的天气信息
     * @param city 城市名称，如"北京"、"上海"
     * @param unit 温度单位（celsius 或 fahrenheit）
     * @return 天气信息
     */
    WeatherInfo getWeather(String city, TemperatureUnit unit);
}
```

---

## 第二部分：定义和使用工具

### 在 DeepSeek API 中使用工具

DeepSeek 支持原生的 Function Calling，使用 OpenAI 兼容的 API 格式：

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://api.deepseek.com"
)

# 定义工具（OpenAI 兼容格式）
tools = [
    {
        "name": "get_weather",
        "description": "获取指定城市的实时天气信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["city"]
        }
    }
]

# 发送消息，同时传递工具定义
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,  # 传递工具列表
    messages=[
        {"role": "user", "content": "北京今天天气怎么样？"}
    ]
)
```

### 解析 LLM 的响应

LLM 的响应可能包含两种类型的内容：

1. **普通文本**：`content` 中的 `type` 为 `text`
2. **工具调用请求**：`content` 中的 `type` 为 `tool_use`

```python
# response.content 是一个列表，可能包含多个 content block
for block in response.content:
    if block.type == "text":
        # 普通文本回复
        print(f"LLM 说：{block.text}")

    elif block.type == "tool_use":
        # 工具调用请求
        tool_name = block.name          # 工具名称
        tool_input = block.input        # 工具参数（dict）
        tool_use_id = block.id          # 工具调用 ID（用于返回结果）

        print(f"LLM 想调用工具：{tool_name}")
        print(f"参数：{tool_input}")
```

**类比 Java**：
```java
// 类似于解析一个多态的响应对象
for (ContentBlock block : response.getContent()) {
    if (block instanceof TextBlock) {
        System.out.println("LLM 说：" + ((TextBlock) block).getText());
    } else if (block instanceof ToolUseBlock) {
        ToolUseBlock toolUse = (ToolUseBlock) block;
        String toolName = toolUse.getName();
        Map<String, Object> input = toolUse.getInput();
        // 执行工具...
    }
}
```

---

## 第三部分：执行工具和返回结果

### 执行工具函数

当 LLM 请求调用工具时，你需要：
1. 根据 `tool_name` 找到对应的函数
2. 使用 `tool_input` 作为参数执行函数
3. 将结果返回给 LLM

```python
# 定义实际的工具函数
def get_weather(city: str) -> dict:
    """
    获取天气信息（这里用模拟数据）
    实际项目中，这里会调用真实的天气 API
    """
    # 模拟数据
    weather_data = {
        "北京": {"temperature": 15, "condition": "晴天"},
        "上海": {"temperature": 20, "condition": "多云"},
    }
    return weather_data.get(city, {"temperature": 0, "condition": "未知"})

# 工具映射表（类似 Spring 的 Bean 容器）
TOOLS_MAP = {
    "get_weather": get_weather,
}

# 执行工具
if block.type == "tool_use":
    tool_name = block.name
    tool_input = block.input
    tool_use_id = block.id

    # 查找并执行工具函数
    tool_function = TOOLS_MAP.get(tool_name)
    if tool_function:
        result = tool_function(**tool_input)  # ** 解包字典为关键字参数
    else:
        result = {"error": f"未找到工具：{tool_name}"}
```

### 将结果返回给 LLM

执行工具后，需要将结果作为新的消息发送给 LLM：

```python
# 构建包含工具结果的消息
messages = [
    {"role": "user", "content": "北京今天天气怎么样？"},
    {"role": "assistant", "content": response.content},  # LLM 的工具调用请求
    {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_id,  # 必须匹配之前的 tool_use_id
                "content": str(result)        # 工具执行结果（字符串格式）
            }
        ]
    }
]

# 再次调用 LLM，让它基于工具结果生成回复
final_response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=messages
)
```

**关键点**：
- `tool_use_id` 必须与之前的工具调用请求匹配
- 工具结果的 `content` 必须是字符串（可以是 JSON 字符串）
- 需要保持完整的对话历史

---

## 第四部分：完整的工具调用循环

### 为什么需要循环？

LLM 可能需要多次调用工具：
```
用户："北京和上海今天天气怎么样？"
→ LLM 调用 get_weather("北京")
→ 返回结果
→ LLM 调用 get_weather("上海")
→ 返回结果
→ LLM 生成最终回复
```

### 完整代码示例

```python
def chat_with_tools(user_message: str, tools: list, tools_map: dict):
    """
    带工具调用的对话函数

    参数：
    - user_message: 用户消息
    - tools: 工具定义列表
    - tools_map: 工具名到函数的映射
    """
    messages = [{"role": "user", "content": user_message}]

    while True:
        # 调用 LLM
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        # 检查是否需要调用工具
        tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

        if not tool_use_blocks:
            # 没有工具调用，返回最终回复
            text_blocks = [block.text for block in response.content if block.type == "text"]
            return " ".join(text_blocks)

        # 添加 LLM 的响应到消息历史
        messages.append({"role": "assistant", "content": response.content})

        # 执行所有工具调用
        tool_results = []
        for tool_use in tool_use_blocks:
            tool_name = tool_use.name
            tool_input = tool_use.input
            tool_use_id = tool_use.id

            # 执行工具
            tool_function = tools_map.get(tool_name)
            if tool_function:
                result = tool_function(**tool_input)
            else:
                result = {"error": f"未找到工具：{tool_name}"}

            # 收集工具结果
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": str(result)
            })

        # 添加工具结果到消息历史
        messages.append({"role": "user", "content": tool_results})

        # 继续循环，让 LLM 处理工具结果
```

---

## 第五部分：最佳实践和注意事项

### 1. 工具描述要清晰

```python
# ❌ 不好的描述
"description": "获取天气"

# ✅ 好的描述
"description": "获取指定城市的实时天气信息，包括温度、天气状况、湿度等"
```

### 2. 参数描述要详细

```python
"city": {
    "type": "string",
    "description": "城市名称，如'北京'、'上海'、'深圳'"  # 给出示例
}
```

### 3. 错误处理

```python
try:
    result = tool_function(**tool_input)
except Exception as e:
    result = {"error": str(e)}
```

### 4. 工具结果格式化

```python
# 返回结构化数据（JSON 字符串）
import json
result = {"temperature": 15, "condition": "晴天"}
tool_result_content = json.dumps(result, ensure_ascii=False)
```

### 5. 限制工具调用次数

```python
max_iterations = 10  # 防止无限循环
for i in range(max_iterations):
    # 工具调用循环
    ...
```

---

## 与健康管家产品的结合

我们的健康管家需要哪些工具？

1. **食物查询工具**
   - `search_food(name: str)` - 搜索食物营养信息
   - `get_food_nutrition(food_id: str)` - 获取详细营养数据

2. **数据记录工具**
   - `log_meal(food_items: list, meal_type: str)` - 记录用餐
   - `log_exercise(activity: str, duration: int)` - 记录运动

3. **数据查询工具**
   - `get_daily_summary(date: str)` - 获取每日摘要
   - `get_nutrition_stats(start_date: str, end_date: str)` - 获取营养统计

4. **计算工具**
   - `calculate_calories(food_items: list)` - 计算总热量
   - `calculate_bmi(weight: float, height: float)` - 计算 BMI

5. **提醒工具**
   - `set_reminder(time: str, message: str)` - 设置提醒

下一步我们会在实践中逐步实现这些工具。
