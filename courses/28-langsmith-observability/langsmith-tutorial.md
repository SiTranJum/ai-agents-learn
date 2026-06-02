# LangSmith 教程：LangGraph 应用的可观测性

> 面向 Java 背景开发者的 LangSmith 上手指南。
> 配套项目：`health-agent`（LangGraph + DashScope/qwen-plus）。

---

## 一、LangSmith 是什么？

一句话：**LangSmith 是 LLM 应用的「APM + 日志平台」**。

用你熟悉的 Java 生态类比：

| LangSmith | Java 世界的对应物 | 作用 |
|-----------|------------------|------|
| Trace（追踪） | SkyWalking / Zipkin 的调用链 | 一次请求里每个节点、每次 LLM 调用的完整链路 |
| Run（运行记录） | 一条 APM span | 单个步骤的输入/输出/耗时/token |
| Project（项目） | 应用维度的日志分组 | 把 trace 按环境/服务分组 |
| Dataset（数据集） | 测试用例库（JUnit 的测试数据） | 收集样本用于回归测试 |
| Evaluation（评估） | 单元测试 + 断言 | 用规则/LLM 给输出打分 |
| Prompt Hub | 配置中心里的模板 | 版本化管理 prompt |

为什么 LLM 应用特别需要它：传统日志只能看到「输入字符串 → 输出字符串」，
但一次 Agent 请求内部可能经过「识别意图 → 检索记忆 → 查知识库 → 调用 LLM → 调工具」
十几个步骤，**出问题时你需要看到每一步的中间状态**，这正是 LangSmith 的价值。

---

## 二、5 分钟接入（你的项目已经接好了）

LangSmith 的接入**不需要改业务代码**，只靠环境变量。你项目的 `.env` 已经有：

```dotenv
LANGCHAIN_TRACING_V2=true                       # 总开关：打开追踪
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=lsv2_pt_xxx                    # 你的密钥（注意保密！）
LANGCHAIN_PROJECT=health-agent-dev               # trace 归到哪个项目
```

原理：LangChain / LangGraph 内部所有 `ainvoke` / `astream_events` 调用，
检测到 `LANGCHAIN_TRACING_V2=true` 就会自动把链路数据异步上报到 LangSmith。
**这就是为什么你不用写任何埋点代码。**

> ⚠️ **安全提醒**：API Key 等同密码，不要提交进 Git。
> 你当前 `.env` 里的 key 已经暴露，建议去 https://smith.langchain.com/settings
> 吊销（Revoke）后重新生成，并确认 `.env` 已加入 `.gitignore`。

新旧环境变量名都支持，等价对照：

| 旧名（LANGCHAIN_） | 新名（LANGSMITH_） |
|--------------------|--------------------|
| `LANGCHAIN_TRACING_V2` | `LANGSMITH_TRACING` |
| `LANGCHAIN_API_KEY` | `LANGSMITH_API_KEY` |
| `LANGCHAIN_PROJECT` | `LANGSMITH_PROJECT` |
| `LANGCHAIN_ENDPOINT` | `LANGSMITH_ENDPOINT` |

---

## 三、页面功能逐个讲解

### 1. Projects（项目列表）

进入后第一眼看到的就是项目列表，每个项目对应一个 `LANGCHAIN_PROJECT`。
点进 `health-agent-dev` 就能看到所有 trace。

**列表页常用列：**
- **Name**：trace 名称（默认是入口函数 / graph 名）
- **Latency**：端到端耗时
- **Tokens**：本次消耗的 token（← 你遇到 0 的就是这里）
- **Cost**：估算费用
- **Status**：Success / Error
- **Time**：发生时间

**顶部过滤器**最实用：
- 按 `Status = Error` 过滤出所有失败请求
- 按 `Latency > 5s` 过滤出慢请求
- 按 `Metadata` / `Tags` 过滤（需要你在代码里打 tag，见第五节）

### 2. Trace 详情页（最核心）

点开任意一条 trace，左侧是**树形调用链**，右侧是**选中节点的详情**。

```
▼ LangGraph: chat_agent              [总耗时 3.2s]
  ├─ identify_intent                 [0.4s]
  ├─ recall_memories                 [0.1s]
  ├─ search_knowledge                [0.6s]
  ├─ ▼ call_llm                      [1.9s]  ← LLM 调用在这里
  │    └─ ChatOpenAI                 [tokens: 1203]
  └─ wrap_response                   [0.05s]
```

左侧树：对应你 LangGraph 里的每个**节点（node）**，嵌套关系就是子图调用关系。
这跟你在 `translator.py` 里翻译的那些 `on_chain_start` / `on_chat_model_stream`
事件是**同一套底层数据**——LangSmith 把它们可视化了。

右侧详情，重点看几个 Tab：
- **Input / Output**：该节点的输入输出（dict 会格式化展示，调 prompt 必看）
- **Metadata**：模型名、温度、`ls_provider` 等元信息
- **Feedback**：人工/自动打分
- **Run ID**：唯一标识，排查问题时可以直接分享这个链接

对 `ChatOpenAI` 节点，还能看到：
- 完整的 **messages 数组**（system / user / assistant 每条）
- **token 明细**：prompt_tokens / completion_tokens / total_tokens
- **耗时**和**估算成本**

### 3. Monitor（监控大盘）

项目内的 `Monitor` 标签页，是按时间聚合的图表：
- 请求量（QPS）趋势
- P50 / P99 延迟
- 错误率
- token 消耗 / 成本趋势

类比 Grafana 面板，用来看整体健康度，而不是单条请求。

### 4. Datasets & Experiments（数据集与实验）

