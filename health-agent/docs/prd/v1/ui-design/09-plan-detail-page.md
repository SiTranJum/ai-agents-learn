# 计划详情页

> 展示单个健康计划的目标信息、执行进度、今日任务和 AI 建议。

---

## 1. 页面目标

展示单个计划的详细信息和执行进度，让用户清楚看到计划目标、当前阶段、每日任务和阶段性趋势，并在需要时修改或终止计划。

---

## 2. 页面入口

- 计划列表页点击某个计划卡片
- 首页 Dashboard 的计划进度卡片点击
- AI 建议中提到当前计划时跳转查看

---

## 3. 页面布局

```
┌─────────────────────────────────┐
│           状态栏 (系统)           │
├─────────────────────────────────┤
│  ←     减脂计划         进行中    │  返回按钮 + 标题 + 状态标签
│                                 │
├─────────────────────────────────┤
│  ┌───────────────────────────┐  │
│  │  目标体重      70kg        │  │
│  │  时间周期      3个月       │  │  目标信息卡片
│  │  当前阶段      第2阶段     │  │  白卡 + 12px 圆角
│  └───────────────────────────┘  │
│          ↕ 12px                  │
│  今日任务                        │  18px SemiBold
│  ┌───────────────────────────┐  │
│  │  ☑ 早餐控制在 450 kcal 内   │  │
│  │  ☑ 午后步行 30 分钟         │  │  勾选任务列表
│  │  ☐ 晚餐不喝含糖饮料         │  │
│  │  ☐ 22:30 前入睡            │  │
│  └───────────────────────────┘  │
│          ↕ 12px                  │
│  执行进度                        │
│  ┌───────────────────────────┐  │
│  │    ╭╮                       │  │
│  │  ╭─╯╰─╮    ╭─╮              │  │  折线趋势图
│  │ ╭╯    ╰╮ ╭─╯ ╰╮             │  │
│  │──────────────────────       │  │
│  │  7天  30天  90天            │  │  时间范围切换
│  └───────────────────────────┘  │
│          ↕ 12px                  │
│  AI 建议                         │
│  ┌───────────────────────────┐  │
│  │  你最近 3 天晚餐热量偏高，   │  │
│  │  建议把晚餐主食减少 1/4，    │  │  建议卡片
│  │  并增加蔬菜比例。            │  │
│  │               [查看详情]     │  │
│  └───────────────────────────┘  │
│          ↕ 12px                  │
│  [ 修改计划 ]   [ 终止计划 ]      │  底部操作按钮双列
│                                 │
│         ↕ 32px 底部留白          │
├─────────────────────────────────┤
│  [📷] [🎤] 说点什么...   [发送]  │  AI 输入框 56px
├─────────────────────────────────┤
│  🏠首页  🍽️饮食  📊数据  👤我的  │  底部 Tab 导航 60px
└─────────────────────────────────┘
```

### 连续未达标状态布局重点

