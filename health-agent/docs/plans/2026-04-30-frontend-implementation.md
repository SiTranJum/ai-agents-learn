# 健康管家前端 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于前端 specs 文档，从零搭建健康管家 React Native (Expo) 前端项目，实现所有页面和组件，使用 mock 数据驱动。

**Architecture:** Expo SDK 52+ 项目，按功能模块划分（features/），共享组件层（shared/），核心基础设施层（core/）。Mock-First 开发，前端独立运行。UI 实现以 `docs/prd/v1/ui-design/*.md` 文稿为准。

**Tech Stack:** React Native (Expo) · TypeScript · React Navigation v7 · Zustand 5.x · TanStack Query 5.x · React Hook Form 7.x · Zod 3.x · react-native-chart-kit · @expo/vector-icons (Feather) · react-native-reanimated · @gorhom/bottom-sheet · date-fns

**Specs 目录:** `docs/specs/frontend/` — 所有实现细节参考此目录下的 spec 文档。

**UI 设计依据:** `docs/prd/v1/ui-design/*.md` — 没有完整视觉稿，以文稿中的 ASCII 线框图、组件树、样式描述为准。

---

## Phase 0: 项目初始化与基础设施

**目标：** 搭建 Expo 项目骨架，配置 TypeScript、路径别名、核心依赖，建立目录结构。

**参考 spec：** `00-implementation-overview.md`、`01-project-structure.md`

### Task 0.1: 初始化 Expo 项目

**Files:**
- Create: `health-agent-app/` (Expo 项目根目录)

- [x] **Step 1: 创建 Expo 项目**

```bash
npx create-expo-app@latest health-agent-app --template blank-typescript
cd health-agent-app
```

- [x] **Step 2: 安装核心依赖**

```bash
# 导航
npx expo install @react-navigation/native @react-navigation/native-stack @react-navigation/bottom-tabs react-native-screens react-native-safe-area-context

# 状态管理
npm install zustand @tanstack/react-query

# 表单
npm install react-hook-form zod @hookform/resolvers

# UI 工具
npx expo install react-native-reanimated react-native-gesture-handler @gorhom/bottom-sheet

# 图表
npm install react-native-chart-kit react-native-svg

# 工具
npm install date-fns

# 安全存储
npx expo install expo-secure-store expo-camera expo-image-picker
```

- [x] **Step 3: 配置 TypeScript 路径别名**

修改 `tsconfig.json`：
```json
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "baseUrl": "./src",
    "paths": {
      "@app/*": ["app/*"],
      "@core/*": ["core/*"],
      "@features/*": ["features/*"],
      "@shared/*": ["shared/*"],
      "@assets/*": ["assets/*"]
    }
  }
}
```

配置 `babel.config.js` 添加 `babel-plugin-module-resolver`：
```bash
npm install --save-dev babel-plugin-module-resolver
```

- [x] **Step 4: 创建完整目录结构**

按 `01-project-structure.md` 创建所有目录和占位 index.ts 文件。

- [x] **Step 5: 验证项目启动**

```bash
npx expo start
```

- [x] **Step 6: Commit**

```bash
git init && git add -A && git commit -m "chore: init Expo project with dependencies and directory structure"
```

---

### Task 0.2: Design Tokens 与全局样式

**参考 spec：** `04-design-system-mapping.md`

**Files:**
- Create: `src/app/styles/tokens.ts`
- Create: `src/app/styles/theme.ts`
- Create: `src/app/styles/globalStyles.ts`

- [x] **Step 1: 创建 Design Tokens**

在 `tokens.ts` 中定义所有 token（颜色、字体、间距、圆角、阴影、动效），严格按照 `04-design-system-mapping.md` 中的值。

- [x] **Step 2: 创建 Theme 汇总**

在 `theme.ts` 中汇总所有 token 为统一的 `theme` 对象。

- [x] **Step 3: 创建全局样式**

在 `globalStyles.ts` 中定义页面容器、卡片容器等通用样式。

- [x] **Step 4: Commit**

