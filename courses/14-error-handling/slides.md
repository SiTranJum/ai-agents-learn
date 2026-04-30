# 课程 14：错误处理与自我修正机制

---

## 第一部分：Agent 中的错误分类

### 1.1 三类错误

在普通程序里，错误就是异常。但 Agent 里的"错误"更复杂，因为多了 LLM 这个不确定因素。

```
┌─────────────────────────────────────────────────────┐
│                Agent 中的三类错误                      │
├─────────────────┬────────────────┬──────────────────┤
│   工具执行错误    │   LLM 输出错误  │   业务逻辑错误    │
├─────────────────┼────────────────┼──────────────────┤
│ API 超时         │ 格式不对        │ 建议不合理        │
│ 数据库连接失败    │ JSON 解析失败   │ 热量计算离谱      │
│ 网络异常         │ 幻觉（编造数据） │ 给痛风患者推荐海鲜 │
│ 权限不足         │ 答非所问        │ 违反安全约束      │
├─────────────────┼────────────────┼──────────────────┤
│ 能捕获异常       │ 不会抛异常！     │ 不会抛异常！      │
│ try-except 搞定  │ 需要校验逻辑    │ 需要业务规则检查   │
└─────────────────┴────────────────┴──────────────────┘
```

**关键认知**：LLM 输出错误和业务逻辑错误**不会抛异常**。LLM 返回一个格式错误的 JSON，Python 不会报错，它只是一个"看起来正常但内容有问题"的字符串。

**Java 类比**：
- 工具执行错误 = `IOException`、`SQLException`（运行时异常，能 catch）
- LLM 输出错误 = 接口返回了 200，但 body 里的数据是错的（需要业务校验）
- 业务逻辑错误 = 代码没 bug，但业务结果不对（需要规则引擎）

### 1.2 为什么 LLM 错误最难处理

```python
# 工具错误 — 简单，try-except 就行
try:
    data = call_food_api("鸡蛋")
except TimeoutError:
    print("API 超时")  # 明确知道出了什么问题

# LLM 错误 — 难，因为它"看起来正常"
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "解析：我吃了两个鸡蛋"}]
)
result = response.choices[0].message.content
# result 可能是：
# ✅ '{"food": "鸡蛋", "amount": 2, "calories": 140}'  正确
# ❌ '{"food": "鸡蛋", "amount": 2, "calories": 14000}' 热量离谱
# ❌ '好的，我帮你记录了两个鸡蛋'                         不是 JSON
# ❌ '{"food": "鸡蛋", "数量": 2}'                       字段名不对
# 以上四种情况，API 调用都是成功的，不会抛异常！
```

---

## 第二部分：课程 13 的错误处理 vs 本课的自我修正

### 2.1 回顾课程 13

课程 13 讲了四种错误处理策略：raise、skip、retry、fallback。

```python
# 课程 13 的 retry — 盲目重试
for attempt in range(max_retries):
    try:
        result = step.func(context)
        return result
    except Exception as e:
        time.sleep(2 ** attempt)  # 等一等再试
```

**问题**：retry 只能处理"偶发性错误"（网络抖动、API 限流）。如果 LLM 输出格式就是错的，重试 100 次还是错的，因为你没告诉它哪里错了。

### 2.2 自我修正 — 带着错误信息重试

```python
# 自我修正 — 告诉 LLM 哪里错了，让它改
result = call_llm("解析：我吃了两个鸡蛋")
# → '好的，我帮你记录了两个鸡蛋'  ← 不是 JSON！

# 把错误信息反馈给 LLM
result = call_llm(
    "你上次的输出不是合法的 JSON 格式。"
    "请严格按照 {\"food\": \"...\", \"amount\": N, \"calories\": N} 格式输出。"
    "原始输入：我吃了两个鸡蛋"
)
# → '{"food": "鸡蛋", "amount": 2, "calories": 140}'  ← 修正成功！
```

**区别**：
| | 简单重试（课程 13） | 自我修正（本课） |
|---|---|---|
| 策略 | 同样的输入再来一次 | 带着错误信息再来一次 |
| 适用 | 网络抖动、API 限流 | LLM 输出格式错、内容错 |
| 类比 | 电话没接通，再拨一次 | 作文被老师打回来，按批注修改 |

---

## 第三部分：自我修正的实现

### 3.1 核心流程

```
用户输入
   ↓
LLM 生成输出
   ↓
校验器检查输出 ──→ 通过 → 返回结果
   │
   ↓ 不通过
生成错误反馈
   ↓
把"原始输入 + 错误反馈"再次发给 LLM
   ↓
LLM 重新生成 → 再次校验 → ...（最多 N 次）
```

### 3.2 校验器（Validator）

校验器是自我修正的核心，它负责检查 LLM 输出是否合格。

