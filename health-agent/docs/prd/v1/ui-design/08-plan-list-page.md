# 计划列表页

> 展示用户所有健康计划，支持新建计划入口。

---

## 1. 页面目标

展示用户创建的所有健康计划，让用户快速了解每个计划的进度和状态，并提供新建计划的入口。

---

## 2. 页面入口

- 数据页内的"计划"入口（Tab 或卡片）
- 首页 Dashboard 计划进度卡片点击
- AI 对话中提到计划相关内容后跳转

---

## 3. 页面布局

```
┌─────────────────────────────────┐
│           状态栏 (系统)           │
├─────────────────────────────────┤
│                                 │
│  我的计划              [+ 新建]  │  页面标题 24px Bold + 胶囊按钮
│                                 │
├─────────────────────────────────┤
│                                 │
│  ┌───────────────────────────┐  │
│  │  🏃 减脂计划               │  │  计划名称 18px SemiBold
│  │                           │  │
│  │  ████████████░░░░  72%    │  │  进度条 brand-primary + 百分比
│  │                           │  │
│  │  03/01 → 06/01            │  │  日期范围 13px #999999
│  │                    进行中  │  │  状态标签 12px #4CD964 背景
│  └───────────────────────────┘  │
│          ↕ 12px                  │
│  ┌───────────────────────────┐  │
│  │  🥗 营养调整计划            │  │
│  │                           │  │
│  │  ████████░░░░░░░░  45%    │  │
│  │                           │  │
│  │  04/01 → 07/01            │  │
│  │                    已暂停  │  │  状态标签 12px #FFC94D 背景
│  └───────────────────────────┘  │
│          ↕ 12px                  │
│  ┌───────────────────────────┐  │
│  │  💪 增肌计划               │  │
│  │                           │  │
│  │  ████████████████  100%   │  │
│  │                           │  │
│  │  01/01 → 03/31            │  │
│  │                    已完成  │  │  状态标签 12px #5AC8FA 背景
│  └───────────────────────────┘  │
│                                 │
│         ↕ 32px 底部留白          │
├─────────────────────────────────┤
│  [📷] [🎤] 说点什么...   [发送]  │  AI 输入框 56px
├─────────────────────────────────┤
│  🏠首页  🍽️饮食  📊数据  👤我的  │  底部 Tab 导航 60px
└─────────────────────────────────┘
```

### 空态布局

```
┌─────────────────────────────────┐
│           状态栏 (系统)           │
├─────────────────────────────────┤
│                                 │
│  我的计划              [+ 新建]  │
│                                 │
├─────────────────────────────────┤
│                                 │
│                                 │
│         ┌──────────┐            │
│         │  空白日历  │            │  空状态插画 200×200px
│         │  插画     │            │
│         └──────────┘            │
│                                 │
│      还没有健康计划哦             │  font-body 16px #666666
│    让 AI 帮你制定一个吧           │  font-body-sm 14px #999999
│                                 │
│       [ 创建我的第一个计划 ]      │  品牌色胶囊按钮
│                                 │
│                                 │
├─────────────────────────────────┤
│  [📷] [🎤] 说点什么...   [发送]  │
├─────────────────────────────────┤
│  🏠首页  🍽️饮食  📊数据  👤我的  │
└─────────────────────────────────┘
```

---

## 4. 组件树

```
PlanListPage
├── StatusBar（系统状态栏）
├── PageHeader
│   ├── PageTitle（"我的计划"）
│   └── CreateButton（"+ 新建"胶囊按钮）
├── ScrollableContent
│   ├── PlanCard（可复用，N 个）
│   │   ├── PlanIcon（计划类型图标）
│   │   ├── PlanName（计划名称）
│   │   ├── ProgressBar（进度条 + 百分比）
│   │   ├── DateRange（开始日期 → 目标日期）
│   │   └── StatusTag（进行中 / 已暂停 / 已完成）
│   └── EmptyState（空态组件，条件渲染）
│       ├── EmptyIllustration（空状态插画）
│       ├── EmptyTitle（提示文案）
│       └── CreateFirstButton（创建按钮）
├── AIInputBar（全局 AI 输入框）
└── BottomTabNav（底部 Tab 导航）
```

---

## 5. 页面状态

### 5.1 空态（无计划）

- 显示空状态插画（空白日历风格）
- 提示文案："还没有健康计划哦"
- 副文案："让 AI 帮你制定一个吧"
- 操作按钮："创建我的第一个计划"（品牌色胶囊按钮）
- "+"新建按钮仍然显示在顶部

### 5.2 有计划列表

