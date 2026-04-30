# MCP SSE 传输机制学习笔记

## 1. 为什么需要 SSE？

MCP 支持两种传输方式：

| 传输方式 | 适用场景 | 通信方式 |
|---------|---------|---------|
| stdio | 本地使用 | stdin/stdout 管道 |
| SSE | 局域网/远程 | HTTP 长连接 |

```
stdio：
  Claude Desktop 启动 Server 子进程
  通过 stdin/stdout 双向通信
  一对一，只能本地

SSE：
  Server 独立运行（HTTP 服务）
  Client 通过 HTTP 连接
  一对多，支持网络
```

## 2. SSE（Server-Sent Events）是什么？

SSE 是一种 **HTTP 长连接**技术，允许服务器主动向客户端推送消息。

```
普通 HTTP：
  Client → 请求 → Server
  Client ← 响应 ← Server
  连接关闭

SSE：
  Client → GET /sse → Server
  Client ← 200 OK（不关闭连接）
  Client ← data: 消息1
  Client ← data: 消息2
  Client ← data: 消息3
  ...（连接一直保持）
```

Java 类比：

```java
// SSE 类似 Spring 的 SseEmitter
@GetMapping("/sse")
public SseEmitter subscribe() {
    SseEmitter emitter = new SseEmitter();
    // 连接保持打开，随时可以推送
    emitter.send("消息1");
    emitter.send("消息2");
    return emitter;
}

// 普通 HTTP 类似 @ResponseBody
@GetMapping("/api")
public String getData() {
    return "响应";  // 返回后连接关闭
}
```

## 3. MCP 的 SSE 双通道设计

SSE 本身是**单向的**（Server → Client），但 MCP 需要**双向通信**。

解决方案：**两个通道**

```
通道 1：GET /sse（Server → Client）
  SSE 长连接，Server 推送响应

通道 2：POST /messages（Client → Server）
  普通 HTTP 请求，Client 发送消息
```

```
Client                              Server
  │                                    │
  │─── GET /sse ─────────────────────→ │  建立推送通道
  │←── SSE 流（一直开着）──────────── │
  │                                    │
  │─── POST /messages ───────────────→ │  发送请求
  │                                    │
  │←── SSE: data: {响应} ────────────  │  通过推送通道返回
```

## 4. 完整的连接流程

### 第一步：建立 SSE 连接

```
Client → GET /sse → Server

Server 返回：
  HTTP/1.1 200 OK
  Content-Type: text/event-stream    ← SSE 标识

  data: {"endpoint": "/messages?session_id=abc123"}
  ↑ 告诉 Client：以后发消息要 POST 到这个地址
```

### 第二步：Client 发送 initialize 请求

```
Client → POST /messages?session_id=abc123
Body: {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {...}
}

Server 通过 SSE 推送响应：
data: {
    "jsonrpc": "2.0",
    "result": {
        "capabilities": {"tools": {}}
    }
}
```

### 第三步：正常的工具调用

```
Client → POST /messages?session_id=abc123
Body: {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "query_database", "arguments": {...}}
}

Server 通过 SSE 推送响应：
data: {
    "jsonrpc": "2.0",
    "result": {
        "content": [{"type": "text", "text": "查询结果..."}]
    }
}
```

### 完整时序图

```
Client                              Server (HTTP)
  │                                    │
  │─── GET /sse ─────────────────────→ │  1. 建立 SSE 长连接
  │←── endpoint=/messages?sid=abc ──── │  2. 告诉 Client 消息端点
  │                                    │
  │─── POST /messages?sid=abc ───────→ │  3. 发送 initialize
  │←── SSE: {"result": {...}} ─────── │  4. 推送 initialize 响应
  │                                    │
  │─── POST /messages?sid=abc ───────→ │  5. 发送 tools/list
  │←── SSE: {"result": [...]} ─────── │  6. 推送工具列表
  │                                    │
  │─── POST /messages?sid=abc ───────→ │  7. 发送 tools/call
  │←── SSE: {"result": {...}} ─────── │  8. 推送工具结果
  │                                    │
  │    （SSE 连接一直保持）              │
```

## 5. session_id 的作用

SSE Server 可以同时服务多个 Client，通过 session_id 区分：

```
Client A ── GET /sse ──→ Server（分配 session_id=aaa）
Client B ── GET /sse ──→ Server（分配 session_id=bbb）

Client A ── POST /messages?sid=aaa ──→ Server
  → Server 知道这是 Client A 的消息
  → 通过 Client A 的 SSE 连接推送响应

Client B ── POST /messages?sid=bbb ──→ Server
  → Server 知道这是 Client B 的消息
  → 通过 Client B 的 SSE 连接推送响应
```

Java 类比：

```java
// session_id 类似 HttpSession 的 JSESSIONID
// 每个用户有独立的会话

Map<String, SseEmitter> sessions = new ConcurrentHashMap<>();

@GetMapping("/sse")
public SseEmitter connect() {
    String sessionId = UUID.randomUUID().toString();
    SseEmitter emitter = new SseEmitter();
    sessions.put(sessionId, emitter);
    emitter.send("endpoint=/messages?session_id=" + sessionId);
    return emitter;
}

@PostMapping("/messages")
public void receive(@RequestParam String session_id, @RequestBody String message) {
    // 根据 session_id 找到对应的 SSE 连接
    SseEmitter emitter = sessions.get(session_id);

    // 处理消息
    String response = process(message);

    // 通过对应的 SSE 连接推送响应
    emitter.send(response);
}
```

## 6. 代码实现解析

### 技术栈

