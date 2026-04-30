# 课程 27：MCP 协议深度解析

## 1. MCP 的设计理念

### 1.1 Agent 工具生态的碎片化问题

想象一下，你开发了一个很棒的工具（比如查询食物营养的工具），你希望它能被各种 Agent 使用：

```
现状的痛点：
├─ LangChain：需要用 @tool 装饰器 + 特定格式
├─ OpenAI Function Calling：需要写 JSON Schema
├─ CrewAI：需要继承 Tool 类
├─ 自定义 Agent：又是另一套接口
└─ 每个框架都要适配一遍，维护成本极高

类比：
就像你开发了一个硬件设备，但：
- 苹果电脑要用 Lightning 接口
- Windows 电脑要用 USB-A 接口
- 新电脑要用 USB-C 接口
→ 你需要为每种接口做一个版本
```

**MCP 的解决方案**：

```
MCP（Model Context Protocol）= Agent 工具的 USB 标准

一次开发 → 所有支持 MCP 的 Agent 都能用

类比：
- MCP 之于 Agent 工具 ≈ USB 之于硬件外设
- MCP 之于 Agent 工具 ≈ HTTP 之于 Web 服务
- MCP 之于 Agent 工具 ≈ JDBC 之于 Java 数据库访问
```

### 1.2 MCP 的核心概念：三层架构

MCP 协议定义了三个角色，理解它们是掌握 MCP 的关键：

```
┌─────────────────────────────────────────┐
│          Host（宿主应用）                │
│  例如：Claude Desktop、VS Code、        │
│        你的自定义 Agent 应用            │
│  职责：管理整体流程、安全策略、UI       │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │     Client（MCP 客户端）          │ │
│  │  每个 Client 连接一个 Server      │ │
│  │  职责：协议协商、消息路由         │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
           ↕ MCP 协议（JSON-RPC 2.0）
┌─────────────────────────────────────────┐
│       Server（MCP 服务器）              │
│  例如：文件系统 Server、数据库 Server   │
│  职责：暴露工具、提供资源、处理调用     │
└─────────────────────────────────────────┘
```

**用 Java 开发类比理解**：

```java
// Host = 你的 Spring Boot 应用
// Client = JDBC DriverManager（管理数据库连接）
// Server = MySQL/PostgreSQL 数据库服务器

// 你的应用代码（Host）
public class MyApp {
    public static void main(String[] args) {
        // 通过 Client 连接 Server
        Connection conn = DriverManager.getConnection(
            "jdbc:mysql://localhost:3306/db"  // Server 地址
        );
        
        // 调用 Server 提供的能力
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery("SELECT * FROM users");
    }
}
```

MCP 的三层架构也是类似的：
- **Host**：你的 Agent 应用（类比 Spring Boot 应用）
- **Client**：MCP 连接管理器（类比 JDBC DriverManager）
- **Server**：提供工具的服务（类比 MySQL 数据库）

### 1.3 为什么需要三层架构？

**为什么不是两层（Host 直接连 Server）？**

```
两层架构的问题：
├─ Host 需要处理协议细节（握手、心跳、重连）
├─ 每个 Host 都要实现一遍协议逻辑
└─ 安全策略、权限管理混在业务代码里

三层架构的好处：
├─ Client 封装了协议细节，Host 只需调用简单 API
├─ Client 可以复用（类比 JDBC Driver）
├─ 安全策略在 Client 层统一管理
└─ Host 专注业务逻辑，Server 专注工具实现
```

**类比理解**：

```
就像 Web 开发：
- 浏览器（Host）：用户交互界面
- HTTP 客户端库（Client）：处理 HTTP 协议细节
- Web 服务器（Server）：提供 API 服务

你不需要在每个网页里实现 HTTP 协议，
浏览器的 fetch() API（Client）帮你搞定了。
```

---

## 2. MCP 协议架构深度解析

### 2.1 通信层：如何传输消息？

MCP 支持两种传输方式，根据场景选择：

#### 方式 1：stdio（标准输入输出）

