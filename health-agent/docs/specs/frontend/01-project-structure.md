# 项目目录结构

> 本文档定义 Expo 项目的完整目录结构、每个目录的职责、文件命名规范和模块边界规则。

---

## 1. 完整目录树

```
health-agent-app/
├── app.json                          # Expo 配置
├── package.json                      # 依赖管理
├── tsconfig.json                     # TypeScript 配置
├── babel.config.js                   # Babel 配置
├── metro.config.js                   # Metro 打包配置
├── .env.example                      # 环境变量示例
├── .gitignore
├── README.md
│
├── src/
│   ├── app/                          # 应用入口和全局配置
│   │   ├── App.tsx                   # Expo 入口组件
│   │   ├── providers/                # 全局 Provider
│   │   │   ├── AppProviders.tsx      # 组装所有 Provider
│   │   │   ├── ThemeProvider.tsx     # 主题 Provider（预留）
│   │   │   └── QueryProvider.tsx     # TanStack Query Provider
│   │   ├── navigation/               # 导航配置
│   │   │   ├── RootNavigator.tsx     # 根导航容器
│   │   │   ├── AuthNavigator.tsx     # 登录注册导航
│   │   │   ├── MainNavigator.tsx     # 主应用导航
│   │   │   ├── TabNavigator.tsx      # 底部 Tab 导航
│   │   │   └── types.ts              # 导航类型定义
│   │   └── styles/                   # 全局样式
│   │       ├── theme.ts              # 主题配置
│   │       ├── tokens.ts             # Design Tokens
│   │       └── globalStyles.ts       # 全局样式
│   │
│   ├── core/                         # 核心基础设施
│   │   ├── api/                      # API 客户端
│   │   │   ├── client.ts             # API client 基础封装
│   │   │   └── types.ts              # API 通用类型
│   │   ├── query/                    # TanStack Query 配置
│   │   │   ├── queryClient.ts        # Query Client 配置
│   │   │   └── hooks.ts              # 通用 query hooks
│   │   ├── store/                    # 全局状态管理
│   │   │   ├── createStore.ts        # Zustand store 工具
│   │   │   └── globalStore.ts        # 全局状态（用户信息、token）
│   │   ├── forms/                    # 表单基础设施
│   │   │   ├── schemas/              # Zod schemas
│   │   │   └── utils.ts              # 表单工具函数
│   │   ├── permissions/              # 权限管理
│   │   │   ├── camera.ts
│   │   │   └── notifications.ts
│   │   ├── constants/                # 常量
│   │   │   ├── config.ts
│   │   │   └── routes.ts
│   │   └── types/                    # 通用类型
│   │       ├── common.ts
│   │       └── models.ts
│   │
│   ├── features/                     # 功能模块（按业务划分）
│   │   │
│   │   ├── auth/                     # 认证模块
│   │   │   ├── screens/
│   │   │   │   ├── LoginScreen.tsx
│   │   │   │   ├── RegisterScreen.tsx
│   │   │   │   ├── ForgotPasswordScreen.tsx
│   │   │   │   └── OnboardingScreen.tsx
│   │   │   ├── components/
│   │   │   │   ├── OnboardingStep.tsx
│   │   │   │   └── OnboardingProgress.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useAuth.ts
│   │   │   ├── store/
│   │   │   │   └── authStore.ts
│   │   │   ├── services/
│   │   │   │   └── authService.ts
│   │   │   ├── mocks/
│   │   │   │   └── authMocks.ts
│   │   │   ├── types/
│   │   │   │   └── auth.types.ts
│   │   │   └── index.ts              # 只导出 screens
│   │   │
│   │   ├── home/                     # 首页模块
│   │   │   ├── screens/
│   │   │   │   └── HomeScreen.tsx
│   │   │   ├── components/
│   │   │   │   ├── HealthOverviewCard.tsx
│   │   │   │   ├── QuickActionBar.tsx
│   │   │   │   ├── AIInsightCard.tsx
│   │   │   │   ├── PlanProgressCard.tsx
│   │   │   │   └── AuxiliaryRecordGrid.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useHomeData.ts
│   │   │   ├── store/
│   │   │   │   └── homeStore.ts
│   │   │   ├── services/
│   │   │   │   └── homeService.ts
│   │   │   ├── mocks/
│   │   │   │   └── homeMocks.ts
│   │   │   ├── types/
│   │   │   │   └── home.types.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── diet/                     # 饮食模块
│   │   │   ├── screens/
│   │   │   │   ├── DietRecordScreen.tsx
│   │   │   │   └── DietEditScreen.tsx
│   │   │   ├── components/
│   │   │   │   ├── DateSwitcher.tsx
│   │   │   │   ├── NutritionSummary.tsx
│   │   │   │   ├── MealCardList.tsx
│   │   │   │   └── FoodSearchModal.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useDietData.ts
│   │   │   │   └── useFoodSearch.ts
│   │   │   ├── store/
│   │   │   │   └── dietStore.ts
│   │   │   ├── services/
│   │   │   │   ├── dietService.ts
│   │   │   │   └── foodService.ts
│   │   │   ├── mocks/
│   │   │   │   ├── dietMocks.ts
│   │   │   │   └── foodMocks.ts
│   │   │   ├── types/
│   │   │   │   └── diet.types.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── data/                     # 数据模块
│   │   │   ├── screens/
│   │   │   │   ├── DataScreen.tsx
│   │   │   │   ├── BodyEditScreen.tsx
│   │   │   │   └── AnalysisScreen.tsx
│   │   │   ├── components/
│   │   │   │   ├── TrendChart.tsx
│   │   │   │   ├── DataRecordList.tsx
│   │   │   │   └── DataTabBar.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useDataTrend.ts
│   │   │   ├── store/
│   │   │   │   └── dataStore.ts
│   │   │   ├── services/
│   │   │   │   └── dataService.ts
│   │   │   ├── mocks/
│   │   │   │   └── dataMocks.ts
│   │   │   ├── types/
│   │   │   │   └── data.types.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── plan/                     # 计划模块
│   │   │   ├── screens/
│   │   │   │   ├── PlanListScreen.tsx
│   │   │   │   ├── PlanDetailScreen.tsx
│   │   │   │   └── PlanCreateChatScreen.tsx
│   │   │   ├── components/
│   │   │   │   ├── PlanCardList.tsx
│   │   │   │   ├── PlanProgressChart.tsx
│   │   │   │   ├── TaskList.tsx
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   └── PlanSummaryCard.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── usePlanData.ts
│   │   │   │   └── usePlanChat.ts
│   │   │   ├── store/
│   │   │   │   └── planStore.ts
│   │   │   ├── services/
│   │   │   │   └── planService.ts
│   │   │   ├── mocks/
│   │   │   │   └── planMocks.ts
│   │   │   ├── types/
│   │   │   │   └── plan.types.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── profile/                  # 个人中心模块
│   │   │   ├── screens/
│   │   │   │   ├── ProfileScreen.tsx
│   │   │   │   ├── EditProfileScreen.tsx
│   │   │   │   └── SettingsScreen.tsx
│   │   │   ├── components/
│   │   │   │   ├── ProfileHeader.tsx
│   │   │   │   ├── ProfileInfoCard.tsx
│   │   │   │   └── SettingsList.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useProfile.ts
│   │   │   ├── store/
│   │   │   │   └── profileStore.ts
│   │   │   ├── services/
│   │   │   │   └── profileService.ts
│   │   │   ├── mocks/
│   │   │   │   └── profileMocks.ts
│   │   │   ├── types/
│   │   │   │   └── profile.types.ts
│   │   │   └── index.ts
│   │   │
│   │   └── ai/                       # AI 对话模块
│   │       ├── screens/
│   │       │   └── AIDialogScreen.tsx
│   │       ├── components/
│   │       │   ├── ChatMessageList.tsx
│   │       │   ├── ChatInput.tsx
│   │       │   ├── ConfirmDialog.tsx
│   │       │   └── NutritionBottomSheet.tsx
│   │       ├── hooks/
│   │       │   └── useAIChat.ts
│   │       ├── store/
│   │       │   └── aiStore.ts
│   │       ├── services/
│   │       │   └── aiService.ts
│   │       ├── mocks/
│   │       │   └── aiMocks.ts
│   │       ├── types/
│   │       │   └── ai.types.ts
│   │       └── index.ts
│   │
│   ├── shared/                       # 共享组件和工具
│   │   │
│   │   ├── ui/                       # 通用 UI 组件
│   │   │   ├── Button/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Button.styles.ts
│   │   │   │   ├── Button.types.ts
│   │   │   │   └── index.ts
│   │   │   ├── Card/
│   │   │   ├── Tag/
│   │   │   ├── Avatar/
│   │   │   ├── ProgressBar/
│   │   │   ├── CircularProgress/
│   │   │   ├── MealCard/
│   │   │   ├── DataRecordCard/
│   │   │   ├── PlanCard/
│   │   │   ├── AIInputBar/
│   │   │   └── index.ts              # 统一导出
│   │   │
│   │   ├── layout/                   # 布局组件
│   │   │   ├── PageContainer/
│   │   │   ├── SectionBlock/
│   │   │   └── index.ts
│   │   │
│   │   ├── feedback/                 # 反馈组件
│   │   │   ├── Toast/
│   │   │   ├── Modal/
│   │   │   ├── ConfirmDialog/
│   │   │   ├── BottomSheet/
│   │   │   ├── EmptyState/
│   │   │   ├── LoadingSpinner/
│   │   │   ├── Skeleton/
│   │   │   └── index.ts
│   │   │
│   │   ├── icons/                    # 图标封装
│   │   │   ├── IconWrapper.tsx
│   │   │   ├── iconMap.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── charts/                   # 图表组件
│   │   │   ├── LineChart/
│   │   │   ├── BarChart/
│   │   │   ├── PieChart/
│   │   │   └── index.ts
│   │   │
│   │   ├── forms/                    # 表单组件
│   │   │   ├── TextInput/
│   │   │   ├── PasswordInput/
│   │   │   ├── DatePicker/
│   │   │   ├── Picker/
│   │   │   ├── MultiSelectTags/
│   │   │   ├── Slider/
│   │   │   ├── Switch/
│   │   │   └── index.ts
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── date.ts
│   │       ├── format.ts
│   │       ├── validation.ts
│   │       └── index.ts
│   │
│   └── assets/                       # 静态资源
│       ├── images/
│       │   ├── logo/
│       │   │   └── app-icon-1024.png
│       │   ├── illustrations/
│       │   │   ├── home-person.png
│       │   │   ├── water-cup.png
│       │   │   ├── exercise.png
│       │   │   ├── sleep.png
│       │   │   ├── empty-diet.png
│       │   │   ├── empty-plan.png
│       │   │   ├── empty-data.png
│       │   │   └── login-hero.png
│       │   └── mockups/
│       │       └── hero-phone-mockup.png
│       └── fonts/
│           └── (自定义字体，如需要)
│
└── __tests__/                        # 测试（V1 可选）
    ├── mocks/
    ├── fixtures/
    └── utils/
```

