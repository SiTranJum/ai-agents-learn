# AI 对话与浮层组件

> 页面编号：P14
> 包含：AI 多轮全屏对话页、跨页面确认弹窗、营养查询浮层卡片
> 设计系统引用：`01-design-system.md`

---

## 1. 页面目标

本文件定义三个 AI 交互相关的组件/页面：
- **A. AI 多轮全屏对话页**：承载计划创建、复杂修改、多轮追问等需要深度对话的场景，当对话超过 2 轮时自动从内联切换到全屏模式。
- **B. 跨页面确认弹窗**：当用户在当前页面触发了属于其他页面的操作时，弹窗确认是否跳转；也用于低置信度意图确认和删除确认。
- **C. 营养查询浮层卡片**：用户查询食物营养信息时，以底部浮层形式展示结果，不离开当前页面。

---

## 2. 页面入口

| 组件 | 触发方式 |
|------|---------|
| A. AI 多轮全屏对话页 | 1) 对话超过 2 轮自动切换进入；2) 点击"创建计划"等需要多轮对话的入口直接进入 |
| B. 跨页面确认弹窗 | AI 检测到跨页面意图时自动弹出；低置信度意图识别时弹出；删除操作时弹出 |
| C. 营养查询浮层卡片 | 用户输入营养查询类问题（如"鸡胸肉多少卡路里"）时自动弹出 |

---

## 3. 页面布局

### A. AI 多轮全屏对话页

```
┌─────────────────────────────────────┐
│            状态栏 (系统)              │
├─────────────────────────────────────┤
│  ← 返回        创建计划              │ ← A1. 顶部导航栏 (56px)
├─────────────────────────────────────┤
│                                     │
│           2024年4月29日 14:32        │ ← 时间戳（居中）
│                                     │
│  ┌──────────────────────────┐       │
│  │ 好的，我来帮你创建减脂   │       │ ← AI 消息（左对齐）
│  │ 计划。先了解一下你的基   │       │
│  │ 本情况：                 │       │ #F2F3F5 背景
│  │                          │       │ 12px 圆角
│  │ 你的身高和体重是多少？   │       │ 最大宽度 80%
│  └──────────────────────────┘       │
│                                     │ ← 消息间距 12px
│       ┌──────────────────────────┐  │
│       │ 身高 175cm，体重 80kg    │  │ ← 用户消息（右对齐）
│       └──────────────────────────┘  │   #FFE7E1 背景
│                                     │
│  ┌──────────────────────────┐       │
│  │ 了解。你的目标体重是多少 │       │ ← AI 消息
│  │ ？希望多长时间达到？     │       │
│  └──────────────────────────┘       │
│                                     │
│       ┌──────────────────────────┐  │
│       │ 目标 70kg，3 个月左右   │  │ ← 用户消息
│       └──────────────────────────┘  │
│                                     │
│  ┌──────────────────────────┐       │
│  │ 你平时的运动习惯是？     │       │
│  │                          │       │ ← AI 消息 + 选项按钮组
│  │ ┌──────┐ ┌──────┐       │       │
│  │ │几乎不│ │偶尔  │       │       │ ← 横排胶囊按钮
│  │ └──────┘ └──────┘       │       │
│  │ ┌──────┐ ┌──────┐       │       │
│  │ │每周3+│ │每天  │       │       │
│  │ └──────┘ └──────┘       │       │
│  └──────────────────────────┘       │
│                                     │
│  ┌──────────────────────────┐       │ ← 计划摘要卡片
│  │ 📋 减脂计划摘要          │       │   （对话结束时展示）
│  │ ─────────────────────── │       │
│  │ 目标：80kg → 70kg       │       │
│  │ 周期：3 个月             │       │
│  │ 每日热量：1,800 kcal     │       │
│  │ 运动建议：每周 3 次      │       │
│  │                          │       │
│  │    ┌──────────────────┐  │       │
│  │    │   确认创建计划    │  │       │ ← 品牌色确认按钮
│  │    └──────────────────┘  │       │
│  │    ┌──────────────────┐  │       │
│  │    │   继续调整       │  │       │ ← 次要按钮
│  │    └──────────────────┘  │       │
│  └──────────────────────────┘       │
│                                     │
│  ○ ○ ○                              │ ← AI 正在输入（loading）
│                                     │
├─────────────────────────────────────┤
│ [📷] [🎤]  输入消息...      [发送]  │ ← A2. 底部输入框 (56px)
└─────────────────────────────────────┘
```