```
适用场景：本地进程间通信
├─ Host 启动 Server 进程
├─ 通过 stdin/stdout 传递 JSON 消息
└─ 类比：Unix 管道（ls | grep）

优点：
├─ 简单、轻量
├─ 不需要网络配置
└─ 适合本地工具（文件系统、本地数据库）

示例：
Host 进程 → stdin → Server 进程
Host 进程 ← stdout ← Server 进程
```

#### 方式 2：SSE（Server-Sent Events）

```
适用场景：远程服务、Web 应用
├─ 基于 HTTP 的长连接
├─ Server 可以主动推送消息
└─ 类比：WebSocket 的单向版本

优点：
├─ 支持远程访问
├─ 基于 HTTP，防火墙友好
└─ 适合云服务、API 集成

示例：
Host → HTTP POST → Server（调用工具）
Host ← SSE Stream ← Server（推送结果）
```

**用 Java 类比理解**：

```java
// stdio 方式 = ProcessBuilder + 管道通信
ProcessBuilder pb = new ProcessBuilder("python", "server.py");
Process process = pb.start();
OutputStream stdin = process.getOutputStream();  // 发送消息
InputStream stdout = process.getInputStream();   // 接收消息

// SSE 方式 = HTTP Client + 长连接
HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("http://server.com/mcp"))
    .POST(...)
    .build();
client.send(request, HttpResponse.BodyHandlers.ofString());
```

### 2.2 协议层：JSON-RPC 2.0

MCP 使用 JSON-RPC 2.0 作为消息格式，这是一个轻量级的 RPC 协议。

#### 请求消息格式

```json
{
    "jsonrpc": "2.0",           // 协议版本（固定值）
    "id": 1,                    // 请求 ID（用于匹配响应）
    "method": "tools/call",     // 调用的方法
    "params": {                 // 方法参数
        "name": "query_food_nutrition",
        "arguments": {
            "food_name": "苹果"
        }
    }
}
```

#### 响应消息格式

```json
{
    "jsonrpc": "2.0",
    "id": 1,                    // 对应请求的 ID
    "result": {                 // 成功结果
        "content": [
            {
                "type": "text",
                "text": "苹果：热量 52kcal/100g，碳水化合物 13.8g..."
            }
        ]
    }
}
```

#### 错误响应格式

```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "error": {                  // 错误信息
        "code": -32602,         // 错误码（标准错误码）
        "message": "Invalid params",
        "data": {               // 额外的错误详情
            "details": "food_name is required"
        }
    }
}
```

**用 Java 类比理解**：

```java
// JSON-RPC 2.0 类似于 Java 的方法调用

// 请求 = 方法调用
String result = server.callTool(
    "query_food_nutrition",     // method
    Map.of("food_name", "苹果")  // params
);

// 响应 = 返回值
return result;

// 错误 = 抛出异常
throw new InvalidParamsException("food_name is required");
```

### 2.3 能力协商：连接建立流程

当 Client 连接 Server 时，需要先进行"握手"，协商双方支持的能力。

#### 握手流程

```
1. Client → Server: initialize 请求
   {
       "method": "initialize",
       "params": {
           "protocolVersion": "2024-11-05",
           "capabilities": {
               "roots": {"listChanged": true},  // Client 支持的能力
               "sampling": {}
           },
           "clientInfo": {
               "name": "my-agent",
               "version": "1.0.0"
           }
       }
   }

2. Server → Client: initialize 响应
   {
       "result": {
           "protocolVersion": "2024-11-05",
           "capabilities": {
               "tools": {},        // Server 支持工具调用
               "resources": {},    // Server 支持资源访问
               "prompts": {}       // Server 支持 Prompt 模板
           },
           "serverInfo": {
               "name": "health-server",
               "version": "1.0.0"
           }
       }
   }

3. Client → Server: initialized 通知
   {
       "method": "notifications/initialized"
   }

握手完成，可以开始调用工具了！
```

**类比理解**：

```
就像 HTTP 的内容协商：
Client: "我支持 gzip 压缩"（Accept-Encoding: gzip）
Server: "好的，我也支持，我会用 gzip 返回"（Content-Encoding: gzip）

MCP 的能力协商：
Client: "我支持 sampling（让 Server 调用 LLM）"
Server: "好的，我支持 tools、resources、prompts"
→ 双方知道对方能做什么，可以安全地调用了
```

