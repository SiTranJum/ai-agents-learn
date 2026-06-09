# 健康管家 V1 待优化清单

> 生成日期：2026-05-15
> 来源：用户在端到端联调中发现的 6 个问题
> 状态：已扫描定位，未修复

---

## 1. 首页下拉无法刷新（疑似）

**现象**：HomeScreen 下拉手势触发后，没有看到重新加载的数据 / 转圈指示器。

**代码位置**：
- `src/features/home/screens/HomeScreen.tsx:122-128`（RefreshControl）
- `src/features/home/hooks/useHomeData.ts`（queryKey: `['home', date]`）
- `src/features/home/services/homeService.ts:assembleHomeData`（前端组合调用 dietService + dataService）

**根因分析**：
- `homeService.getHomeData()` 内部并行调用 `dietService.getDietByDate()` + `dataService.getTodayRecords()`，但**这两个调用是 service 直接发起的，不走 react-query 缓存**。
- `query.refetch()` 会重新执行 `homeService.getHomeData(date)`，理论上应该重新发请求。
- 可能问题：
  - a. `RefreshControl` 的 `tintColor` 设了 primary 色，但 Web 端在浅色背景下不可见；
  - b. `isRefetching` 状态切换太快，用户没看到指示器；
  - c. 后端响应过快，下拉手势还没结束就完成了。

**建议优化**：
- 改用 `useQueries` 把 diet/body 两个调用拆开，分别走缓存，refetch 时分别命中对应 cacheKey；
- 或者下拉时强制 `await new Promise(r => setTimeout(r, 500))` 让用户看到指示器（属于 UX 妥协）；
- Web 端检查 RefreshControl 的兼容性（react-native-web 对 RefreshControl 支持不完整，可能需要自己实现 pull-to-refresh）。

---

## 2. 记录保存后延迟几秒才显示

**现象**：用户在编辑页保存饮食/身体数据后，回到列表/今日卡片，需要等几秒才能看到新数据。

**代码位置**：
- `src/features/data/hooks/useDataTrend.ts:useSaveBodyData`（onSuccess 调 `invalidateQueries(['data'])`）
- `src/features/diet/hooks/useDietData.ts:saveMutation`（onSuccess 调 `invalidateQueries(['diet', date])`）
- `src/features/diet/services/dietService.ts:saveDietRecord`（PUT /diet/records/upsert 后端要软删多条 + 创建新条 + 重新查询）

**根因分析**：
1. **后端慢**：upsert 端点要执行"软删除旧记录 → 创建新记录 → RAG 补全营养"，单次写入可能 1-3 秒。
2. **前端策略不优**：当前是"`mutation.onSuccess` → `invalidateQueries` → 触发新一次 GET → 后端再查一次 → 返回 → UI 更新"。即使后端写入只要 500ms，整个链路要 1-2 次往返。
3. 可优化：mutation 的 `onSuccess` 拿到的 `data` 已经是最新结果，应该用 `queryClient.setQueryData` **直接乐观更新**缓存，不再发新请求。

**建议优化**（P1）：
```ts
// useSaveBodyData
onSuccess: (saved, vars) => {
  // 直接把返回的最新数据写进 today cache，不再发 GET
  qc.setQueryData(['data', 'today'], (old: TodayRecords | undefined) => ({
    ...(old ?? emptyToday),
    [vars.type]: saved,
  }));
  qc.invalidateQueries({ queryKey: ['data', 'trend'] });
  qc.invalidateQueries({ queryKey: ['home'] });
}
```

后端层面也可以查：
- `PUT /diet/records/upsert` 是否需要在事务结束后再做一次完整查询返回？能否直接返回新插入的那一条？
- RAG 营养补全是否可以异步（先返回基础数据，后端 background task 补全）？

---

## 3. 首页辅助卡片跳转不带维度

**现象**：首页 2×2 网格点击"饮水/睡眠/运动/排便"，都跳到数据页，但数据页 Tab 没切到对应维度。

