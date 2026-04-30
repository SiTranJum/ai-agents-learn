"""
交互式数据库查询 Agent

直接对话的 Agent，不需要 MCP 协议。
复用所有 core/ 的业务逻辑。

使用方式：
    python interactive_agent.py

功能：
1. 查询数据库（自然语言 → SQL）
2. 查看模块信息
3. 同步表结构
4. 更新 SKILL.md
"""

import os
import sys
from openai import OpenAI

from core import (
    SkillManager,
    DatabaseManager,
    DatabaseConfig,
    LLMClient,
    LLMConfig,
    AgentHarness
)


# ============ 配置 ============

def load_config():
    """从环境变量加载配置"""
    db_config = DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "test")
    )

    llm_config = LLMConfig(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model=os.getenv("LLM_MODEL", "qwen-plus")
    )

    skills_dir = os.getenv("SKILLS_DIR", "./skills")

    return db_config, llm_config, skills_dir


# ============ 初始化组件 ============

def initialize_components():
    """初始化所有组件"""
    print("\n" + "="*60)
    print("数据库查询 Agent 启动中...")
    print("="*60)

    db_config, llm_config, skills_dir = load_config()

    print(f"\n[配置]")
    print(f"  数据库: {db_config.host}:{db_config.port}/{db_config.database}")
    print(f"  LLM: {llm_config.model}")
    print(f"  Skills 目录: {skills_dir}")

    print(f"\n[初始化组件]")

    # 初始化数据库管理器
    try:
        db_manager = DatabaseManager(db_config)
        print("  [OK] 数据库管理器")
    except Exception as e:
        print(f"  [FAIL] 数据库管理器初始化失败: {e}")
        sys.exit(1)

    # 初始化 LLM 客户端
    llm_client = LLMClient(llm_config)
    print("  [OK] LLM 客户端")

    # 初始化 Skills 管理器
    skill_manager = SkillManager(skills_dir)
    print("  [OK] Skills 管理器")

    # 初始化 Agent Harness
    agent_harness = AgentHarness(
        skill_manager=skill_manager,
        db_manager=db_manager,
        llm_client=llm_client
    )
    print("  [OK] Agent Harness")

    # 测试连接
    print(f"\n[测试连接]")
    db_result = db_manager.test_connection()
    if db_result["connected"]:
        print(f"  [OK] 数据库: {db_result['database']} (版本 {db_result['version']})")
    else:
        print(f"  [FAIL] 数据库连接失败: {db_result['error']}")
        sys.exit(1)

    llm_result = llm_client.test_connection()
    if llm_result["connected"]:
        print(f"  [OK] LLM: {llm_result['model']}")
    else:
        print(f"  [FAIL] LLM 连接失败: {llm_result['error']}")
        sys.exit(1)

    return agent_harness, skill_manager, llm_client


# ============ 工具定义 ============

def get_tools():
    """定义 Agent 可用的工具"""
    return [
        {
            "type": "function",
            "function": {
                "name": "query_database",
                "description": "根据自然语言问题查询数据库，自动生成 SQL 并执行",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "用户的查询问题，例如：查询所有正常状态的用户"
                        }
                    },
                    "required": ["question"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_modules",
                "description": "列出所有可用的数据库模块",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_module_detail",
                "description": "查看指定模块的详细信息（表结构、SOP、约束等）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "module_name": {
                            "type": "string",
                            "description": "模块名称，例如：user_module"
                        }
                    },
                    "required": ["module_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sync_schema_check",
                "description": "检查数据库表结构变更。扫描指定表并与模块定义对比，返回差异报告（不执行更新）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "module_name": {
                            "type": "string",
                            "description": "模块名称，例如：user_module"
                        },
                        "table_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "要检查的表名列表，例如：['users', 'login_logs']"
                        }
                    },
                    "required": ["module_name", "table_names"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sync_schema_apply",
                "description": "应用表结构更新。将数据库表结构同步到模块文件。只有在用户确认后才调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "module_name": {
                            "type": "string",
                            "description": "模块名称，例如：user_module"
                        },
                        "table_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "要更新的表名列表，例如：['users', 'login_logs']"
                        }
                    },
                    "required": ["module_name", "table_names"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_skill_modules",
                "description": "更新 SKILL.md 的 modules 列表，添加新模块。当用户明确要求更新 SKILL.md 时使用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "module_name": {
                            "type": "string",
                            "description": "要添加到 SKILL.md 的模块名称"
                        }
                    },
                    "required": ["module_name"]
                }
            }
        }
    ]


# ============ 工具调用处理 ============

