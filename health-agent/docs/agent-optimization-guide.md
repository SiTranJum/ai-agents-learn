# Health-Agent Agent 层优化梳理

> 状态：产品功能已实现，进入**优化/增强**阶段。
> 本文把你提出的 10 个优化点逐一对应到代码位置，给出现状分析、优化方向、
> 查缺补漏，以及优先级建议，作为后续优化的 backlog 参考。

---

## 0. 当前架构速览（优化的基础）

主对话图 `app/agents/chat/graph.py`：

```
identify_intent
   ├─(diet)──→ diet subgraph ─────────────────────────────┐
   └─(general)→ recall_memories → search_knowledge →       │
                assemble_prompt → call_llm →               │
                trigger_memory_extract → wrap_response ─────┴→ END
```

关键特征（决定了优化空间）：
- **纯顺序 pipeline**：节点写死先后顺序，没有 LLM 决策的循环（非 ReAct）。
- **工具是固定节点**：`recall_memories` / `search_knowledge` 每次都跑，不是按需调用。
- **记忆抽取已异步化**：`trigger_memory_extract` 用 `asyncio.create_task` fire-and-forget。
- **多次 LLM 调用**：`identify_intent`（结构化）→ `call_llm`（流式）→ 后台 `extract`+`score`（结构化）。

---

## 1. 缓存命中优化：Prompt 前缀化提升命中率

**现状代码**：`app/agents/prompts/chat_system.py` → `build_chat_messages()`

**问题**：当前把「用户记忆 + 知识库片段」**拼接进 SystemMessage**（第 72-74 行）：
```python
system_content = SYSTEM_PROMPT
if context:
    system_content += "\n\n可用上下文：\n" + ...   # ← 每次请求 system 都不一样
```
这会**破坏前缀缓存**。DashScope/qwen 的 Context Cache 是按「最长公共前缀」命中的，
而你把每次都变化的记忆/知识塞在了最前面的 system 里，导致前缀几乎无法复用。

**优化方向**：
1. **稳定前缀置顶**：`SYSTEM_PROMPT`（固定不变）单独作为第一条 SystemMessage，
   保持逐字节稳定（连标点、空格都不要动），让它成为可缓存前缀。
2. **动态内容后置**：把记忆/知识/历史放到**靠后**的独立 message 里，
   顺序为 `[固定System] → [历史] → [动态上下文] → [用户输入]`。
3. **开启 DashScope 缓存**：qwen-plus 支持 Context Cache，确认请求未禁用；
   稳定前缀越长，节省的 input token 越多。
4. **意图分类前缀**：`INTENT_PROMPT`（`chat_system.py` 第 19 行）是固定模板，
   只有 `{message}` 变化，已经是好的前缀结构，保持即可。

**收益**：input token 成本下降 + 首 token 延迟下降（命中缓存时 prefill 更快）。
**优先级**：⭐⭐⭐（改动小、收益直接）。

---

## 2. Prompt 理解力优化：提升理解的同时简化 Prompt

**现状代码**：`app/agents/prompts/`（11 个 prompt builder）

**现状**：prompt 写得比较直白，`SYSTEM_PROMPT` 简洁；意图分类靠
`INTENT_PROMPT` 列举 6 个 intent + 规则兜底 `_rule_based_intent`
（`chat/nodes.py` 第 34 行）。

**优化方向**：
1. **Few-shot 压缩**：与其堆叠规则文字，不如给 2-3 个**高质量示例**，
   模型对示例的「理解」往往优于冗长描述，同时 token 更省。
2. **结构化约束代替自然语言约束**：意图分类已用 `with_structured_output`
   （`IntentResult`），可以进一步把「输出限制」交给 schema，
   prompt 里就不用再写「不要输出解释」这类话。
3. **指令分层**：稳定的「角色 + 边界」放 system，「任务 + 输出格式」放靠近用户输入处，
   既利于缓存（见第 1 点）又利于模型聚焦。
4. **A/B 验证**：用 LangSmith 的 Dataset/Experiment（见第 9 点）对比
   「精简版 prompt vs 原版」的意图准确率，用数据驱动简化，避免凭感觉删。

**优先级**：⭐⭐（需要配合评估，建议在第 9 点就绪后做）。

---

## 3. RAG + 记忆优化：多层记忆架构落地

**现状代码**：
- 记忆召回：`app/services/memory_service.py` → `recall_memories()`
- 记忆抽取子图：`app/agents/memory/subgraph.py` + `nodes.py`
- 记忆合并：`build_consolidate_subgraph()`（`subgraph.py` 第 29 行）
- 知识检索：`app/services/rag_service.py` → `search_knowledge()`