---

## 3. MCP Server 的三大能力

MCP Server 可以提供三种能力，根据场景选择：

### 3.1 Tools（工具）：让 Agent 执行操作

**工具 = Agent 可以调用的函数**

```python
# 工具定义（类似 OpenAI Function Calling）
{
    "name": "query_food_nutrition",
    "description": "查询食物的营养成分",
    "inputSchema": {                    # JSON Schema 格式
        "type": "object",
        "properties": {
            "food_name": {
                "type": "string",
                "description": "食物名称，例如：苹果、米饭"
            }
        },
        "required": ["food_name"]
    }
}
```

**工具调用流程**：

```
1. Agent 决定调用工具
   ↓
2. Client → Server: tools/call 请求
   {
       "method": "tools/call",
       "params": {
           "name": "query_food_nutrition",
           "arguments": {"food_name": "苹果"}
       }
   }
   ↓
3. Server 执行工具逻辑（查询数据库、调用 API 等）
   ↓
4. Server → Client: 返回结果
   {
       "result": {
           "content": [
               {"type": "text", "text": "苹果：热量 52kcal/100g..."}
           ]
       }
   }
   ↓
5. Agent 获得结果，继续推理
```

**用 Java 类比理解**：

```java
// Tools = Spring 的 @RestController 方法

@RestController
public class NutritionController {
    
    @PostMapping("/query")  // 类似 MCP 的 tools/call
    public NutritionInfo queryNutrition(
        @RequestParam String foodName  // 类似 inputSchema
    ) {
        // 工具逻辑
        return nutritionService.query(foodName);
    }
}
```

### 3.2 Resources（资源）：让 Agent 读取数据

**资源 = Agent 可以读取的数据源**

```python
# 资源定义
{
    "uri": "health://user/profile",        # 资源的唯一标识（类似 URL）
    "name": "用户健康档案",
    "description": "用户的基本信息、健康目标、饮食偏好",
    "mimeType": "application/json"         # 数据格式
}
```

**Resources vs Tools 的区别**：

```
Tools（工具）：
├─ 用于执行操作（查询、计算、修改）
├─ 需要传参数
├─ 类比：POST /api/query（带参数的 API）
└─ 例如：query_food_nutrition(food_name="苹果")

Resources（资源）：
├─ 用于读取数据（配置、知识库、用户档案）
├─ 通过 URI 访问，不需要参数
├─ 类比：GET /api/profile（RESTful 的资源）
└─ 例如：读取 health://user/profile
```

**资源访问流程**：

```
1. Agent 需要用户档案信息
   ↓
2. Client → Server: resources/read 请求
   {
       "method": "resources/read",
       "params": {
           "uri": "health://user/profile"
       }
   }
   ↓
3. Server 返回资源内容
   {
       "result": {
           "contents": [
               {
                   "uri": "health://user/profile",
                   "mimeType": "application/json",
                   "text": "{\"name\": \"张三\", \"age\": 30, ...}"
               }
           ]
       }
   }
```

**用 Java 类比理解**：

```java
// Resources = Spring 的静态资源或 RESTful GET 端点

@RestController
public class ResourceController {
    
    @GetMapping("/user/profile")  // 类似 MCP 的 resources/read
    public UserProfile getUserProfile() {
        // 返回资源数据
        return userService.getProfile();
    }
}
```

### 3.3 Prompts（Prompt 模板）：预定义的交互模式

**Prompt 模板 = 预设的对话场景**

```python
# Prompt 模板定义
{
    "name": "analyze_diet",
    "description": "分析用户的饮食记录，给出健康建议",
    "arguments": [
        {
            "name": "diet_record",
            "description": "饮食记录文本",
            "required": true
        },
        {
            "name": "user_goal",
            "description": "用户的健康目标（减重/增肌/维持）",
            "required": false
        }
    ]
}
```

**Prompts 的作用**：

