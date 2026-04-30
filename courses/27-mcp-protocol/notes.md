# 第 27 课学习笔记

## 核心概念

### MCP 的本质
- MCP = Agent 工具的标准化协议
- 类比：USB 之于硬件、HTTP 之于 Web、JDBC 之于数据库
- 解决问题：Agent 工具生态的碎片化

### 三层架构
```
Host（宿主应用）
  ↓
Client（MCP 客户端）- 协议管理器
  ↓ MCP 协议
Server（MCP 服务器）- 提供工具
```

**为什么需要三层？**
- Client 封装协议细节，Host 专注业务逻辑
- 类比：浏览器（Host）+ HTTP 客户端库（Client）+ Web 服务器（Server）

### 通信方式

**stdio（标准输入输出）**
- 适合：本地进程间通信
- 类比：Unix 管道
- 用法：Host 启动 Server 进程，通过 stdin/stdout 通信

**SSE（Server-Sent Events）**
- 适合：远程服务、Web 应用
- 类比：WebSocket 的单向版本
- 用法：基于 HTTP 的长连接

### 消息格式：JSON-RPC 2.0

```json
// 请求
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {...}
}

// 响应
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {...}
}
```

### 能力协商（握手流程）

```
1. Client → Server: initialize（声明客户端能力）
2. Server → Client: initialize 响应（声明服务端能力）
3. Client → Server: initialized（确认）
```

## MCP Server 的三大能力

### 1. Tools（工具）
- 用途：让 Agent 执行操作
- 类比：Spring 的 @RestController 方法
- 示例：query_nutrition、calculate_bmi

### 2. Resources（资源）
- 用途：让 Agent 读取数据
- 类比：RESTful 的 GET 端点
- 区别：通过 URI 访问，不需要参数
- 示例：health://user/profile

### 3. Prompts（Prompt 模板）
- 用途：预定义的交互模式
- 类比：模板引擎（Thymeleaf）
- 示例：diet_analysis 模板

## Python MCP SDK 关键 API

### Server 端

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("server-name")

# 定义工具列表
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(...)]

# 处理工具调用
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    return [TextContent(type="text", text="...")]

# 启动 Server（stdio 方式）
from mcp.server.stdio import stdio_server
async with stdio_server() as (read, write):
    await server.run(read, write, server.create_initialization_options())
```

### Client 端

```python
from mcp.client import Client
from mcp.client.stdio import stdio_client

# 连接 Server
async with stdio_client(command="python", args=["server.py"]) as (read, write):
    async with Client(read, write) as client:
        await client.initialize()
        
        # 列出工具
        tools = await client.list_tools()
        
        # 调用工具
        result = await client.call_tool("tool_name", {"arg": "value"})
```

## 与 Java 的类比

| MCP 概念 | Java 类比 |
|---------|----------|
| Host | Spring Boot 应用 |
| Client | JDBC DriverManager |
| Server | MySQL 数据库 |
| Tools | @RestController 方法 |
| Resources | RESTful GET 端点 |
| stdio 通信 | ProcessBuilder + 管道 |
| JSON-RPC | 方法调用 + 返回值 |

## 易混淆点

### Tools vs Resources
- **Tools**：需要参数，执行操作（查询、计算、修改）
- **Resources**：通过 URI 访问，读取数据（配置、知识库）

### MCP vs Agent 框架
- **MCP**：工具接入的标准协议（不负责推理）
- **LangChain/LangGraph**：Agent 框架（负责推理、规划）
- **关系**：框架可以使用 MCP 工具

### stdio vs SSE
- **stdio**：本地进程间通信，简单轻量
- **SSE**：远程 HTTP 通信，支持云服务

## 实战要点

### 开发 MCP Server 的步骤
1. 定义工具列表（`@server.list_tools()`）
2. 实现工具调用路由（`@server.call_tool()`）
3. 实现具体的工具逻辑
4. 启动 Server（stdio 或 SSE）

### 测试 MCP Server 的方式
1. MCP Inspector（官方调试工具）
2. Claude Desktop 配置
3. 自定义 Agent 集成

### 与 LangChain 集成
- 将 MCP Tool 转换为 LangChain Tool
- 包装 MCP 工具调用
- 在 Agent 中使用

## 健康管家项目中的应用

```
健康管家 Agent（Host）
  ↓ MCP 协议
