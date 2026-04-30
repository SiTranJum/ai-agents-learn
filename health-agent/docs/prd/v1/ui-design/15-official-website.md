# 官网 Landing Page

> 页面编号：P15
> 类型：桌面端 + 移动端响应式网页
> 设计系统引用：`01-design-system.md`

---

## 1. 页面目标

对外展示"健康管家"产品价值，传递 AI-first 的健康管理理念，引导目标用户申请内测。页面需要在 5 秒内让访客理解产品是什么、解决什么问题，并产生试用兴趣。

---

## 2. 页面入口

独立域名访问（如 healthmate.ai 或 jiankangguanjia.com）。来源渠道包括搜索引擎、社交媒体分享、产品 Hunt 等。

---

## 3. 页面布局

### 桌面端布局（1440px 设计稿宽度，内容区 1200px）

```
┌─────────────────────────────────────────────────────────────────┐
│  🏠 健康管家          功能  场景  关于       [申请内测]          │ ← 顶部导航
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    Section 1: Hero 区                           │
│                                                                 │
│   像和朋友聊天一样，              ┌─────────────┐              │
│   管理你的健康                    │             │              │
│                                   │   📱 App    │              │
│   记录饮食、追踪身体数据、        │   Mockup    │              │
│   制定健康计划。                   │   (倾斜)    │              │
│   AI 懂你，也记得你。             │             │              │
│                                   │             │              │
│   ┌──────────┐ ┌──────────┐      │             │              │
│   │ 申请内测  │ │ 了解更多  │      └─────────────┘              │
│   └──────────┘ └──────────┘                                    │
│                                                                 │
│   背景：白色 → #FFF5F2 浅渐变                                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                  Section 2: 核心价值区                           │
│                                                                 │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│   │ 💬       │ │ 🧠       │ │ 🎯       │ │ ✅       │        │
│   │ 自然语言 │ │ AI 记得你│ │ 个性化   │ │ 轻量但   │        │
│   │ 记录     │ │          │ │ 建议     │ │ 完整     │        │
│   │          │ │ 你的习惯 │ │          │ │          │        │
│   │ 说一句话 │ │ 和偏好， │ │ 基于你的 │ │ 饮食、体 │        │
│   │ 就能记录 │ │ AI 都记得│ │ 数据，给 │ │ 重、计划 │        │
│   │ 饮食     │ │          │ │ 出专属建 │ │ 分析，一 │        │
│   │          │ │          │ │ 议       │ │ 站搞定   │        │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                  Section 3: 产品展示区                           │
│                                                                 │
│        ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐              │
│        │ 📱  │    │ 📱  │    │ 📱  │    │ 📱  │              │
│        │首页 │    │饮食 │    │数据 │    │对话 │              │
│        │截图 │    │记录 │    │分析 │    │创建 │              │
│        │     │    │截图 │    │截图 │    │截图 │              │
│        └─────┘    └─────┘    └─────┘    └─────┘              │
│                                                                 │
│        Dashboard   饮食记录    数据分析   计划创建               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                 Section 4: AI 能力介绍区                         │
│                                                                 │
│   ┌─────────────┐            常驻 AI 输入框                     │
│   │   截图      │            任何页面都能自然发起对话           │
│   │  AI 输入框  │            记录饮食、修改计划、查询营养       │
│   └─────────────┘                                            │
│                                                                 │
│                           对话式记录和修改        ┌─────────┐   │
│                           不用点很多按钮，         │  截图   │   │
│                           直接说出需求即可         │  对话流 │   │
│                                                   └─────────┘   │
│                                                                 │
│   ┌─────────────┐            三层记忆系统                       │
│   │   图示      │            短期/中期/长期记忆，               │
│   │   记忆架构  │            AI 懂你现在，也记得你过去           │
│   └─────────────┘                                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                 Section 5: 用户场景区                            │
│                                                                 │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│   │ 想减脂的人       │ │ 健身人群         │ │ 需要控制饮食的人 │ │
│   │                 │ │                 │ │                 │ │
│   │ AI 帮你制定     │ │ 精确记录蛋白质   │ │ 痛风、糖尿病等   │ │
│   │ 减脂计划，追踪   │ │ 摄入，优化饮食   │ │ 慢性病饮食管理   │ │
│   │ 每日热量         │ │ 结构             │ │                 │ │
│   └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                 Section 6: 底部 CTA                              │
│                                                                 │
│                 加入内测，和 AI 一起管理健康                     │
│                                                                 │
│                    ┌──────────────┐                             │
│                    │   立即申请    │                             │
│                    └──────────────┘                             │
│                                                                 │
│   © 2026 健康管家    隐私政策    联系方式                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 移动端布局（390px 宽度）

```
┌─────────────────────────────┐
│ ☰ 健康管家        [申请内测] │ ← 顶部导航（简化）
├─────────────────────────────┤
│                             │
│  像和朋友聊天一样，         │
│  管理你的健康               │ ← Hero 标题改为单列
│                             │
│  记录饮食、追踪身体数据、   │
│  制定健康计划。AI 懂你，    │
│  也记得你。                 │
│                             │
│   ┌─────────────────────┐   │
│   │      申请内测        │   │
│   └─────────────────────┘   │
│   ┌─────────────────────┐   │
│   │      了解更多        │   │
│   └─────────────────────┘   │
│                             │
│        ┌──────────┐         │
│        │  📱 App   │         │ ← 手机 mockup 下移到按钮后
│        │  Mockup   │         │
│        └──────────┘         │
│                             │
├─────────────────────────────┤
│  [价值卡片 1]               │
│  [价值卡片 2]               │ ← 所有 section 改为纵向堆叠
│  [价值卡片 3]               │
│  [价值卡片 4]               │
├─────────────────────────────┤
│  [产品截图轮播/横滑]         │
├─────────────────────────────┤
│  [AI 能力模块 1]            │
│  [AI 能力模块 2]            │
│  [AI 能力模块 3]            │
├─────────────────────────────┤
│  [用户场景卡片 1]           │
│  [用户场景卡片 2]           │
│  [用户场景卡片 3]           │
├─────────────────────────────┤
│   加入内测，和 AI 一起       │
│      管理健康               │
│                             │
│   ┌─────────────────────┐   │
│   │      立即申请        │   │
│   └─────────────────────┘   │
│                             │
│  © 2026 健康管家            │
│  隐私政策 · 联系方式        │
└─────────────────────────────┘
```

### 区域说明

| Section | 桌面端布局 | 移动端布局 | 说明 |
|---------|-----------|-----------|------|
| 顶部导航 | Logo + 菜单 + CTA 按钮 | 汉堡菜单 + Logo + CTA | 吸顶导航，滚动后保留 |
| Hero 区 | 左文案右手机 mockup | 单列纵向堆叠 | 首屏突出产品价值和 CTA |
| 核心价值区 | 4 卡片横排 | 4 卡片纵向堆叠 | 每卡片含图标 + 标题 + 描述 |
| 产品展示区 | 4 张手机 mockup 横排 | 横向轮播 | 展示核心页面视觉 |
| AI 能力介绍区 | 左右交替布局 | 单列堆叠 | 图文结合解释 AI 核心能力 |
| 用户场景区 | 3 卡片横排 | 3 卡片纵向堆叠 | 面向不同用户群体 |
| 底部 CTA | 居中大标题 + 按钮 + Footer | 同结构压缩 | 承接最终转化 |

---

## 4. 组件树

```
OfficialWebsitePage
├── StickyHeader                         # 吸顶顶部导航
│   ├── Logo                             # 品牌 Logo + 名称
│   ├── NavMenu                          # 桌面端导航菜单
│   │   ├── NavItem (功能)
│   │   ├── NavItem (场景)
│   │   └── NavItem (关于)
│   ├── CTAButton (申请内测)             # 顶部主 CTA
│   └── MobileMenuButton                 # 移动端汉堡按钮
│
├── HeroSection                          # Section 1: Hero 区
│   ├── HeroContent                      # 左侧文案区
│   │   ├── Headline                     # 主标题
│   │   ├── Subheadline                  # 副标题
│   │   └── CTAGroup                     # 按钮组
│   │       ├── PrimaryButton (申请内测)
│   │       └── SecondaryButton (了解更多)
│   └── HeroVisual                       # 右侧视觉区
│       └── PhoneMockup                  # App 手机 mockup
│
├── CoreValueSection                     # Section 2: 核心价值区
│   └── ValueCardGrid                    # 四列/单列网格
│       ├── ValueCard (自然语言记录)
│       │   ├── Icon
│       │   ├── Title
│       │   └── Description
│       ├── ValueCard (AI 记得你)
│       ├── ValueCard (个性化建议)
│       └── ValueCard (轻量但完整)
│
├── ProductShowcaseSection               # Section 3: 产品展示区
│   ├── SectionTitle                     # 区块标题
│   └── MockupGallery                    # 手机截图画廊
│       ├── MockupItem (首页 Dashboard)
│       ├── MockupItem (饮食记录页)
│       ├── MockupItem (数据分析页)
│       └── MockupItem (计划创建对话页)
│
├── AICapabilitySection                  # Section 4: AI 能力介绍区
│   ├── CapabilityBlock (常驻 AI 输入框)
│   │   ├── Screenshot
│   │   └── TextContent
│   ├── CapabilityBlock (对话式记录和修改)
│   │   ├── TextContent
│   │   └── Screenshot
│   └── CapabilityBlock (三层记忆系统)
│       ├── Diagram
│       └── TextContent
│
├── UserScenarioSection                  # Section 5: 用户场景区
│   └── ScenarioCardGrid                 # 三列/单列网格
│       ├── ScenarioCard (想减脂的人)
│       ├── ScenarioCard (健身人群)
│       └── ScenarioCard (需要控制饮食的人)
│
├── BottomCTASection                     # Section 6: 底部 CTA
│   ├── Headline                         # CTA 标题
│   ├── PrimaryButton (立即申请)         # 主按钮
│   └── FooterMeta                       # 底部信息
│       ├── CopyrightText
│       ├── PrivacyLink
│       └── ContactLink
│
└── MobileDrawer                         # 移动端抽屉菜单（可选）
    ├── DrawerNavItem (功能)
    ├── DrawerNavItem (场景)
    ├── DrawerNavItem (关于)
    └── DrawerCTAButton (申请内测)