```
场景：用户说"帮我分析今天的饮食"

不用 Prompts：
├─ Agent 需要自己组织 Prompt
├─ 可能遗漏关键信息
└─ 每次分析的角度可能不一致

用 Prompts：
├─ Server 提供标准化的分析模板
├─ 包含专业的分析维度（热量、营养均衡、建议）
├─ 保证分析质量和一致性
└─ Agent 只需填入参数，调用模板即可
```

**Prompt 调用流程**：

```
1. Agent 调用 Prompt 模板
   ↓
2. Client → Server: prompts/get 请求
   {
       "method": "prompts/get",
       "params": {
           "name": "analyze_diet",
           "arguments": {
               "diet_record": "早餐：煎蛋、牛奶...",
               "user_goal": "减重"
           }
       }
   }
   ↓
3. Server 返回填充好的 Prompt
   {
       "result": {
           "messages": [
               {
                   "role": "user",
                   "content": {
                       "type": "text",
                       "text": "你是营养师，分析以下饮食记录：\n早餐：煎蛋、牛奶...\n用户目标：减重\n请从热量、营养均衡、改进建议三个维度分析。"
                   }
               }
           ]
       }
   }
   ↓
4. Agent 用这个 Prompt 调用 LLM，得到分析结果
```

**用 Java 类比理解**：

```java
// Prompts = 模板引擎（Thymeleaf、FreeMarker）

@Service
public class PromptService {
    
    @Autowired
    private TemplateEngine templateEngine;
    
    public String getAnalyzeDietPrompt(String dietRecord, String userGoal) {
        // 填充模板
        Context context = new Context();
        context.setVariable("dietRecord", dietRecord);
        context.setVariable("userGoal", userGoal);
        
        // 返回填充好的 Prompt
        return templateEngine.process("analyze_diet", context);
    }
}
```

---

## 4. 实战：开发健康管家 MCP Server

现在我们来开发一个真实的 MCP Server，提供健康管家需要的工具。

### 4.1 项目结构

```
health-mcp-server/
├─ server.py              # MCP Server 主文件
├─ tools/
│   ├─ __init__.py
│   ├─ nutrition.py       # 食物营养查询工具
│   └─ bmi.py             # BMI 计算工具
├─ resources/
│   ├─ __init__.py
│   └─ knowledge.py       # 健康知识资源
├─ requirements.txt       # 依赖
└─ README.md
```

### 4.2 核心代码解析

#### 安装 MCP SDK

```bash
pip install mcp
```

#### server.py - MCP Server 主文件

