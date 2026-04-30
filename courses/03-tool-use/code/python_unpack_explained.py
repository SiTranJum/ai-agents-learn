"""
Python 解包操作符 ** 详解

在 Tool Use 场景中，LLM 返回的参数是字典格式，
需要用 ** 解包为函数的关键字参数
"""

# ============================================
# 示例 1：基础用法
# ============================================
def greet(name: str, age: int):
    """打招呼函数"""
    return f"你好，{name}！你今年 {age} 岁。"

# 方式 1：直接传参
result1 = greet("张三", 25)
print(result1)  # 你好，张三！你今年 25 岁。

# 方式 2：用字典 + 解包
params = {"name": "张三", "age": 25}
result2 = greet(**params)  # ** 解包字典
print(result2)  # 你好，张三！你今年 25 岁。

# 方式 3：如果不解包会怎样？
try:
    result3 = greet(params)  # ❌ 错误！
except TypeError as e:
    print(f"错误：{e}")
    # 错误：greet() missing 1 required positional argument: 'age'
    # 因为 greet 期望 2 个参数，但只收到 1 个（字典本身）


# ============================================
# 示例 2：解包的好处 - 不关心参数顺序
# ============================================
def calculate(a: int, b: int, operation: str):
    """计算函数"""
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b

# 字典的键顺序可以和函数参数顺序不同
params = {
    "operation": "add",  # 第 3 个参数
    "b": 20,             # 第 2 个参数
    "a": 10              # 第 1 个参数
}
result = calculate(**params)  # 自动匹配参数名
print(f"结果：{result}")  # 结果：30


# ============================================
# 示例 3：Tool Use 场景（模拟 LLM 返回）
# ============================================
import json

# 定义工具函数
def get_weather(city: str, unit: str = "celsius") -> dict:
    """获取天气信息"""
    return {
        "city": city,
        "temperature": 15,
        "unit": unit
    }

# 模拟 LLM 返回的工具调用请求
llm_response = {
    "tool_name": "get_weather",
    "arguments": '{"city": "北京", "unit": "celsius"}'  # JSON 字符串
}

# 解析参数
tool_name = llm_response["tool_name"]
tool_args = json.loads(llm_response["arguments"])  # 解析 JSON 为字典
print(f"\n工具名称：{tool_name}")
print(f"参数（字典）：{tool_args}")

# 方式 1：不解包（错误）
print("\n❌ 不解包的方式：")
try:
    result = get_weather(tool_args)
except TypeError as e:
    print(f"错误：{e}")
    # 错误：get_weather() missing 1 required positional argument: 'unit'

# 方式 2：解包（正确）
print("\n✅ 解包的方式：")
result = get_weather(**tool_args)
print(f"结果：{result}")


# ============================================
# 示例 4：动态调用不同的工具
# ============================================
def search_food(name: str) -> dict:
    """搜索食物"""
    return {"name": name, "calories": 200}

def calculate_bmi(weight: float, height: float) -> float:
    """计算 BMI"""
    return weight / (height ** 2)

# 工具映射表（类似 Spring 的 Bean 容器）
tools_map = {
    "get_weather": get_weather,
    "search_food": search_food,
    "calculate_bmi": calculate_bmi
}

# 模拟多个工具调用
tool_calls = [
    {"name": "get_weather", "args": {"city": "上海"}},
    {"name": "search_food", "args": {"name": "苹果"}},
    {"name": "calculate_bmi", "args": {"weight": 70, "height": 1.75}}
]

print("\n" + "=" * 50)
print("动态调用多个工具：")
print("=" * 50)

for call in tool_calls:
    tool_name = call["name"]
    tool_args = call["args"]

    # 查找工具函数
    tool_function = tools_map.get(tool_name)

    if tool_function:
        # 解包参数并调用
        result = tool_function(**tool_args)
        print(f"\n工具：{tool_name}")
        print(f"参数：{tool_args}")
        print(f"结果：{result}")


# ============================================
# 示例 5：* 和 ** 的区别
# ============================================
print("\n" + "=" * 50)
print("* 和 ** 的区别：")
print("=" * 50)

def example(a, b, c):
    return a + b + c

# * 解包列表/元组为位置参数
args_list = [1, 2, 3]
result = example(*args_list)  # 相当于 example(1, 2, 3)
print(f"* 解包列表：{result}")

# ** 解包字典为关键字参数
args_dict = {"a": 1, "b": 2, "c": 3}
result = example(**args_dict)  # 相当于 example(a=1, b=2, c=3)
print(f"** 解包字典：{result}")


# ============================================
# 总结
# ============================================
print("\n" + "=" * 50)
print("总结：")
print("=" * 50)
print("""
1. ** 的作用：
   - 将字典解包为关键字参数
   - 字典的键 → 参数名
   - 字典的值 → 参数值

2. 为什么在 Tool Use 中需要解包：
   - LLM 返回的参数是 JSON 格式（字典）
   - 工具函数期望的是独立的参数
   - ** 解包可以自动匹配参数名

3. 类比 Java：
   - Java：method.invoke(obj, args) - 需要反射
   - Python：function(**args) - 语言内置支持

4. * 和 ** 的区别：
   - *  解包列表/元组 → 位置参数
   - ** 解包字典 → 关键字参数
""")