```bash
git add src/app/styles/ && git commit -m "feat: add design tokens and theme configuration"
```

---

### Task 0.3: 核心基础设施

**参考 spec：** `03-state-and-data-flow.md`

**Files:**
- Create: `src/core/store/globalStore.ts`
- Create: `src/core/store/createStore.ts`
- Create: `src/core/query/queryClient.ts`
- Create: `src/core/types/common.ts`
- Create: `src/core/types/models.ts`
- Create: `src/core/constants/config.ts`
- Create: `src/core/constants/routes.ts`

- [x] **Step 1: 创建 Zustand 全局 Store**

按 `03-state-and-data-flow.md` 中的 `GlobalState` 接口实现。

- [x] **Step 2: 创建 TanStack Query Client**

配置默认选项（staleTime、gcTime、retry）。

- [x] **Step 3: 创建通用类型定义**

在 `models.ts` 中定义 `UserProfile`、`MealRecord`、`BodyRecord`、`Plan` 等核心数据模型。

- [x] **Step 4: 创建路由常量**

在 `routes.ts` 中定义所有路由名称常量。

- [x] **Step 5: Commit**

```bash
git add src/core/ && git commit -m "feat: add core infrastructure (store, query, types, constants)"
```

---

### Task 0.4: 全局 Providers 与导航骨架

**参考 spec：** `02-navigation-and-routing.md`

**Files:**
- Create: `src/app/providers/AppProviders.tsx`
- Create: `src/app/providers/QueryProvider.tsx`
- Create: `src/app/navigation/RootNavigator.tsx`
- Create: `src/app/navigation/AuthNavigator.tsx`
- Create: `src/app/navigation/MainNavigator.tsx`
- Create: `src/app/navigation/TabNavigator.tsx`
- Create: `src/app/navigation/types.ts`
- Modify: `App.tsx`

- [x] **Step 1: 创建导航类型定义**

在 `types.ts` 中定义 `RootStackParamList`、`AuthStackParamList`、`MainStackParamList`、`TabParamList`。

- [x] **Step 2: 创建导航器**

按 `02-navigation-and-routing.md` 的导航层级实现：
- `RootNavigator`：Auth / Main 切换
- `AuthNavigator`：Login / Register / ForgotPassword / Onboarding
- `MainNavigator`：TabNavigator + Stack 页面
- `TabNavigator`：4 个 Tab（首页、饮食、数据、我的）

所有 Screen 先用占位组件（显示页面名称）。

- [x] **Step 3: 创建 Providers**

`AppProviders.tsx` 组装 QueryProvider + NavigationContainer。

- [x] **Step 4: 修改 App.tsx 入口**

引入 AppProviders + RootNavigator。

- [x] **Step 5: 验证导航可运行**

启动 app，确认可以看到 Tab 导航和占位页面。

- [x] **Step 6: Commit**

```bash
git add src/app/ App.tsx && git commit -m "feat: add navigation skeleton with placeholder screens"
```

---

## Phase 1: 共享组件层

**目标：** 实现所有 shared 组件，为后续页面开发提供基础。

**参考 spec：** `shared/20-shared-ui-components.md`、`shared/21-form-components.md`、`shared/22-chart-components.md`、`shared/23-feedback-components.md`

### Task 1.1: 基础 UI 组件

**Files:**
- Create: `src/shared/ui/Button/`
- Create: `src/shared/ui/Card/`
- Create: `src/shared/ui/Tag/`
- Create: `src/shared/ui/Avatar/`
- Create: `src/shared/ui/ProgressBar/`
- Create: `src/shared/ui/CircularProgress/`
- Create: `src/shared/layout/PageContainer/`
- Create: `src/shared/layout/SectionBlock/`

