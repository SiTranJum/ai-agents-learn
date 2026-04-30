# AI Agents Learn

AI Agent 学习项目 —— 从基础概念到健康管家 Agent 完整实战。

## 快速开始

### 1. 配置 API Key

本项目所有代码示例通过**环境变量**读取 API Key，不会在代码中硬编码密钥。

```bash
# 复制模板文件
cp .env.example .env

# 编辑 .env，填入你自己的 API Key
```

`.env` 文件内容示例：

```bash
# 通义千问 / DashScope（主力 LLM，课程默认使用）
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# DeepSeek（早期课程使用，可选）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

> ⚠️ **安全提示**：`.env` 已被 `.gitignore` 忽略，不会被提交。**永远不要将真实 API Key 提交到版本库。**

### 2. 在代码中加载环境变量

```python
import os
from dotenv import load_dotenv

load_dotenv()  # 自动读取 .env 文件

api_key = os.getenv("DASHSCOPE_API_KEY")
```

或直接通过 shell 环境变量：

```bash
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
python courses/01-what-is-llm/code/example.py
```

---

## 防止 API Key 泄露

以下规则帮助避免意外提交密钥：

1. **永远用 `.env` + `os.getenv()`**，不要把 key 写死在代码里
2. **提交前用 `git diff` 检查**，确认没有 `sk-` 开头的字符串
3. **`.gitignore` 已包含** `.env`、`.env.*`、`*.secrets` 等敏感文件模式
4. 如果不小心提交了密钥，立即**到 API 控制台撤销该 Key 并重新生成**

---

## 目录结构

```
.
├── courses/          # 课程代码和笔记
│   ├── 01-what-is-llm/
│   ├── 02-prompt-engineering/
│   └── ...
├── health-agent/     # 健康管家 Agent 项目
├── health-agent-app/ # 前端应用
├── .env.example      # 环境变量模板（安全，可提交）
└── .gitignore
```
