"""
数据库查询 MCP Server - SSE/HTTP 版本

支持局域网/远程访问的 MCP Server。

使用方式：
    python server_sse.py --host 0.0.0.0 --port 8000

同事连接方式（Claude Desktop 配置）：
    {
      "mcpServers": {
        "db-query": {
          "url": "http://你的IP:8000/sse"
        }
      }
    }
"""

import os
import sys
import argparse
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent

from core import (
    SkillManager,
    DatabaseManager,
    DatabaseConfig,
    LLMClient,
    LLMConfig,
    AgentHarness
)


# ============ 创建 MCP Server 实例 ============

server = Server("db-query-assistant")

# 全局变量
agent_harness: AgentHarness = None
skill_manager: SkillManager = None


# ============ 定义 MCP 工具 ============

@server.list_tools()
async def list_tools() -> list[Tool]:
    """返回 MCP Server 提供的所有工具"""
    return [
        Tool(
            name="query_database",
            description="根据自然语言问题查询数据库，自动生成 SQL 并执行",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "用户的查询问题，例如：查询所有正常状态的用户"
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="list_modules",
            description="列出所有可用的数据库模块",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_module_detail",
            description="查看指定模块的详细信息（表结构、SOP、约束等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "description": "模块名称，例如：user_module"
                    }
                },
                "required": ["module_name"]
            }
        ),
        Tool(
            name="sync_schema_check",
            description="检查数据库表结构变更。扫描指定表并与模块定义对比，返回差异报告（不执行更新）。",
            inputSchema={
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
        ),
        Tool(
            name="sync_schema_apply",
            description="应用表结构更新。将数据库表结构同步到模块文件。只有在用户确认后才调用。",
            inputSchema={
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
        ),
        Tool(
            name="update_skill_modules",
            description="更新 SKILL.md 的 modules 列表，添加新模块。当用户明确要求更新 SKILL.md 时使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "description": "要添加到 SKILL.md 的模块名称"
                    }
                },
                "required": ["module_name"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用请求"""
    try:
        if name == "query_database":
            question = arguments.get("question", "")
            result = agent_harness.query_database(question)
            return [TextContent(type="text", text=result)]

        elif name == "list_modules":
            modules = skill_manager.list_available_modules()
            result = "可用的数据库模块：\n\n" + "\n".join([f"- {m}" for m in modules])
            return [TextContent(type="text", text=result)]

        elif name == "get_module_detail":
            module_name = arguments.get("module_name", "")
            content = skill_manager.get_module_detail(module_name)
            if content:
                return [TextContent(type="text", text=content)]
            else:
                return [TextContent(type="text", text=f"模块 '{module_name}' 不存在")]

        elif name == "sync_schema_check":
            module_name = arguments.get("module_name", "")
            table_names = arguments.get("table_names", [])
            result = agent_harness.sync_schema_check(module_name, table_names)
            return [TextContent(type="text", text=result)]

        elif name == "sync_schema_apply":
            module_name = arguments.get("module_name", "")
            table_names = arguments.get("table_names", [])
            result = agent_harness.sync_schema_apply(module_name, table_names)
            return [TextContent(type="text", text=result)]

        elif name == "update_skill_modules":
            module_name = arguments.get("module_name", "")
            result = skill_manager.update_skill_modules(module_name)
            if result.get("success"):
                if result.get("already_exists"):
                    return [TextContent(type="text", text=f"模块 {module_name} 已在 SKILL.md 中")]
                else:
                    return [TextContent(type="text", text=f"已将 {module_name} 添加到 SKILL.md\n当前模块列表: {result.get('modules', [])}")]
            else:
                return [TextContent(type="text", text=f"更新失败: {result.get('error', '未知错误')}")]

        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]

    except Exception as e:
        error_msg = f"工具调用失败: {type(e).__name__}: {str(e)}"
        print(f"[错误] {error_msg}", file=sys.stderr)
        return [TextContent(type="text", text=error_msg)]


# ============ 初始化组件 ============

def initialize_components():
    """初始化所有组件"""
    global agent_harness, skill_manager

    print("="*60)
    print("数据库查询 MCP Server (SSE) 启动中...")
    print("="*60)

    # 加载配置
    db_config = DatabaseConfig(
        host=os.getenv("DB_HOST", "172.25.0.19"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "ad_coin"),
        pool_size=int(os.getenv("DB_POOL_SIZE", "5"))
    )

    llm_config = LLMConfig(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model=os.getenv("LLM_MODEL", "qwen-plus")
    )

    skills_dir = os.getenv("SKILLS_DIR", "./skills")

    print(f"\n[配置]")
    print(f"  数据库: {db_config.host}:{db_config.port}/{db_config.database}")
    print(f"  LLM: {llm_config.model}")
    print(f"  Skills 目录: {skills_dir}")

    # 初始化组件
    print(f"\n[初始化组件]")

    try:
        db_manager = DatabaseManager(db_config)
        print("  [OK] 数据库管理器")
    except Exception as e:
        print(f"  [FAIL] 数据库管理器初始化失败: {e}")
        sys.exit(1)

    llm_client = LLMClient(llm_config)
    print("  [OK] LLM 客户端")

    skill_manager = SkillManager(skills_dir)
    print("  [OK] Skills 管理器")

    agent_harness = AgentHarness(
        skill_manager=skill_manager,
        db_manager=db_manager,
        llm_client=llm_client,
        max_iterations=10
    )
    print("  [OK] Agent Harness")

    # 测试连接
    print(f"\n[测试连接]")

    db_result = db_manager.test_connection()
    if db_result["connected"]:
        print(f"  [OK] 数据库连接成功: {db_result['database']} (版本 {db_result['version']})")
    else:
        print(f"  [FAIL] 数据库连接失败: {db_result['error']}")
        sys.exit(1)

    llm_result = llm_client.test_connection()
    if llm_result["connected"]:
        print(f"  [OK] LLM 连接成功: {llm_result['model']}")
    else:
        print(f"  [FAIL] LLM 连接失败: {llm_result['error']}")
        sys.exit(1)


# ============ SSE 传输层 ============

sse_transport = SseServerTransport("/messages")


from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response


async def handle_sse(request):
    """处理 SSE 连接"""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0],
            streams[1],
            server.create_initialization_options()
        )
    # 虽然 SSE 传输层已经发送了响应，但 Starlette 仍需要返回值
    # 返回空 Response 避免 TypeError
    return Response(status_code=200)


async def handle_messages(request):
    """处理消息"""
    await sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )
    # 同上
    return Response(status_code=200)


# ============ Starlette 应用 ============

app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)


# ============ 主函数 ============

def main():
    """启动 SSE Server"""
    parser = argparse.ArgumentParser(description="数据库查询 MCP Server (SSE)")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址（默认：0.0.0.0）")
    parser.add_argument("--port", type=int, default=8000, help="监听端口（默认：8000）")
    args = parser.parse_args()

    # 初始化组件
    initialize_components()

    print(f"\n[启动 SSE Server]")
    print(f"  监听地址: {args.host}:{args.port}")
    print(f"  SSE 端点: http://{args.host}:{args.port}/sse")
    print(f"\n同事连接方式（Claude Desktop 配置）：")
    print(f'  {{"url": "http://你的IP:{args.port}/sse"}}')
    print(f"\n等待连接...\n")

    # 启动 uvicorn
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
