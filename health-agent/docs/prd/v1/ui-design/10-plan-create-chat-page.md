# 计划创建对话页

> 通过多轮 AI 对话引导用户创建个性化健康计划，全屏对话体验。

---

## 1. 页面目标

通过多轮对话引导用户明确健康目标、时间周期和执行方式，最终由 AI 生成个性化健康计划。全屏对话页，沉浸式体验。

---

## 2. 页面入口

- 计划列表页点击"+ 新建计划"按钮
- AI 输入框中说"帮我制定计划"后自动跳转
- 首页计划卡片空态点击"创建我的第一个计划"

---

## 3. 页面布局

```
┌─────────────────────────────────┐
│           状态栏 (系统)           │
├─────────────────────────────────┤
│  ←       创建计划                │  返回按钮 + 标题
├─────────────────────────────────┤
│                                 │
│  ┌─────────────────────────┐    │
│  │ 你好！我来帮你制定健康    │    │  AI 消息气泡
│  │ 计划。你想制定什么类型    │    │  左对齐，#F2F3F5 背景
│  │ 的计划？                 │    │  12px 圆角
│  └─────────────────────────┘    │
│                                 │
│  [减重计划] [营养调整] [习惯养成] │  快捷选项按钮组
│                                 │
│    ┌─────────────────────────┐  │
│    │          减重计划         │  │  用户消息气泡
│    └─────────────────────────┘  │  右对齐，#FFE7E1 背景
│                                 │  12px 圆角
│  ┌─────────────────────────┐    │
│  │ 好的！你的目标体重是      │    │  AI 消息气泡
│  │ 多少？                   │    │
│  └─────────────────────────┘    │
│                                 │
│    ┌─────────────────────────┐  │
│    │          70kg            │  │  用户消息气泡
│    └─────────────────────────┘  │
│                                 │
│  ┌─────────────────────────┐    │
│  │ 你希望多久达成这个目标？  │    │  AI 消息气泡
│  └─────────────────────────┘    │
│                                 │
│  [1个月] [3个月] [6个月]         │  快捷选项按钮组
│                                 │
│    ┌─────────────────────────┐  │
│    │          3个月           │  │  用户消息气泡
│    └─────────────────────────┘  │
│                                 │
│  ┌─────────────────────────┐    │
│  │ 明白了，我为你制定了以下  │    │  AI 消息气泡
│  │ 计划：                   │    │
│  │ ┌─────────────────────┐ │    │
│  │ │ 📋 减重计划           │ │    │  计划摘要卡片（嵌套）
│  │ │ 目标：70kg           │ │    │  白底 12px 圆角
│  │ │ 周期：3个月          │ │    │  品牌色左边框
│  │ │ 阶段：3个阶段        │ │    │
│  │ │ 每日热量：1600 kcal  │ │    │
│  │ └─────────────────────┘ │    │
│  └─────────────────────────┘    │
│                                 │
│  [确认创建]       [修改目标]      │  操作按钮组
│                                 │
├─────────────────────────────────┤
│  [📷] [🎤] 输入你的想法... [发送] │  底部输入框 56px
└─────────────────────────────────┘
```

### 消息气泡设计细节

```
AI 消息气泡：
┌──────────────────────────────┐
│  ← 12px 内边距               │
│                              │  背景色：#F2F3F5
│  消息文字内容                 │  圆角：12px
│                              │  最大宽度：屏幕宽度 75%
│               12px 内边距 →  │  左对齐，左侧距屏幕 16px
└──────────────────────────────┘

用户消息气泡：
┌──────────────────────────────┐
│  ← 12px 内边距               │
│                              │  背景色：#FFE7E1
│  消息文字内容                 │  圆角：12px
│                              │  最大宽度：屏幕宽度 75%
│               12px 内边距 →  │  右对齐，右侧距屏幕 16px
└──────────────────────────────┘

消息间距：12px
```

---

## 4. 组件树