这是 LangSmith 区别于普通 APM 的「测试」能力：

1. 从生产 trace 里**挑选**典型样本，一键「Add to Dataset」存成测试集
2. 改了 prompt 或换了模型后，对整个数据集**批量跑一遍**（Experiment）
3. 对比新旧版本的输出差异、打分、耗时、成本

类比：把线上真实请求沉淀成 JUnit 测试用例，每次改动跑回归。

### 5. Evaluations（评估）

给输出自动打分，两种方式：
- **规则评估**：写代码断言（如「输出必须是合法 JSON」「必须包含卡路里字段」）
- **LLM-as-Judge**：用另一个 LLM 给「回答质量/相关性/安全性」打分

类比：测试里的 `assertEquals`，只是断言对象是「自然语言质量」。

### 6. Prompts（Prompt Hub）

在线版本化管理 prompt 模板，可以：
- 在 Playground 里改 prompt 直接试跑
- 给 prompt 打版本号，回滚
- 团队共享

你项目目前把 prompt 写在 `app/agents/prompts/` 代码里，属于另一种管理方式，
两者二选一即可，不强制用 Hub。

### 7. Playground（调试台）

把某条 trace 的 LLM 调用「一键打开到 Playground」，
可以在网页上直接改 messages / 参数 / 模型，反复试跑，
**不用回到代码里改了重启**。调 prompt 时极大提速。

---

## 四、为什么 token 用量是 0？（你的核心问题）

### 结论先行

你的 `health-agent` 用 **流式（streaming）** 方式调用 LLM
（`translator.py` 里的 `agent.astream_events(...)` + `on_chat_model_stream`），
而 **OpenAI 兼容接口在流式模式下默认不返回 token usage**，
所以 LangSmith 拿不到 token 数，显示 0。

### 原因详解

普通（非流式）调用，响应体最后会带一段 usage：

```json
{
  "choices": [...],
  "usage": { "prompt_tokens": 50, "completion_tokens": 120, "total_tokens": 170 }
}
```

但**流式**调用是一个个 chunk 推回来的（SSE），默认每个 chunk 里**没有 usage 字段**，
整个流结束也不带统计。OpenAI 协议为此提供了一个开关：

```jsonc
// 请求里加上这个，流的最后一帧才会带 usage
"stream_options": { "include_usage": true }
```

LangChain 的 `ChatOpenAI` 把这个开关封装成了参数 **`stream_usage=True`**。
你的 `get_chat_model()` 目前**没有传**这个参数，所以流式调用拿不到 token，
LangSmith 自然显示 0。

### 修复方法（针对你的 `app/agents/base.py`）

在工厂函数里加上 `stream_usage=True`：

```python
return ChatOpenAI(
    model=settings.llm_model,
    base_url=settings.dashscope_base_url,
    api_key=settings.dashscope_api_key,
    temperature=temperature,
    timeout=timeout,
    max_retries=max_retries,
    stream_usage=True,          # ← 关键：流式调用也返回 token 统计
    **kwargs,
)
```

DashScope 的 OpenAI 兼容模式支持 `stream_options.include_usage`，所以这个开关对 qwen 有效。

### 验证

改完重启后端，发一条对话，再回 LangSmith 看那条 trace 的 `call_llm → ChatOpenAI` 节点，
Tokens 应该就不是 0 了。

### 其他可能导致 0 的情况（排查清单）

1. **用了 `with_structured_output` 的节点**（如 `identify_intent` / `parse_text`）：
   这些是非流式 `ainvoke`，通常**本来就有** token；如果它们也是 0，往下看第 2、3 条。
2. **模型提供商根本不回传 usage**：少数三方兼容网关会丢掉 usage 字段，
   这种情况 LangSmith 会退化成「按字符估算」或显示 0，属于上游限制。
3. **看的是 LangGraph 父节点而不是 LLM 子节点**：token 统计挂在最里层的
   `ChatOpenAI` 运行上，父级 `chat_agent` 节点显示的是汇总，
   如果汇总逻辑没拿到子节点 usage，也会是 0——修了第四节的开关后汇总会恢复。
4. **缓存命中**：如果命中了 LLM 缓存，没有真实请求，token 也会是 0（符合预期）。

---

## 五、进阶：给 trace 加业务上下文

默认 trace 只有函数名，排查时不好定位。可以打 tag / metadata，
之后在 LangSmith 用过滤器精准查找。

```python
from langchain_core.runnables import RunnableConfig

config: RunnableConfig = {
    "run_name": "chat_turn",                 # trace 显示名
    "tags": ["chat", "prod"],                # 标签，可在 UI 过滤
    "metadata": {                            # 自定义字段
        "user_id": user_id,
        "request_id": request_id,
    },
}

async for ev in agent.astream_events(state, version="v2", config=config):
    ...
```

这样在 LangSmith 就能用 `metadata.user_id = xxx` 直接定位某个用户的所有请求，
对线上排障非常有用。

> 你项目的 `translate_langgraph_events()` 已经支持透传 `config`，
> 只要在调用处把上面的 `config` 传进去即可。

---

## 六、小结

- LangSmith = LLM 应用的 APM + 测试平台，**靠环境变量零侵入接入**。
- 核心页面：**Projects**（找请求）→ **Trace 详情**（看链路）→ **Monitor**（看大盘）
  → **Datasets/Evaluations**（做回归测试）→ **Playground**（在线调 prompt）。
- **token=0 的根因**：流式调用默认不返回 usage，解决办法是给 `ChatOpenAI`
  加 `stream_usage=True`。
- 记得**吊销已泄露的 API Key**，并用 tag/metadata 丰富 trace 上下文。
```