---

## 2. 目录职责说明

### 2.1 顶层目录

| 目录 | 职责 |
|------|------|
| `src/app/` | 应用入口、全局 Provider、导航配置、全局样式 |
| `src/core/` | 核心基础设施（API、状态、表单、权限、常量、类型） |
| `src/features/` | 功能模块，按业务划分，每个模块自包含 |
| `src/shared/` | 跨模块共享的组件和工具 |
| `src/assets/` | 静态资源（图片、字体） |

### 2.2 功能模块内部结构

每个 `features/` 下的模块必须遵循统一结构：

| 子目录 | 职责 | 必需 |
|--------|------|------|
| `screens/` | 页面组件 | ✅ |
| `components/` | 模块内私有组件 | 可选 |
| `hooks/` | 模块内自定义 hooks | 可选 |
| `store/` | 模块级状态管理（Zustand） | 可选 |
| `services/` | 数据服务层（mock 或 API） | ✅ |
| `mocks/` | mock 数据 | ✅ |
| `types/` | 模块内类型定义 | ✅ |
| `index.ts` | 模块导出（只导出 screens） | ✅ |

### 2.3 共享组件结构

`shared/` 下的组件按类型分类：

| 子目录 | 内容 |
|--------|------|
| `ui/` | 通用 UI 组件（Button、Card、Tag 等） |
| `layout/` | 布局组件（PageContainer、SectionBlock） |
| `feedback/` | 反馈组件（Toast、Modal、EmptyState） |
| `icons/` | 图标封装 |
| `charts/` | 图表组件 |
| `forms/` | 表单组件 |
| `utils/` | 工具函数 |

