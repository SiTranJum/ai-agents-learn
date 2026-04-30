import os
"""
课程 14：错误处理与自我修正机制

核心思想：
- LLM 的输出不会抛异常，但可能格式错、内容错、不合理
- 自我修正 = 校验输出 → 告诉 LLM 哪里错了 → 让它重新生成
- 与课程 13 的 retry 区别：retry 是盲目重试，自我修正是带着错误信息重试

Java 类比：
- 校验器 = Spring Validation（@Valid + @NotNull + @Range）
- 自我修正 = 单元测试失败后看报错信息修 bug，而不是盲目重跑
- 护栏 = Spring Security 的 Filter Chain
"""

import json
import sys
import io
from openai import OpenAI

# ========== Windows 终端中文输出修复 ==========
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# ========== DeepSeek API 客户端 ==========
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


# ========== 校验器（Validator） ==========

def validate_meal_record(output: str):
    """
    校验饮食记录的 LLM 输出

    返回：(is_valid, parsed_data_or_none, error_message)

    Java 类比：类似 @Valid 注解触发的校验逻辑
    - 先检查格式（JSON 是否合法）
    - 再检查字段（必要字段是否存在）
    - 最后检查业务（数值是否合理）
    """
    # 检查 1：是否是合法 JSON
    # 有时 LLM 会在 JSON 前后加上 ```json 标记，先清理掉
    cleaned = output.strip()
    if cleaned.startswith("```"):
        # 去掉 markdown 代码块标记
        lines = cleaned.split("\n")
        # 过滤掉以 ``` 开头的行
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return False, None, f"输出不是合法的 JSON。解析错误：{e}。你的输出是：{output[:200]}"

    # 检查 2：必要字段是否存在
    required_fields = ["food", "amount", "unit", "calories"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return False, None, f"缺少必要字段：{missing}。完整字段列表：{required_fields}"

    # 检查 3：数据类型
    if not isinstance(data["calories"], (int, float)):
        return False, None, f"calories 必须是数字，收到了：{type(data['calories']).__name__}"

    if not isinstance(data["amount"], (int, float)):
        return False, None, f"amount 必须是数字，收到了：{type(data['amount']).__name__}"

    # 检查 4：业务合理性
    if data["calories"] < 0:
        return False, None, "calories 不能为负数"

    if data["calories"] > 5000:
        return False, None, (
            f"calories={data['calories']} 不合理。"
            f"单份 {data['food']} 不太可能超过 5000 卡。"
            f"请重新估算。"
        )

    if data["amount"] <= 0:
        return False, None, "amount 必须大于 0"

    return True, data, ""


# ========== 护栏（Guardrails） ==========

def input_guardrail(user_input: str):
    """
    输入护栏：过滤不合理的用户输入

    返回：(is_safe, message)

    Java 类比：类似 Spring Security 的请求过滤器
    """
    # 规则 1：拒绝医疗诊断请求
    medical_keywords = ["处方", "开药", "诊断", "治疗方案", "吃什么药"]
    for keyword in medical_keywords:
        if keyword in user_input:
            return False, (
                "我是健康管家，不能提供医疗诊断或用药建议。"
                "如果身体不适，建议咨询专业医生。"
            )

    # 规则 2：拒绝极端饮食请求
    extreme_keywords = ["断食", "催吐", "不吃饭减肥", "只喝水"]
    for keyword in extreme_keywords:
        if keyword in user_input:
            return False, (
                "这种方式对身体有害，我不能提供相关建议。"
                "健康减重建议每周减 0.5-1kg，通过合理饮食和运动实现。"
            )

    return True, ""


def output_guardrail(output: str):
    """
    输出护栏：校验 LLM 输出是否安全

    返回：(is_safe, message)
    """
    dangerous_patterns = [
        ("不吃饭", "不建议完全不吃饭"),
        ("断食", "不建议断食"),
        ("每天只吃", "不建议极端限制饮食"),
        ("低于800卡", "每日摄入不应低于 1200 卡"),
        ("催吐", "催吐对身体有严重伤害"),
    ]

    for pattern, reason in dangerous_patterns:
        if pattern in output:
            return False, f"输出包含不安全建议（{reason}），已拦截"

    return True, ""


# ========== 自我修正 LLM 调用 ==========

def self_correcting_call(system_prompt, user_prompt, validator, max_attempts=3):
    """
    带自我修正的 LLM 调用

    流程：
    1. 调用 LLM 生成输出
    2. 用 validator 校验
    3. 如果校验失败，把错误信息追加到消息中，让 LLM 重新生成
    4. 最多尝试 max_attempts 次

    参数：
    - system_prompt: 系统提示词
    - user_prompt: 用户输入
    - validator: 校验函数，返回 (is_valid, parsed_data, error_message)
    - max_attempts: 最大尝试次数

    返回：
    - 校验通过的解析结果

    Java 类比：
    - 类似写了一个 while 循环调接口，每次根据返回的错误码调整请求参数
    """
    # 构建初始消息列表
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    for attempt in range(max_attempts):
        print(f"\n  【第 {attempt + 1} 次尝试】")

        # 调用 LLM
        # temperature 设低一点（0.3），让输出更稳定，减少格式错误
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.3
        )
        output = response.choices[0].message.content
        print(f"  LLM 输出：{output[:200]}")

        # 校验输出
        is_valid, parsed_data, error_msg = validator(output)

        if is_valid:
            print(f"  ✓ 校验通过！")
            return parsed_data

        # 校验失败 — 把错误信息反馈给 LLM
        # 关键：这里不是盲目重试，而是告诉 LLM 具体哪里错了
        print(f"  ✗ 校验失败：{error_msg}")

        # 追加 LLM 的错误输出和修正指令到消息历史
        # 这样 LLM 能看到自己之前的错误，避免重复犯错
        messages.append({"role": "assistant", "content": output})
        messages.append({"role": "user", "content": (
            f"你的输出有问题：{error_msg}\n"
            f"请严格按照要求修正后重新输出，只输出 JSON，不要包含任何其他文字。"
        )})

    raise ValueError(f"经过 {max_attempts} 次修正仍未通过校验")