**代码位置**：
- `src/features/home/screens/HomeScreen.tsx:85-91`：
  ```ts
  const handleAuxItemPress = useCallback((_type: AuxiliaryItemType) => {
    navigation.navigate('DataTab');
    // DataTab 内部 tab 切换由 Phase 5 DataScreen 处理  ← 注释里写了 TODO
  }, [navigation]);
  ```
- `src/features/data/store/dataStore.ts`（持有 `selectedTab`）

**根因**：HomeScreen 接到了 `type` 参数（`AuxiliaryItemType`），但故意丢弃了，注释里挂了"Phase 5 处理"的 TODO 至今未做。

**建议优化**（P1，简单）：
```ts
const setSelectedTab = useDataStore((s) => s.setSelectedTab);

const handleAuxItemPress = useCallback((type: AuxiliaryItemType) => {
  setSelectedTab(type);  // 切换 dataStore 的 tab
  navigation.navigate('DataTab');
}, [navigation, setSelectedTab]);
```

注意 `AuxiliaryItemType` (`water | sleep | exercise | bowel`) 与 `DataTabType` (`weight | measurement | sleep | exercise | water | bowel`) 的子集关系，可以直接复用类型。

---

## 4. AI 输入框：发送即全屏跳转，缺少"渐进展开"

**现象**：用户在底部 GlobalAIInputBar 发一条消息，立即跳转到 `AIDialog` 全屏页。期望是：
- 第一条消息后，输入栏上方"浮起"一个聊天窗口（带高度上限）；
- 超过上限或用户主动点"展开"才进全屏。

**代码位置**：
- `src/features/ai/components/GlobalAIInputBar.tsx:18-31`：
  ```ts
  const handleSend = (text) => {
    navigation.navigate('AIDialog', { initialMessage: text });  // 直接跳全屏
  };
  ```
- `src/features/ai/screens/AIDialogScreen.tsx`：当前 P17 全屏页

**产品/UI 文档参考**：`docs/prd/v1/ui-design/14-ai-dialog-and-overlays.md`（如果有"浮层"设计稿，对照实现）

**改造范围（P1，工作量较大）**：
- 新增组件 `<AIChatOverlay>`（挂在 GlobalAIInputBar 上方）
- 状态机：`collapsed`（仅输入栏） → `floating`（消息浮层，最大高度 50% 屏高） → `fullscreen`（导航到 AIDialog）
- 触发条件：
  - collapsed → floating：发送第一条消息
  - floating → fullscreen：消息条数 > 阈值（如 6 条）OR 浮层内容高度超过最大值 OR 用户点"展开"按钮
- 浮层 UI：复用 `<ChatMessageList>`，外层加最大高度约束 + "展开/折叠"按钮
- AIDialog 全屏页保留作为 floating 升级目标 + 历史会话入口

---

## 5. AI 解析饮食后的"修改"应回到原卡片，不是聊天里弹按钮

**现象**：当前 AI 解析"我今天吃了 X"后，在聊天里给用户一组 actions（确认 / 修改食物）。用户点"修改食物"会触发某种操作，但产品 UI 文档要求：**修改要直接跳到首页/饮食页对应的餐次卡片去编辑，不是在聊天里改**。

**代码位置**：
- `src/features/ai/services/aiService.ts:mapCardActions`：
  ```ts
  // 当前：把后端 cards.actions 映射成聊天里的 ActionButton
  action.kind === 'confirm_create_diet_record' ? 'confirm' : 'navigate'
  ```
- `src/features/ai/hooks/useAIChat.ts:handleAction`（具体处理 action 点击）
- 后端返回 `cards: [{ type: 'diet_parse', actions: [{ kind: 'confirm_create_diet_record' }, { kind: 'edit_diet_items' }] }]`

**改造方案**（P1）：

**核心思路：AI 解析结果同时写入饮食模块 pending 状态，两个入口都能看到、都能操作。**

