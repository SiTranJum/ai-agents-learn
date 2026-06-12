# AI 交互模式后端实施总结

> 日期：2026-06-12
> 状态：后端已完成，前端待工程建立

---

## 一、实施范围

根据补充计划（`2026-06-12-interaction-mode-gap-supplement.md`），决策为：
- **D1 = 方案 B**：注册时强制选择交互模式（Onboarding 5 步 → 6 步）
- **D2 = 要做**：V1 真正实现三种模式的 AI 行为差异

**本次实施**：完成后端全部改造（阶段 1 + 阶段 2），前端因工程尚未建立而待后续执行。

---

## 二、后端已完成改造

### 2.1 协议层：ChatCard 扩展

**文件**：`backend/app/schemas/chat.py`

**改动**：`ChatCard` 增加两个协议字段：

```python
class ChatCard(BaseModel):
    # ... 现有字段 ...
    requires_confirmation: bool = True   # False 表示后端已直接执行（效率模式）
    knowledge: str | None = None         # 学习模式附带的知识讲解文本
```

**语义**：
- `requires_confirmation=False`：效率模式，后端已自动保存记录，前端以 Toast 风格呈现结果，不显示"确认保存"按钮。
- `knowledge` 非空：学习模式，前端在卡片下方显示知识讲解区块。

---

### 2.2 State 层：注入 interaction_mode

**文件**：`backend/app/agents/chat/state.py`

**改动**：`ChatState` 增加字段：

```python
interaction_mode: str | None
```

**注入点**：`backend/app/api/v1/ai.py:449、457`

```python
interaction_mode = await user_service.get_interaction_mode()
state = {
    ...
    "interaction_mode": interaction_mode,
    ...
}
```

---

### 2.3 Prompt 层：模式感知的 system prompt

**文件**：`backend/app/agents/prompts/chat_system.py`

**改动**：

1. 新增 `MODE_INSTRUCTIONS` 字典，定义三种模式的追加指令：
   - `efficiency`：回复精简，直接给结论
   - `confirmation`：简洁，提示用户确认
   - `learning`：结论 + 简短知识讲解

2. `build_chat_messages` 新增 `interaction_mode` 参数，追加模式指令到 `SYSTEM_PROMPT`。

3. `assemble_prompt` 节点（`chat/nodes.py:148`）传递 `state.get("interaction_mode")`。

**效果**：general chat 对话在学习模式下会附带知识讲解，效率模式下更简洁。

---

### 2.4 响应层：wrap_response 按模式分流

**文件**：`backend/app/agents/chat/nodes.py`

**改动**：

1. **新增知识讲解生成函数**：
   - `_diet_knowledge_text(parse_result)`：基于 `NutritionSummary` 生成饮食知识
   - `_body_knowledge_text(parse_result)`：针对身体数据类型（水/睡眠/运动/排便）生成健康知识

2. **改造 `_parse_result_to_card` / `_body_result_to_card`**：
   - 接受 `requires_confirmation` 和 `knowledge` 参数
   - 效率模式下 `actions` 不含"确认保存"按钮，仅保留"修改食物"纠错入口

3. **改造 `wrap_response` 节点（262 行）**：
   - 读取 `interaction_mode`，区分三种模式
   - **效率模式**（`is_efficiency`）：
     - diet 子图已自动落库（见 2.5），返回 `requires_confirmation=False` 的卡片
     - 文案："已记录 lunch，1 项食物，共 232kcal"（Toast 风格）
   - **确认模式**：现有行为，出带"确认保存"按钮的卡片（`requires_confirmation=True`）
   - **学习模式**（`is_learning`）：确认卡片 + `knowledge` 字段

**body 限制**：body 子图尚无自动落库能力（V1 简化），效率模式下仍走确认卡片，学习模式正常附带知识。

---

### 2.5 执行层：效率模式自动保存

**文件**：`backend/app/agents/diet/nodes.py`

**改动**：`save_or_end` 节点（221 行）增加效率模式判断：

