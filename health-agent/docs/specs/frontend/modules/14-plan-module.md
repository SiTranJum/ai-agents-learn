# 计划模块前端实现规格

## 1. 模块职责

计划列表展示、计划详情查看、对话式创建计划、计划修改和终止。

## 2. 对应 UI 设计文稿

- `health-agent/docs/prd/v1/ui-design/08-plan-list-page.md`
- `health-agent/docs/prd/v1/ui-design/09-plan-detail-page.md`
- `health-agent/docs/prd/v1/ui-design/10-plan-create-chat-page.md`

## 3. 页面列表

- P06 PlanListScreen — 计划列表页
- P07 PlanDetailScreen — 计划详情页
- P08 PlanCreateChatScreen — 计划创建对话页

## 4. 页面详细规格

### P06 PlanListScreen

- **页面职责**：展示用户创建的所有健康计划，快速了解每个计划的进度和状态
- **对应 UI 文稿**：`08-plan-list-page.md`
- **页面结构**：
  - 顶部标题区："我的计划" + "+ 新建"胶囊按钮
  - 计划卡片列表（可滚动）
    - 每张卡片：计划名称 + 进度条 + 日期范围 + 状态标签
  - 空态：空白日历插画 + "还没有健康计划哦" + "创建我的第一个计划"按钮
  - AI 输入框（常驻）
  - 底部 Tab 导航
- **页面状态**：
  - 空态（无计划）
  - 有计划态（按状态排序：进行中 → 已暂停 → 已完成）
- **数据字段**：
```typescript
interface PlanListItem {
  id: string;
  name: string;
  type: 'lose_weight' | 'nutrition' | 'habit';
  status: 'active' | 'paused' | 'completed' | 'terminated';
  progress: number; // 0-100
  startDate: string;
  endDate: string;
}
```
- **跳转关系**：
  - 点击计划卡片 → PlanDetail { planId }
  - 点击"+ 新建" → PlanCreateChat

### P07 PlanDetailScreen

- **页面职责**：展示单个计划的详细信息和执行进度
- **对应 UI 文稿**：`09-plan-detail-page.md`
- **页面结构**：
  - 顶部导航栏（返回 + 计划名称 + 状态标签）
  - 目标信息卡片（目标体重、时间周期、当前阶段）
  - 今日任务（勾选任务列表，4 个任务示例）
  - 执行进度（折线趋势图 + 时间范围切换）
  - AI 建议卡片（建议内容 + "查看详情"按钮）
  - 底部操作栏（"修改计划" + "终止计划"按钮）
  - AI 输入框（常驻）
  - 底部 Tab 导航
- **页面状态**：
  - 正常执行中（绿色"进行中"标签）
  - 已暂停（黄色"已暂停"标签，按钮变为"恢复计划"）
  - 已完成（蓝色"已完成"标签，显示完成时间和达成结果）
  - 连续未达标（顶部黄色警告卡片）
- **数据字段**：
```typescript
interface PlanDetail {
  id: string;
  name: string;
  type: 'lose_weight' | 'nutrition' | 'habit';
  status: 'active' | 'paused' | 'completed' | 'terminated';
  targetWeight?: number;
  dailyCalorieTarget?: number;
  startDate: string;
  endDate: string;
  progress: number;
  tasks: PlanTask[];
  trendData: { date: string; value: number }[];
  aiSuggestion: string;
}
```
- **关键交互**：
  - 勾选/取消勾选任务 → 更新任务状态
  - 切换趋势时间范围 → 更新折线图
  - 点击"修改计划" → 进入编辑流程
  - 点击"终止计划" → 弹出确认对话框

### P08 PlanCreateChatScreen

- **页面职责**：通过多轮 AI 对话引导用户明确健康目标、时间周期和执行方式，最终由 AI 生成个性化健康计划
- **对应 UI 文稿**：`10-plan-create-chat-page.md`
- **页面结构**：
  - 顶部导航栏（返回 + "创建计划"）
  - 中间全屏对话流（可滚动）
    - AI 消息气泡（左对齐，#F2F3F5 背景）
    - 用户消息气泡（右对齐，#FFE7E1 背景）
    - 快捷选项按钮（AI 提问后出现）
    - 计划摘要卡片（嵌入 AI 最后一条消息）
  - 底部 AI 输入框（56px 高）