- [ ] **Step 1: 实现 Button 组件**（primary / secondary / text，3 种尺寸，loading 态）
- [ ] **Step 2: 实现 Card 组件**（白底、12px 圆角、shadow-card）
- [ ] **Step 3: 实现 Tag 组件**（4 种 variant、2 种 size）
- [ ] **Step 4: 实现 Avatar 组件**（图片 / 首字母默认头像）
- [ ] **Step 5: 实现 ProgressBar 组件**（线性进度条）
- [ ] **Step 6: 实现 CircularProgress 组件**（环形进度图）
- [ ] **Step 7: 实现 PageContainer 和 SectionBlock 布局组件**
- [ ] **Step 8: 创建统一导出 index.ts**
- [ ] **Step 9: Commit**

### Task 1.2: 业务 UI 组件

**Files:**
- Create: `src/shared/ui/MealCard/`
- Create: `src/shared/ui/DataRecordCard/`
- Create: `src/shared/ui/PlanCard/`
- Create: `src/shared/ui/AIInputBar/`

- [ ] **Step 1: 实现 MealCard**（empty / pending / recorded 三态）
- [ ] **Step 2: 实现 DataRecordCard**（6 种记录类型，三态）
- [ ] **Step 3: 实现 PlanCard**（进度条 + 状态标签）
- [ ] **Step 4: 实现 AIInputBar**（拍照 + 语音 + 文本输入 + 发送）
- [ ] **Step 5: Commit**

### Task 1.3: 表单组件

**参考 spec：** `shared/21-form-components.md`

**Files:**
- Create: `src/shared/forms/TextInput/`
- Create: `src/shared/forms/PasswordInput/`
- Create: `src/shared/forms/DatePicker/`
- Create: `src/shared/forms/Picker/`
- Create: `src/shared/forms/MultiSelectTags/`
- Create: `src/shared/forms/Slider/`
- Create: `src/shared/forms/Switch/`

- [ ] **Step 1-7: 逐个实现 7 个表单组件**（均兼容 React Hook Form 的 Controller）
- [ ] **Step 8: Commit**

### Task 1.4: 图表组件

**参考 spec：** `shared/22-chart-components.md`

**Files:**
- Create: `src/shared/charts/LineChart/`
- Create: `src/shared/charts/BarChart/`
- Create: `src/shared/charts/PieChart/`

- [ ] **Step 1-3: 逐个实现 3 个图表组件**（封装 react-native-chart-kit）
- [ ] **Step 4: Commit**

### Task 1.5: 反馈组件

**参考 spec：** `shared/23-feedback-components.md`

**Files:**
- Create: `src/shared/feedback/Toast/`
- Create: `src/shared/feedback/Modal/`
- Create: `src/shared/feedback/ConfirmDialog/`
- Create: `src/shared/feedback/BottomSheet/`
- Create: `src/shared/feedback/EmptyState/`
- Create: `src/shared/feedback/LoadingSpinner/`
- Create: `src/shared/feedback/Skeleton/`

- [ ] **Step 1-7: 逐个实现 7 个反馈组件**
- [ ] **Step 8: 在 AppProviders 中注册 Toast 和 ConfirmDialog 的全局 Provider**
- [ ] **Step 9: Commit**

---

## Phase 2: 认证模块

**目标：** 实现登录、注册、忘记密码、Onboarding 完整流程。

**参考 spec：** `modules/10-auth-module.md`
**参考 UI 文稿：** `ui-design/13-auth-and-onboarding.md`

### Task 2.1: Auth 类型、Store、Mock Service

**Files:**
- Create: `src/features/auth/types/auth.types.ts`
- Create: `src/features/auth/store/authStore.ts`
- Create: `src/features/auth/services/authService.ts`
- Create: `src/features/auth/mocks/authMocks.ts`

- [ ] **Step 1: 定义 Auth 类型**
- [ ] **Step 2: 实现 authStore**（Zustand）
- [ ] **Step 3: 实现 mock 数据和 authService**
- [ ] **Step 4: Commit**

### Task 2.2: 登录与注册页面

**Files:**
- Create: `src/features/auth/screens/LoginScreen.tsx`
- Create: `src/features/auth/screens/RegisterScreen.tsx`
- Create: `src/features/auth/screens/ForgotPasswordScreen.tsx`
- Create: `src/features/auth/hooks/useAuth.ts`