```python
def save_or_end(state: ChatState) -> str:
    mode = state.get("mode")
    interaction_mode = state.get("interaction_mode")
    if mode == "create" or interaction_mode == "efficiency":
        return "save_record"  # 进入保存节点
    return "__end__"
```

**流程**：
- 确认/学习模式：diet 子图解析后直接结束，返回 `parse_result`，由 `wrap_response` 出确认卡片。
- 效率模式：diet 子图解析后自动进入 `save_record` 节点落库，`wrap_response` 检测到已保存，返回 Toast 风格结果。

---

### 2.6 Onboarding 层：接收并写入交互模式

**文件**：
- `backend/app/schemas/user.py`（113 行）
- `backend/app/services/user_service.py`（266-268 行）

**改动**：

1. `OnboardingPayload` 增加字段：

```python
interaction_mode: InteractionMode = InteractionMode.confirmation  # 默认确认模式，兼容旧客户端
```

2. `complete_onboarding` 写入 settings：

```python
await self.repo.update_settings(
    {"interaction_mode": payload.interaction_mode.value}
)
```

**前端对接**：前端 Onboarding 第 6 步（新增）提交 `interaction_mode`，后端直接落库。

---

### 2.7 单测覆盖

**文件**：`backend/tests/agents/test_interaction_mode.py`

**覆盖场景**：
1. `test_confirmation_mode_emits_confirm_card`：确认模式出确认卡片，`requires_confirmation=True`，有"确认保存"按钮。
2. `test_efficiency_mode_no_confirm_card`：效率模式卡片 `requires_confirmation=False`，无"确认保存"按钮，文案含"已记录"。
3. `test_learning_mode_attaches_knowledge`：学习模式卡片附带非空 `knowledge` 字段。
4. `test_build_chat_messages_mode_changes_system_prompt`：三种模式的 system prompt 不同。
5. `test_efficiency_mode_auto_saves_via_graph`：效率模式跑完整 graph，diet 子图自动落库（`_FakeDietService.saved == True`）。

**运行结果**：全部通过（8 passed in 7.57s）。

---

## 三、前端待办（工程建立后执行）

**阻塞原因**：`health-agent/app/` 目录尚不存在，前端工程未搭建。

**待办任务**：

### 3.1 Onboarding 改造（阶段 2）

- [ ] UI 设计稿更新：`docs/prd/v1/ui-design/13-auth-and-onboarding.md` 新增第 6 步"选择交互模式"
- [ ] `OnboardingScreen.tsx`：
  - `TOTAL_STEPS` 改为 6
  - 新增 step 6 的 UI（三选一 radio：效率/确认/学习，附简短说明）
  - `OnboardingData` 增加 `interactionMode: InteractionMode` 字段
  - 提交时携带 `interaction_mode`
- [ ] 预览页展示所选模式

### 3.2 AI 浮层/对话改造（阶段 1）

- [ ] 读取 `globalMode` 或当前用户的 `interactionMode`
- [ ] 解析 SSE 流中的 `ChatCard`，读取 `requires_confirmation` / `knowledge` 字段
- [ ] 按协议渲染：
  - `requires_confirmation=false`：Toast 风格，不显示确认按钮
  - `requires_confirmation=true`：确认卡片，显示"确认保存"按钮
  - `knowledge` 非空：在卡片下方显示知识讲解区块（可折叠）

### 3.3 文档补充（阶段 0/3）

- [ ] 后端 spec（`specs/backend/02-ai-modules/`）补充交互模式影响 agent 行为的说明
- [ ] 前端 spec（`specs/frontend/modules/16-ai-dialog-module.md`）补充模式渲染规则
- [ ] 统一 master PRD / 子 PRD 的注册流程描述（均改为"Onboarding 第 X 步选模式"）

---

## 四、验证清单

后端实施完成后，可通过以下方式验证：

### 4.1 单测验证

```bash
cd backend
pytest tests/agents/test_interaction_mode.py tests/agents/test_chat_agent.py -v
```

**预期**：全部通过，覆盖三模式行为差异。

### 4.2 API 集成测试（前端工程建立后）