- 计划卡片按状态排序：进行中 → 已暂停 → 已完成
- 每张卡片可点击进入计划详情页
- 卡片间距 12px

### 5.3 多个计划

- 列表可滚动
- 底部预留 116px 安全区（AI 输入框 56px + Tab 导航 60px）
- 无分页，全量加载（V1 计划数量有限）

---

## 6. 关键交互

| 交互 | 行为 | 动效 |
|------|------|------|
| 点击计划卡片 | 跳转到计划详情页（09-plan-detail-page） | 卡片按下背景变 #F5F5F5，100ms；页面右滑切换 300ms |
| 点击"+ 新建"按钮 | 跳转到计划创建对话页（10-plan-create-chat-page） | 按钮缩放 0.95，100ms；页面右滑切换 300ms |
| 点击空态"创建我的第一个计划" | 同上，跳转计划创建对话页 | 同上 |
| AI 输入框说"帮我制定计划" | 自动跳转到计划创建对话页 | 页面切换 300ms |
| 下拉刷新 | 刷新计划列表数据 | 旋转加载图标 |
| 计划完成 | 状态标签变为"已完成"蓝色，进度条满格 | 进度条填充动画 500ms |

---

## 7. 页面文案

| 位置 | 文案 | 字体 |
|------|------|------|
| 页面标题 | 我的计划 | font-page-title 24px Bold #222222 |
| 新建按钮 | + 新建计划 | font-body-sm 14px Medium #FFFFFF，背景 #FF7A5C |
| 进行中标签 | 进行中 | font-tag 12px Medium #4CD964 |
| 已暂停标签 | 已暂停 | font-tag 12px Medium #FFC94D |
| 已完成标签 | 已完成 | font-tag 12px Medium #5AC8FA |
| 日期格式 | MM/DD → MM/DD | font-caption 13px #999999 |
| 空态主文案 | 还没有健康计划哦 | font-body 16px #666666 |
| 空态副文案 | 让 AI 帮你制定一个吧 | font-body-sm 14px #999999 |
| 空态按钮 | 创建我的第一个计划 | font-body 16px Medium #FFFFFF，背景 #FF7A5C |

---

## 8. Figma AI 生成描述

Design a mobile app screen titled "我的计划" (My Plans) for a health management app. The screen uses a light warm style with coral orange (#FF7A5C) as the brand color and #F7F8FA as the page background.

**Layout from top to bottom:**
1. A page header with the title "我的计划" on the left (24px bold, #222222) and a small coral orange pill-shaped button "+ 新建计划" on the right.
2. A vertically scrollable list of plan cards, each card is white (#FFFFFF) with 12px border-radius and a subtle shadow (0 2px 8px rgba(0,0,0,0.06)). Card spacing is 12px. Each card contains:
   - A plan name in 18px semibold (e.g., "减脂计划")
   - A horizontal progress bar: filled portion in coral orange (#FF7A5C), unfilled in #F0F0F0, with a percentage label on the right
   - A date range in 13px gray (#999999), format "MM/DD → MM/DD"
   - A small status tag in the bottom-right corner: "进行中" with green (#4CD964) background at 10% opacity and green text, "已暂停" with yellow (#FFC94D) background, or "已完成" with blue (#5AC8FA) background. Tag uses 12px medium font with 8px border-radius.
3. A fixed bottom area with an AI input bar (56px height, white background, pill-shaped input field with camera and microphone icons on the left, send button on the right) and a 4-tab bottom navigation (首页/饮食/数据/我的) with line-style icons, 60px height.

**Empty state variant:** When no plans exist, show a 200x200px illustration of an empty calendar in warm coral tones, centered. Below it: "还没有健康计划哦" in 16px #666666, then "让 AI 帮你制定一个吧" in 14px #999999, then a coral orange pill button "创建我的第一个计划".

**Style:** Light, warm, health-oriented. No heavy shadows. Chinese text. iPhone 14/15 dimensions. Phosphor Icons Light style for all icons.

---

## 9. 相关素材

| 素材 | 用途 | 尺寸 | 说明 |
|------|------|------|------|
| 空状态插画-无计划 | 空态页面展示 | 200×200px | 空白日历风格，暖色调，扁平插画 |
| 计划类型图标-减重 | 计划卡片装饰 | 24×24px | 线性图标，体重秤或跑步人物 |
| 计划类型图标-营养 | 计划卡片装饰 | 24×24px | 线性图标，蔬菜或餐盘 |
| 计划类型图标-习惯 | 计划卡片装饰 | 24×24px | 线性图标，打勾日历或闹钟 |