1. **AI 解析成功后**（收到 `diet_parse` 卡片）：
   - 聊天里正常渲染卡片 + 确认/修改按钮（现有逻辑保留）
   - **同时**把解析结果写入 `dietStore` 的 pending 队列（新增 `pendingRecords: Map<mealType, ParsedFoods>`）
   - 首页/饮食页的对应餐次卡片自动变为 `status: 'pending'`（从 store 读取）

2. **用户在 AI 全屏对话里操作**：
   - 点"确认保存" → 调 upsert → 清除 pending → 两边同步更新为 recorded
   - 点"修改食物" → 跳转 DietEdit（prefillFoods）→ 保存后清除 pending

3. **用户没确认就返回首页**：
   - 首页/饮食页看到对应餐次卡片是 pending 状态（黄色边框 + 确认/修改/取消按钮）
   - 用户可以在这里直接确认/修改/取消
   - 操作后 pending 清除，AI 对话里的卡片状态也同步更新（通过 store 订阅）

4. **取消**：
   - 任一入口点"取消" → 清除 pending → 两边恢复为 empty/recorded

**状态同步机制**：
- `dietStore.pendingRecords`（Zustand）作为 single source of truth
- 首页 MealCard 组件：优先读 `pendingRecords[mealType]`，有则显示 pending 态
- AI 对话 diet_parse 卡片：读同一个 store，确认/取消后更新
- `invalidateQueries(['diet', date])` + `invalidateQueries(['home'])` 保证 UI 刷新

**需要新增/修改的文件**：
- `src/features/diet/store/dietStore.ts`：新增 `pendingRecords` 字段和操作方法
- `src/features/ai/hooks/useAIChat.ts:handleAction`：确认时调 upsert + 清 pending
- `src/features/diet/components/MealCardList.tsx`：读 pending store 渲染 pending 态
- `src/app/navigation/types.ts`：DietEdit 加 `prefillFoods` 参数
- `src/features/diet/screens/DietEditScreen.tsx`：支持从 prefillFoods 初始化

**需要核对的点**：
- DietEdit 页面是否支持"接受外部 foods 作为初始值"？目前是用 `recordId` 参数从已有记录加载。需要扩展 `MainStackParamList.DietEdit` 加一个 `prefillFoods` 参数。

---

## 6. AI 洞察卡片 → 数据分析页是 mock

**现象**：首页"AI 洞察"卡片点击跳转 `Analysis` 页，但页面里的图表和总结都是 mock 数据。

**代码位置**：
- `src/features/data/services/dataService.ts:getAnalysisData`：
  ```ts
  async getAnalysisData(range) {
    // V1: 分析页数据依赖多个模块（饮食/身体/计划/建议），Phase 8/9 完成前保持 mock。
    // TODO(Phase 8/9): 改为前端组合调用 /diet/weekly-summary + /body/trends + /plans + /suggestions
    await new Promise((r) => setTimeout(r, 300));
    return { ...analysisDataMock, timeRange: range };
  }
  ```

**改造方案**（P0，现在 Phase 8/9 都已完成，**可以做了**）：
前端组合调用：
- 热量/营养趋势：`GET /diet/weekly-summary?start_date=...`
- 体重变化：`GET /body/trends?type=weight&period=30d`
- 计划达成：`GET /plans/{active_id}/progress`（先用 `GET /plans?status=active` 拿 id）
- AI 洞察：`GET /suggestions/insights`

后端字段映射：
```ts
async getAnalysisData(range) {
  const [diet, weight, plans, insights] = await Promise.all([
    apiClient.get('/diet/weekly-summary?start_date=...'),
    apiClient.get(`/body/trends?type=weight&period=${range}`),
    apiClient.get('/plans?status=active&page_size=1'),
    apiClient.get('/suggestions/insights'),
  ]);
  // 组装为 AnalysisData
  return {
    timeRange: range,
    calorieTrend: diet.daily_breakdowns.map(...),
    nutritionDistribution: { carbs, protein, fat },
    weightTrend: weight.data_points.map(...),
    planCompletion: plans.data[0]?.progress ?? null,
    insights: insights.insights,
  };
}
```

