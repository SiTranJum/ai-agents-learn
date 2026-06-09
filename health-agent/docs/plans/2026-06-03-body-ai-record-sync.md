# 身体数据 AI 记录 + 首页双向同步（饮水/睡眠/运动/排便）

## 目标
把饮食已有的「AI 对话解析 → 首页卡片 pending → 确认/取消双向同步」能力，
复刻到饮水、睡眠、运动、排便四类身体数据。

## 用户已拍板的决策
1. **四类一起做**（water/sleep/exercise/bowel）
2. **饮水区分 append/replace**（"又喝了"→append；"说错了是500ml"→replace）
3. **首页直接确认**（不跳编辑页，卡片内确认/取消）

## 现状盘点
| 层 | 现状 |
|----|------|
| 后端 body CRUD | ✅ 完整（`api/v1/body.py` 全类型 POST/PUT/GET/DELETE） |
| 后端 body Agent | ❌ 无 subgraph，chat graph 只路由 diet |
| 后端 intent | ⚠️ `Intent` 已含 `body`，但 `route_after_intent` 只走 diet/general |
| 后端 body 卡片 | ❌ 无 body_parse 卡片 schema/builder |
| 前端 body service | ✅ `dataService.saveBodyData` 支持全 6 类 |
| 前端 pending | ❌ 仅 diet 有 pending store |
| 前端首页辅助卡片 | ⚠️ `AuxiliaryRecordGrid` 仅展示，无 pending/确认交互 |

## 架构对称参考（diet 已有实现）
- subgraph: `agents/diet/{nodes,subgraph}.py`
- prompt: `agents/prompts/diet_parse.py`（含 append/replace 判断）
- schema: `schemas/diet.py`（`ParseResult` 带 `operation`）
- 卡片: `agents/chat/nodes.py::_parse_result_to_card` + `wrap_response`
- 前端 pending: `diet/store/dietStore.ts`
- 前端同步: `ai/hooks/useStreamingChat.ts::syncDietParseToPending`
- 前端确认: `home/screens/HomeScreen.tsx::handleConfirmMeal`

## 关键设计决策

### 1. 单一 body subgraph，而非 4 个
四类共用一个 `body` subgraph，内部用 `body_record_type` 区分。
理由：避免 4 套几乎相同的 graph 装配；intent 已是单一 `body`。

### 2. 一个 LLM 调用同时解析「类型 + 字段 + operation」
prompt 让 LLM 输出 `BodyParseResult`：
```python
class BodyParseResult(BaseModel):
    record_type: BodyRecordType  # water/sleep/exercise/bowel（weight/measurement 暂不接 AI）
    operation: DietOperation     # 复用，仅 water 用 append；其余恒 replace
    # 各类型字段（可选，按 record_type 填充）
    water_amount: int | None
    sleep_bed_time / wake_time / quality
    exercise_type / duration
    bowel_time / status
    confidence: float
```

### 3. operation 仅对 water 生效
- water: LLM 判断 append/replace
- sleep/exercise/bowel: 强制 replace（prompt 说明 + 后端兜底）

### 4. 前端统一 pending store（bodyPendingStore）
新建 `data/store/bodyPendingStore.ts`，key = `${date}_${recordType}`，
value 含 `recordType / fields / operation / cardId`。
不复用 dietStore（语义/字段差异大）。

## 实施步骤（按 commit 粒度）

### Commit 1：后端 body subgraph + 卡片 + 路由
**新增**
- `agents/prompts/body_parse.py`：BodyParseResult prompt（四类解析 + append/replace）
- `agents/body/nodes.py`：`parse_body_text` / `normalize_body` / `route_body_input`
- `agents/body/subgraph.py`：装配
- `schemas/body.py`：加 `BodyParseResult`、各类型 `*Create` 加 `operation`（仅 water 用）

**修改**
- `agents/chat/state.py`：加 `body_*` 字段（input_text/parse_result/record_type/date/body_service）
- `agents/chat/graph.py`：挂 `body` node，`route_after_intent` 加 body 分支
- `agents/chat/nodes.py`：`route_after_intent` 返回 body；`_parse_result_to_card`
  支持 body_parse 卡片；`wrap_response` 处理 body intent
- `api/v1/ai.py`：state 注入 `body_service`、`body_input_text` 等

**验证**：`python -c "import app.agents.chat.graph; ..."` + 现有 pytest

### Commit 2：后端 water append + body upsert 语义
- `services/body_service.py`：`create_water` 已支持累加；确认 append 行为
- sleep/exercise/bowel：按 date+type upsert（已有记录则 PUT，否则 POST）
  —— 复用前端 `saveBodyData` 现成逻辑，后端无需大改
- `api/v1/body.py`：water POST 透传 operation（append/replace）

### Commit 3：前端类型 + pending store + AI 同步
- `ai/types/ai.types.ts`：加 `BodyParseCardPayload` + `BodyParseCard`
- `data/store/bodyPendingStore.ts`：新建（仿 dietStore）
- `ai/hooks/useStreamingChat.ts`：`syncBodyParseToPending`（解析 body_parse 卡片）
- `ai/utils/cardId.ts`：getCardId 已通用，无需改

### Commit 4：前端首页辅助卡片 pending + 确认/取消
- `home/types/home.types.ts`：HomeAuxiliary 各项加 pending 态字段
- `home/services/homeService.ts`：`fetchBodyToday` 合并 bodyPending
- `home/components/AuxiliaryRecordGrid.tsx`：pending 态展示 + 确认/取消按钮
- `home/screens/HomeScreen.tsx`：`handleConfirmAux` / `handleCancelAux`
  （调 dataService.saveBodyData，确认后清 pending + 同步卡片状态）

### Commit 5：联调 + 测试
- tsc 校验
- 后端 import + pytest
- 三类场景：饮水累加、睡眠 replace、运动/排便确认

## 风险与注意
- **intent 误判**：body 关键词和 diet 可能重叠（如"运动后吃了…"），
  靠 LLM 分类 + 规则兜底，必要时迭代 prompt。
- **sleep/exercise 多字段缺失**：用户只说"睡了8小时"没说入睡时间，
  LLM 需推断或留空；首页确认时缺字段如何处理 → 缺 bed_time/wake_time
  时用 duration 反推或给默认值，确认前端做必填校验。
- **water 单位**：ml/杯/瓶换算（一杯=250ml），prompt 给换算表。
- **不接 AI 的类型**：weight/measurement 不在本次范围（首页也没这俩卡片）。

## 不做（明确排除）
- 体重/围度的 AI 解析
- 编辑页预填路径（用户选了首页直接确认）
- 历史记录的 AI 修改
