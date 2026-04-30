# 数据库查询 MCP Server - 练习项目

## 项目概述

这是一个结合了 **MCP 协议** + **Agent 循环** + **Skills 渐进式加载** 的综合练习。

### 核心设计思想：渐进式上下文注入

**传统方式的问题**：
```
System Prompt = 角色定义 + 所有表结构（5000+ tokens）
↓
每次调用都消耗大量 tokens，成本高
```

**Skills 渐进式加载**：
```
第一轮：只加载 Skills 目录（200 tokens）
  LLM: "我需要 user_module skill"
  
第二轮：加载 user_module.md 详细内容（800 tokens）
  LLM: 生成 SQL
  
↓
大幅减少 token 消耗，按需加载
```

## 项目结构

```
db-query-mcp-server/
├── server.py                    # MCP Server 主入口（框架已提供）
├── requirements.txt             # 依赖清单
├── README.md                    # 本文件
│
├── core/                        # 核心模块
│   ├── __init__.py
│   ├── agent_harness.py         # Agent Harness（核心练习）
│   ├── skill_manager.py         # Skills 管理器（练习）
│   ├── db_manager.py            # 数据库管理器（框架已提供）
│   └── llm_client.py            # LLM 客户端（框架已提供）
│
├── skills/                      # Skills Markdown 文件
│   ├── user_module.md           # 示例：用户模块
│   └── README.md                # Skills 编写指南
│
└── tools/                       # 工具函数（可选）
    ├── __init__.py
    └── sql_validator.py         # SQL 验证器
```

## 配置方式

通过 MCP 初始化参数传入配置：

```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",
    "database": "test_db"
  },
  "llm": {
    "api_key": "sk-xxx",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-plus"
  },
  "skills_dir": "./skills"
}
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python server.py
```

## 测试

### 使用 MCP Inspector

```bash
npm install -g @modelcontextprotocol/inspector
mcp-inspector python server.py
```

### 在 Claude Desktop 中配置

编辑配置文件，添加：

```json
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
```

## 练习任务

### 任务 1：实现 SkillManager（渐进式加载）

文件：`core/skill_manager.py`

**目标**：实现 Skills 的加载和检索逻辑

**关键方法**：
- `load_all_skills()` - 加载所有 Markdown 文件
- `get_skills_summary()` - 返回简短的 skills 列表（第一轮用）
- `get_skill_detail(skill_name)` - 返回完整的 skill 内容（第二轮用）
- `search_relevant_skills(query)` - 根据用户问题检索相关 skills

### 任务 2：实现 AgentHarness（Agent 循环）

文件：`core/agent_harness.py`

**目标**：实现两阶段 Agent 循环

**第一阶段**：选择 Skill
- System Prompt 只包含 skills 目录
- LLM 决定需要哪个 skill
- 调用 `load_skill` 工具

**第二阶段**：生成和执行 SQL
- System Prompt 包含完整的 skill 内容
- LLM 生成 SQL
- 调用 `execute_sql` 工具
- 返回结果

### 任务 3：测试和优化

- 测试不同的查询场景
- 观察 token 消耗
- 优化 Skills 的组织方式

## Skills 编写指南

每个 Skill Markdown 文件应包含：

1. **模块概述**：模块名、用途、包含的表
2. **SOP（标准操作流程）**：如何使用这个模块
3. **约束条件**：安全规则、性能规则、业务规则
4. **表结构**：字段、类型、索引
5. **示例查询**：常见查询模板

参考：`skills/user_module.md`

## 学习要点

1. **渐进式上下文注入**：如何减少 token 消耗
2. **Agent 循环**：多轮 LLM 调用和工具执行
3. **MCP 协议**：如何在 MCP Server 内嵌 Agent
4. **Skills 设计**：如何组织和管理数据库知识

## 扩展思考

1. 如何让 LLM 自动判断需要哪些 skills？
2. 如何处理跨模块的关联查询？
3. 如何实现 SQL 的安全校验？
4. 如何支持用户动态添加新的 skills？