def call_tool(tool_name, arguments, agent_harness, skill_manager):
    """调用工具并返回结果"""
    try:
        if tool_name == "query_database":
            question = arguments.get("question", "")
            return agent_harness.query_database(question)

        elif tool_name == "list_modules":
            modules = skill_manager.list_available_modules()
            return "可用的数据库模块：\n\n" + "\n".join([f"- {m}" for m in modules])

        elif tool_name == "get_module_detail":
            module_name = arguments.get("module_name", "")
            content = skill_manager.get_module_detail(module_name)
            if content:
                return content
            else:
                return f"模块 '{module_name}' 不存在"

        elif tool_name == "sync_schema_check":
            module_name = arguments.get("module_name", "")
            table_names = arguments.get("table_names", [])
            return agent_harness.sync_schema_check(module_name, table_names)

        elif tool_name == "sync_schema_apply":
            module_name = arguments.get("module_name", "")
            table_names = arguments.get("table_names", [])
            return agent_harness.sync_schema_apply(module_name, table_names)

        elif tool_name == "update_skill_modules":
            module_name = arguments.get("module_name", "")
            result = skill_manager.update_skill_modules(module_name)
            if result.get("success"):
                if result.get("already_exists"):
                    return f"模块 {module_name} 已在 SKILL.md 中"
                else:
                    return f"已将 {module_name} 添加到 SKILL.md\n当前模块列表: {result.get('modules', [])}"
            else:
                return f"更新失败: {result.get('error', '未知错误')}"

        else:
            return f"未知工具: {tool_name}"

    except Exception as e:
        return f"工具调用失败: {str(e)}"


# ============ Agent 循环 ============

def agent_loop(agent_harness, skill_manager, llm_client):
    """Agent 主循环"""
    print("\n" + "="*60)
    print("数据库查询助手 Agent 已启动（输入 quit 退出）")
    print("="*60)

    tools = get_tools()

    # System Prompt
    system_prompt = """你是数据库查询助手 Agent，可以帮用户：

1. **查询数据库**：使用 query_database 工具
   - 用户问："查询所有正常状态的用户"
   - 用户问："统计订单数量"

2. **查看模块信息**：使用 list_modules 和 get_module_detail 工具
   - 用户问："有哪些模块"
   - 用户问："user_module 包含哪些表"

3. **同步表结构**：使用 sync_schema_check 和 sync_schema_apply 工具
   - 用户说："新增了 challenge 模块，包含 4 个表：challenge_config、challenge_progress、challenge_task、challenge_task_config"
   - 用户说："users 表新增了 vip_level 字段"

   流程：
   a) 如果是新增模块，直接调用 sync_schema_apply（会自动创建模块文件）
   b) 如果是更新现有模块，先调用 sync_schema_check 检查差异，再调用 sync_schema_apply
   c) 将结果用自然语言解释给用户

重要：
- 识别用户意图，选择正确的工具
- 新增模块时，直接调用 sync_schema_apply，无需先 check（因为模块不存在）
- 更新现有模块时，先 check 再 apply
- 将工具返回的结果用自然语言解释给用户
"""

    # 对话历史
    messages = [{"role": "system", "content": system_prompt}]

    while True:
        # 获取用户输入
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n再见！")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "q"]:
            print("\n再见！")
            break

        # 添加用户消息
        messages.append({"role": "user", "content": user_input})

        # Agent 循环（最多 5 轮）
        for iteration in range(5):
            # 调用 LLM
            response = llm_client.chat(messages, tools)
            if response is None:
                print("\n助手: LLM 调用失败，请重试。")
                break

            message = response.choices[0].message

            # 检查是否调用工具
            if message.tool_calls:
                # 将 LLM 的决策加入历史
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })

                # 处理每个工具调用
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    import json
                    arguments = json.loads(tool_call.function.arguments)

                    print(f"  [调用工具] {tool_name}({arguments})")

                    # 调用工具
                    result = call_tool(tool_name, arguments, agent_harness, skill_manager)

                    print(f"  [结果] {result[:200]}{'...' if len(result) > 200 else ''}")

                    # 将工具结果返回给 LLM
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

            else:
                # LLM 给出最终回复
                print(f"\n助手: {message.content}")
                messages.append({"role": "assistant", "content": message.content})
                break


# ============ 主函数 ============

def main():
    """主函数"""
    # 初始化组件
    agent_harness, skill_manager, llm_client = initialize_components()

    # 启动 Agent 循环
    agent_loop(agent_harness, skill_manager, llm_client)


if __name__ == "__main__":
    main()
