# 课程 27：MCP 协议深度解析

## 学习目标
1. 理解 MCP（Model Context Protocol）的设计理念和解决的问题
2. 掌握 MCP 的三层架构：Host / Client / Server
3. 深入理解 MCP 协议的通信机制和消息格式
4. 能开发一个完整的 MCP Server
5. 理解 MCP 如何标准化 Agent 的工具生态

## 为什么这节课重要？

MCP 是 Anthropic 提出的开放协议，正在成为 Agent 工具接入的标准：
- **碎片化问题**：每个框架有自己的工具定义方式，互不兼容
- **MCP 的价值**：一次开发，所有支持 MCP 的 Agent 都能用
- **类比**：MCP 之于 Agent 工具 ≈ USB 之于外设 ≈ HTTP 之于 Web

## 课程内容

### 1. MCP 的设计理念（25 分钟）

#### 1.1 Agent 工具生态的碎片化问题
```
现状：
├─ LangChain 的 @tool 装饰器
├─ OpenAI 的 Function Calling JSON Schema
├─ CrewAI 的 Tool 类
├─ 自定义的工具接口
└─ 每个框架都要适配一遍

MCP 的解决方案：
├─ 统一的工具描述协议
├─ 标准化的通信方式
├─ 一次开发，处处可用
└─ 类比：JDBC 统一了 Java 的数据库访问
```

#### 1.2 MCP 的核心概念
```
MCP 协议的三个角色：

Host（宿主）：运行 Agent 的应用
├─ 例如：Claude Desktop、VS Code、自定义 Agent 应用
├─ 职责：管理 Client 连接、安全策略、用户交互
│
Client（客户端）：Host 内部的 MCP 连接管理器
├─ 每个 Client 连接一个 Server
├─ 职责：协议协商、消息路由、能力发现
│
Server（服务器）：提供工具和资源的服务
├─ 例如：文件系统 Server、数据库 Server、API Server
├─ 职责：暴露工具、提供资源、处理调用
```

### 2. MCP 协议架构深度解析（35 分钟）

#### 2.1 通信层
```
传输方式：
├─ stdio：标准输入输出（本地进程间通信）
│   - 适合：本地工具、CLI 工具
│   - 类比：Unix 管道
│
└─ SSE（Server-Sent Events）：HTTP 长连接
    - 适合：远程服务、Web 应用
    - 类比：WebSocket 的单向版本

消息格式：JSON-RPC 2.0
```

#### 2.2 协议层
```python
# MCP 消息格式（JSON-RPC 2.0）

# 请求
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "query_food_nutrition",
        "arguments": {"food_name": "苹果"}
    }
}

# 响应
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "content": [
            {"type": "text", "text": "苹果：热量 52kcal/100g..."}
        ]
    }
}
```

#### 2.3 能力协商
```
连接建立时的握手流程：

Client → Server: initialize（声明客户端能力）
Server → Client: initialize 响应（声明服务端能力）
Client → Server: initialized（确认）

能力包括：
├─ tools：工具调用
├─ resources：资源访问
├─ prompts：Prompt 模板
└─ sampling：LLM 采样（Server 请求 Client 调用 LLM）
```

### 3. MCP Server 的三大能力（30 分钟）

#### 3.1 Tools（工具）
```python
# 工具定义
{
    "name": "query_food_nutrition",
    "description": "查询食物的营养成分",
    "inputSchema": {
        "type": "object",
        "properties": {
            "food_name": {"type": "string", "description": "食物名称"}
        },
        "required": ["food_name"]
    }
}
```

#### 3.2 Resources（资源）
```python
# 资源：Agent 可以读取的数据源
# 类比：REST API 的 GET 端点

# 资源列表
{
    "resources": [
        {
            "uri": "health://user/profile",
            "name": "用户健康档案",
            "mimeType": "application/json"
        }
    ]
}
```

#### 3.3 Prompts（Prompt 模板）
```python
# Prompt 模板：预定义的交互模式
{
    "prompts": [
        {
            "name": "analyze_diet",
            "description": "分析饮食记录",
            "arguments": [
                {"name": "diet_record", "description": "饮食记录文本"}
            ]
        }
    ]
}
```

### 4. 实战：开发健康管家 MCP Server（50 分钟）

#### 4.1 项目结构
```
health-mcp-server/
├─ server.py           # MCP Server 主文件
├─ tools/
│   ├─ nutrition.py    # 食物营养查询工具
│   └─ bmi.py          # BMI 计算工具
├─ resources/
│   └─ knowledge.py    # 健康知识资源
└─ requirements.txt
```

#### 4.2 使用 Python MCP SDK 开发
```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("health-assistant")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="query_nutrition",
            description="查询食物营养成分",
            inputSchema={...}
        ),
        Tool(
            name="calculate_bmi",
            description="计算 BMI 指数",
            inputSchema={...}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_nutrition":
        result = query_nutrition(arguments["food_name"])
        return [TextContent(type="text", text=result)]
    elif name == "calculate_bmi":
        result = calculate_bmi(arguments["height"], arguments["weight"])
        return [TextContent(type="text", text=result)]
```

#### 4.3 测试 MCP Server
- 使用 MCP Inspector 调试
- 在 Claude Desktop 中配置和测试
- 在自定义 Agent 中集成

### 5. MCP 与框架的集成（20 分钟）

#### 5.1 LangChain + MCP
#### 5.2 LangGraph + MCP
#### 5.3 MCP 在健康管家项目中的定位

### 6. 练习（30 分钟）

#### 练习 1：开发一个食物营养查询 MCP Server
#### 练习 2：在 Agent 中集成 MCP Server

## 预计时长
约 3 小时

## 完成标准
- 理解 MCP 协议的设计理念和架构
- 掌握 Host/Client/Server 三层模型
- 能开发一个完整的 MCP Server
- 理解 MCP 在 Agent 生态中的定位