**多层记忆现状盘点**（已经有雏形，但未完全落地）：

| 层级 | 现有实现 | 落地情况 |
|------|---------|---------|
| 短期（会话内） | `ChatState.chat_history`（最近 10 条，`chat_system.py` 第 77 行） | ✅ 有，但只是滑动窗口 |
| 中期（结构化记忆） | `Memory` 表 + `recall_memories` 打分召回 | ✅ 有，质量打分 + 时间衰减 |
| 长期（摘要/档案） | `MemorySummary`（consolidate）+ profile 记忆 | ⚠️ consolidate 子图存在但**未见定时调度** |

**关键缺口与优化方向**：
1. **consolidate 没有触发器**：`build_consolidate_subgraph` 定义了，
   但没找到定时任务/阈值触发它。建议加：
   - 当某用户 active 记忆数超过阈值（如 50）→ 触发合并归档；
   - 或定时（每周）把过去 N 天的记忆汇总成 `MemorySummary`。
2. **召回融合**：目前 `recall_memories` 和 `search_knowledge` 是**两个独立节点**，
   各自检索后拼进 prompt。可引入**统一上下文预算**（如总共最多 1500 token），
   按 `recall_score` / 知识 `score` 跨源排序后截断，避免上下文超长。
3. **召回质量**：`recall_memories` 已有
   `vector_similarity × time_decay × type_weight × quality`（很不错的设计），
   可补充**去重**（相似记忆合并）和 **rerank**（见第 7 点）。
4. **短期记忆升级**：当前 history 是定长窗口，可加「会话内滚动摘要」——
   超过 N 轮时用一次小模型调用把早期对话压缩成摘要，节省 token。

**优先级**：⭐⭐⭐（consolidate 调度是明确缺口，应补齐）。

---

## 4. LangGraph 优化：并行与图走向

**现状代码**：`app/agents/chat/graph.py`

**问题**：`recall_memories`（第 49 行）和 `search_knowledge`（第 50 行）是
**串行边**，但两者**互不依赖**（一个查记忆、一个查知识），白白串行等待两次 IO。

**优化方向**：
1. **并行 fan-out / fan-in**：LangGraph 支持从一个节点扇出到多个节点并发执行，
   再汇聚。把：
   ```
   identify_intent →(general)→ recall_memories → search_knowledge → assemble_prompt
   ```
   改成：
   ```
   identify_intent →(general)→ ┌ recall_memories ┐
                               ┤                 ├→ assemble_prompt → call_llm
                               └ search_knowledge ┘
   ```
   两个检索节点并发跑，`assemble_prompt` 作为 join 点（LangGraph 会等两个分支都完成）。
   预计省下一次 embedding+检索的串行耗时（百毫秒级）。
2. **注意 state 合并**：并行分支写入 `ChatState` 的**不同字段**
   （`recalled_memories` vs `knowledge`），不会冲突，天然安全。
   若未来并行写同一字段，需用 `Annotated[..., reducer]` 定义合并策略。
3. **条件边精简**：`route_after_intent`（`nodes.py` 第 79 行）目前只区分
   diet / general，其他 intent（body/plan/suggestion）都走 general。
   随着这些域 subgraph 落地，扩展这里的路由表即可。

**优先级**：⭐⭐⭐（并行化是确定可落地的提速点）。

---

## 5. 其它 Token 消耗优化

**现状代码**：`app/agents/base.py`（已加 `stream_usage=True`）、各 prompt builder

**优化清单**：
1. **设置 `max_tokens` 上限**：`get_chat_model` 目前没有限制输出长度，
   对话回复可加 `max_tokens`（如 800），防止超长回复烧 token。
2. **历史窗口动态裁剪**：`build_chat_messages` 固定取最近 10 条
   （`chat_system.py` 第 77 行），可改为**按 token 预算**裁剪 + 早期摘要（见第 3 点）。
3. **意图分类降本**：`identify_intent` 每条消息都调一次 LLM。可以**先跑规则**
   （`_rule_based_intent` 已存在），高置信度命中时**跳过 LLM**，只在规则不确定时调模型。
4. **上下文预算化**：记忆 top_k=3、知识 top_k=3 是定值，可根据消息复杂度动态调整，
   简单闲聊不需要塞知识库。
5. **后台 extract/score 合并**：记忆子图里 `extract` 和 `score` 是两次 LLM 调用
   （`memory/nodes.py`），可考虑合并成一次「抽取并打分」的结构化调用，省一次往返。

**优先级**：⭐⭐（第 3、5 点收益明显）。

---

## 6. 是否需要 ReAct 模式？