```

---

## 5. 页面状态

### 5.1 默认加载完成态

| 区域 | 展示 |
|------|------|
| 顶部导航 | 正常显示 Logo、菜单项和 CTA 按钮 |
| Hero 区 | 主标题、副标题、按钮和手机 mockup 完整展示 |
| 核心价值区 | 四张价值卡片完整展示 |
| 产品展示区 | 4 张产品截图可见 |
| AI 能力介绍区 | 三个能力模块按左右交替方式排布 |
| 用户场景区 | 3 张场景卡片横排 |
| 底部 CTA | 大标题 + 主按钮 + Footer |

### 5.2 首屏加载中态

| 区域 | 展示差异 |
|------|---------|
| Hero 区文案 | 标题和副标题位置显示骨架屏 |
| 按钮 | 显示灰色圆角骨架块 |
| 手机 mockup | 显示设备轮廓骨架图 |
| 下方各 section | 延迟懒加载，滚动进入视口时再展示 |

### 5.3 移动端响应式态

| 区域 | 展示差异 |
|------|---------|
| 顶部导航 | 菜单折叠为汉堡按钮，右侧保留"申请内测" |
| Hero 区 | 改为纵向堆叠，按钮全宽 |
| 核心价值区 | 4 卡片改为单列堆叠 |
| 产品展示区 | 改为横向滑动截图轮播 |
| AI 能力介绍区 | 左右交替改为统一纵向排列 |
| Footer | 链接换行，保持可点击区域充足 |

### 5.4 CTA 提交成功态

| 场景 | 展示差异 |
|------|---------|
| 点击"申请内测"后提交成功 | 弹出成功反馈："申请已收到，我们会尽快联系你"，按钮短暂变为完成态 |
| 表单校验失败 | 在输入框下方显示错误提示，如"请输入有效邮箱" |

---

## 6. 关键交互

### 6.1 顶部导航交互

| 操作 | 行为 |
|------|------|
| 点击 Logo | 平滑滚动回页面顶部 |
| 点击"功能" | 平滑滚动到 Section 4 AI 能力介绍区 |
| 点击"场景" | 平滑滚动到 Section 5 用户场景区 |
| 点击"关于" | 平滑滚动到页面底部 Footer 区 |
| 点击顶部"申请内测" | 打开申请内测表单弹窗或跳转到申请表单页 |
| 页面向下滚动 | 顶部导航固定吸顶，背景从透明变为白色带阴影 |

### 6.2 Hero 区交互

| 操作 | 行为 |
|------|------|
| 点击"申请内测" | 直接打开申请表单，减少转化路径 |
| 点击"了解更多" | 平滑滚动到 Section 2 核心价值区 |
| 手机 mockup 悬停（桌面端） | 轻微上浮 + 阴影增强，增加质感 |

### 6.3 产品展示区交互

| 操作 | 行为 |
|------|------|
| 点击任意手机 mockup | 放大查看大图或切换到对应截图详情 |
| 移动端左右滑动 | 水平浏览产品截图 |
| 截图悬停（桌面端） | 当前截图轻微放大，标题高亮 |

### 6.4 CTA 转化交互

| 操作 | 行为 |
|------|------|
| 点击任一"申请内测"/"立即申请"按钮 | 打开表单弹窗，收集姓名、邮箱、使用目标 |
| 表单提交成功 | 显示成功状态，并可引导加入微信/邮件通知 |
| 点击隐私政策 | 打开隐私政策页面 |
| 点击联系方式 | 打开邮件客户端或复制联系邮箱 |

---

## 7. 页面文案

### 7.1 顶部导航

| 位置 | 文案 |
|------|------|
| Logo 旁品牌名 | "健康管家" |
| 导航项 1 | "功能" |
| 导航项 2 | "场景" |
| 导航项 3 | "关于" |
| 顶部 CTA | "申请内测" |

### 7.2 Hero 区

| 元素 | 文案 |
|------|------|
| 主标题 | "像和朋友聊天一样，管理你的健康" |
| 副标题 | "记录饮食、追踪身体数据、制定健康计划。AI 懂你，也记得你。" |
| 主按钮 | "申请内测" |
| 次按钮 | "了解更多" |

### 7.3 核心价值区

| 卡片标题 | 描述 |
|---------|------|
| "自然语言记录" | "说一句话就能记录饮食" |
| "AI 记得你" | "你的习惯和偏好，AI 都记得" |
| "个性化建议" | "基于你的数据，给出专属建议" |
| "轻量但完整" | "饮食、体重、计划、分析，一站搞定" |

### 7.4 产品展示区

| 元素 | 文案 |
|------|------|
| 区块标题 | "一个 App，管理你的完整健康日常" |
| 截图 1 标题 | "首页 Dashboard" |
| 截图 2 标题 | "饮食记录页" |
| 截图 3 标题 | "数据分析页" |
| 截图 4 标题 | "计划创建对话页" |

### 7.5 AI 能力介绍区

| 模块标题 | 描述 |
|---------|------|
| "常驻 AI 输入框" | "无论你在哪个页面，都可以直接和 AI 说一句话完成记录或查询。" |
| "对话式记录和修改" | "不用反复点按钮，直接告诉 AI 你吃了什么、想改什么。" |
| "三层记忆系统" | "AI 不只理解你当下的一句话，也会记得你的历史习惯、偏好和目标。" |

### 7.6 用户场景区

| 场景 | 描述 |
|------|------|
| "想减脂的人" | "AI 帮你制定减脂计划，追踪每日热量" |
| "健身人群" | "精确记录蛋白质摄入，优化饮食结构" |
| "需要控制饮食的人" | "痛风、糖尿病等慢性病饮食管理" |

### 7.7 底部 CTA

| 元素 | 文案 |
|------|------|
| CTA 标题 | "加入内测，和 AI 一起管理健康" |
| CTA 按钮 | "立即申请" |
| 版权信息 | "© 2026 健康管家" |
| 隐私政策 | "隐私政策" |
| 联系方式 | "联系方式" |

---

## 8. Figma AI 生成描述

Design a modern responsive landing page for an AI-first health management product called "健康管家". The brand feeling should be warm, approachable, lifestyle-oriented, and trustworthy, not overly futuristic. Use coral orange (#FF7A5C) as the brand primary color, light gray background (#F7F8FA), white cards with 12px border radius, and plenty of whitespace.

Desktop layout is 1440px wide with a centered 1200px content container. The page starts with a sticky top navigation bar: logo on the left, simple text navigation in the middle (功能 / 场景 / 关于), and a coral CTA button "申请内测" on the right.

Section 1 Hero: left side has a large bold Chinese headline "像和朋友聊天一样，管理你的健康" (36px bold), subheadline "记录饮食、追踪身体数据、制定健康计划。AI 懂你，也记得你。" (18px), a coral primary button "申请内测", and an outlined secondary button "了解更多". Right side shows an angled mobile app mockup with a beautiful app homepage screenshot. Background uses a soft gradient from white to very light coral.

Section 2 Core Value: four horizontal cards, each with a minimal icon, a short title, and one-line description. Titles: 自然语言记录, AI 记得你, 个性化建议, 轻量但完整.

Section 3 Product Showcase: 3 to 4 mobile phone mockups side by side showing the app’s main screens: Dashboard, food record page, analytics page, and AI plan creation conversation page.

Section 4 AI Capability: alternating left-right visual and text blocks. Show a screenshot of the persistent AI input bar, a screenshot of conversational editing, and a simple diagram for a three-layer memory system (short-term / mid-term / long-term memory).

Section 5 User Scenarios: three cards for different user groups: fat loss users, fitness users, and users with dietary control needs such as diabetes or gout.

Section 6 Bottom CTA: centered headline "加入内测，和 AI 一起管理健康", large coral button "立即申请", and a minimal footer with copyright, privacy policy, and contact info.

Mobile responsive version should stack all sections vertically, use full-width buttons, convert the product gallery into a swipeable horizontal carousel, and collapse the navigation into a simple top bar with a menu icon. Chinese interface, polished startup landing page aesthetic, inspired by modern wellness apps and clean SaaS landing pages.

---

## 9. 相关素材

### 9.1 官网视觉素材

| 素材名称 | 用途 | 风格描述 |
|---------|------|---------|
| 官网 Hero 区手机 mockup | 首屏右侧主视觉 | 倾斜展示的高保真 iPhone mockup，屏幕内为首页 Dashboard 截图，干净精致 |
| 产品展示截图组 | Section 3 产品展示区 | 4 张高保真 App 页面截图，统一设备边框和阴影样式 |
| 三层记忆系统图示 | Section 4 AI 能力介绍区 | 简洁结构图，三层卡片或同心圆样式，分别标注短期/中期/长期记忆 |

### 9.2 图标素材

| 图标名称 | 用途 | 风格描述 |
|---------|------|---------|
| 自然语言记录图标 | 核心价值卡片 | 对话气泡 + 餐具元素，线性风格 |
| AI 记忆图标 | 核心价值卡片 | 大脑/记忆节点图标，线性风格 |
| 个性化建议图标 | 核心价值卡片 | 靶心/灯泡图标，线性风格 |
| 轻量完整图标 | 核心价值卡片 | 四宫格/整合面板图标，线性风格 |

### 9.3 品牌与规范

| 元素 | 说明 |
|------|------|
| 品牌主色 | 珊瑚橙 `#FF7A5C` |
| 页面背景 | 浅灰 `#F7F8FA` |
| 卡片底色 | 白色 `#FFFFFF` |
| 卡片圆角 | 12px |
| Hero 渐变背景 | 白色 → 品牌浅色 `#FFF5F2` |
| 按钮风格 | 主按钮品牌色填充，次按钮白底灰边框 |

### 9.4 转化相关素材

| 素材名称 | 用途 | 说明 |
|---------|------|------|
| 申请内测表单弹窗 | CTA 点击后 | 收集姓名、邮箱、目标场景，可作为独立弹窗组件 |
| 联系方式图标 | Footer | 邮件/微信/社媒图标，线性风格，保持简洁 |