```
┌─────────────────────────────────┐
│  ←     减脂计划         进行中    │
├─────────────────────────────────┤
│  ┌───────────────────────────┐  │
│  │  连续 5 天未达标            │  │  警告提示卡片
│  │  最近晚餐和加餐热量偏高，    │  │  浅黄色背景 #FFF7E0
│  │  AI 建议调整当前计划强度。   │  │
│  │          [查看调整建议]      │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

---

## 4. 组件树

```
PlanDetailPage
├── StatusBar（系统状态栏）
├── TopNav
│   ├── BackButton
│   ├── PlanTitle（计划名称）
│   └── StatusTag（进行中 / 已暂停 / 已完成）
├── ScrollableContent
│   ├── GoalInfoCard
│   │   ├── GoalWeightRow（目标体重）
│   │   ├── DurationRow（时间周期）
│   │   └── CurrentPhaseRow（当前阶段）
│   ├── TaskSection
│   │   ├── SectionTitle（"今日任务"）
│   │   └── TaskList
│   │       └── TaskItem（复选框 + 文案，N 个）
│   ├── TrendSection
│   │   ├── SectionTitle（"执行进度"）
│   │   └── TrendChartCard
│   │       ├── LineChart
│   │       └── RangeSwitcher（7天 / 30天 / 90天）
│   ├── AIAdviceSection
│   │   ├── SectionTitle（"AI 建议"）
│   │   └── AdviceCard
│   │       ├── AdviceText
│   │       └── ViewDetailButton
│   ├── WarningCard（连续未达标时条件渲染）
│   └── ActionButtons
│       ├── EditPlanButton（"修改计划"）
│       └── TerminatePlanButton（"终止计划"）
├── AIInputBar（全局 AI 输入框）
└── BottomTabNav（底部 Tab 导航）
```

---

## 5. 页面状态

### 5.1 正常执行中

- 顶部状态标签为"进行中"，绿色标签 `#4CD964`
- 今日任务可勾选完成
- 趋势图显示最近执行进度
- AI 建议区域展示常规优化建议

### 5.2 已暂停

- 顶部状态标签为"已暂停"，黄色标签 `#FFC94D`
- 今日任务区域变为只读，不可勾选
- AI 建议区域提示："计划已暂停，恢复后将继续追踪进度"
- 操作按钮变为："恢复计划"、"终止计划"

### 5.3 已完成

- 顶部状态标签为"已完成"，蓝色标签 `#5AC8FA`
- 目标信息卡片增加完成时间和达成结果
- 今日任务区域替换为"计划总结"
- 操作按钮变为单按钮："创建新计划"

### 5.4 连续未达标

- 页面顶部或 AI 建议区域上方显示警告提示卡片
- 卡片背景使用浅黄色 `#FFF7E0`
- 文案提示用户最近执行偏差较大，建议调整计划
- CTA："查看调整建议" 或 "修改计划"

---

## 6. 关键交互

| 交互 | 行为 | 动效 |
|------|------|------|
| 点击返回按钮 | 返回计划列表页 | 页面左滑返回 300ms |
| 勾选今日任务 | 标记任务完成，更新任务状态 | 复选框勾选动画 200ms，文字变灰 |
| 取消勾选任务 | 恢复未完成状态 | 复选框过渡动画 200ms |
| 切换趋势时间范围 | 更新折线图数据 | 图表数据渐变更新 300ms |
| 点击"查看详情" | 跳转 AI 建议详情页或展开全文 | 卡片展开 250ms |
| 点击"修改计划" | 进入计划编辑流程或对话页 | 页面切换 300ms |
| 点击"终止计划" | 弹出确认对话框 | 弹窗底部滑入 250ms |
| 点击"恢复计划" | 将暂停计划恢复为进行中 | 状态标签颜色过渡 200ms |
| 连续未达标点击"查看调整建议" | 打开 AI 调整建议 | 页面切换或卡片展开 |

---

## 7. 页面文案