**场景 1：效率模式饮食记录**

```bash
# 1. 设置用户为效率模式
PUT /api/v1/users/me/settings
{"interaction_mode": "efficiency"}

# 2. 发送饮食记录
POST /api/v1/ai/chat (SSE)
{"type": "text", "message": "午饭吃了一碗米饭"}

# 预期响应：
# - ai_response: "已记录 lunch，1 项食物，共 232kcal"
# - response_cards[0].requires_confirmation: false
# - response_cards[0].actions: 不含 "confirm_create_diet_record"
# - 数据库已有记录（diet_records 表）
```

**场景 2：学习模式饮食记录**

```bash
PUT /api/v1/users/me/settings
{"interaction_mode": "learning"}

POST /api/v1/ai/chat
{"type": "text", "message": "午饭吃了一碗米饭"}

# 预期响应：
# - response_cards[0].requires_confirmation: true
# - response_cards[0].knowledge: "本餐约 232kcal，三大营养素：..."
# - 数据库无记录（需用户点"确认保存"）
```

**场景 3：确认模式（默认）**

```bash
POST /api/v1/ai/chat
{"type": "text", "message": "午饭吃了一碗米饭"}

# 预期响应：
# - response_cards[0].requires_confirmation: true
# - response_cards[0].knowledge: null
# - response_cards[0].actions: 含 "confirm_create_diet_record"
```

---

## 五、技术要点与设计考量

### 5.1 为什么 body 效率模式不自动保存？

body 子图解析出 4 种不同类型数据（水/睡眠/运动/排便），各有独立的 save 方法（`create_water` / `create_sleep` 等）。要实现效率模式自动保存，需在 body 子图增加：
1. `save_body_record` 节点，内部根据 `record_type` dispatch 到不同 service 方法。
2. `save_or_end` 条件边，逻辑同 diet。

**V1 简化决策**：body 效率模式仍走确认卡片，标注为"V1 限制，V2 实现"，避免过度工程化。学习模式的知识讲解已支持。

### 5.2 为什么 state 字段名是 interaction_mode 而不是 mode？

`state["mode"]` 已被 diet 子图占用，值为 `"create"` 或 `None`，是**保存开关**（决定是否调 `save_record` 节点）。`interaction_mode` 是用户偏好，两者语义不同，必须分开。

### 5.3 knowledge 文本如何生成？

**diet**：基于 `NutritionSummary`（总热量、蛋白质、脂肪、碳水）生成固定模板：

```python
f"本餐约 {s.total_calories:.0f}kcal，三大营养素：碳水 {s.total_carbs:.0f}g、蛋白质 {s.total_protein:.0f}g、脂肪 {s.total_fat:.0f}g。碳水是主要供能来源，蛋白质有助于肌肉合成与饱腹，脂肪需适量控制。"
```

**body**：根据 `record_type` 返回对应健康知识（如睡眠："规律作息和 7–9 小时睡眠有助于代谢和食欲激素平衡"）。

**未来优化**：可用 LLM 动态生成更个性化的讲解，但 V1 固定模板已足够。

---

## 六、小结

**已完成**：
- ✅ ChatCard 协议扩展（`requires_confirmation` / `knowledge`）
- ✅ State / Prompt / 响应层全部模式感知
- ✅ 效率模式 diet 自动保存
- ✅ Onboarding 接收并落库 `interaction_mode`
- ✅ 单测覆盖三模式行为差异

**待前端工程建立后执行**：
- ⏳ Onboarding UI 增加第 6 步"选择交互模式"
- ⏳ AI 浮层/对话按 `requires_confirmation` / `knowledge` 渲染
- ⏳ 文档对齐（PRD / spec）

**V2 优化方向**：
- body 效率模式自动保存
- LLM 驱动的个性化知识讲解
- plan / suggestion 等场景的模式差异（V1 仅落地 diet / body / general chat）

---

**实施人员**：Claude Opus 4.6
**实施日期**：2026-06-12
**代码审查**：待前端工程建立后统一 review