### B. 跨页面确认弹窗

```
┌─────────────────────────────────────┐
│                                     │
│          (当前页面内容)               │
│                                     │
│   ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐   │ ← 半透明遮罩
│   │                             │   │   rgba(0,0,0,0.4)
│   │   ┌───────────────────┐    │   │
│   │   │                   │    │   │ ← 白色对话框
│   │   │  需要跳转页面      │    │   │   宽度 280px
│   │   │                   │    │   │   16px 圆角
│   │   │  检测到你想创建    │    │   │   居中显示
│   │   │  计划，需要跳转到  │    │   │
│   │   │  计划页面          │    │   │
│   │   │                   │    │   │
│   │   │  ┌─────────────┐  │    │   │
│   │   │  │  去创建      │  │    │   │ ← 主按钮 #FF7A5C
│   │   │  └─────────────┘  │    │   │   白色文字，圆角 8px
│   │   │  ┌─────────────┐  │    │   │
│   │   │  │  取消        │  │    │   │ ← 次按钮 灰色边框
│   │   │  └─────────────┘  │    │   │   #666 文字，圆角 8px
│   │   │                   │    │   │
│   │   └───────────────────┘    │   │
│   │                             │   │
│   └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘   │
│                                     │
└─────────────────────────────────────┘
```

**变体 1：低置信度意图确认**

```
┌───────────────────┐
│                   │
│  你是想创建       │
│  减脂计划吗？     │
│                   │
│  ┌─────┐ ┌─────┐ │
│  │ 是的 │ │不是 │ │ ← 双按钮横排
│  └─────┘ └─────┘ │   "是的"品牌色
│                   │   "不是"灰色边框
└───────────────────┘
```

**变体 2：删除确认**

```
┌───────────────────┐
│                   │
│  确定删除         │
│  午餐记录吗？     │
│                   │
│  删除后无法恢复   │ ← 提示文案 #999
│                   │
│  ┌─────────────┐  │
│  │  确定删除    │  │ ← 红色按钮 #FF5A5F
│  └─────────────┘  │
│  ┌─────────────┐  │
│  │  取消        │  │ ← 灰色边框按钮
│  └─────────────┘  │
│                   │
└───────────────────┘
```

### C. 营养查询浮层卡片