**现状**：**没有 ReAct**。当前是固定 pipeline，工具（recall/search）是写死的节点，
不是由 LLM 「思考 → 决定调用哪个工具 → 观察结果 → 再思考」的循环。

**分析**：
- **现状的好处**：确定性强、延迟可控、易测试、token 可预测——
  对「健康记录/查询」这类**流程明确**的任务，固定 pipeline 反而更优。
- **何时需要 ReAct**：当出现「需要多步推理 + 动态决定调用顺序」的场景，例如：
  - 「我最近一周吃得健康吗」→ 需要先查饮食记录、再查目标、再算差距、再给建议；
  - 用户问题跨多个域，需要 agent 自主编排多个工具。

**优化建议**：
1. **不要全局改 ReAct**，保留主 pipeline 的确定性。
2. **局部引入**：在 `suggestion` / 复杂分析类 intent 下，挂一个 **ReAct 子图**
   （LangGraph 官方有 `create_react_agent`），把饮食查询、营养计算、目标对比
   做成 tool 交给它自主编排。
3. 工具已经具备改造基础：`chat/tools.py` 的 `recall_memories_tool` /
   `search_knowledge_tool`、`rag_service.lookup_nutrition` 都可包成 LangChain tool。

**优先级**：⭐（按需，等复杂分析需求出现再做）。

---

## 7. Embedding 是否要优化？

**现状代码**：`app/integrations/embedding/client.py`

**现状**：单条 `embed()` + 批量 `embed_batch()`（≤25），**无缓存**，每次查询都实时调用 API。

**优化方向**：
1. **查询向量缓存**：用户高频查询/重复消息会重复 embedding。加一层缓存
   （Redis 或内存 LRU，key = 文本 hash），命中则免一次 API 调用。
   记忆召回（`memory_service.recall_memories`）和知识检索都会受益。
2. **入库去重**：写记忆前 `embed_and_store`（`memory/nodes.py` 第 116 行）
   对每条 approved 记忆单独 `embed`，可改用 `embed_batch` 一次性批量，省往返。
3. **rerank（检索后精排）**：embedding 召回是「粗排」，可在 top-N 候选上接一个
   rerank 模型（如 DashScope `gte-rerank`）做精排，显著提升 RAG 命中质量。
   接入点：`rag_service.search_knowledge` 和 `memory_service.recall_memories`
   拿到候选后、返回前。
4. **维度权衡**：当前 1024 维，若召回质量足够，可评估更低维度换取存储/检索提速
   （需重建索引，谨慎）。

**优先级**：⭐⭐（查询缓存 + rerank 性价比高）。

---

## 8. LLM 返回格式有没有控制？

**现状代码**：多处用 `with_structured_output`

**盘点**：
- ✅ **结构化已覆盖**：`identify_intent`（`IntentResult`）、记忆
  `extract`/`score`/`consolidate`、diet 解析（`ParseResult`）都用了
  `with_structured_output(PydanticModel)`，格式有强约束。
- ⚠️ **自由文本未约束**：`call_llm`（`chat/nodes.py` 第 139 行）返回纯文本回复，
  没有结构约束（这对对话是合理的）。

**优化方向**：
1. **卡片/富文本结构化**：如果未来要让对话回复里带结构化卡片（如营养卡、建议列表），
   可让 `call_llm` 也走结构化输出（text + cards 的混合 schema），
   而不是现在在 `wrap_response` 里用规则拼卡片（`nodes.py` 第 193-245 行）。
2. **健壮性兜底**：`with_structured_output` 偶尔会解析失败，
   现有代码大多有 try/except fallback（很好），建议**统一**成一个装饰器/辅助函数，
   避免每个节点重复写兜底逻辑。
3. **JSON 模式显式化**：确认 DashScope 的 structured output 走的是 function-calling
   而非 prompt 约束，可靠性更高。

**优先级**：⭐（现状已不错，按产品需求推进）。

---

## 9. LLM 评分如何设计？

**现状代码**：`app/agents/prompts/memory_score.py` +
`app/agents/memory/nodes.py` → `score()` + `MemoryQualityScore` schema

**现状（已有不错的基础）**：记忆打分用 LLM 输出 4 个维度
`relevance / accuracy / actionability / uniqueness` + `overall_score`，
按阈值（≥80 active，≥60 pending，<60 丢弃）落库（`nodes.py` 第 92-112 行）。

**优化方向（分两类评分）**：

**A. 在线评分（已有，可增强）**——给记忆/输出打分用于过滤：
- 当前每条记忆一次 LLM 打分，成本不低。可批量打分（一次调用评多条），
  或对明显低价值内容先用规则过滤再送 LLM。

