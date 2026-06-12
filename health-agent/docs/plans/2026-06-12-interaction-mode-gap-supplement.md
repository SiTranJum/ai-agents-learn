# AI 交互模式 —— 文档与实现差异分析及补充计划

> 日期：2026-06-12
> 范围：master PRD v2 第 4 节「AI 交互模式配置」（效率 / 确认 / 学习）
> 目的：盘点"交互模式"从 PRD 到代码的落地缺口，给出补充计划
>
> **决策已定（2026-06-12）：**
> - **D1 = 方案 B**：注册时强制选模式，Onboarding 由 5 步增至 6 步。
> - **D2 = 要做**：V1 范围内真正实现三种模式的 AI 行为差异。
> - 即缺口 1、缺口 2 全部要做（阶段 1 + 阶段 2 均执行）。
>
> **实施进度（2026-06-12 15:00）：**
> - ✅ **后端已完成**：阶段 1（AI 行为按模式区分）+ 阶段 2（OnboardingPayload 接收模式）全部落地，单测通过。
> - ⏳ **前端待工程建立**：`app/` 目录尚不存在，前端任务（Onboarding 改造、AI 浮层渲染）需等前端工程搭建完成后执行。

---

## 一、背景

master PRD v2 把「AI 交互模式」列为核心设计之一（第 4 节）：

- **效率模式**：AI 直接执行，Toast 提示，不需确认
- **确认模式**（默认）：AI 解析后展示结果，用户确认才生效
- **学习模式**：AI 解析后展示结果 + 知识讲解，用户确认才生效

它的产品价值是：**同一句话输入，三种模式下 AI 的输出方式（是否确认、是否附带知识）不同**。这是模式存在的"灵魂"。

---

## 二、各层现状盘点

| 层级 | 文件 | 现状 | 状态 |
|------|------|------|------|
| Master PRD | `docs/prd/00-master-prd-v2.md` §4 | 定义三种模式 + 注册第二步"必填选择" | ✅ 有 |
| 子 PRD | `docs/prd/v1/02-app-framework.md` §2.9 | 定义三种模式 + 影响范围表 + "注册后选择（推荐确认模式）" | ✅ 有 |
| 子 PRD | `docs/prd/v1/01-user-system.md` | 注册流程 **未提** 交互模式 | ⚠️ 缺 |
| UI 设计 | `docs/prd/v1/ui-design/13-auth-and-onboarding.md` | Onboarding 设计为 **5 步**，无模式选择步骤 | ⚠️ 缺 |
| UI 设计 | `docs/prd/v1/ui-design/12-profile-and-settings.md` | 设置页有交互模式入口 | ✅ 有 |
| 后端 schema | `backend/app/schemas/user.py` | `InteractionMode` 枚举 + Settings 模型，默认 `confirmation` | ✅ 有 |
| 后端 DB | `backend/app/db/models/user.py` + alembic | `interaction_mode` 字段，默认 `confirmation` | ✅ 有 |
| 后端 API | `PUT /users/me/settings`、`GET /users/me` | 可读写 `interaction_mode` | ✅ 有 |
| **后端 AI 消费** | `backend/app/services/user_service.py` `get_profile_for_ai()` | **不返回** `interaction_mode`（user_service.py:138） | ❌ 缺 |
| **后端 AI 消费** | `backend/app/agents/**`（chat / diet / body 等） | `ChatState` 无模式字段；`SYSTEM_PROMPT` 写死、`build_chat_messages` 不读模式；`wrap_response` 无条件出确认卡片 | ❌ 缺 |
| 前端设置页 | `app/src/features/profile/screens/SettingsScreen.tsx` | 三种模式 radio 选择，可保存 | ✅ 有 |
| 前端服务 | `app/src/features/profile/services/profileService.ts` | 读写 `interaction_mode` 接口打通 | ✅ 有 |
| 前端全局态 | `app/src/core/store/globalStore.ts` | 存有 `globalMode` | ✅ 有 |
| 前端注册 | `app/src/features/auth/screens/OnboardingScreen.tsx` | Onboarding 5 步，**无模式选择** | ⚠️ 缺 |
| **前端 AI 行为** | `app/src/features/ai/**` | **完全不读取** `interactionMode`，浮层/对话行为对三种模式无差异 | ❌ 缺 |

---

## 三、差异归纳（按严重程度）

### 🔴 缺口 1：AI 行为未按模式区分（最严重，模式形同虚设）