```
PlanCreateChatPage
├── StatusBar（系统状态栏）
├── TopNav
│   ├── BackButton
│   └── PageTitle（"创建计划"）
├── ChatMessageFlow（可滚动区域）
│   ├── AIMessage（AI 消息气泡，N 个）
│   │   ├── AvatarIcon（AI 头像，可选）
│   │   └── BubbleContent
│   │       ├── MessageText
│   │       └── PlanSummaryCard（条件渲染，对话末尾）
│   │           ├── PlanName
│   │           ├── GoalWeight
│   │           ├── Duration
│   │           ├── Phases
│   │           └── DailyCalorie
│   ├── UserMessage（用户消息气泡，N 个）
│   │   └── BubbleContent
│   │       └── MessageText
│   ├── QuickOptionGroup（快捷选项按钮组，条件渲染）
│   │   └── OptionButton（N 个）
│   ├── ActionButtonGroup（确认/修改按钮组，条件渲染）
│   │   ├── ConfirmButton（"确认创建"）
│   │   └── ModifyButton（"修改目标"）
│   └── TypingIndicator（AI 思考中动画，条件渲染）
└── ChatInputBar（底部输入框）
    ├── CameraButton
    ├── VoiceButton
    ├── TextInput
    └── SendButton
```

---

## 5. 页面状态

### 5.1 对话进行中

- 消息流持续增长，新消息自动滚动到底部
- AI 回复前显示"思考中"动画（三个点依次跳动）
- 快捷选项按钮在 AI 提问后出现，用户选择后消失
- 输入框可用，用户可自由输入或选择快捷选项

### 5.2 对话完成（展示计划摘要）

- AI 最后一条消息中嵌入计划摘要卡片
- 摘要卡片白底，品牌色左边框 3px，12px 圆角
- 卡片下方显示操作按钮组："确认创建"、"修改目标"
- 输入框仍可用，用户可继续追问或调整

### 5.3 用户确认创建

- 用户点击"确认创建"后：
  - 按钮变为加载状态
  - 创建成功后 AI 发送确认消息："计划已创建！你可以在计划详情页查看。"
  - 消息下方显示"查看计划"按钮
  - 点击后跳转到计划详情页

---

## 6. 关键交互

| 交互 | 行为 | 动效 |
|------|------|------|
| 点击返回按钮 | 弹出确认弹窗"退出将丢失当前对话，确定退出？" | 弹窗底部滑入 250ms |
| 点击快捷选项按钮 | 将选项文字作为用户消息发送，按钮组消失 | 按钮缩放 0.95 100ms，消息气泡渐入 200ms |
| 输入文字并发送 | 用户消息气泡出现，触发 AI 回复 | 消息气泡渐入 200ms |
| AI 思考中 | 显示三个点跳动动画 | 每点 300ms 循环跳动 |
| AI 回复到达 | 思考动画消失，AI 消息气泡出现 | 气泡渐入 200ms，自动滚动到底部 |
| 点击"确认创建" | 创建计划，显示成功消息 | 按钮加载态 → 成功消息渐入 |
| 点击"修改目标" | AI 追问需要修改哪部分 | 新消息气泡渐入 200ms |
| 点击"查看计划" | 跳转到新创建的计划详情页 | 页面右滑切换 300ms |
| 新消息到达 | 消息流自动滚动到底部 | 平滑滚动 200ms |

---

## 7. 页面文案

### 7.1 固定文案

| 位置 | 文案 | 字体 |
|------|------|------|
| 页面标题 | 创建计划 | font-card-title 18px SemiBold #222222 |
| 输入框 placeholder | 输入你的想法... | font-body 16px #999999 |
| 确认按钮 | 确认创建 | font-body 16px Medium #FFFFFF，背景 #FF7A5C |
| 修改按钮 | 修改目标 | font-body 16px Medium #FF7A5C，白底描边 |
| 退出弹窗标题 | 退出创建 | font-card-title 18px SemiBold #222222 |
| 退出弹窗文案 | 退出将丢失当前对话，确定退出？ | font-body 16px #666666 |
| 退出弹窗确认 | 确定退出 | font-body 16px Medium #FF5A5F |
| 退出弹窗取消 | 继续创建 | font-body 16px Medium #FF7A5C |

