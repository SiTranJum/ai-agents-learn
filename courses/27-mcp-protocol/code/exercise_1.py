"""
练习 1：扩展健康管家 MCP Server

目标：
    在现有的 health-mcp-server 基础上，添加更多工具和 Resources

任务：

1. 添加一个新工具：calculate_daily_calories
   - 功能：根据性别、年龄、身高、体重、活动水平，计算每日推荐热量
   - 公式：使用 Harris-Benedict 公式
     - 男性 BMR = 88.362 + (13.397 × 体重kg) + (4.799 × 身高cm) - (5.677 × 年龄)
     - 女性 BMR = 447.593 + (9.247 × 体重kg) + (3.098 × 身高cm) - (4.330 × 年龄)
     - 活动系数：
       - 久坐（几乎不运动）：BMR × 1.2
       - 轻度活动（每周 1-3 天）：BMR × 1.375
       - 中度活动（每周 3-5 天）：BMR × 1.55
       - 高度活动（每周 6-7 天）：BMR × 1.725
   - inputSchema 需要包含：gender, age, height, weight, activity_level

2. 添加一个 Resource：health://foods/list
   - 功能：返回所有支持查询的食物列表
   - 格式：JSON 数组

3. 添加一个 Prompt 模板：diet_analysis
   - 功能：生成饮食分析的 Prompt
   - 参数：diet_record（饮食记录文本）
   - 返回：一个结构化的分析 Prompt

提示：
    - 参考 server.py 中已有的工具定义方式
    - 使用 @server.list_resources() 和 @server.read_resource() 添加 Resources
    - 使用 @server.list_prompts() 和 @server.get_prompt() 添加 Prompts
    - 记得在 list_tools() 中添加新工具的定义
    - 记得在 call_tool() 中添加新工具的路由

完成后：
    使用 MCP Inspector 测试所有工具是否正常工作
"""

# ============ 在这里编写你的代码 ============

from mcp.server import Server
from mcp.types import Tool, TextContent, Resource, Prompt, PromptArgument, PromptMessage, GetPromptResult
import asyncio
import json

