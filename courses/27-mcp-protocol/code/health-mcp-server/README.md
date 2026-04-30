# 健康管家 MCP Server

这是一个示例 MCP Server，提供健康管理相关的工具。

## 功能

### 工具（Tools）

1. **query_nutrition** - 查询食物营养成分
   - 输入：食物名称
   - 输出：热量、蛋白质、脂肪、碳水化合物

2. **calculate_bmi** - 计算 BMI 指数
   - 输入：身高（cm）、体重（kg）
   - 输出：BMI 值和健康评估

## 安装

```bash
pip install -r requirements.txt
```

## 运行

### 方式 1：直接运行（用于测试）

```bash
python server.py
```

### 方式 2：使用 MCP Inspector 调试

```bash
# 安装 MCP Inspector
npm install -g @modelcontextprotocol/inspector

# 启动 Inspector
mcp-inspector python server.py

# 在浏览器中打开 http://localhost:5173
```

### 方式 3：在 Claude Desktop 中使用

编辑 Claude Desktop 配置文件：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

添加配置：

```json
{
  "mcpServers": {
    "health-assistant": {
      "command": "python",
      "args": ["D:/path/to/server.py"]
    }
  }
}
```

重启 Claude Desktop 即可使用。

### 方式 4：在自定义 Agent 中集成

```python
from mcp.client import Client
from mcp.client.stdio import stdio_client

async def use_mcp_tools():
    async with stdio_client(
        command="python",
        args=["server.py"]
    ) as (read, write):
        async with Client(read, write) as client:
            await client.initialize()
            
            # 列出工具
            tools = await client.list_tools()
            print("可用工具：", [t.name for t in tools])
            
            # 调用工具
            result = await client.call_tool(
                "query_nutrition",
                {"food_name": "苹果"}
            )
            print(result.content[0].text)
```

## 扩展

### 添加新工具

1. 在 `list_tools()` 中添加工具定义
2. 在 `call_tool()` 中添加路由逻辑
3. 实现工具的具体逻辑

### 添加 Resources

```python
@server.list_resources()
async def list_resources():
    return [
        Resource(
            uri="health://knowledge/nutrition",
            name="营养知识库",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str):
    if uri == "health://knowledge/nutrition":
        return ResourceContents(
            uri=uri,
            mimeType="application/json",
            text='{"topic": "营养学基础", ...}'
        )
```

### 添加 Prompts

```python
@server.list_prompts()
async def list_prompts():
    return [
        Prompt(
            name="analyze_diet",
            description="分析饮食记录",
            arguments=[
                PromptArgument(
                    name="diet_record",
                    description="饮食记录文本",
                    required=True
                )
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict):
    if name == "analyze_diet":
        diet_record = arguments["diet_record"]
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"分析以下饮食记录：\n{diet_record}"
                    )
                )
            ]
        )
```

## 学习资源

- [MCP 官方文档](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP 规范](https://spec.modelcontextprotocol.io)