# ========== 完整的健康管家解析流程 ==========

def parse_meal_input(user_input: str):
    """
    解析用户的饮食输入

    完整流程：输入护栏 → LLM 解析 → 自我修正 → 输出护栏

    参数：
    - user_input: 用户的自然语言输入，如"我中午吃了一碗牛肉面"

    返回：
    - 解析后的结构化数据
    """
    print("=" * 60)
    print(f"用户输入：{user_input}")
    print("=" * 60)

    # 第 1 步：输入护栏
    print("\n[1] 输入护栏检查...")
    is_safe, message = input_guardrail(user_input)
    if not is_safe:
        print(f"  ✗ 输入被拦截：{message}")
        return {"error": message}
    print("  ✓ 输入安全")

    # 第 2 步：LLM 解析 + 自我修正
    print("\n[2] LLM 解析（带自我修正）...")

    system_prompt = """你是一个饮食记录解析器。
用户会用自然语言描述吃了什么，你需要解析成结构化的 JSON。

输出格式（严格遵守，只输出 JSON，不要其他文字）：
{"food": "食物名称", "amount": 数量, "unit": "单位", "calories": 估算热量}

示例：
输入：我吃了两个鸡蛋
输出：{"food": "鸡蛋", "amount": 2, "unit": "个", "calories": 140}

输入：中午吃了一碗牛肉面
输出：{"food": "牛肉面", "amount": 1, "unit": "碗", "calories": 550}
"""

    parsed_data = self_correcting_call(
        system_prompt=system_prompt,
        user_prompt=f"解析以下饮食记录：{user_input}",
        validator=validate_meal_record,
        max_attempts=3
    )

    # 第 3 步：输出护栏（检查 LLM 是否在结果中夹带了不安全内容）
    print("\n[3] 输出护栏检查...")
    # 对于结构化数据，主要检查 food 字段
    is_safe, message = output_guardrail(json.dumps(parsed_data, ensure_ascii=False))
    if not is_safe:
        print(f"  ✗ 输出被拦截：{message}")
        return {"error": message}
    print("  ✓ 输出安全")

    # 第 4 步：返回结果
    print(f"\n[结果] {json.dumps(parsed_data, ensure_ascii=False, indent=2)}")
    return parsed_data


# ========== 主程序 ==========

if __name__ == "__main__":
    print("\n课程 14：错误处理与自我修正机制 演示\n")

    # 测试 1：正常输入
    print("\n" + "=" * 60)
    print("测试 1：正常输入")
    result = parse_meal_input("我中午吃了一碗牛肉面加一个鸡蛋")

    # 测试 2：输入护栏拦截
    print("\n" + "=" * 60)
    print("测试 2：输入护栏拦截")
    result = parse_meal_input("我头疼，应该吃什么药？")

    # 测试 3：输入护栏拦截（极端饮食）
    print("\n" + "=" * 60)
    print("测试 3：极端饮食拦截")
    result = parse_meal_input("我想断食三天减肥")

    # 测试 4：模糊输入（测试 LLM 的解析能力）
    print("\n" + "=" * 60)
    print("测试 4：模糊输入")
    result = parse_meal_input("随便吃了点东西")