```
┌─────────────────────────────────────┐
│                                     │
│          (当前页面内容)               │
│                                     │
│   ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐   │ ← 半透明遮罩
│   │                             │   │
│   │                             │   │
│   ├─────────────────────────────┤   │ ← 从底部弹出
│   │         ────                │   │ ← 顶部拖拽条（灰色短横线）
│   │                             │   │   16px 顶部圆角
│   │   🍗 鸡胸肉（100g）         │   │ ← 食物名称 + 份量
│   │                             │   │
│   │        231                  │   │ ← 热量大数字
│   │       kcal                  │   │   36px 粗体
│   │                             │   │
│   │   ┌────────┬────────┬─────┐│   │
│   │   │ 碳水   │ 蛋白质 │脂肪 ││   │ ← 三大营养素
│   │   │  0g    │ 31.4g  │5.0g ││   │   等宽三列
│   │   └────────┴────────┴─────┘│   │
│   │                             │   │
│   │   数据来源：知识库 ✓         │   │ ← 数据来源标记
│   │                             │   │   知识库/API/AI估算
│   │   ┌─────────────────────┐  │   │
│   │   │  记录到今日饮食      │  │   │ ← 主按钮 #FF7A5C
│   │   └─────────────────────┘  │   │
│   │   ┌─────────────────────┐  │   │
│   │   │  关闭               │  │   │ ← 次按钮 灰色文字
│   │   └─────────────────────┘  │   │
│   │                             │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 区域说明

| 组件 | 区域 | 高度/尺寸 | 说明 |
|------|------|----------|------|
| A | A1. 顶部导航栏 | 56px | 左侧返回按钮，中间标题（如"创建计划"/"AI 对话"） |
| A | A2. 对话消息流区域 | 自适应 | 可滚动，消息气泡从上到下排列，自动滚动到最新消息 |
| A | A3. 底部输入框 | 56px | 与全局 AI 输入框风格一致，拍照 + 语音 + 文字输入 + 发送 |
| B | 遮罩层 | 全屏 | 半透明黑色 rgba(0,0,0,0.4) |
| B | 对话框 | 宽 280px | 白色背景，16px 圆角，垂直居中 |
| C | 浮层卡片 | 自适应高度 | 从底部弹出，16px 顶部圆角，白色背景 |

---

## 4. 组件树

### A. AI 多轮全屏对话页

```
AIDialogPage
├── TopBar                              # 顶部导航栏
│   ├── BackButton                      # 返回按钮
│   └── TitleText                       # 页面标题
│
├── MessageScrollView                   # 对话消息流区域（可滚动）
│   ├── TimestampDivider                # 时间戳分隔线
│   │   └── TimeText                    # 时间文字（居中）
│   │
│   ├── AIMessage                       # AI 消息气泡
│   │   ├── AvatarIcon                  # AI 头像（可选）
│   │   ├── MessageBubble               # 消息气泡容器
│   │   │   └── MessageText             # 消息文字
│   │   └── TimestampText               # 消息时间（可选）
│   │
│   ├── UserMessage                     # 用户消息气泡
│   │   ├── MessageBubble               # 消息气泡容器
│   │   │   └── MessageText             # 消息文字
│   │   └── TimestampText               # 消息时间（可选）
│   │
│   ├── AIMessageWithOptions            # AI 消息 + 选项按钮组
│   │   ├── MessageBubble               # 消息气泡
│   │   │   ├── MessageText             # 消息文字
│   │   │   └── OptionButtonGroup       # 选项按钮组
│   │   │       ├── OptionButton        # 胶囊按钮（横排）
│   │   │       ├── OptionButton
│   │   │       └── ...
│   │   └── TimestampText
│   │
│   ├── PlanSummaryCard                 # 计划摘要卡片（对话结束时）
│   │   ├── CardHeader                  # 卡片标题
│   │   ├── SummaryContent              # 摘要内容
│   │   │   ├── SummaryItem (目标)
│   │   │   ├── SummaryItem (周期)
│   │   │   ├── SummaryItem (热量)
│   │   │   └── SummaryItem (运动)
│   │   └── ActionButtons               # 操作按钮组
│   │       ├── PrimaryButton (确认创建) # 品牌色主按钮
│   │       └── SecondaryButton (继续调整) # 次要按钮
│   │
│   └── TypingIndicator                 # AI 正在输入动画
│       └── DotAnimation                # 三个点动画
│
└── AIInputBar                          # 底部输入框（固定）
    ├── CameraButton                    # 拍照按钮
    ├── VoiceButton                     # 语音按钮
    ├── TextInput                       # 文字输入框
    └── SendButton                      # 发送按钮
```

### B. 跨页面确认弹窗

```
ConfirmDialog
├── Overlay                             # 半透明遮罩
│   └── OverlayBackground               # rgba(0,0,0,0.4)
│
└── DialogBox                           # 白色对话框
    ├── TitleText                       # 标题文字
    ├── ContentText                     # 内容文字
    └── ButtonGroup                     # 按钮组
        ├── PrimaryButton               # 主按钮（品牌色/红色）
        └── SecondaryButton             # 次按钮（灰色边框）