server = Server("health-assistant-extended")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # 保留原有的两个工具...
        Tool(
            name="query_nutrition",
            description="查询食物的营养成分，包括热量、蛋白质、脂肪、碳水化合物。支持常见食物如水果、主食、肉类等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "food_name":{
                        "type": "string",
                        "description": "食物名称，例如：苹果、米饭、鸡胸肉"
                    }
                },
                "required": ["food_name"]
            }
        ),
        Tool(
            name="calculate_bmi",
            description="根据身高和体重计算 BMI 指数，并给出健康评估（偏瘦/正常/偏胖/肥胖）",
            inputSchema={
                "type": "object",
                "properties": {
                    "height": {
                        "type": "number",
                        "description": "身高，单位 cm"
                    },
                    "weight": {
                        "type": "number",
                        "description": "体重，单位 kg"
                    }
                },
                "required": ["height", "weight"]
            }
        ),
        # 提示：inputSchema 需要包含 gender, age, height, weight, activity_level
        # pass
        Tool(
            name="calculate_daily_calories",
            description="根据性别、年龄、身高、体重、活动水平，计算每日推荐热量",
            inputSchema={
                "type": "object",
                "properties": {
                    "gender": {
                        "type": "string",
                        "description": "性别，例如：male 或 female"
                    },
                    "age": {
                        "type": "number",
                        "description": "年龄，单位：岁，例如：30"
                    },
                    "height": {
                        "type": "number",
                        "description": "身高，单位：厘米（cm），例如：175"
                    },
                    "weight": {
                        "type": "number",
                        "description": "体重，单位：公斤（kg），例如：70"
                    },
                    "activity_level": {
                        "type": "string",
                        "description": "活动水平，例如：sedentary（久坐）、light（轻度活动）、moderate（中度活动）、active（高度活动）"
                    },
                },
                "required": ["gender", "age", "height", "weight", "activity_level"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "query_nutrition":
        # 调用营养查询逻辑
        food_name = arguments["food_name"]
        result = query_nutrition_logic(food_name)
        return [TextContent(type="text", text=result)]

    elif name == "calculate_bmi":
        # 调用 BMI 计算逻辑
        height = arguments["height"]
        weight = arguments["weight"]
        result = calculate_bmi_logic(height, weight)
        return [TextContent(type="text", text=result)]
    elif name == "calculate_daily_calories":
        # 调用每日热量计算逻辑
        gender = arguments["gender"]
        age = arguments["age"]
        height = arguments["height"]
        weight = arguments["weight"]
        activity_level = arguments["activity_level"]
        result = calculate_daily_calories_logic(gender, age, height, weight, activity_level)
        return [TextContent(type="text", text=result)]

    else:
        return [TextContent(type="text", text=f"未知工具: {name}")]


# TODO 3: 实现 calculate_daily_calories 逻辑
def calculate_daily_calories_logic(
        gender: str,
        age: int,
        height: float,
        weight: float,
        activity_level: str
) -> str:
    """
    使用 Harris-Benedict 公式计算每日推荐热量

    参数：
        gender: 性别（"male" 或 "female"）
        age: 年龄
        height: 身高（cm）
        weight: 体重（kg）
        activity_level: 活动水平
            - "sedentary": 久坐
            - "light": 轻度活动
            - "moderate": 中度活动
            - "active": 高度活动
    """
    # 1. 根据性别计算 BMR
    if gender == "male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    elif gender == "female":
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    else:
        return "无效的性别输入，请使用 'male' 或 'female'"
    # 2. 根据活动水平计算每日热量需求
    activity_factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725
    }
    if activity_level not in activity_factors:
        return "无效的活动水平输入，请使用 'sedentary', 'light', 'moderate' 或 'active'"

    # 3. 计算每日热量需求
    daily_calories = bmr * activity_factors[activity_level]

    return f"""每日推荐热量计算结果：
- 性别：{gender}
- 年龄：{age} 岁
- 身高：{height} cm
- 体重：{weight} kg
- 活动水平：{activity_level}
- 基础代谢率（BMR）：{bmr:.0f} kcal
- 每日推荐热量：{daily_calories:.0f} kcal

说明：
- 久坐（sedentary）：几乎不运动
- 轻度活动（light）：每周运动 1-3 天
- 中度活动（moderate）：每周运动 3-5 天
- 高度活动（active）：每周运动 6-7 天"""

def query_nutrition_logic(food_name: str) -> str:
    """
    查询食物营养成分

    实际项目中应该：
    1. 查询数据库（Supabase）
    2. 调用第三方营养 API
    3. 使用 RAG 从知识库检索

    这里为了演示，使用硬编码的数据
    """
    # 模拟营养数据库
    nutrition_db = {
        "苹果": {"热量": 52, "蛋白质": 0.3, "脂肪": 0.2, "碳水": 13.8},
        "香蕉": {"热量": 89, "蛋白质": 1.1, "脂肪": 0.3, "碳水": 22.8},
        "米饭": {"热量": 116, "蛋白质": 2.6, "脂肪": 0.3, "碳水": 25.9},
        "鸡胸肉": {"热量": 133, "蛋白质": 24.6, "脂肪": 5.0, "碳水": 0.0},
        "鸡蛋": {"热量": 147, "蛋白质": 12.8, "脂肪": 10.6, "碳水": 1.3},
    }

    if food_name in nutrition_db:
        data = nutrition_db[food_name]
        return f"""{food_name}的营养成分（每100g）：
- 热量：{data['热量']} kcal
- 蛋白质：{data['蛋白质']} g
- 脂肪：{data['脂肪']} g
- 碳水化合物：{data['碳水']} g"""
    else:
        return f"抱歉，暂无 {food_name} 的营养数据。当前支持的食物：苹果、香蕉、米饭、鸡胸肉、鸡蛋"

def calculate_bmi_logic(height: float, weight: float) -> str:
    """
    计算 BMI 指数

    BMI 计算公式：
        BMI = 体重(kg) / 身高(m)^2

    健康标准（中国标准）：
        < 18.5: 偏瘦
        18.5 - 23.9: 正常
        24.0 - 27.9: 偏胖
        >= 28.0: 肥胖
    """
    # 身高转换为米
    height_m = height / 100

    # 计算 BMI
    bmi = weight / (height_m ** 2)

    # 健康评估
    if bmi < 18.5:
        status = "偏瘦"
        advice = "建议增加营养摄入，适当增重"
    elif bmi < 24:
        status = "正常"
        advice = "保持当前体重，继续健康饮食"
    elif bmi < 28:
        status = "偏胖"
        advice = "建议控制饮食，增加运动"
    else:
        status = "肥胖"
        advice = "建议咨询医生，制定减重计划"

    return f"""BMI 计算结果：
- 身高：{height} cm
- 体重：{weight} kg
- BMI：{bmi:.1f}
- 评估：{status}
- 建议：{advice}"""

# TODO 4: 添加 Resources
@server.list_resources()
async def list_resources() -> list[Resource]:
    """
    返回可用的资源列表

    Resources 用于提供静态数据或配置信息，
    通过 URI 访问，不需要参数。
    """
    return [
        Resource(
            uri="health://foods/list",
            name="支持的食物列表",
            description="返回当前系统支持查询营养信息的所有食物列表",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """
    读取指定 URI 的资源内容

    参数：
        uri: 资源 URI（例如：health://foods/list）

    返回：
        资源内容（JSON 格式）
    """
    if uri == "health://foods/list":
        # 返回支持的食物列表
        foods_list = {
            "foods": [
                {"name": "苹果", "category": "水果", "热量": 52},
                {"name": "香蕉", "category": "水果", "热量": 89},
                {"name": "米饭", "category": "主食", "热量": 116},
                {"name": "鸡胸肉", "category": "肉类", "热量": 133},
                {"name": "鸡蛋", "category": "蛋类", "热量": 147}
            ],
            "total": 5,
            "last_updated": "2024-01-01"
        }
        return json.dumps(foods_list, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": f"未知资源: {uri}"}, ensure_ascii=False)


# TODO 5: 添加 Prompts
@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    """
    返回可用的 Prompt 模板列表

    Prompts 用于提供预定义的交互模式，
    帮助 Agent 更好地完成特定任务。
    """
    return [
        Prompt(
            name="diet_analysis",
            description="分析用户的饮食记录，给出营养评估和改进建议",
            arguments=[
                PromptArgument(
                    name="diet_record",
                    description="用户的饮食记录文本，例如：早餐吃了一个苹果和一个鸡蛋",
                    required=True
                )
            ]
        )
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict) -> GetPromptResult:
    """
    获取填充好参数的 Prompt

    参数：
        name: Prompt 名称
        arguments: Prompt 参数

    返回：
        填充好的 Prompt 消息
    """
    if name == "diet_analysis":
        diet_record = arguments.get("diet_record", "")

        # 构建分析 Prompt
        prompt_text = f"""请分析以下饮食记录，并给出营养评估和改进建议：

饮食记录：
{diet_record}

请按以下步骤分析：
1. 识别记录中提到的所有食物
2. 使用 query_nutrition 工具查询每种食物的营养成分
3. 汇总计算总热量、蛋白质、脂肪、碳水化合物
4. 评估营养均衡性（蛋白质、脂肪、碳水比例是否合理）
5. 给出具体的改进建议

注意：
- 如果某种食物不在数据库中，请说明并跳过
- 建议要具体可行，不要泛泛而谈
- 考虑用户的整体营养摄入情况"""

        return GetPromptResult(
            description="饮食分析 Prompt",
            messages=[
                PromptMessage(
                    role="user",
                    content={"type": "text", "text": prompt_text}
                )
            ]
        )
    else:
        raise ValueError(f"未知 Prompt: {name}")


# ============ 启动 Server ============

async def main():
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