```python
"""
健康管家 MCP Server
提供食物营养查询、BMI 计算等工具
"""

from mcp.server import Server
from mcp.types import Tool, TextContent, Resource
import asyncio

# 创建 MCP Server 实例
# 参数：Server 名称（唯一标识）
server = Server("health-assistant")

# ============ 1. 定义工具列表 ============

@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    返回 Server 提供的所有工具
    
    这个方法会在 Client 连接时被调用，告诉 Client 有哪些工具可用
    类比：Spring Boot 的 @RequestMapping 注解扫描
    """
    return [
        Tool(
            name="query_nutrition",
            description="查询食物的营养成分（热量、蛋白质、脂肪、碳水化合物）",
            inputSchema={
                "type": "object",
                "properties": {
                    "food_name": {
                        "type": "string",
                        "description": "食物名称，例如：苹果、米饭、鸡胸肉"
                    }
                },
                "required": ["food_name"]
            }
        ),
        Tool(
            name="calculate_bmi",
            description="计算 BMI 指数并给出健康评估",
            inputSchema={
                "type": "object",
                "properties": {
                    "height": {
                        "type": "number",
                        "description": "身高（厘米），例如：175"
                    },
                    "weight": {
                        "type": "number",
                        "description": "体重（公斤），例如：70"
                    }
                },
                "required": ["height", "weight"]
            }
        )
    ]

# ============ 2. 处理工具调用 ============

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    处理工具调用请求
    
    参数：
        name: 工具名称（对应 list_tools 返回的 Tool.name）
        arguments: 工具参数（对应 Tool.inputSchema）
    
    返回：
        list[TextContent]: 工具执行结果（文本内容列表）
    
    类比：Spring Boot 的 Controller 方法
    """
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
    
    else:
        # 未知工具
        raise ValueError(f"Unknown tool: {name}")

# ============ 3. 工具实现逻辑 ============

def query_nutrition_logic(food_name: str) -> str:
    """
    查询食物营养成分（简化版，实际应该查询数据库）
    """
    # 模拟数据库查询
    nutrition_db = {
        "苹果": {"热量": 52, "蛋白质": 0.3, "脂肪": 0.2, "碳水": 13.8},
        "米饭": {"热量": 116, "蛋白质": 2.6, "脂肪": 0.3, "碳水": 25.9},
        "鸡胸肉": {"热量": 133, "蛋白质": 24.6, "脂肪": 5.0, "碳水": 0.0},
    }
    
    if food_name in nutrition_db:
        data = nutrition_db[food_name]
        return f"""
{food_name}的营养成分（每100g）：
- 热量：{data['热量']} kcal
- 蛋白质：{data['蛋白质']} g
- 脂肪：{data['脂肪']} g
- 碳水化合物：{data['碳水']} g
"""
    else:
        return f"抱歉，暂无 {food_name} 的营养数据"

def calculate_bmi_logic(height: float, weight: float) -> str:
    """
    计算 BMI 指数
    """
    # BMI = 体重(kg) / 身高(m)^2
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    
    # 健康评估
    if bmi < 18.5:
        status = "偏瘦"
    elif bmi < 24:
        status = "正常"
    elif bmi < 28:
        status = "偏胖"
    else:
        status = "肥胖"
    
    return f"""
BMI 计算结果：
- 身高：{height} cm
- 体重：{weight} kg
- BMI：{bmi:.1f}
- 评估：{status}
"""

# ============ 4. 启动 Server ============

async def main():
    """
    启动 MCP Server
    
    使用 stdio 传输方式（标准输入输出）
    适合本地进程间通信
    """
    from mcp.server.stdio import stdio_server
    
    # 通过 stdio 运行 Server
    # Host 会启动这个进程，通过 stdin/stdout 通信
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.3 关键概念解析

#### @server.list_tools() 装饰器

```python
# 这个装饰器的作用：
# 1. 注册一个处理器，响应 "tools/list" 请求
# 2. Client 连接时会调用这个方法，获取工具列表
# 3. 类比 Spring Boot 的组件扫描

# Java 类比：
@RestController
@RequestMapping("/tools")
public class ToolController {
    
    @GetMapping("/list")  // 类似 @server.list_tools()
    public List<Tool> listTools() {
        return Arrays.asList(
            new Tool("query_nutrition", "查询营养", schema),
            new Tool("calculate_bmi", "计算BMI", schema)
        );
    }
}
```

#### @server.call_tool() 装饰器

```python
# 这个装饰器的作用：
# 1. 注册一个处理器，响应 "tools/call" 请求
# 2. 根据 name 参数路由到具体的工具逻辑
# 3. 类比 Spring Boot 的请求处理方法

# Java 类比：
@PostMapping("/call")  // 类似 @server.call_tool()
public ToolResult callTool(
    @RequestParam String name,
    @RequestBody Map<String, Object> arguments
) {
    if ("query_nutrition".equals(name)) {
        return queryNutrition(arguments);
    } else if ("calculate_bmi".equals(name)) {
        return calculateBmi(arguments);
    }
    throw new IllegalArgumentException("Unknown tool: " + name);
}
```

#### stdio_server() 上下文管理器

```python
# stdio_server() 的作用：
# 1. 创建基于 stdin/stdout 的通信通道
# 2. read_stream：从 stdin 读取 Client 的请求
# 3. write_stream：向 stdout 写入响应
# 4. 类比：Socket 的 InputStream/OutputStream

# Java 类比：
Process serverProcess = new ProcessBuilder("python", "server.py").start();

// read_stream = serverProcess.getInputStream()
InputStream readStream = serverProcess.getInputStream();

// write_stream = serverProcess.getOutputStream()
OutputStream writeStream = serverProcess.getOutputStream();