| 位置 | 文案 | 字体 |
|------|------|------|
| 顶部标题示例 | 减脂计划 | font-card-title 18px SemiBold #222222 |
| 状态标签-进行中 | 进行中 | font-tag 12px Medium #4CD964 |
| 状态标签-已暂停 | 已暂停 | font-tag 12px Medium #FFC94D |
| 状态标签-已完成 | 已完成 | font-tag 12px Medium #5AC8FA |
| 目标信息标题 | 目标体重 | font-body-sm 14px #666666 |
| 目标值示例 | 70kg | font-body 16px SemiBold #222222 |
| 时间周期标题 | 时间周期 | font-body-sm 14px #666666 |
| 时间周期值 | 3个月 | font-body 16px SemiBold #222222 |
| 当前阶段标题 | 当前阶段 | font-body-sm 14px #666666 |
| 当前阶段值 | 第2阶段 | font-body 16px SemiBold #222222 |
| 任务区域标题 | 今日任务 | font-card-title 18px SemiBold #222222 |
| 趋势图标题 | 执行进度 | font-card-title 18px SemiBold #222222 |
| AI 建议标题 | AI 建议 | font-card-title 18px SemiBold #222222 |
| AI 建议示例 | 你最近 3 天晚餐热量偏高，建议把晚餐主食减少 1/4，并增加蔬菜比例。 | font-body 16px #666666 |
| 建议按钮 | 查看详情 | font-body-sm 14px Medium #FF7A5C |
| 修改按钮 | 修改计划 | font-body 16px Medium #FFFFFF，背景 #FF7A5C |
| 终止按钮 | 终止计划 | font-body 16px Medium #FF5A5F，白底描边 |
| 警告提示标题 | 连续 5 天未达标 | font-body 16px SemiBold #222222 |
| 警告提示正文 | 最近晚餐和加餐热量偏高，AI 建议调整当前计划强度。 | font-body-sm 14px #666666 |
| 警告按钮 | 查看调整建议 | font-body-sm 14px Medium #FF7A5C |

---

## 8. Figma AI 生成描述

Design a mobile app screen for a health plan detail page. The screen uses a light warm style with coral orange (#FF7A5C) as the brand color and #F7F8FA as the page background.

**Layout from top to bottom:**
1. A top navigation bar with a back arrow button on the left, plan title "减脂计划" in the center (18px semibold, #222222), and a status tag on the right: "进行中" with green (#4CD964) background at 10% opacity and green text, 12px medium font, 8px border-radius.
2. A white card with 12px border-radius showing goal information in a 2-column layout:
   - Left labels in 14px #666666: "目标体重", "时间周期", "当前阶段"
   - Right values in 16px semibold #222222: "70kg", "3个月", "第2阶段"
3. A section title "今日任务" in 18px semibold, followed by a white card containing a checklist:
   - Each task has a checkbox (checked items show coral orange checkmark, unchecked show gray outline) and task text in 16px #222222
   - Task items: "早餐控制在 450 kcal 内", "午后步行 30 分钟", "晚餐不喝含糖饮料", "22:30 前入睡"
4. A section title "执行进度" in 18px semibold, followed by a white card with:
   - A line chart showing trend data with coral orange line
   - Below the chart: time range toggle buttons [7天] [30天] [90天], selected button has coral orange background
5. A section title "AI 建议" in 18px semibold, followed by a white card with:
   - Advice text in 16px #666666: "你最近 3 天晚餐热量偏高，建议把晚餐主食减少 1/4，并增加蔬菜比例。"
   - A "查看详情" link button in 14px coral orange on the right
6. Two action buttons at the bottom: "修改计划" (coral orange filled button) and "终止计划" (red #FF5A5F outlined button), side by side with equal width.
7. A fixed bottom area with an AI input bar (56px height) and a 4-tab bottom navigation (60px height).

**Warning state variant:** When the user has consecutive unmet goals, add a warning card at the top with light yellow background (#FFF7E0), 12px border-radius, containing warning text "连续 5 天未达标" in 16px semibold, description text in 14px #666666, and a "查看调整建议" button in coral orange.

**Style:** Light, warm, health-oriented. Card spacing is 12px. All cards have subtle shadow (0 2px 8px rgba(0,0,0,0.06)). Chinese text. iPhone 14/15 dimensions. Phosphor Icons Light style for all icons.

---

## 9. 相关素材

| 素材 | 用途 | 尺寸 | 说明 |
|------|------|------|------|
| 折线趋势图组件 | 执行进度展示 | 卡片宽度×180px | 珊瑚橙折线，浅灰网格背景 |
| 复选框图标-已勾选 | 任务列表 | 20×20px | 珊瑚橙填充 + 白色勾 |
| 复选框图标-未勾选 | 任务列表 | 20×20px | 灰色描边圆角方框 |