- [ ] **Step 1: 实现 useAuth hook**（封装登录/注册/忘记密码逻辑）
- [ ] **Step 2: 实现 LoginScreen**（邮箱 + 密码 + 登录按钮 + 跳转链接）
- [ ] **Step 3: 实现 RegisterScreen**（邮箱 + 密码 + 确认密码 + 注册按钮）
- [ ] **Step 4: 实现 ForgotPasswordScreen**（邮箱 + 发送按钮）
- [ ] **Step 5: 接入 AuthNavigator，验证登录流程**
- [ ] **Step 6: Commit**

### Task 2.3: Onboarding 引导页

**Files:**
- Create: `src/features/auth/screens/OnboardingScreen.tsx`
- Create: `src/features/auth/components/OnboardingStep.tsx`
- Create: `src/features/auth/components/OnboardingProgress.tsx`

- [ ] **Step 1: 实现 OnboardingProgress 进度条组件**
- [ ] **Step 2: 实现 OnboardingStep 单步容器组件**
- [ ] **Step 3: 实现 OnboardingScreen**（4 步表单：基础信息 → 健康目标 → 饮食偏好 → 疾病信息）
- [ ] **Step 4: 接入导航，验证完整 Auth 流程**（登录 → Onboarding → 首页）
- [ ] **Step 5: Commit**

---

## Phase 3: 首页模块

**目标：** 实现首页 Dashboard，展示今日健康概览。

**参考 spec：** `modules/11-home-module.md`
**参考 UI 文稿：** `ui-design/03-home-dashboard.md`

### Task 3.1: Home 类型、Store、Mock Service

**Files:**
- Create: `src/features/home/types/home.types.ts`
- Create: `src/features/home/store/homeStore.ts`
- Create: `src/features/home/services/homeService.ts`
- Create: `src/features/home/mocks/homeMocks.ts`

- [x] **Step 1-4: 类型 → Store → Mock → Service**
- [x] **Step 5: Commit**

### Task 3.2: 首页组件与页面

**Files:**
- Create: `src/features/home/components/HealthOverviewCard.tsx`
- Create: `src/features/home/components/QuickActionBar.tsx`
- Create: `src/features/home/components/AIInsightCard.tsx`
- Create: `src/features/home/components/PlanProgressCard.tsx`
- Create: `src/features/home/components/AuxiliaryRecordGrid.tsx`
- Create: `src/features/home/screens/HomeScreen.tsx`
- Create: `src/features/home/hooks/useHomeData.ts`

- [x] **Step 1: 实现 useHomeData hook**
- [x] **Step 2: 实现 HealthOverviewCard**（热量环形图 + 营养素进度条）
- [x] **Step 3: 实现 QuickActionBar**（记录饮食 / 记录体重 / 查看计划 / 更多）
- [x] **Step 4: 实现 AIInsightCard**（AI 建议卡片）
- [x] **Step 5: 实现 PlanProgressCard**（计划进度卡片）
- [x] **Step 6: 实现 AuxiliaryRecordGrid**（饮水 / 运动 / 睡眠小卡片）
- [x] **Step 7: 组装 HomeScreen**
- [x] **Step 8: 验证首页展示**
- [x] **Step 9: Commit**

---

## Phase 4: 饮食模块

**目标：** 实现饮食记录页和编辑页。

**参考 spec：** `modules/12-diet-module.md`
**参考 UI 文稿：** `ui-design/04-diet-record-page.md`、`ui-design/05-diet-edit-page.md`

### Task 4.1: Diet 类型、Store、Mock Service

- [x] **Step 1-4: 类型 → Store → Mock → Service**
- [x] **Step 5: Commit**

### Task 4.2: 饮食记录页

**Files:**
- Create: `src/features/diet/screens/DietRecordScreen.tsx`
- Create: `src/features/diet/components/DateSwitcher.tsx`
- Create: `src/features/diet/components/NutritionSummary.tsx`
- Create: `src/features/diet/components/MealCardList.tsx`
- Create: `src/features/diet/hooks/useDietData.ts`

