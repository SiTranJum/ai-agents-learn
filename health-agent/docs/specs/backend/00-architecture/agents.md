# Agent 层架构（LangGraph 统一编排）

> 本文档定义健康管家后端的 Agent 层架构。**所有 LLM 推理一律通过 LangGraph Agent 发起**，不在 Agent 之外直接调用 LLM 客户端。Agent 是后端对 AI 行为的唯一抽象入口。
>
> 实现依据：`00-architecture/overview.md`、`00-architecture/integrations.md`

---

## 1. 核心原则

### 1.1 LangGraph 作为唯一 LLM 入口

- 所有涉及 LLM 推理的业务，必须通过对应的 Agent Graph 发起。
- 禁止在 `services/` 或 `api/` 层直接实例化 `ChatOpenAI` 或调用 LLM HTTP API。
- "单次 LLM 调用" 的场景同样以单节点 Graph 表达，保持一致的入口形态。
- Embedding 和 pgvector 属于 **确定性工具能力**，不走 Graph，由 Agent 节点或 Service 直接调用。

### 1.2 Agent 即业务 AI 入口

一个 Agent 对应一个**业务意图域**（饮食记录、对话、计划、建议、记忆），不以"任务大小"划分。

| Agent | 业务域 | 编译产物 |
|-------|-------|---------|
| `chat_agent` | 全局 AI 对话 | `app/agents/chat/graph.py` |
| `diet_agent` | 饮食文本/照片解析与记录 | `app/agents/diet/graph.py` |
| `plan_agent` | 计划 4 步对话创建、修改建议 | `app/agents/plan/graph.py` |
| `memory_agent` | 记忆提取、评分、合并 | `app/agents/memory/graph.py` |
| `suggestion_agent` | 每日建议、餐食建议、健康洞察 | `app/agents/suggestion/graph.py` |

### 1.3 Agent-first 调用链（方案 A）

```
FastAPI Router
     ↓ 直接调用
Agent.invoke(input)         ← 业务 AI 入口
     ↓ Tool 调用
Service / Repository        ← DB CRUD、RAG 检索等确定性能力
     ↓
PostgreSQL / pgvector
```

**Service 层退化为"工具实现者"**：只负责 DB CRUD、营养计算、BMR 计算等纯业务/纯算法逻辑，不包含 LLM 调用编排。

### 1.4 状态持久化策略

- **V1**：使用 `MemorySaver`（in-memory checkpointer），Agent 状态仅存活在单次请求。
- **V2+**：切换到 `PostgresSaver`，支持多轮会话、断点续跑、Human-in-the-Loop。
- 切换时只改 `build_<name>_graph()` 中的 checkpointer 参数，Graph 结构不变。

---

## 2. 目录结构

```
app/agents/
├── __init__.py
├── base.py                       # 公共工具：模型工厂、通用 State 字段、错误转换
├── prompts/                      # Prompt 模板（纯文本/Jinja，与 Graph 解耦）
│   ├── diet_parse.py
│   ├── memory_extract.py
│   ├── plan_create.py
│   ├── suggestion.py
│   └── chat_system.py
│
├── chat/
│   ├── __init__.py
│   ├── state.py                  # ChatState TypedDict
│   ├── nodes.py                  # 各节点函数
│   ├── tools.py                  # Agent 可调用的工具（wrap service 方法）
│   └── graph.py                  # build_chat_graph() + compiled agent
│
├── diet/
│   ├── state.py                  # DietState: input_text, parsed_foods, ...
│   ├── nodes.py                  # parse_text / enrich_nutrition / save_record ...
│   ├── tools.py                  # search_food / save_diet_record / get_user_preferences
│   └── graph.py
│
├── plan/
│   ├── state.py                  # PlanState: step (1-4), profile, targets, ...
│   ├── nodes.py                  # confirm_goal / analyze_status / draft_plan / validate
│   ├── tools.py                  # get_profile / get_recent_diet / save_plan / calc_bmr
│   └── graph.py
│
├── memory/
│   ├── state.py
│   ├── nodes.py                  # extract / score / filter / embed_and_store
│   ├── tools.py                  # save_memory / list_memories
│   └── graph.py
│
└── suggestion/
    ├── state.py
    ├── nodes.py                  # collect_data / recall_memories / search_kb / generate / dedup
    ├── tools.py                  # get_plan_progress / recall_memories / search_knowledge
    └── graph.py
```

---

## 3. LLM 客户端约定

### 3.1 唯一模型工厂

```python
# app/agents/base.py
from langchain_openai import ChatOpenAI
from app.config import settings

def get_chat_model(temperature: float = 0.3, **kwargs) -> ChatOpenAI:
    """
    全局 LLM 模型工厂。所有 Agent 节点通过此函数获取 ChatOpenAI 实例。
    DashScope 走 OpenAI 兼容接口：base_url + api_key + model=qwen-plus。
    """
    return ChatOpenAI(
        model=settings.llm_model,                # qwen-plus
        base_url=settings.dashscope_base_url,    # https://dashscope.aliyuncs.com/compatible-mode/v1
        api_key=settings.dashscope_api_key,
        temperature=temperature,
        **kwargs,
    )
```