需要先看一下 `AnalysisData` 当前结构和后端返回结构差异多大。

---

## 优先级总览

| # | 问题 | 优先级 | 工作量 | 阻塞性 |
|---|---|---|---|---|
| 1 | 首页下拉刷新 | P2 | 中（需排查根因） | 低 |
| 2 | 记录保存延迟 | P1 | 小（onSuccess setQueryData） | 中 |
| 3 | 辅助卡片跳转不带 tab | P1 | **极小（5 行代码）** | 低 |
| 4 | AI 输入框渐进式展开 | P1 | **大（新增组件 + 状态机）** | 低（产品要求） |
| 5 | AI 修改饮食回到原卡片 | P1 | 中（DietEdit 加 prefill 参数） | 中（产品要求） |
| 6 | 数据分析页 mock → 真实 | P0 | 中（前端组合 4 个 API） | 高（影响首页洞察体验） |

**建议处理顺序**：6 → 3 → 2 → 5 → 4 → 1

- 先做 #6（影响首页可见效果，且后端已就绪）
- 再做 #3（5 行代码搞定）
- 再做 #2（提升整体感知速度）
- #5 涉及产品交互调整，需要再次对照设计稿
- #4 是较大改造，可以放到一个独立 sprint
- #1 偶发问题，等其他做完再排查

---

## 后续跟踪

每修复一项请在 commit message 里引用本文档：
```
fix(ui): improve home pull-to-refresh — closes optimization #1
```



还有这些饮水、睡眠、运动、排便等卡片，我在详情页保存了最新消息，都没有同步到首页，首页需要刷新才能看到更新后的数据。感觉是保存后没有正确更新缓存导致的，麻烦帮看一下，谢谢！


ai对话，我说喝水两瓶后端传给前端最终的card数据:
{"card":{"type":"body_parse","payload":{"record_type":"water","operation":"append","confidence":1.0,"water_amount":1000,"sleep_bed_time":null,"sleep_wake_time":null,"sleep_quality":null,"exercise_type":null,"exercise_duration":null,"bowel_time":null,"bowel_status":null,"suggested_date":"2026-06-03"},"actions":[{"kind":"confirm_create_body_record","label":"确认保存"},{"kind":"cancel_body_record","label":"取消"}]}}
前端展示的卡片里全是字段名的东西：body_parserecord_typeoperation
√已确认water
append
confidencewater_amountsleep_bed_timesleep_wake_time
1
1000
null
null
sleep_qualityexercise_typeexercise_durationbowel_time
null
null
null
null
bowel_status
null
suggested_date2026-06-03
这不对，没有具体看到用户喝了多少水，看看后端传给前端的字段是不是有问题，或者前端解析展示的时候出了问题？点击保存后，对话如下：
[card_action]
confirm_create_body_record
暂不支持的操作：
confirm_create_body_record
睡眠、运动、排便模块都同理



饮食页面最上面的日期选择组件，点击后会弹出日期选择框，选择一个日期后，页面会刷新并展示该日期的饮食记录。但是现在的ui做法是没有日期组件的，而是左右有一个箭头，点击箭头会切换日期并刷新数据。感觉用户不太好发现这个功能，建议改成日期组件的形式。


首页没有维度记录的卡片，请你思考，按现在市面的产品，是否需要在首页增加一个维度记录的入口卡片？如果需要，应该放在什么位置，点击后应该跳转到哪里？如果不需要，请说明理由。


需要改造程Checkpointer（Postgres 版）（没有 checkpointer 就没法暂停/恢复）。核心是 interrupt()


https://github.com/datawhalechina/easy-langent/blob/main/docs/guide/chapter8.md