- [x] **Step 1: 实现 DateSwitcher**（日期左右切换）
- [x] **Step 2: 实现 NutritionSummary**（今日营养汇总）
- [x] **Step 3: 实现 MealCardList**（早/午/晚/加餐卡片列表，复用 shared MealCard）
- [x] **Step 4: 组装 DietRecordScreen**
- [x] **Step 5: Commit**

### Task 4.3: 饮食编辑页

**Files:**
- Create: `src/features/diet/screens/DietEditScreen.tsx`
- Create: `src/features/diet/components/FoodSearchModal.tsx`
- Create: `src/features/diet/hooks/useFoodSearch.ts`

- [x] **Step 1: 实现 FoodSearchModal**（食物搜索弹窗）
- [x] **Step 2: 实现 DietEditScreen**（食物列表 + 添加/删除/修改份量）
- [x] **Step 3: 验证饮食记录 → 编辑完整流程**
- [x] **Step 4: Commit**

---

## Phase 5: 数据模块

**目标：** 实现数据页（6 个 Tab）、身体数据编辑页、数据分析页。

**参考 spec：** `modules/13-data-module.md`
**参考 UI 文稿：** `ui-design/06-data-page.md`、`ui-design/07-body-edit-page.md`、`ui-design/11-analysis-page.md`

### Task 5.1: Data 类型、Store、Mock Service

- [x] **Step 1-4: 类型 → Store → Mock → Service**
- [x] **Step 5: Commit**

### Task 5.2: 数据页

**Files:**
- Create: `src/features/data/screens/DataScreen.tsx`
- Create: `src/features/data/components/DataTabBar.tsx`
- Create: `src/features/data/components/TrendChart.tsx`
- Create: `src/features/data/components/DataRecordList.tsx`

- [x] **Step 1: 实现 DataTabBar**（6 个 Tab 横向滚动切换）
- [x] **Step 2: 实现 TrendChart**（趋势折线图 + 时间范围切换）
- [x] **Step 3: 实现 DataRecordList**（历史记录列表）
- [x] **Step 4: 组装 DataScreen**（Tab 切换 → 动态展示对应卡片和趋势）
- [x] **Step 5: Commit**

### Task 5.3: 身体数据编辑页

**Files:**
- Create: `src/features/data/screens/BodyEditScreen.tsx`

- [x] **Step 1: 实现 BodyEditScreen**（根据 recordType 动态渲染表单）
- [x] **Step 2: 验证数据页 → 编辑页完整流程**
- [x] **Step 3: Commit**

### Task 5.4: 数据分析页

**Files:**
- Create: `src/features/data/screens/AnalysisScreen.tsx`

- [x] **Step 1: 实现 AnalysisScreen**（热量趋势 + 营养分布 + 体重变化 + 计划达成 + AI 洞察）
- [x] **Step 2: Commit**

---

## Phase 6: 计划模块

**目标：** 实现计划列表、详情、对话式创建。

**参考 spec：** `modules/14-plan-module.md`
**参考 UI 文稿：** `ui-design/08-plan-list-page.md`、`ui-design/09-plan-detail-page.md`、`ui-design/10-plan-create-chat-page.md`

### Task 6.1: Plan 类型、Store、Mock Service

- [x] **Step 1-4: 类型 → Store → Mock → Service**
- [x] **Step 5: Commit**

### Task 6.2: 计划列表与详情页

- [x] **Step 1: 实现 PlanListScreen**（计划卡片列表 + 新建入口）
- [x] **Step 2: 实现 PlanDetailScreen**（计划概览 + 任务列表 + 进度图表）
- [x] **Step 3: Commit**

### Task 6.3: 计划创建对话页

- [x] **Step 1: 实现 ChatMessage 组件**（用户消息 / AI 消息 / 计划摘要卡片）
- [x] **Step 2: 实现 PlanCreateChatScreen**（多轮对话 → 生成计划）
- [x] **Step 3: 验证计划创建 → 列表 → 详情完整流程**
- [x] **Step 4: Commit**