├─ nutrition-server（营养查询工具）
├─ health-data-server（用户数据管理）
└─ knowledge-server（健康知识库）
```

**优势**：
- 工具解耦，独立开发
- 可复用，其他 Agent 也能用
- 易扩展，新增工具只需开发新 Server

## MCP 参数 Schema 详解

### inputSchema 就是 JSON Schema

```python
inputSchema={
    "type": "object",                    # 参数整体是一个对象（固定写法）
    "properties": {                      # 定义每个参数
        "question": {
            "type": "string",            # 参数类型
            "description": "用户的查询问题"  # 参数描述（LLM 看这个）
        }
    },
    "required": ["question"]             # 必填参数列表
}
```

### 字段含义

| 字段 | 含义 | Java 类比 |
|------|------|----------|
| `type` | 参数类型 | `String`, `int`, `boolean` |
| `description` | 参数描述（最重要！） | `@ApiParam` 注解 |
| `enum` | 限定取值范围 | `enum` 枚举类型 |
| `default` | 默认值 | 方法参数默认值 |
| `minimum/maximum` | 数值范围 | `@Min/@Max` 注解 |
| `required` | 必填参数 | `@NotNull` 注解 |

### LLM 如何理解和传参

```
用户说："帮我查一下所有正常状态的用户"

LLM 思考：
1. 用户想查数据库 → 应该调用 query_database 工具
2. question 参数的 description 说"用户的查询问题" → 传用户原话
3. limit 参数是可选的 → 不传，用默认值

LLM 输出：
{
    "name": "query_database",
    "arguments": "{\"question\": \"查询所有正常状态的用户\"}"
}
```

**关键**：`description` 是 LLM 理解参数的唯一依据，写得越清晰，LLM 传参越准确。

### 好的 description 示例

```python
# ❌ 差的 description
"description": "参数"

# ✓ 好的 description
"description": "用户的查询问题，例如：查询所有正常状态的用户"

# ✓ 更好的 description（带约束）
"description": "SQL 语句，必须是 SELECT 开头，禁止 DROP/TRUNCATE"
```

## MCP 装饰器原理

### 装饰器的本质

```python
@server.call_tool()
async def call_tool(name, arguments):
    ...

# 等价于：
async def call_tool(name, arguments):
    ...
call_tool = server.call_tool()(call_tool)
```

### 执行时机：文件加载时立即执行

```python
# server.py

print("1. 文件开始加载")

server = Server("my-server")
print("2. Server 对象创建")

@server.list_tools()        # ← 这里立即执行，注册函数
async def list_tools():
    return [...]

print("3. list_tools 已注册")  # ← server.run() 还没执行

async def main():
    print("4. main 开始")
    await server.run(...)   # ← 只是启动监听，路由表早就准备好了
```

**时间线**：
1. Python 加载文件 → 创建 `server` 对象
2. 遇到 `@server.xxx()` → 立即执行装饰器，注册函数到路由表
3. `server.run()` → 启动消息循环，开始监听请求
4. Client 发请求 → 查路由表，调用对应函数

### 装饰器 vs 直接注册

```python
# 方式 1：用装饰器（推荐）
@server.call_tool()
async def call_tool(name, arguments):
    ...

# 方式 2：直接注册（等价，但不推荐）
async def call_tool(name, arguments):
    ...