这是最核心的问题。当前 `interaction_mode` 只是一个"存了但没人用"的字段。经核对 graph 代码确认，**graph 流程、state、prompt 三处都不感知模式**：

- **State 不携带模式**：`backend/app/agents/chat/state.py` 的 `ChatState` 无 `interaction_mode` 字段。唯一的 `mode`（state.py:46）是 diet 子图的**保存开关**，值为 `"create"`/`None`，由 `save_or_end`（diet/nodes.py:221）判断是否落库，与交互模式无关。
- **Prompt 写死，不读模式**：`build_chat_messages`（prompts/chat_system.py:47）入参仅 user_message / history / memories / knowledge；`SYSTEM_PROMPT`（chat_system.py:10）是固定常量，无模式分支。`assemble_prompt` 节点（chat/nodes.py:140）调用时也未传模式。
- **响应结构对所有模式一视同仁**：`wrap_response`（chat/nodes.py:260）**无条件**给饮食/身体数据生成带「确认保存」按钮的卡片（diet action `confirm_create_diet_record` 见 nodes.py:213，body 同理）。等于无论用户选效率/确认/学习，AI 都按"确认模式"行为——都出确认卡片、都不附知识讲解。
- **AI 档案不返回模式**：`get_profile_for_ai()`（user_service.py:138）不返回 `interaction_mode`，agent 即便想读也拿不到。
- **前端**：`features/ai` 浮层与对话页不读取 `interactionMode`，三种模式下展示完全相同。

**后果**：用户在设置页切换模式没有任何实际效果，效率模式（应直接执行 + Toast）与学习模式（应附知识讲解）在 graph 层根本没有对应分支，模式功能实际未生效。

### 🟡 缺口 2：注册流程缺模式选择，且 PRD 内部自相矛盾

- master PRD v2（§3.3 注册第二步）：交互偏好 **必填**，注册时选择模式。
- 子 PRD `02-app-framework.md`（§2.9.2）：注册 **完成后** 选择，推荐确认模式。
- UI 设计稿 `13-auth-and-onboarding.md`：Onboarding 共 **5 步**，无模式选择。
- 实际代码 `OnboardingScreen.tsx`：5 步，无模式选择，新用户默认 `confirmation`。

**三份文档说法不一致**，需要先拍板"注册时到底选不选"，再统一文档与实现。

### 🟢 缺口 3：子 PRD `01-user-system.md` 未提交互模式

用户体系子 PRD 的注册流程章节完全没提交互模式，与 `02-app-framework.md` 存在职责重叠/遗漏。需明确：交互模式归属哪个模块、在哪份子 PRD 描述。

---

## 四、补充计划

### 决策项（已确认 2026-06-12）

> **D1. 注册时是否强制选模式？→ ✅ 方案 B**
> - ~~方案 A：注册不选，统一默认 `confirmation`~~
> - **方案 B（已选）**：Onboarding 增加 1 步模式选择（5 步 → 6 步）。需改 UI 设计稿、`OnboardingScreen.tsx`、onboarding 提交逻辑。

> **D2. V1 范围内，AI 行为是否要真正实现三模式差异？→ ✅ 要做**
> - 缺口 1 必须做，工作量集中在后端 agent（state/prompt/wrap_response）与前端 AI 浮层。
> - ~~暂不做~~

> **结论**：阶段 0、阶段 1、阶段 2、阶段 3 全部执行。

---

### 任务清单

#### 阶段 0：决策与文档对齐（必做，先行）

- [x] 确认 D1（方案 B）、D2（要做）两个决策项
- [ ] 统一 master PRD v2 §3.3 与子 PRD `02-app-framework.md` §2.9.2 的描述：均改为"注册时（Onboarding 第 X 步）强制选择交互模式"，与 D1=方案 B 对齐
- [ ] 在 `01-user-system.md` 或 `02-app-framework.md` 中明确交互模式的归属模块，消除重叠

#### 阶段 1：AI 行为按模式区分（缺口 1，D2=要做，✅ 后端已完成 2026-06-12）