---

## 3. 文件命名规范

### 3.1 组件文件

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| Screen | `{Name}Screen.tsx` | `HomeScreen.tsx` |
| Component | `{Name}.tsx` | `Button.tsx`, `MealCard.tsx` |
| Styles | `{Name}.styles.ts` | `Button.styles.ts` |
| Types | `{Name}.types.ts` | `Button.types.ts` |
| Hooks | `use{Name}.ts` | `useAuth.ts`, `useHomeData.ts` |
| Store | `{name}Store.ts` | `authStore.ts`, `globalStore.ts` |
| Service | `{name}Service.ts` | `authService.ts`, `dietService.ts` |
| Mocks | `{name}Mocks.ts` | `authMocks.ts`, `dietMocks.ts` |
| Types | `{name}.types.ts` | `auth.types.ts`, `diet.types.ts` |

### 3.2 目录命名

- 功能模块目录：小写，单数形式（`auth`, `home`, `diet`）
- 组件目录：PascalCase（`Button`, `MealCard`）
- 工具目录：小写（`utils`, `hooks`, `services`）

---

## 4. 模块边界规则

### 4.1 模块自治原则

**规则 1：模块内组件不对外暴露**
- `features/{module}/components/` 下的组件只能在该模块内使用
- `index.ts` 只导出 `screens/`，不导出 `components/`

