# Python for Java Developers —— AI 开发快速入门

> 你不需要精通 Python，只需要掌握写 AI Agent 代码用到的那部分。
> 本指南用 Java 对照的方式，帮你 10 分钟上手。

---

## 1. 环境管理（对标 Maven/Gradle）

### Java 的方式
```xml
<!-- pom.xml -->
<dependency>
    <groupId>com.openai</groupId>
    <artifactId>openai-sdk</artifactId>
</dependency>
```

### Python 的方式
```bash
# 安装包（相当于 mvn install）
pip install openai

# 从文件批量安装（相当于 pom.xml）
pip install -r requirements.txt

# 查看已安装的包
pip list
```

**requirements.txt** 就是 Python 的 pom.xml：
```
openai>=1.0.0
requests>=2.28.0
```

### 虚拟环境（推荐）
Java 项目之间的依赖天然隔离（每个项目有自己的 classpath）。
Python 默认全局共享，所以需要手动创建隔离环境：

```bash
# 创建虚拟环境（只需一次，相当于创建项目）
python -m venv .venv

# 激活（每次打开终端都要执行）
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 激活后，pip install 只影响当前环境
pip install openai
```

---

## 2. 基础语法对照

### 变量和类型
```java
// Java：必须声明类型
String name = "健康管家";
int age = 1;
boolean isActive = true;
List<String> foods = List.of("苹果", "香蕉");
Map<String, Integer> calories = Map.of("苹果", 52);
```

```python
# Python：不需要声明类型，直接赋值
name = "健康管家"
age = 1
is_active = True  # 注意大写
foods = ["苹果", "香蕉"]  # list，对标 List
calories = {"苹果": 52}   # dict，对标 Map
```

### 函数
```java
// Java
public String greet(String name) {
    return "你好，" + name;
}
```

```python
# Python：def 定义，缩进代替花括号
def greet(name):
    return f"你好，{name}"

# 带默认参数（Java 没有这个特性）
def greet(name, greeting="你好"):
    return f"{greeting}，{name}"

greet("小明")            # "你好，小明"
greet("小明", "早上好")   # "早上好，小明"
```

### 字符串格式化
```java
// Java
String msg = String.format("温度：%s，Token：%d", temp, tokens);
```

```python
# Python：f-string（最常用，类似模板字符串）
msg = f"温度：{temp}，Token：{tokens}"
```

### 条件和循环
```java
// Java
if (temperature > 1.0) {
    System.out.println("随机性高");
} else if (temperature > 0.5) {
    System.out.println("适中");
} else {
    System.out.println("确定性高");
}

for (String food : foods) {
    System.out.println(food);
}
```

```python
# Python：冒号 + 缩进，没有花括号
if temperature > 1.0:
    print("随机性高")
elif temperature > 0.5:
    print("适中")
else:
    print("确定性高")

for food in foods:
    print(food)
```

### 异常处理
```java
// Java
try {
    response = client.chat(request);
} catch (ApiException e) {
    System.out.println("API 调用失败：" + e.getMessage());
}
```

```python
# Python
try:
    response = client.chat.completions.create(...)
except Exception as e:
    print(f"API 调用失败：{e}")
```

---

## 3. Python 特有的常用语法

这些在 AI 代码中经常出现，Java 里没有直接对应：

### 字典操作（写 API 参数时大量使用）
```python
# 创建
message = {
    "role": "user",
    "content": "你好"
}

# 读取
print(message["role"])       # "user"
print(message.get("name"))   # None（不报错，Java 的 getOrDefault）

# 遍历
for key, value in message.items():
    print(f"{key}: {value}")
```

### 列表推导式（处理 API 返回数据时常用）
```python
# Java 的 Stream
numbers = [1, 2, 3, 4, 5]
# Java: numbers.stream().filter(n -> n > 2).map(n -> n * 2).collect(toList())
# Python:
result = [n * 2 for n in numbers if n > 2]  # [6, 8, 10]
```

### 解包赋值
```python
# 一次赋多个值
prompt_tokens, completion_tokens = 10, 25

# 从函数返回多个值（Java 需要包装成对象）
def get_usage(response):
    return response.usage.prompt_tokens, response.usage.completion_tokens

input_tokens, output_tokens = get_usage(response)
```

---

## 4. AI 开发中最常见的模式

### 模式一：调用 LLM API
```python
from openai import OpenAI

client = OpenAI(api_key="your-key", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是健康顾问"},
        {"role": "user", "content": "苹果的热量是多少？"}
    ]
)

answer = response.choices[0].message.content
print(answer)
```

### 模式二：多轮对话（维护消息列表）
```python
# 对话历史就是一个 list，不断追加
messages = [
    {"role": "system", "content": "你是健康顾问"}
]

# 用户说话 → 加入列表
messages.append({"role": "user", "content": "我今天吃了炸鸡"})

# 调用 API
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages
)

# AI 回复 → 也加入列表（这样下次调用就有上下文了）
assistant_msg = response.choices[0].message.content
messages.append({"role": "assistant", "content": assistant_msg})

# 用户继续说话
messages.append({"role": "user", "content": "热量大概多少？"})
# 再次调用 API，AI 就知道你在问炸鸡的热量
```

### 模式三：环境变量管理 API Key（不要硬编码！）
```python
import os

# 方式一：直接读环境变量
api_key = os.getenv("DEEPSEEK_API_KEY")

# 方式二：用 .env 文件（推荐）
# 先 pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()  # 读取 .env 文件
api_key = os.getenv("DEEPSEEK_API_KEY")
```

`.env` 文件内容：
```
DEEPSEEK_API_KEY=sk-xxxxx
```

---

## 5. 运行 Python 代码

```bash
# 直接运行
python example.py

# 如果系统有 python2 和 python3，用：
python3 example.py
```

就这些。遇到不懂的语法随时问我，我会用 Java 对照来解释。