- **对话流程（4 步）**：
  - Step 1：目标确认（"你想制定什么类型的计划？"）
  - Step 2：现状分析（AI 分析用户近期数据）
  - Step 3：方案制定（AI 提出具体方案）
  - Step 4：确认与启动（展示计划摘要 + 操作按钮）
- **页面状态**：
  - 对话进行中（消息流增长，新消息自动滚动到底部）
  - AI 思考中（三个点跳动动画）
  - 对话完成（显示计划摘要卡片 + 操作按钮）
  - 用户确认创建（按钮变为加载状态，成功后显示确认消息）
- **数据字段**：
```typescript
interface ChatMessage {
  id: string;
  role: 'ai' | 'user';
  content: string;
  timestamp: string;
  quickOptions?: string[]; // AI 消息可能带快捷选项
}

interface PlanSummary {
  name: string;
  type: string;
  targetWeight?: number;
  dailyCalorieTarget?: number;
  duration: string;
  keyRules: string[];
}
```
- **关键交互**：
  - 点击返回按钮 → 弹出确认弹窗："退出将丢失当前对话，确定退出？"
  - 点击快捷选项 → 选项文字作为用户消息发送，按钮组消失
  - 输入文字并发送 → 用户消息气泡出现，触发 AI 回复
  - AI 思考中 → 三个点跳动动画（每点 300ms）
  - 点击"确认创建" → 创建计划，显示成功消息
  - 点击"修改目标" → AI 追问需要修改哪部分
  - 点击"查看计划" → 跳转到新创建的计划详情页

## 5. 模块内组件

- **PlanCardList**：计划卡片列表
- **PlanProgressChart**：计划进度折线图
- **TaskList**：任务列表（可勾选）
- **ChatMessage**：对话消息气泡
- **PlanSummaryCard**：计划摘要卡片
- **QuickOptionButtons**：快捷选项按钮组

## 6. 模块内 Store

```typescript
interface PlanStore {
  chatMessages: ChatMessage[];
  isAIThinking: boolean;
  addMessage: (message: ChatMessage) => void;
  setAIThinking: (thinking: boolean) => void;
  clearChat: () => void;
}
```

## 7. 模块内 Services

```typescript
interface PlanService {
  getPlans(): Promise<PlanListItem[]>;
  getPlanDetail(planId: string): Promise<PlanDetail>;
  createPlan(data: PlanSummary): Promise<Plan>;
  updatePlan(planId: string, data: Partial<Plan>): Promise<Plan>;
  terminatePlan(planId: string): Promise<void>;
  toggleTask(planId: string, taskId: string): Promise<void>;
  sendChatMessage(message: string): Promise<ChatMessage>; // AI 回复
}
```

## 8. Mock 数据要求

- 计划列表 mock：3 个计划（1 个进行中、1 个已暂停、1 个已完成）
- 计划详情 mock：完整的计划信息 + 任务列表 + 趋势数据
- 对话 mock：模拟 AI 回复（4 步对话流程）
- 计划摘要 mock：生成的计划摘要

## 9. 模块依赖

- `@shared/ui/Card`
- `@shared/ui/PlanCard`
- `@shared/ui/ProgressBar`
- `@shared/ui/Button`
- `@shared/ui/Tag`
- `@shared/ui/AIInputBar`
- `@shared/charts/LineChart`
- `@shared/feedback/Toast`
- `@shared/feedback/ConfirmDialog`
- `@shared/feedback/EmptyState`

## 10. 实现约束

- 必须参考 `08-plan-list-page.md`、`09-plan-detail-page.md`、`10-plan-create-chat-page.md` 文稿实现
- 没有完整视觉稿，以文稿中的 ASCII 线框图、组件树、样式描述为准
- 对话气泡样式：AI 左对齐灰底、用户右对齐浅橙底
- 颜色、字体、间距遵循 `04-design-system-mapping.md`
- 插画使用 `assets/images/illustrations/empty-plan.png`