// 发送请求
writeStream.write(jsonRequest.getBytes());

// 读取响应
byte[] response = readStream.readAllBytes();
```

### 4.4 测试 MCP Server

#### 方式 1：使用 MCP Inspector（官方调试工具）

```bash
# 安装 MCP Inspector
npm install -g @modelcontextprotocol/inspector

# 启动 Inspector
mcp-inspector python server.py

# 在浏览器中打开 http://localhost:5173
# 可以可视化地测试工具调用
```

#### 方式 2：在 Claude Desktop 中配置

```json
// Claude Desktop 配置文件
// macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
// Windows: %APPDATA%\Claude\claude_desktop_config.json

{
  "mcpServers": {
    "health-assistant": {
      "command": "python",
      "args": ["D:/path/to/server.py"]
    }
  }
}
```

重启 Claude Desktop，就可以在对话中使用这些工具了！

#### 方式 3：在自定义 Agent 中集成

```python
# 使用 MCP Client SDK 连接 Server

from mcp.client import Client
from mcp.client.stdio import stdio_client

async def use_mcp_tools():
    # 启动 Server 进程并连接
    async with stdio_client(
        command="python",
        args=["server.py"]
    ) as (read, write):
        async with Client(read, write) as client:
            # 初始化连接
            await client.initialize()
            
            # 列出可用工具
            tools = await client.list_tools()
            print("可用工具：", [t.name for t in tools])
            
            # 调用工具
            result = await client.call_tool(
                "query_nutrition",
                {"food_name": "苹果"}
            )
            print("查询结果：", result.content[0].text)

asyncio.run(use_mcp_tools())
```

---

## 5. MCP 与框架的集成

MCP 的强大之处在于它是一个开放协议，可以与各种 Agent 框架集成。

### 5.1 LangChain + MCP

```python
"""
在 LangChain 中使用 MCP Server 的工具
"""

from langchain.tools import Tool
from mcp.client import Client
from mcp.client.stdio import stdio_client

# 1. 连接 MCP Server
async def connect_mcp():
    async with stdio_client(
        command="python",
        args=["server.py"]
    ) as (read, write):
        async with Client(read, write) as client:
            await client.initialize()
            return client

# 2. 将 MCP 工具转换为 LangChain Tool
async def create_langchain_tools():
    client = await connect_mcp()
    tools = await client.list_tools()
    
    langchain_tools = []
    for mcp_tool in tools:
        # 包装 MCP 工具调用
        async def call_mcp_tool(arguments: str):
            result = await client.call_tool(
                mcp_tool.name,
                eval(arguments)  # 简化处理，实际应该用 JSON
            )
            return result.content[0].text
        
        # 创建 LangChain Tool
        langchain_tool = Tool(
            name=mcp_tool.name,
            description=mcp_tool.description,
            func=call_mcp_tool
        )
        langchain_tools.append(langchain_tool)
    
    return langchain_tools

# 3. 在 Agent 中使用
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

async def main():
    tools = await create_langchain_tools()
    llm = ChatOpenAI(model="qwen-plus", base_url="...")
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS
    )
    
    result = agent.run("苹果的热量是多少？")
    print(result)
```

### 5.2 LangGraph + MCP

```python
"""
在 LangGraph 中使用 MCP Server
"""

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

async def main():
    # 获取 MCP 工具
    tools = await create_langchain_tools()
    
    # 创建 LangGraph Agent
    llm = ChatOpenAI(model="qwen-plus", base_url="...")
    agent = create_react_agent(llm, tools)
    
    # 运行 Agent
    result = await agent.ainvoke({
        "messages": [("user", "帮我计算 BMI，身高 175cm，体重 70kg")]
    })
    
    print(result["messages"][-1].content)
```

### 5.3 MCP 在健康管家项目中的定位

```
健康管家的工具架构：

┌─────────────────────────────────────────┐
│         健康管家 Agent（Host）           │
│  - 对话管理                              │
│  - 记忆系统                              │
│  - 多 Agent 协调                         │
└─────────────────────────────────────────┘
                  ↓ MCP 协议