**规则 2：共享组件必须被 2+ 模块使用**
- 只有被至少 2 个模块使用的组件才能放入 `shared/`
- 单模块使用的组件必须留在模块内

**规则 3：模块间通过导航和全局 store 通信**
- 模块间跳转通过 React Navigation 的 `navigation.navigate()`
- 模块间数据共享通过 `core/store/globalStore.ts`
- 禁止模块间直接 import 对方的 components 或 hooks

### 4.2 依赖方向

```
features/ → shared/ → core/ → app/
  ↓          ↓         ↓
禁止反向依赖
```

- `features/` 可以依赖 `shared/` 和 `core/`
- `shared/` 可以依赖 `core/`
- `core/` 不依赖任何业务模块
- 禁止循环依赖

### 4.3 什么能进 shared/

**✅ 可以进 shared/**
- 被 2+ 模块使用的 UI 组件（Button、Card、MealCard）
- 被 2+ 模块使用的布局组件（PageContainer）
- 被 2+ 模块使用的反馈组件（Toast、Modal）
- 通用工具函数（date、format、validation）

**❌ 不能进 shared/**
- 只被 1 个模块使用的组件
- 包含业务逻辑的组件
- 与特定模块强耦合的组件

---

## 5. 导入路径规范

### 5.1 路径别名配置

在 `tsconfig.json` 中配置：

```json
{
  "compilerOptions": {
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

### 5.2 导入示例

```typescript
// ✅ 正确：使用路径别名
import { Button } from '@shared/ui';
import { useAuth } from '@features/auth/hooks/useAuth';
import { globalStore } from '@core/store/globalStore';
import { tokens } from '@app/styles/tokens';

// ❌ 错误：相对路径过长
import { Button } from '../../../shared/ui/Button';
```

---

## 6. index.ts 导出规范

### 6.1 模块 index.ts

每个 `features/{module}/index.ts` 只导出 screens：

```typescript
// features/auth/index.ts
export { LoginScreen } from './screens/LoginScreen';
export { RegisterScreen } from './screens/RegisterScreen';
export { ForgotPasswordScreen } from './screens/ForgotPasswordScreen';
export { OnboardingScreen } from './screens/OnboardingScreen';
```

### 6.2 共享组件 index.ts

`shared/ui/index.ts` 统一导出所有 UI 组件：

```typescript
// shared/ui/index.ts
export * from './Button';
export * from './Card';
export * from './Tag';
export * from './Avatar';
export * from './ProgressBar';
export * from './MealCard';
// ...
```

---

## 7. 特殊说明

### 7.1 mock 数据组织

- 每个模块的 `mocks/` 目录包含该模块所有 mock 数据
- mock 数据结构与未来 API 接口一致
- mock 数据通过 services 层封装，不直接在组件中使用

### 7.2 类型定义组织

- 模块内类型放在 `features/{module}/types/`
- 跨模块通用类型放在 `core/types/`
- 组件 props 类型放在组件同级的 `.types.ts` 文件

### 7.3 样式文件组织

- 组件样式放在组件同级的 `.styles.ts` 文件
- 使用 `StyleSheet.create()` 创建样式
- 样式必须引用 Design Tokens，禁止硬编码

---

## 8. 检查清单

在创建新模块或组件时，检查以下事项：

- [ ] 目录结构符合规范
- [ ] 文件命名符合规范
- [ ] 模块边界清晰，无循环依赖
- [ ] 共享组件确实被 2+ 模块使用
- [ ] 使用路径别名而非相对路径
- [ ] index.ts 只导出必要内容
- [ ] 类型定义完整
- [ ] 样式分离到 .styles.ts
- [ ] mock 数据完整