```
Python 自带：
  asyncio          # 异步编程

MCP SDK（pip install mcp）：
  mcp.server.Server              # MCP Server 核心
  mcp.server.sse.SseServerTransport  # SSE 传输层

第三方库：
  starlette        # 轻量级 Web 框架（类似 Spring WebFlux）
  uvicorn          # ASGI 服务器（类似 Tomcat）
```

### 组件关系

```
uvicorn（ASGI 服务器）     ←→  Tomcat（Servlet 容器）
  ↓                              ↓
Starlette（Web 框架）      ←→  Spring MVC（Web 框架）
  ↓                              ↓
Route（路由）              ←→  @RequestMapping（路由注解）
  ↓                              ↓
handle_sse()               ←→  @GetMapping("/sse")
handle_messages()          ←→  @PostMapping("/messages")
  ↓                              ↓
SseServerTransport         ←→  WebSocket Handler
  ↓                              ↓
server.run()               ←→  Service 层
```

### 请求处理链路

```
Client 发送 HTTP 请求
  ↓
uvicorn 接收请求（类似 Tomcat）
  ↓
Starlette 路由匹配（类似 DispatcherServlet）
  ↓
handle_sse() 或 handle_messages()（类似 Controller）
  ↓
MCP SseServerTransport 处理协议（类似 Service）
  ↓
server.run() 执行 MCP 逻辑（类似业务逻辑）
  ↓
调用 AgentHarness / SkillManager 等
```

### 核心代码解析

```python
# 1. 创建 SSE 传输层
sse_transport = SseServerTransport("/messages")
#                                  ↑ 告诉 Client 消息端点的路径


# 2. SSE 连接处理（GET /sse）
async def handle_sse(request):
    # connect_sse() 内部做了：
    # a) 建立 SSE 长连接（设置 Content-Type: text/event-stream）
    # b) 生成 session_id
    # c) 推送 endpoint=/messages?session_id=xxx
    # d) 返回 (read_stream, write_stream)
    async with sse_transport.connect_sse(
        request.scope,      # 请求元信息（URL、方法、头部）
        request.receive,    # 接收数据的回调
        request._send       # 发送数据的回调
    ) as streams:
        # server.run() 启动 MCP 消息循环
        # 和 stdio 方式完全一样！
        await server.run(
            streams[0],       # read_stream（来自 POST /messages）
            streams[1],       # write_stream（推送到 SSE）
            server.create_initialization_options()
        )


# 3. 消息接收处理（POST /messages）
async def handle_messages(request):
    # handle_post_message() 内部做了：
    # a) 解析 POST body 中的 JSON-RPC 消息
    # b) 根据 session_id 找到对应的 read_stream
    # c) 将消息写入 read_stream
    # d) server.run() 的循环会读到这条消息并处理
    await sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )


# 4. Starlette 路由
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)


# 5. 启动 uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### ASGI 三个参数

```python
request.scope    # 请求元信息（URL、方法、头部等）
request.receive  # 接收客户端数据的异步回调
request._send    # 发送响应给客户端的异步回调
```

Java 类比：

```java
public void handle(
    HttpServletRequest request,   // scope + receive
    HttpServletResponse response  // send
) {
    String url = request.getRequestURI();      // scope
    InputStream in = request.getInputStream();  // receive
    OutputStream out = response.getOutputStream(); // send
}
```

## 7. stdio vs SSE 对比

| 特性 | stdio | SSE |
|------|-------|-----|
| 启动方式 | Client 启动 Server 子进程 | Server 独立运行 |
| 通信方式 | stdin/stdout 管道 | HTTP 长连接 |
| 连接数 | 一对一 | 一对多 |
| 网络支持 | 仅本地 | 局域网/公网 |
| 配置传递 | 通过 env 环境变量 | Server 自己读取 |
| 适用场景 | 本地开发调试 | 团队共享/部署 |

### 代码差异

```python
# stdio 方式
from mcp.server.stdio import stdio_server

async with stdio_server() as (read, write):
    await server.run(read, write, ...)

# SSE 方式
from mcp.server.sse import SseServerTransport

sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(scope, receive, send) as (read, write):
        await server.run(read, write, ...)
        #              ↑ 和 stdio 完全一样！
```

**关键点**：`server.run(read, write, ...)` 的调用方式完全一样，只是底层传输不同。所以 `core/` 下的所有业务代码一行都不用改。

## 8. 实际使用

### 你的机器（启动 SSE Server）

```bash
python server_sse.py --host 0.0.0.0 --port 8000
```

### 同事的机器（Claude Desktop 配置）

```json
{
  "mcpServers": {
    "db-query": {
      "url": "http://你的IP:8000/sse"
    }
  }
}
```

### 同事不需要

- 安装 Python
- 安装依赖
- 配置数据库密码
- 配置 API Key

所有配置都在你的机器上，同事只是通过 HTTP 连接过来。

## 9. 安全考虑

### 局域网共享

```
当前：无认证，局域网内任何人都能连
风险：低（局域网内部）
```

### 如果要加认证

```python
# 方式 1：Token 认证
# Client 配置
{
    "url": "http://IP:8000/sse",
    "headers": {
        "Authorization": "Bearer your-token"
    }
}

# Server 端验证
async def handle_sse(request):
    token = request.headers.get("Authorization")
    if token != "Bearer your-token":
        return Response(status_code=401)
    # ...
```

## 10. 关键要点

1. **SSE 是单向推送**：Server → Client，所以需要 POST 通道补充 Client → Server
2. **session_id 区分用户**：多个 Client 连接时，通过 session_id 隔离
3. **server.run() 不变**：无论 stdio 还是 SSE，MCP 消息循环的调用方式完全一样
4. **业务代码不用改**：只改传输层（server.py → server_sse.py），core/ 完全复用
5. **Starlette + uvicorn**：轻量级 Web 框架 + ASGI 服务器，类似 Spring WebFlux + Netty