┌─────────────────────────────────────────┐
│          MCP Servers（工具层）           │
├─────────────────────────────────────────┤
│  nutrition-server:                      │
│    - query_nutrition（查询营养）        │
│    - search_food（搜索食物）            │
│    - analyze_diet（分析饮食）           │
├─────────────────────────────────────────┤
│  health-data-server:                    │
│    - get_user_profile（用户档案）       │
│    - save_diet_record（保存记录）       │
│    - get_health_stats（健康统计）       │
├─────────────────────────────────────────┤
│  knowledge-server:                      │
│    - query_health_knowledge（健康知识） │
│    - get_diet_suggestions（饮食建议）   │
└─────────────────────────────────────────┘

优势：
1. 工具解耦：每个 Server 独立开发、测试、部署
2. 可复用：nutrition-server 可以被其他健康类 Agent 使用
3. 易扩展：新增工具只需开发新的 MCP Server
4. 标准化：遵循 MCP 协议，与生态兼容
```

---

## 6. MCP 的核心价值总结

### 6.1 解决的问题

```
问题 1：工具碎片化
├─ 每个框架有自己的工具定义方式
├─ 开发者需要为每个框架适配一遍
└─ MCP 解决：统一的工具协议，一次开发处处可用

问题 2：工具发现困难
├─ Agent 不知道有哪些工具可用
├─ 需要手动配置工具列表
└─ MCP 解决：能力协商机制，自动发现工具

问题 3：工具调用不标准
├─ 不同工具的调用方式不一致
├─ 错误处理各不相同
└─ MCP 解决：标准化的 JSON-RPC 2.0 协议
```

### 6.2 MCP 的生态位

```
AI 应用技术栈：

┌─────────────────────────────────────────┐
│         应用层（Agent 应用）             │
│  Claude Desktop、VS Code、自定义 Agent  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         框架层（Agent 框架）             │
│  LangChain、LangGraph、CrewAI           │
└─────────────────────────────────────────┘
                  ↓ MCP 协议（这一层）
┌─────────────────────────────────────────┐
│         工具层（MCP Servers）            │
│  文件系统、数据库、API、知识库...        │
└─────────────────────────────────────────┘

MCP 的定位：
- 不是 Agent 框架（不负责推理、规划）
- 不是 LLM API（不负责生成文本）
- 是工具接入的标准协议（类比 USB、HTTP）
```

### 6.3 何时使用 MCP？

```
适合用 MCP 的场景：
✅ 开发可复用的工具（希望被多个 Agent 使用）
✅ 集成外部服务（数据库、API、文件系统）
✅ 构建工具生态（让社区贡献工具）
✅ 标准化团队的工具开发

不需要 MCP 的场景：
❌ 简单的一次性脚本（直接写函数即可）
❌ 框架内置的工具（LangChain 已有的工具）
❌ 性能极致要求（MCP 有协议开销）
```

---

## 7. 关键要点回顾

1. **MCP 的本质**：Agent 工具的标准化协议，类比 USB、HTTP、JDBC

2. **三层架构**：
   - Host：运行 Agent 的应用
   - Client：协议管理器
   - Server：提供工具的服务

3. **通信方式**：
   - stdio：本地进程间通信
   - SSE：远程 HTTP 通信
   - 消息格式：JSON-RPC 2.0

4. **三大能力**：
   - Tools：执行操作（函数调用）
   - Resources：读取数据（资源访问）
   - Prompts：预定义交互模式

5. **开发流程**：
   - 使用 MCP SDK 定义工具
   - 实现工具逻辑
   - 通过 stdio/SSE 启动 Server
   - 在 Agent 中集成使用

6. **生态价值**：
   - 一次开发，处处可用
   - 标准化工具接入
   - 促进工具生态发展

---

## 下一步

现在你已经理解了 MCP 协议的核心概念，接下来我们会：

1. **练习 1**：开发一个完整的食物营养查询 MCP Server
2. **练习 2**：在健康管家 Agent 中集成 MCP Server
3. **思考**：健康管家项目中哪些功能适合做成 MCP Server？

准备好了吗？让我们开始实战练习！
```

