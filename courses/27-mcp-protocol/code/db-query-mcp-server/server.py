"""
数据库查询 MCP Server - 主入口

这是 MCP Server 的主入口文件，负责：
1. 初始化各个组件（SkillManager、DatabaseManager、LLMClient、AgentHarness）
2. 定义 MCP 工具（query_database、list_skills 等）
3. 处理工具调用
4. 启动 MCP Server

这个文件提供框架，核心逻辑在 core/ 模块中实现。

类比 Java：
    @SpringBootApplication
    public class Application {
        public static void main(String[] args) {
            SpringApplication.run(Application.class, args);
        }
    }
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio
import os
import sys
import io

# 强制 stderr 使用 UTF-8，避免 Windows GBK 乱码
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from core import (
    SkillManager,
    DatabaseManager,
    DatabaseConfig,
    LLMClient,
    LLMConfig,
    AgentHarness
)


# ============ 日志输出到 stderr ============
# stdio 模式下 stdout 是 MCP 协议通道，print 会污染协议数据
# 所有日志必须输出到 stderr
def log(msg: str):
    print(msg, file=sys.stderr, flush=True)

# ============ 创建 MCP Server 实例 ============

# Server(name) - 创建 MCP Server
# name: Server 的唯一标识符
server = Server("db-query-assistant")

# 全局变量（在 main() 中初始化）
# 类比 Spring 的 @Autowired 依赖注入
agent_harness: AgentHarness = None
skill_manager: SkillManager = None


# ============ 定义 MCP 工具 ============

@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    返回 MCP Server 提供的所有工具

    这个方法会在 Client 连接时被调用。

    返回：
        工具列表，每个工具包含：
        - name: 工具名称
        - description: 工具描述（LLM 根据这个决定是否调用）
        - inputSchema: 参数 Schema（JSON Schema 格式）

    类比 Java：
        @GetMapping("/tools")
        public List<Tool> listTools() {
            return Arrays.asList(
                new Tool("query_database", "查询数据库", schema),
                new Tool("list_skills", "列出所有 skills", schema)
            );
        }
    """
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
    """
    处理工具调用请求

    当 Agent 决定调用工具时，会发送请求到这个方法。

    参数：
        name: 工具名称（对应 list_tools 返回的 Tool.name）
        arguments: 工具参数（dict 格式）

    返回：
        工具执行结果（TextContent 列表）

    类比 Java：
        @PostMapping("/tools/call")
        public ToolResult callTool(
            @RequestParam String name,
            @RequestBody Map<String, Object> arguments
        ) {
            if ("query_database".equals(name)) {
                return queryDatabase(arguments);
            }
            // ...
        }
    """
    try:
        if name == "query_database":
            # 调用 Agent Harness 处理查询
            question = arguments.get("question", "")
            result = agent_harness.query_database(question)
            return [TextContent(type="text", text=result)]

        elif name == "list_modules":
            # 列出所有可用模块
            modules = skill_manager.list_available_modules()
            result = "可用的数据库模块：\n\n" + "\n".join([f"- {m}" for m in modules])
            return [TextContent(type="text", text=result)]

        elif name == "get_module_detail":
            # 获取模块详细信息
            module_name = arguments.get("module_name", "")
            content = skill_manager.get_module_detail(module_name)

            if content:
                return [TextContent(type="text", text=content)]
            else:
                return [TextContent(type="text", text=f"模块 '{module_name}' 不存在")]

        elif name == "sync_schema_check":
            # 检查表结构变更
            module_name = arguments.get("module_name", "")
            table_names = arguments.get("table_names", [])
            result = agent_harness.sync_schema_check(module_name, table_names)
            return [TextContent(type="text", text=result)]

        elif name == "sync_schema_apply":
            # 应用表结构更新
            module_name = arguments.get("module_name", "")
            table_names = arguments.get("table_names", [])
            result = agent_harness.sync_schema_apply(module_name, table_names)
            return [TextContent(type="text", text=result)]

        elif name == "update_skill_modules":
            # 更新 SKILL.md 的 modules 列表
            module_name = arguments.get("module_name", "")
            result = skill_manager.update_skill_modules(module_name)

            if result.get("success"):
                msg = result.get("message", "")
                if result.get("already_exists"):
                    return [TextContent(type="text", text=f"模块 {module_name} 已在 SKILL.md 中")]
                else:
                    return [TextContent(type="text", text=f"已将 {module_name} 添加到 SKILL.md\n当前模块列表: {result.get('modules', [])}")]
            else:
                return [TextContent(type="text", text=f"更新失败: {result.get('error', '未知错误')}")]

        else:
            # 未知工具
            return [TextContent(type="text", text=f"未知工具: {name}")]

    except Exception as e:
        # 错误处理
        error_msg = f"工具调用失败: {type(e).__name__}: {str(e)}"
        log(f"[错误] {error_msg}")
        return [TextContent(type="text", text=error_msg)]