**B. 离线评估（缺口）**——评估 Agent 整体质量，建议补齐：
1. **建评估集**：用 LangSmith Dataset 收集真实对话样本
   （意图分类、饮食解析、回复质量各建一个集）。
2. **LLM-as-Judge**：写评估器给「回复相关性/安全性/个性化程度」打分，
   回归测试 prompt 改动（呼应第 2 点的 A/B）。
3. **关键指标**：意图分类准确率、饮食解析字段准确率、记忆召回 precision@k。
4. 接入方式：LangSmith Evaluations（你已接入 LangSmith，详见
   `courses/28-langsmith-observability/langsmith-tutorial.md`）。

**优先级**：⭐⭐⭐（离线评估是当前最大缺口，支撑后续所有优化的「度量」）。

---

## 10. 速度优化

**汇总（很多与前面点重叠，这里按「延迟」视角归类）**：

1. **并行检索**（第 4 点）：recall + search 并发，省一次串行 IO。⭐⭐⭐
2. **Prompt 前缀缓存**（第 1 点）：命中缓存降低 prefill 延迟。⭐⭐⭐
3. **规则短路意图分类**（第 5 点）：高置信度规则命中时跳过一次 LLM 往返。⭐⭐⭐
4. **Embedding 缓存**（第 7 点）：重复查询免 API 调用。⭐⭐
5. **流式已就绪**：`call_llm` 已 `streaming=True` + SSE
   （`chat/nodes.py` 第 151 行 / `streaming/translator.py`），首 token 体验已优化。✅
6. **后台任务已异步**：记忆抽取 fire-and-forget（`nodes.py` 第 175 行），
   不阻塞主回复。✅
7. **连接复用**：确认 `AsyncOpenAI` / DB 连接池复用，避免每请求新建连接
   （`embedding/client.py`、`db/session.py`）。⭐
8. **模型选择**：意图分类/记忆打分这类「轻任务」可用更快更便宜的小模型
   （如 `qwen-turbo`），把 `qwen-plus` 留给对话生成。⭐⭐

---

## 查缺补漏：你没列到但建议关注的点

| 缺口 | 说明 | 优先级 |
|------|------|--------|
| **离线评估体系** | 第 9B 点，所有优化都需要「能度量」才能验证，建议优先建 | ⭐⭐⭐ |
| **consolidate 调度** | 第 3 点，合并子图已写但没触发器，长期记忆无法真正沉淀 | ⭐⭐⭐ |
| **可观测性 metadata** | trace 未打 `user_id`/`request_id` tag，线上排障困难（见 langsmith 教程第五节） | ⭐⭐ |
| **限流/重试/降级** | LLM/embedding API 的限流与重试策略是否完善，高并发下的稳定性 | ⭐⭐ |
| **成本监控告警** | 用 LangSmith Monitor 对 token/成本设告警阈值，防止异常烧钱 | ⭐⭐ |
| **小模型分级** | 轻任务用 qwen-turbo、重任务用 qwen-plus，成本与速度双优化 | ⭐⭐ |
| **Prompt 版本管理** | prompt 散在代码里，改动无版本追踪，可考虑 LangSmith Prompt Hub 或 git tag | ⭐ |

---

## 建议的优化推进顺序

1. **先建「度量」**：离线评估体系（第 9B）+ LangSmith metadata（查缺补漏）——
   没有度量，后面的优化无法验证好坏。
2. **再做「确定收益」的提速**：并行检索（第 4）+ Prompt 前缀缓存（第 1）+
   规则短路意图（第 5）。
3. **接着补「能力缺口」**：consolidate 调度（第 3）+ embedding 缓存/rerank（第 7）。
4. **最后做「按需增强」**：局部 ReAct（第 6）+ 结构化回复（第 8）+ prompt 简化（第 2）。

---

## 代码位置速查表

| 优化点 | 主要文件 |
|--------|---------|
| Prompt / 前缀缓存 | `app/agents/prompts/chat_system.py` |
| 图走向 / 并行 | `app/agents/chat/graph.py` |
| 节点逻辑 / 意图分类 | `app/agents/chat/nodes.py` |
| 工具封装 | `app/agents/chat/tools.py` |
| 记忆召回 / 打分算法 | `app/services/memory_service.py` |
| 记忆抽取子图 | `app/agents/memory/subgraph.py` + `nodes.py` |
| 记忆评分 prompt | `app/agents/prompts/memory_score.py` |
| RAG 检索 | `app/services/rag_service.py` |
| Embedding 客户端 | `app/integrations/embedding/client.py` |
| 模型工厂 / token 控制 | `app/agents/base.py` |
| 流式翻译 | `app/streaming/translator.py` |
| diet 子图 | `app/agents/diet/subgraph.py` + `nodes.py` |