```python
def validate_meal_record(output: str) -> tuple:
    """
    校验饮食记录的 LLM 输出

    返回：(is_valid, error_message)
    - is_valid: True 表示通过，False 表示需要修正
    - error_message: 具体的错误描述，会反馈给 LLM
    """
    # 检查 1：是否是合法 JSON
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return False, f"输出不是合法的 JSON 格式。你的输出是：{output[:100]}"

    # 检查 2：必要字段是否存在
    required_fields = ["food", "amount", "calories"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return False, f"缺少必要字段：{missing}。需要的字段：{required_fields}"

    # 检查 3：数据类型是否正确
    if not isinstance(data["amount"], (int, float)):
        return False, f"amount 必须是数字，但收到了：{data['amount']}"
    if not isinstance(data["calories"], (int, float)):
        return False, f"calories 必须是数字，但收到了：{data['calories']}"

    # 检查 4：业务合理性
    if data["calories"] < 0:
        return False, "calories 不能为负数"
    if data["calories"] > 5000:
        return False, f"calories={data['calories']} 不合理，单个食物不太可能超过 5000 卡"
    if data["amount"] <= 0:
        return False, "amount 必须大于 0"

    return True, ""
```

**Java 类比**：
```java
// 类似 Spring Validation
@Valid
public class MealRecord {
    @NotNull String food;
    @Positive int amount;
    @Range(min=0, max=5000) int calories;
}
```

### 3.3 自我修正循环

```python
def self_correcting_call(messages, validator, max_attempts=3):
    """
    带自我修正的 LLM 调用

    参数：
    - messages: 初始消息列表
    - validator: 校验函数，返回 (is_valid, error_message)
    - max_attempts: 最大尝试次数
    """
    for attempt in range(max_attempts):
        # 调用 LLM
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7
        )
        output = response.choices[0].message.content

        # 校验输出
        is_valid, error_msg = validator(output)

        if is_valid:
            return output  # 校验通过，返回结果

        # 校验失败，把错误信息追加到消息中
        # 关键：告诉 LLM 哪里错了，而不是盲目重试
        messages.append({"role": "assistant", "content": output})
        messages.append({"role": "user", "content": 
            f"你的输出有问题：{error_msg}\n请修正后重新输出。"
        })

        print(f"  第 {attempt+1} 次输出未通过校验：{error_msg}")

    # 所有尝试都失败
    raise ValueError(f"LLM 经过 {max_attempts} 次修正仍未通过校验")
```

---

## 第四部分：Guardrails（护栏）

### 4.1 什么是 Guardrails

Guardrails = 防止 Agent 做出危险或不合理行为的安全机制。

```
用户输入 → [输入护栏] → Agent 处理 → [输出护栏] → 返回用户
              ↑                          ↑
          过滤危险输入              校验输出安全性
```

### 4.2 三层护栏

**输入护栏**：过滤不合理的用户输入
```python
def input_guardrail(user_input: str) -> tuple:
    """检查用户输入是否安全"""
    # 拒绝医疗诊断请求
    medical_keywords = ["处方", "用药", "诊断", "治疗方案"]
    for keyword in medical_keywords:
        if keyword in user_input:
            return False, "我是健康管家，不能提供医疗诊断。建议咨询专业医生。"
    return True, ""
```

**输出护栏**：校验 LLM 输出是否合规
```python
def output_guardrail(output: str) -> tuple:
    """检查 LLM 输出是否安全"""
    # 不能给出极端饮食建议
    dangerous_patterns = ["不吃饭", "断食", "每天只吃", "催吐"]
    for pattern in dangerous_patterns:
        if pattern in output:
            return False, f"输出包含危险建议：{pattern}"
    return True, ""
```

**业务护栏**：确保数据在合理范围内
```python
def business_guardrail(data: dict) -> tuple:
    """检查业务数据是否合理"""
    if data.get("target_calories", 0) < 1200:
        return False, "每日目标热量不应低于 1200 卡，这对健康有害"
    if data.get("weight_loss_per_week", 0) > 1.0:
        return False, "每周减重不应超过 1kg，过快减重不健康"
    return True, ""
```

### 4.3 健康场景为什么特别需要护栏

```
普通 Agent（写代码）：
  LLM 犯错 → 代码跑不通 → 用户自己能发现 → 风险低

健康 Agent：
  LLM 犯错 → "你可以每天只吃 500 卡" → 用户照做 → 身体出问题 → 风险高！
```

**所以健康管家的护栏不是可选的，是必须的。**

---

## 第五部分：完整的错误处理架构

### 5.1 把所有机制组合起来

```
用户输入
   ↓
[输入护栏] ──→ 拒绝 → 返回安全提示
   ↓ 通过
LLM 生成输出
   ↓
[格式校验] ──→ 失败 → 自我修正（带错误信息重试）
   ↓ 通过
[业务校验] ──→ 失败 → 自我修正（带业务规则重试）
   ↓ 通过
[输出护栏] ──→ 危险 → 替换为安全回复
   ↓ 通过
返回用户
```

### 5.2 与课程 13 的关系

```
课程 13 Multi-Step 的错误处理：
  针对"步骤执行失败"（工具错误）
  策略：raise / skip / retry / fallback

课程 14 自我修正：
  针对"LLM 输出有问题"（内容错误）
  策略：校验 → 反馈 → 重新生成

两者互补，不是替代关系：
  Multi-Step 的某个步骤里调用 LLM 时，可以用自我修正
```

---

## 小结

### 核心概念

1. **三类错误**：工具错误（能 catch）、LLM 错误（需要校验）、业务错误（需要规则）
2. **自我修正**：校验输出 → 生成错误反馈 → 让 LLM 重新生成（不是盲目重试）
3. **Guardrails**：输入护栏 + 输出护栏 + 业务护栏，健康场景必须有
4. **与课程 13 互补**：Multi-Step 处理工具错误，自我修正处理 LLM 错误