---

## Phase 7: 个人中心模块

**目标：** 实现个人中心、编辑档案、设置页。

**参考 spec：** `modules/15-profile-module.md`
**参考 UI 文稿：** `ui-design/12-profile-and-settings.md`

### Task 7.1: Profile 类型、Store、Mock Service

- [x] **Step 1-4: 类型 → Store → Mock → Service**
- [x] **Step 5: Commit**

### Task 7.2: 个人中心页面

- [x] **Step 1: 实现 ProfileScreen**（头像 + 基本信息 + 功能入口列表）
- [x] **Step 2: 实现 EditProfileScreen**（编辑档案表单）
- [x] **Step 3: 实现 SettingsScreen**（交互模式切换 + 通知 + 退出登录）
- [x] **Step 4: Commit**

---

## Phase 8: AI 对话模块

**目标：** 实现 AI 全屏对话页和跨页面浮层。

**参考 spec：** `modules/16-ai-dialog-module.md`
**参考 UI 文稿：** `ui-design/14-ai-dialog-and-overlays.md`

### Task 8.1: AI 类型、Store、Mock Service

- [ ] **Step 1-4: 类型 → Store → Mock → Service**
- [ ] **Step 5: Commit**

### Task 8.2: AI 对话页面与浮层

- [ ] **Step 1: 实现 ChatMessageList 组件**（消息列表 + 自动滚动）
- [ ] **Step 2: 实现 ChatInput 组件**（文本 + 拍照 + 语音）
- [ ] **Step 3: 实现 AIDialogScreen**（全屏对话页）
- [ ] **Step 4: 实现 NutritionBottomSheet**（营养查询结果浮层）
- [ ] **Step 5: 实现 ConfirmDialog**（跨页面确认弹窗）
- [ ] **Step 6: Commit**

---

## Phase 9: 全局联调与收尾

**目标：** 串联所有模块，验证完整用户流程，修复问题。

### Task 9.1: 全局 AIInputBar 接入

- [ ] **Step 1: 在 MainNavigator 中全局挂载 AIInputBar**
- [ ] **Step 2: 实现 AIInputBar 的全局消息分发逻辑**（根据当前页面上下文路由到对应模块）
- [ ] **Step 3: Commit**

### Task 9.2: 完整流程验证

- [ ] **Step 1: 验证 Auth 流程**（注册 → Onboarding → 首页）
- [ ] **Step 2: 验证饮食流程**（首页快捷入口 → 饮食记录 → 编辑 → 返回）
- [ ] **Step 3: 验证数据流程**（数据页 Tab 切换 → 编辑 → 分析页）
- [ ] **Step 4: 验证计划流程**（创建计划 → 列表 → 详情）
- [ ] **Step 5: 验证个人中心**（查看 → 编辑 → 设置）
- [ ] **Step 6: 验证 AI 对话**（全屏对话 → 浮层 → 确认弹窗）
- [ ] **Step 7: 修复发现的问题**
- [ ] **Step 8: Final Commit**

```bash
git add -A && git commit -m "feat: complete health-agent frontend v1 with mock data"
```

---

## 进度追踪

| Phase | 名称 | 预估 Task 数 | 状态 |
|-------|------|-------------|------|
| 0 | 项目初始化与基础设施 | 4 | ✅ 已完成 |
| 1 | 共享组件层 | 5 | ✅ 已完成 |
| 2 | 认证模块 | 3 | ✅ 已完成 |
| 3 | 首页模块 | 2 | ✅ 已完成 |
| 4 | 饮食模块 | 3 | ✅ 已完成 |
| 5 | 数据模块 | 3 | ✅ 已完成 |
| 6 | 计划模块 | 3 | ✅ 已完成 |
| 7 | 个人中心模块 | 2 | ✅ 已完成 |
| 8 | AI 对话模块 | 3 | 🔄 进行中 |
| 9 | 全局联调与收尾 | 2 | ⬜ 未开始 |
| **总计** | | **30 Tasks** | |