server._handlers["tools/call"] = call_tool
```

**为什么用装饰器？**
1. **可读性**：定义和注册在一起，一眼看出函数用途
2. **封装**：不直接操作 `_handlers` 内部实现，通过公开 API

### 装饰器对应的 JSON-RPC method

| 装饰器 | JSON-RPC method | 触发时机 |
|--------|----------------|---------|
| `@server.list_tools()` | `tools/list` | Client 获取工具列表 |
| `@server.call_tool()` | `tools/call` | Client 调用工具 |
| `@server.list_resources()` | `resources/list` | Client 获取资源列表 |
| `@server.read_resource()` | `resources/read` | Client 读取资源 |

### 同个装饰器不能写多次

```python
# ❌ 错误：第二个会覆盖第一个
@server.call_tool()
async def handle_v1(name, arguments):
    ...

@server.call_tool()
async def handle_v2(name, arguments):
    ...  # 只有这个生效

# ✓ 正确：一个函数，内部路由
@server.call_tool()
async def call_tool(name, arguments):
    if name == "tool1":
        return handle_tool1(arguments)
    elif name == "tool2":
        return handle_tool2(arguments)
```

## MCP Client 端集成

### 正确的导入方式（MCP SDK 1.26.0+）

```python
# Server 端
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Client 端
from mcp.client.session import ClientSession          # 不是 Client
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import Tool
```

### Client 使用流程

```python
# 1. 连接 Server
server_params = StdioServerParameters(
    command="python",
    args=["server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # 2. 握手
        await session.initialize()
        
        # 3. 获取工具列表
        result = await session.list_tools()
        mcp_tools = result.tools
        
        # 4. 转换为 OpenAI Function Calling 格式
        openai_tools = [mcp_tool_to_openai(t) for t in mcp_tools]
        
        # 5. 在 Agent 循环中使用
        response = llm.chat.completions.create(
            messages=messages,
            tools=openai_tools
        )
        
        # 6. 调用 MCP 工具
        if response.choices[0].message.tool_calls:
            result = await session.call_tool(tool_name, tool_args)
```

## 开发 MCP 工具的角色分工

### 你只需要写 Server 端

```
开发 MCP 工具 = 只写 Server 端

你写：
  server.py              # MCP Server
  requirements.txt       # 依赖
  README.md              # 使用说明

用户用：
  Claude Desktop（内置 MCP Client）
  VS Code（内置 MCP Client）
  自定义 Agent（用 MCP Client SDK）
```

### Client 端是可选的

```python
# client.py 只是用于：
# 1. 演示如何集成
# 2. 测试 Server 功能
# 3. 学习 MCP 通信流程

# 不是必须的！
```

**类比**：写 REST API 只需要写 Server 端（Spring Boot），不需要写 Client（浏览器、Postman 会调用）。

## 渐进式上下文注入（Skills 设计思想）

### 传统方式的问题

```
System Prompt = 角色定义 + 所有表结构（5000+ tokens）
↓
每次调用都消耗大量 tokens
```

### Skills 渐进式加载

```
第一轮：只加载 Skills 目录（200 tokens）
  LLM: "我需要 user_module skill"

第二轮：加载 user_module.md 详细内容（800 tokens）
  LLM: 生成 SQL

↓
大幅减少 token 消耗，按需加载
```

### Skills 文件结构（Markdown）

```markdown
# Skill: 用户模块

## 模块概述
| 属性 | 值 |
|------|-----|
| 模块名 | user_module |
| 用途 | 用户基本信息管理 |

## SOP（标准操作流程）
### 查询用户信息
1. 优先使用 id 或 username 精确查询
2. 模糊查询必须加 LIMIT

## 约束条件
- 安全约束：禁止查询 password_hash
- 性能约束：必须加 LIMIT

## 表结构
### users（用户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |

## 示例查询
```sql
SELECT * FROM users WHERE status = 1 LIMIT 100;
```
```

## 下一步学习

- 练习 1：扩展 MCP Server（添加新工具、Resources、Prompts）
- 练习 2：在 Agent 中集成 MCP Server
- 练习 3：实现渐进式上下文注入的数据库查询 MCP Server
- 思考：健康管家项目中哪些功能适合做成 MCP Server？