- **禁止** 其他模块直接 `ChatOpenAI(...)`。
- **禁止** 保留 `app/integrations/llm/client.py`（旧的 `LLMClient` 封装）。
- Embedding 继续使用 `app/integrations/embedding/client.py`（这不是 LLM 推理）。

### 3.2 Prompt 管理

- Prompt 模板放 `app/agents/prompts/`，每个场景一个文件。
- 节点函数从 `prompts/` 导入 `build_messages(...)`，不把长文本写死在 `nodes.py`。
- Structured Output 通过 `.with_structured_output(PydanticSchema)` 绑定，替代旧的 `chat_with_json`。

---

## 4. State 约定

### 4.1 通用 State 基字段

所有 Agent State 必须包含：

```python
class BaseAgentState(TypedDict, total=False):
    user_id: str          # 强制：所有 Agent 必须知道当前用户
    request_id: str       # 可选：追踪 ID，用于日志关联
    error: str | None     # 可选：节点失败时的错误信息
```

### 4.2 节点签名

```python
async def some_node(state: SomeState) -> dict:
    """节点只返回要更新的字段，不返回完整 state。"""
    ...
    return {"parsed_foods": [...], "confidence": 0.9}
```

---

## 5. Tool 约定

Agent 通过 Tool 调用 Service/Repository。Tool 本身是对 Service 方法的**薄封装**：

```python
# app/agents/diet/tools.py
from langchain_core.tools import tool
from app.services.diet_service import DietService

def make_save_diet_record_tool(service: DietService, user_id: UUID):
    @tool
    async def save_diet_record(meal_type: str, foods: list[dict], date: str) -> dict:
        """保存饮食记录到数据库。返回记录 id 和营养汇总。"""
        record = await service.create_record_from_parsed(user_id, meal_type, foods, date)
        return {"id": str(record.id), "nutrition": record.nutrition_summary.model_dump()}
    return save_diet_record
```

**原则**：

- Tool 的 `@tool` docstring 就是给 LLM 的工具说明，必须清晰。
- Tool 返回必须可 JSON 序列化（dict / list / 基础类型）。
- Tool 不直接操作数据库，一律通过注入的 Service 调用。

---

## 6. 路由机制（Graph 内分流）

LangGraph 有两种分支机制，按场景选择：

| 机制 | 何时用 | 代价 |
|------|------|------|
| `add_conditional_edges(fn)` | state 已有明确字段可判定，如 `meal_type is None` | 0 tokens |
| LLM 作为 supervisor | 意图模糊、需要理解自然语言才能决定分支 | 1 次 LLM 调用 |

**默认选代码条件边**。只有真正模糊的路由（如对话意图分流）才让 LLM 当 supervisor。

---

## 7. 依赖注入

Agent 的**编译产物**（compiled graph）无状态，可在应用启动时构建一次并复用：

```python
# app/dependencies.py
from app.agents.diet.graph import build_diet_agent

_diet_agent_singleton = None

def get_diet_agent():
    global _diet_agent_singleton
    if _diet_agent_singleton is None:
        _diet_agent_singleton = build_diet_agent()
    return _diet_agent_singleton

# API 层用法
@router.post("/diet/records")
async def create_diet_record(
    payload: DietRecordCreate,
    user: CurrentUserDep,
    agent = Depends(get_diet_agent),
    diet_service: DietServiceDep,
):
    result = await agent.ainvoke({
        "user_id": str(user.id),
        "input_text": payload.input_text,
        "image_url": payload.image_url,
        "meal_type": payload.meal_type,
        "date": payload.date.isoformat(),
    }, config={
        "configurable": {
            "diet_service": diet_service,  # 通过 config 注入工具依赖
        }
    })
    return success(result["final_record"])
```

Tool 所需的 Service 实例通过 `ainvoke(..., config={"configurable": {...}})` 注入，节点内用 `config["configurable"]["diet_service"]` 取。

---

## 8. 禁止的模式

| 反模式 | 原因 |
|-------|------|
| 在 `services/*.py` 里 `from openai import OpenAI` | LLM 调用必须走 Agent |
| 保留 `LLMService.parse_diet_input()` 等场景方法 | 由 Agent 节点取代，Service 不做 AI 编排 |
| 在 API 层同时调 Agent 和 Service 做串联 | Agent 内部通过 Tool 调用 Service |
| Graph 内再 import 另一个 Graph 的 compiled 产物 | Agent 之间通过"子图 + add_node(subgraph)"或通过 Tool 桥接 |
| 把 embedding 调用包成 Graph | embedding 是工具，不是推理 |

---

## 9. 与现有 specs 的关系

本文档是 AI 层的**总纲**。以下模块 spec 必须以本文档为基准：

- `02-ai-modules/ai-memory.md` → memory_agent
- `02-ai-modules/ai-suggestion.md` → suggestion_agent
- `02-ai-modules/plan-system.md` → plan_agent
- `01-core-modules/diet-recording.md` → diet_agent（解析 + 记录）
- `02-ai-modules/rag-knowledge.md` → 仍是 Service，但只作为 Agent 的 Tool 被调用

`00-architecture/integrations.md` 负责 DashScope/Embedding/pgvector 三件套的技术细节（URL、重试、索引 SQL 等），不再定义 LLM 场景方法。