# ============ 主函数 ============

async def main():
    """
    启动 MCP Server

    流程：
    1. 从环境变量加载配置
    2. 初始化各个组件
    3. 测试数据库和 LLM 连接
    4. 启动 MCP Server

    类比 Java：
        @SpringBootApplication
        public class Application {
            public static void main(String[] args) {
                ApplicationContext context = SpringApplication.run(Application.class, args);
                // 初始化组件
            }
        }
    """
    global agent_harness, skill_manager

    log("="*60)
    log("数据库查询 MCP Server 启动中...")
    log("="*60)

    # ============ 1. 加载配置 ============

    # 从环境变量读取配置
    # 类比 Spring 的 @Value("${database.host}")
    db_config = DatabaseConfig(
        host=os.getenv("DB_HOST", "172.25.0.19"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "ad_coin"),
        pool_size=int(os.getenv("DB_POOL_SIZE", "5"))
    )

    llm_config = LLMConfig(
        api_key=os.getenv("LLM_API_KEY", "sk-a4ae611c3f9c4df89a133e621b2b7851"),
        base_url=os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model=os.getenv("LLM_MODEL", "qwen-plus")
    )

    skills_dir = os.getenv("SKILLS_DIR", "./skills")

    log(f"\n[配置]")
    log(f"  数据库: {db_config.host}:{db_config.port}/{db_config.database}")
    log(f"  LLM: {llm_config.model}")
    log(f"  Skills 目录: {skills_dir}")

    # ============ 2. 初始化组件 ============

    log(f"\n[初始化组件]")

    # 初始化数据库管理器
    try:
        db_manager = DatabaseManager(db_config)
        log("  [OK] 数据库管理器")
    except Exception as e:
        log(f"  [FAIL] 数据库管理器初始化失败: {e}")
        return

    # 初始化 LLM 客户端
    llm_client = LLMClient(llm_config)
    log("  [OK] LLM 客户端")

    # 初始化 Skills 管理器
    skill_manager = SkillManager(skills_dir)
    log("  [OK] Skills 管理器")

    agent_harness = AgentHarness(
        skill_manager=skill_manager,
        db_manager=db_manager,
        llm_client=llm_client,
        max_iterations=10
    )
    log("  [OK] Agent Harness")

    log(f"\n[测试连接]")

    db_result = db_manager.test_connection()
    if db_result["connected"]:
        log(f"  [OK] 数据库连接成功: {db_result['database']} (版本 {db_result['version']})")
    else:
        log(f"  [FAIL] 数据库连接失败: {db_result['error']}")
        return

    llm_result = llm_client.test_connection()
    if llm_result["connected"]:
        log(f"  [OK] LLM 连接成功: {llm_result['model']}")
    else:
        log(f"  [FAIL] LLM 连接失败: {llm_result['error']}")
        return

    log(f"\n[启动 MCP Server]")
    log("  等待 Client 连接...")

    log(f"\n[启动 MCP Server]")
    log("  等待 Client 连接...")

    from mcp.server.stdio import stdio_server

    # stdio_server() - 创建基于 stdin/stdout 的通信通道
    # 类比 Java 的 Socket 通信
    async with stdio_server() as (read_stream, write_stream):
        # server.run() - 启动消息循环
        # 类比 Spring Boot 的 Tomcat 启动
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    # 运行异步主函数
    # 类比 Java 的 main() 方法
    asyncio.run(main())


# ============ 使用说明 ============

"""
运行方式：

1. 设置环境变量：
   export DB_HOST=localhost
   export DB_PORT=3306
   export DB_USER=root
   export DB_PASSWORD=your_password
   export DB_NAME=test_db
   export LLM_API_KEY=sk-xxx

2. 运行 Server：
   python server.py

3. 使用 MCP Inspector 测试：
   mcp-inspector python server.py

4. 在 Claude Desktop 中配置：
   {
     "mcpServers": {
       "db-query": {
         "command": "python",
         "args": ["D:/path/to/server.py"],
         "env": {
           "DB_HOST": "localhost",
           "DB_USER": "root",
           "DB_PASSWORD": "password",
           "DB_NAME": "test_db",
           "LLM_API_KEY": "sk-xxx"
         }
       }
     }
   }

练习任务：

1. 完成 core/skill_manager.py 中的 TODO
2. 完成 core/agent_harness.py 中的 TODO
3. 测试整个流程

关键概念：

1. 渐进式上下文注入
   - 第一轮：只加载 skills 摘要
   - 第二轮：加载完整内容
   - 大幅减少 token 消耗

2. Agent 循环
   - LLM 思考 → 决定行动 → 执行工具 → 观察结果
   - 多轮交互，直到得出最终答案

3. MCP 协议
   - Server 对外暴露工具
   - Client 调用工具
   - 标准化的通信协议
"""