### 7.2 对话流程文案

| 步骤 | 角色 | 文案 |
|------|------|------|
| 1 | AI | 你好！我来帮你制定健康计划。你想制定什么类型的计划？ |
| 1 | 快捷选项 | [减重计划] [营养调整] [习惯养成] |
| 2 | 用户 | 减重计划 |
| 3 | AI | 好的！你的目标体重是多少？ |
| 4 | 用户 | 70kg |
| 5 | AI | 你希望多久达成这个目标？ |
| 5 | 快捷选项 | [1个月] [3个月] [6个月] |
| 6 | 用户 | 3个月 |
| 7 | AI | 明白了，我为你制定了以下计划：（展示计划摘要卡片） |
| 7 | 操作按钮 | [确认创建] [修改目标] |
| 8 | AI（确认后） | 计划已创建！你可以在计划详情页查看每日任务和进度。 |
| 8 | 操作按钮 | [查看计划] |

---

## 8. Figma AI 生成描述

Design a mobile app full-screen chat page for creating a health plan through AI conversation. The screen uses a light warm style with coral orange (#FF7A5C) as the brand color and #F7F8FA as the page background.

**Layout from top to bottom:**
1. A top navigation bar with a back arrow button on the left and the title "创建计划" (18px semibold, #222222). No bottom tab navigation on this page — it is a full-screen overlay.
2. A scrollable chat message area taking up the remaining space above the input bar. Messages alternate between AI and user:
   - **AI messages:** Left-aligned bubbles with #F2F3F5 background, 12px border-radius on all corners, 12px internal padding. Max width 75% of screen. Text in 16px #222222.
   - **User messages:** Right-aligned bubbles with #FFE7E1 (brand light) background, 12px border-radius on all corners, 12px internal padding. Max width 75% of screen. Text in 16px #222222.
   - **Message spacing:** 12px between consecutive messages.
   - **Quick option buttons:** Appear below AI messages when choices are offered. Horizontal row of pill-shaped buttons (24px border-radius, 8px vertical padding, 16px horizontal padding) with white background, 1px #EEEEEE border, text in 14px #222222. Selected option highlights with coral orange border.
3. After the AI generates a plan, a **plan summary card** is embedded inside the AI bubble:
   - White background, 12px border-radius, 3px left border in coral orange (#FF7A5C)
   - Content: plan name (16px semibold), goal weight, duration, phases, daily calorie target (14px #666666)
4. Below the plan summary, two action buttons: "确认创建" (coral orange filled pill button, white text) and "修改目标" (white pill button with coral orange border and text), side by side.
5. A fixed bottom input bar (56px height, white background, subtle upward shadow) with camera icon, microphone icon, text input field (pill-shaped, #F7F8FA background), and send button. This input bar matches the global AI input bar style but without the bottom tab navigation.

**AI thinking state:** Three dots bouncing animation in a left-aligned gray bubble, each dot is 8px circle in #999999, bouncing sequentially with 300ms interval.

**Style:** Light, warm, conversational, health-oriented. No heavy shadows. Chinese text. iPhone 14/15 dimensions. Phosphor Icons Light style for all icons. The overall feel should be friendly and approachable, like chatting with a health-savvy friend.

---

## 9. 相关素材

| 素材 | 用途 | 尺寸 | 说明 |
|------|------|------|------|
| AI 头像图标 | 对话气泡左侧 | 32×32px | 品牌风格圆形头像，健康管家形象 |
| 思考中动画 | AI 回复等待 | 48×24px | 三个点跳动动画，灰色 |
| 计划摘要卡片图标 | 摘要卡片装饰 | 20×20px | 线性剪贴板图标，珊瑚橙色 |