```

### C. 营养查询浮层卡片

```
NutritionSheet
├── Overlay                             # 半透明遮罩
│   └── OverlayBackground               # rgba(0,0,0,0.4)
│
└── SheetCard                           # 底部浮层卡片
    ├── DragHandle                      # 顶部拖拽条
    ├── FoodHeader                      # 食物名称 + 份量
    │   ├── FoodNameText
    │   └── PortionText
    ├── CalorieDisplay                  # 热量大数字
    │   ├── CalorieValue                # 数值（36px 粗体）
    │   └── CalorieUnit                 # 单位 "kcal"
    ├── MacroNutrientGrid               # 三大营养素网格
    │   ├── MacroItem (碳水)
    │   │   ├── MacroLabel
    │   │   └── MacroValue
    │   ├── MacroItem (蛋白质)
    │   └── MacroItem (脂肪)
    ├── DataSourceTag                   # 数据来源标记
    │   └── SourceText                  # "知识库 ✓" / "API" / "AI估算"
    └── ActionButtons                   # 操作按钮组
        ├── PrimaryButton (记录到今日饮食) # 品牌色主按钮
        └── SecondaryButton (关闭)      # 灰色文字按钮
```

---

## 5. 页面状态

### A. AI 多轮全屏对话页状态

| 状态 | 说明 | 视觉差异 |
|------|------|---------|
| 对话进行中 | 用户和 AI 正在多轮对话 | 消息流正常显示，输入框可用 |
| 等待 AI 回复 | 用户发送消息后等待 AI 响应 | 底部显示"○ ○ ○"动画，输入框禁用 |
| 对话完成 | AI 完成任务，展示摘要卡片 | 显示计划摘要卡片 + 确认按钮，输入框隐藏或禁用 |
| 选项待选择 | AI 提供选项按钮等待用户选择 | 选项按钮高亮可点击，输入框可用（用户可选择或直接输入） |

### B. 跨页面确认弹窗状态

| 状态 | 说明 | 视觉差异 |
|------|------|---------|
| 跨页面确认 | 检测到跨页面意图 | 标题"需要跳转页面"，主按钮"去创建"，次按钮"取消" |
| 低置信度确认 | AI 不确定用户意图 | 标题为问句，双按钮横排"是的"/"不是" |
| 删除确认 | 用户触发删除操作 | 标题"确定删除"，提示"删除后无法恢复"，主按钮红色"确定删除" |

### C. 营养查询浮层卡片状态

| 状态 | 说明 | 视觉差异 |
|------|------|---------|
| 加载中 | 正在查询营养数据 | 显示骨架屏或 loading 动画 |
| 已加载（知识库） | 从知识库获取到精确数据 | 数据来源标记"知识库 ✓"，绿色勾选图标 |
| 已加载（API） | 从第三方 API 获取数据 | 数据来源标记"API"，蓝色图标 |
| AI 估算 | AI 根据常识估算的数据 | 数据来源标记"AI估算"，橙色警告图标，数值带"约"字 |

---

## 6. 关键交互

### A. AI 多轮全屏对话页交互

| 操作 | 行为 |
|------|------|
| 点击返回按钮 | 弹出确认弹窗："对话尚未完成，确定退出吗？"，确认后返回原页面 |
| 输入文字并发送 | 消息添加到消息流，页面滚动到底部，显示 AI 正在输入动画 |
| 点击选项按钮 | 选项按钮变为选中态，自动作为用户消息发送，触发 AI 下一轮回复 |
| 点击计划摘要卡片的"确认创建" | 创建计划，返回计划列表页，显示成功 Toast |
| 点击计划摘要卡片的"继续调整" | 摘要卡片收起，输入框重新激活，用户可继续对话调整 |
| 对话完成后点击返回 | 直接返回原页面，不弹确认（因为任务已完成） |

### B. 跨页面确认弹窗交互

| 操作 | 行为 |
|------|------|
| 点击主按钮（如"去创建"） | 关闭弹窗，跳转到目标页面，携带上下文信息 |
| 点击次按钮（如"取消"） | 关闭弹窗，停留在当前页面，AI 输入框清空 |
| 点击遮罩层 | 关闭弹窗，等同于点击"取消" |
| 低置信度确认点击"是的" | 关闭弹窗，AI 按确认的意图执行操作 |
| 低置信度确认点击"不是" | 关闭弹窗，AI 输入框重新激活，提示"请重新描述你的需求" |
| 删除确认点击"确定删除" | 关闭弹窗，执行删除操作，显示成功 Toast |

### C. 营养查询浮层卡片交互

| 操作 | 行为 |
|------|------|
| 点击"记录到今日饮食" | 关闭浮层，跳转到饮食记录页，自动填充食物和营养数据 |
| 点击"关闭" | 关闭浮层，停留在当前页面 |
| 向下拖拽卡片 | 卡片跟随手指移动，松手后自动关闭（拖拽距离超过 100px） |
| 点击遮罩层 | 关闭浮层 |
| 加载中状态 | 显示骨架屏，按钮禁用 |

---

## 7. 页面文案

### A. AI 多轮全屏对话页文案

| 位置 | 文案示例 |
|------|---------|
| 页面标题（创建计划） | "创建计划" |
| 页面标题（通用对话） | "AI 对话" |
| 页面标题（修改计划） | "修改计划" |
| 返回确认弹窗标题 | "对话尚未完成" |
| 返回确认弹窗内容 | "确定退出吗？当前对话内容将不会保存。" |
| 返回确认弹窗按钮 | "继续对话" / "确定退出" |
| AI 正在输入 | "○ ○ ○"（动画） |
| 计划摘要卡片标题 | "📋 减脂计划摘要" |
| 计划摘要卡片按钮 | "确认创建计划" / "继续调整" |
| 输入框 placeholder | "输入消息..." |

### B. 跨页面确认弹窗文案

| 场景 | 标题 | 内容 | 主按钮 | 次按钮 |
|------|------|------|--------|--------|
| 跨页面跳转 | "需要跳转页面" | "检测到你想创建计划，需要跳转到计划页面" | "去创建" | "取消" |
| 低置信度确认 | "你是想创建减脂计划吗？" | （无） | "是的" | "不是" |
| 删除确认 | "确定删除午餐记录吗？" | "删除后无法恢复" | "确定删除" | "取消" |

### C. 营养查询浮层卡片文案

| 位置 | 文案示例 |
|------|---------|
| 食物名称 | "鸡胸肉" |
| 份量 | "100g" |
| 热量单位 | "kcal" |
| 营养素标签 | "碳水" / "蛋白质" / "脂肪" |
| 数据来源（知识库） | "数据来源：知识库 ✓" |
| 数据来源（API） | "数据来源：第三方 API" |
| 数据来源（AI 估算） | "数据来源：AI 估算（仅供参考）" |
| 主按钮 | "记录到今日饮食" |
| 次按钮 | "关闭" |
| 加载中 | "正在查询营养数据..." |

---

## 8. Figma AI 生成描述

### A. AI 多轮全屏对话页

Design a full-screen AI conversation page for a mobile health app. The page has a clean, chat-like interface with a warm and friendly feel. Top navigation bar (56px height) with a back arrow on the left and page title "创建计划" (Create Plan) in the center, white background.

The main area is a scrollable message feed with alternating AI and user message bubbles. AI messages are left-aligned with light gray background (#F2F3F5), 12px border radius, max width 80% of screen. User messages are right-aligned with coral-tinted background (#FFE7E1), same styling. Message spacing is 12px vertical. Timestamps are centered between message groups in small gray text (13px, #999999).

Special message types include: AI messages with option buttons (horizontal pill-shaped buttons in a grid below the message text), and a plan summary card at the end of conversation (white card with coral accent, showing plan details like target weight, duration, daily calories, with two buttons: primary "确认创建计划" in coral #FF7A5C and secondary "继续调整" with gray border).

At the bottom, a typing indicator shows three animated dots when AI is responding. The bottom input bar (56px height) matches the global AI input style: camera icon, microphone icon, text input field with placeholder "输入消息...", and send button, all in a white container with subtle shadow.

Overall style: modern, conversational, health-focused, coral orange (#FF7A5C) as primary color, light gray (#F7F8FA) background, 12px card radius throughout. Chinese interface. iPhone 14/15 dimensions.

### B. 跨页面确认弹窗

Design a modal confirmation dialog for a mobile health app. Semi-transparent black overlay (rgba(0,0,0,0.4)) covering the entire screen. Centered white dialog box (280px width, 16px border radius) with vertical padding.

Dialog contains: title text at top (16px, medium weight, #333333), body text below (14px, regular weight, #666666), and two stacked buttons at bottom. Primary button has coral background (#FF7A5C) with white text, 8px border radius, full width. Secondary button below has gray border (#DDDDDD) with gray text (#666666), same styling.

Variants: 1) Cross-page navigation: title "需要跳转页面", body "检测到你想创建计划，需要跳转到计划页面", buttons "去创建" / "取消". 2) Low confidence confirmation: title "你是想创建减脂计划吗？", two horizontal buttons "是的" (coral) / "不是" (gray border). 3) Delete confirmation: title "确定删除午餐记录吗？", body "删除后无法恢复" in gray, primary button in red (#FF5A5F) "确定删除", secondary "取消".

Style: clean, minimal, health app aesthetic, coral orange primary color, clear hierarchy. Chinese interface.

### C. 营养查询浮层卡片

Design a bottom sheet card for displaying food nutrition information in a mobile health app. Semi-transparent black overlay (rgba(0,0,0,0.4)) covering screen. White card slides up from bottom with 16px top border radius only.

Card structure from top to bottom: small gray drag handle (horizontal line, 4px height, 32px width, centered, 12px from top), food name and portion "🍗 鸡胸肉 (100g)" in 18px medium weight, large calorie number "231" in 36px bold with "kcal" unit below in 14px, three-column grid showing macronutrients (碳水 0g / 蛋白质 31.4g / 脂肪 5.0g) with equal width columns and light gray dividers, data source tag "数据来源：知识库 ✓" with green checkmark icon (or orange warning icon for AI estimates), primary button "记录到今日饮食" in coral (#FF7A5C) with white text and 8px radius, secondary text button "关闭" in gray below.

Loading state shows skeleton screens for numbers. AI estimate state shows "约" prefix on numbers and orange warning icon. Style: modern, clean, health-focused, coral orange primary color, clear information hierarchy. Chinese interface. iPhone dimensions.

---

## 9. 相关素材

### 9.1 图标素材

| 图标名称 | 用途 | 风格描述 |
|---------|------|---------|
| 返回箭头 | AI 对话页顶部导航 | 线性左箭头，1.5px 线宽，#333333 |
| AI 头像（可选） | AI 消息气泡旁 | 圆形机器人头像或品牌 logo，24×24px |
| 用户头像（可选） | 用户消息气泡旁 | 圆形用户头像占位符，24×24px |
| 拖拽条 | 营养查询浮层顶部 | 灰色短横线，4px 高 32px 宽，#DDDDDD |
| 数据来源图标 | 营养查询浮层 | 知识库：绿色勾选 ✓；API：蓝色数据库图标；AI 估算：橙色警告图标 |

### 9.2 动画素材

| 动画名称 | 用途 | 说明 |
|---------|------|------|
| AI 正在输入动画 | 对话页等待 AI 回复 | 三个圆点依次放大缩小，循环播放，灰色 #999999 |
| 消息发送动画 | 用户发送消息后 | 消息气泡从底部淡入并上移到位置 |
| 浮层弹出动画 | 营养查询浮层 | 从底部向上滑入，带缓动效果，300ms |
| 浮层关闭动画 | 营养查询浮层 | 向下滑出屏幕，带缓动效果，250ms |
| 弹窗淡入动画 | 跨页面确认弹窗 | 遮罩淡入 + 对话框缩放淡入，200ms |

### 9.3 交互反馈

| 反馈类型 | 说明 |
|---------|------|
| 按钮点击 | 按下时背景色加深 10%，松开恢复，带 100ms 过渡 |
| 选项按钮选中 | 边框变为品牌色，背景变为品牌浅色 #FFE7E1 |
| 消息气泡长按 | 触发震动反馈，弹出操作菜单（复制/删除） |
| 浮层拖拽 | 卡片跟随手指移动，拖拽超过 100px 松手后自动关闭 |