后端（✅ 已完成）：
- [x] `user_service.get_profile_for_ai()` 增加返回 `interaction_mode`（user_service.py:179）
- [x] `ChatState` 新增 `interaction_mode: str | None` 字段（chat/state.py:59）
- [x] API 层注入 `interaction_mode` 到 graph state（ai.py:449、457）
- [x] `build_chat_messages` 接收 `interaction_mode` 参数，按模式追加 `MODE_INSTRUCTIONS` 到 system prompt（prompts/chat_system.py:53、74）
- [x] `assemble_prompt` 传递 `state.get("interaction_mode")` 到 `build_chat_messages`（chat/nodes.py:148）
- [x] `save_or_end` 节点：效率模式下自动触发 diet 子图保存（diet/nodes.py:221）
- [x] `wrap_response` 按模式区分响应结构（chat/nodes.py:262）：
  - 效率模式：diet 子图已落库，返回 `requires_confirmation=False` 的结果卡片（无"确认保存"按钮）+ "已记录" Toast 文案
  - 确认模式：生成带"确认保存"按钮的卡片（`requires_confirmation=True`）
  - 学习模式：确认卡片 + `knowledge` 字段附带知识讲解（基于 `NutritionSummary` 生成）
- [x] `ChatCard` schema 增加 `requires_confirmation: bool` 和 `knowledge: str | None` 协议字段（schemas/chat.py:81-82）
- [x] 补充单测 `tests/agents/test_interaction_mode.py`：验证三模式行为差异 + 效率模式自动保存

前端（⏳ 待前端工程建立）：
- [ ] `features/ai` 浮层/对话组件读取 `globalMode` / `interactionMode`
- [ ] 按模式渲染：效率（Toast）/ 确认（确认按钮卡片）/ 学习（卡片 + 知识区块）
- [ ] 对齐后端 `requires_confirmation` / `knowledge` 协议字段

文档（⏳ 待执行）：
- [ ] 在后端 spec（`specs/backend/02-ai-modules/` 相关文件）补充"交互模式如何影响 agent 行为"
- [ ] 在前端 spec（`specs/frontend/modules/16-ai-dialog-module.md`）补充模式渲染规则

#### 阶段 2：注册流程补模式选择（缺口 2，D1=方案 B，✅ 后端已完成 2026-06-12）

后端（✅ 已完成）：
- [x] `OnboardingPayload` 增加 `interaction_mode: InteractionMode` 字段，默认 `confirmation`（schemas/user.py:113）
- [x] `complete_onboarding` 写入 `interaction_mode` 到 settings 表（services/user_service.py:266-268）

前端（⏳ 待前端工程建立）：
- [ ] UI 设计稿 `13-auth-and-onboarding.md`：新增模式选择步骤，更新进度条 5→6 步、文案、组件树
- [ ] `OnboardingScreen.tsx`：`TOTAL_STEPS` 5→6，新增模式选择 step，`canProceed` 校验，`OnboardingData` 增加 `interactionMode`
- [ ] `auth.types.ts` / onboarding 提交逻辑：携带 `interaction_mode` 提交
- [ ] 预览页展示所选模式

#### 阶段 3：子 PRD 收口（缺口 3）

- [ ] 按阶段 0 的归属决策，在对应子 PRD 补全交互模式描述
- [ ] 检查 `08-ai-suggestion.md`、`07-plan-system.md` 等是否需要标注"受交互模式影响"

---

## 五、最小可行建议（已被决策覆盖，仅留存参考）

> 注：D1 已定方案 B、D2 已定要做，本节的"省力路线"不再采用，保留仅作背景参考。

若学习/内测阶段想省力（**未采用**）：

1. ~~D1 选方案 A（注册不选，默认确认模式）~~ → 实际选方案 B。
2. **D2 的"只做饮食记录一个场景"仍可作为阶段 1 的落地起点**：AI 行为差异先在「饮食记录」场景跑通（master PRD 影响范围表里最核心的场景，对应 `wrap_response` 的 diet 分支），验证前后端协议后再扩展到 body 等其余场景。
3. 文档同步对齐，避免再出现"字段存了但没人用"的状态。

---

## 附录：关键代码位置

| 用途 | 路径 |
|------|------|
| 后端枚举/Settings 模型 | `backend/app/schemas/user.py:52-55, 97, 155` |
| 后端 DB 字段 | `backend/app/db/models/user.py:86` |
| 后端 AI 脱敏档案（待补字段） | `backend/app/services/user_service.py:138` |
| 后端 agent 目录（待接入） | `backend/app/agents/` |
| 前端设置页（已实现选择） | `app/src/features/profile/screens/SettingsScreen.tsx:39-131` |
| 前端 profile 服务 | `app/src/features/profile/services/profileService.ts:172-194` |
| 前端全局态 | `app/src/core/store/globalStore.ts` |
| 前端 Onboarding（5 步，待补） | `app/src/features/auth/screens/OnboardingScreen.tsx:45` |
| 前端 AI 模块（待接入行为差异） | `app/src/features/ai/` |
