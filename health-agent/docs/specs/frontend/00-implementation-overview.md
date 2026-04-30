# 前端实现 Specs 总览

> 本文档是前端实现的总纲，所有 specs 文档的入口。
> 目标读者：AI（Claude），用于产出技术方案和直接开发。

---

## 1. 实现依据

### 1.1 产品文档（PRD）
- `health-agent/docs/prd/v1/00-overview.md` — V1 内测版总览
- `health-agent/docs/prd/v1/01-user-system.md` — 用户体系
- `health-agent/docs/prd/v1/02-app-framework.md` — 应用框架
- `health-agent/docs/prd/v1/03-diet-recording.md` — 饮食记录
- `health-agent/docs/prd/v1/04-body-tracking.md` — 身体数据追踪
- `health-agent/docs/prd/v1/05-ai-memory.md` — AI 记忆系统
- `health-agent/docs/prd/v1/06-rag-knowledge.md` — RAG 知识库
- `health-agent/docs/prd/v1/07-plan-system.md` — 计划系统
- `health-agent/docs/prd/v1/08-ai-suggestion.md` — AI 建议系统
- `health-agent/docs/prd/v1/09-data-analysis.md` — 数据分析

### 1.2 UI 设计文稿（核心实现依据）
- `health-agent/docs/prd/v1/ui-design/00-ui-overview.md` — UI 总览
- `health-agent/docs/prd/v1/ui-design/01-design-system.md` — 设计系统（Design Tokens）
- `health-agent/docs/prd/v1/ui-design/02-components.md` — 全局组件规范
- `health-agent/docs/prd/v1/ui-design/03-home-dashboard.md` — 首页 Dashboard
- `health-agent/docs/prd/v1/ui-design/04-diet-record-page.md` — 饮食记录页
- `health-agent/docs/prd/v1/ui-design/05-diet-edit-page.md` — 饮食编辑页
- `health-agent/docs/prd/v1/ui-design/06-data-page.md` — 数据页
- `health-agent/docs/prd/v1/ui-design/07-body-edit-page.md` — 身体数据编辑页
- `health-agent/docs/prd/v1/ui-design/08-plan-list-page.md` — 计划列表页
- `health-agent/docs/prd/v1/ui-design/09-plan-detail-page.md` — 计划详情页
- `health-agent/docs/prd/v1/ui-design/10-plan-create-chat-page.md` — 计划创建对话页
- `health-agent/docs/prd/v1/ui-design/11-analysis-page.md` — 数据分析页
- `health-agent/docs/prd/v1/ui-design/12-profile-and-settings.md` — 个人中心与设置
- `health-agent/docs/prd/v1/ui-design/13-auth-and-onboarding.md` — 登录注册与引导
- `health-agent/docs/prd/v1/ui-design/14-ai-dialog-and-overlays.md` — AI 对话与浮层
- `health-agent/docs/prd/v1/ui-design/16-asset-prompts.md` — 素材生成提示词

### 1.3 素材资源
- 素材图由用户提供，对应 `16-asset-prompts.md` 中描述的图片
- 放置在 `src/assets/images/` 目录下
- 没有完整的 Figma/Sketch 视觉稿，以 UI 设计文稿中的 ASCII 线框图、组件树、样式描述为准

---

## 2. 技术栈

| 类别 | 选型 | 版本要求 | 说明 |
|------|------|---------|------|
| 框架 | React Native (Expo) | SDK 52+ | 跨平台移动端 |
| 语言 | TypeScript | 5.x | 严格模式 |
| 导航 | React Navigation v7 | 7.x | Stack + Bottom Tabs |
| 状态管理 | Zustand | 5.x | 轻量、按模块分 store |
| 服务端状态 | TanStack Query | 5.x | 数据获取、缓存、mock |
| 表单 | React Hook Form + Zod | RHF 7.x, Zod 3.x | 表单状态 + 校验 |
| 图表 | react-native-chart-kit 或 victory-native | 最新稳定版 | 折线图、柱状图、环形图 |
| 图标 | @expo/vector-icons (Feather) | Expo 内置 | 线性图标，1.5px 线宽 |
| 动画 | react-native-reanimated | 3.x | 页面切换、卡片动效 |
| 手势 | react-native-gesture-handler | 2.x | 滑动、拖拽 |
| 底部弹层 | @gorhom/bottom-sheet | 5.x | BottomSheet 组件 |
| 日期处理 | date-fns | 3.x | 日期格式化、计算 |
| 安全存储 | expo-secure-store | Expo 内置 | Token 存储 |
| 相机 | expo-camera | Expo 内置 | 拍照识别 |
| 图片选择 | expo-image-picker | Expo 内置 | 相册选择 |

---

## 3. 核心原则

### 3.1 UI 文稿为准
- **没有完整视觉稿**，所有页面实现以 UI 设计文稿（`ui-design/*.md`）为唯一依据
- 文稿中的 ASCII 线框图定义页面结构
- 文稿中的组件树定义组件层级
- 文稿中的样式描述定义视觉表现
- 文稿中的交互说明定义行为逻辑
- 素材图（`16-asset-prompts.md`）只是补充，不替代文稿

### 3.2 Mock-First 开发
- 前端独立开发，不依赖后端 API
- 所有数据通过 mock 服务提供
- mock 数据结构与未来 API 接口一致
- 每个模块的 `mocks/` 目录包含该模块所有 mock 数据
- 使用 TanStack Query 的 queryFn 封装 mock，未来替换为真实 API 时只需改 queryFn

### 3.3 模块自治
- 每个 feature 模块内部自包含（screens、components、hooks、store、services、mocks、types）
- 模块间通过导航参数和全局 store 通信
- 共享组件必须被 2 个以上模块使用才能放入 `shared/`
- 模块内组件不对外暴露，通过 `index.ts` 只导出 screens

### 3.4 类型安全
- 所有 props、state、API 返回值必须有 TypeScript 类型定义
- 导航参数必须类型安全（React Navigation 的 ParamList）
- Zod schema 与 TypeScript 类型保持同步
- 禁止使用 `any`

### 3.5 样式规范
- Design Tokens 统一定义在 `src/app/styles/tokens.ts`
- 组件样式使用 StyleSheet.create()，放在 `.styles.ts` 文件中
- 禁止内联样式（动态计算的样式除外）
- 颜色、字体、间距必须引用 tokens，禁止硬编码

---

## 4. 页面范围

### 4.1 V1 前端页面清单

| 页面 ID | 页面名称 | 所属模块 | UI 文稿 |
|---------|---------|---------|---------|
| P01 | 首页 Dashboard | home | `03-home-dashboard.md` |
| P02 | 饮食记录页 | diet | `04-diet-record-page.md` |
| P03 | 饮食编辑页 | diet | `05-diet-edit-page.md` |
| P04 | 数据页 | data | `06-data-page.md` |
| P05 | 身体数据编辑页 | data | `07-body-edit-page.md` |
| P06 | 计划列表页 | plan | `08-plan-list-page.md` |
| P07 | 计划详情页 | plan | `09-plan-detail-page.md` |
| P08 | 计划创建对话页 | plan | `10-plan-create-chat-page.md` |
| P09 | 数据分析页 | data | `11-analysis-page.md` |
| P10 | 个人中心页 | profile | `12-profile-and-settings.md` |
| P11 | 编辑档案页 | profile | `12-profile-and-settings.md` |
| P12 | 设置页 | profile | `12-profile-and-settings.md` |
| P13 | 登录页 | auth | `13-auth-and-onboarding.md` |
| P14 | 注册页 | auth | `13-auth-and-onboarding.md` |
| P15 | 忘记密码页 | auth | `13-auth-and-onboarding.md` |
| P16 | Onboarding 引导页 | auth | `13-auth-and-onboarding.md` |
| P17 | AI 全屏对话页 | ai | `14-ai-dialog-and-overlays.md` |

### 4.2 全局浮层/弹窗

| 浮层 ID | 名称 | UI 文稿 |
|---------|------|---------|
| O01 | 营养查询结果浮层（BottomSheet） | `14-ai-dialog-and-overlays.md` |
| O02 | 确认对话框 | `02-components.md` |
| O03 | Toast 提示 | `02-components.md` |
| O04 | 食物搜索 Modal | `05-diet-edit-page.md` |

### 4.3 不包含的页面
- 官网（`15-official-website.md`）— 不在移动端范围内

---

## 5. Specs 文档索引

### 架构总规
| 文件 | 内容 |
|------|------|
| `00-implementation-overview.md` | 本文档，总览 |
| `01-project-structure.md` | 项目目录结构详解 |
| `02-navigation-and-routing.md` | 导航结构、路由配置 |
| `03-state-and-data-flow.md` | 状态管理、数据流、mock 策略 |
| `04-design-system-mapping.md` | Design Tokens 到代码的映射 |
| `05-asset-management.md` | 素材组织、图标、插画、字体 |

### 功能模块
| 文件 | 内容 |
|------|------|
| `modules/10-auth-module.md` | 登录、注册、Onboarding |
| `modules/11-home-module.md` | 首页 Dashboard |
| `modules/12-diet-module.md` | 饮食记录、编辑 |
| `modules/13-data-module.md` | 数据页、身体数据编辑、数据分析 |
| `modules/14-plan-module.md` | 计划列表、详情、创建 |
| `modules/15-profile-module.md` | 个人中心、设置 |
| `modules/16-ai-dialog-module.md` | AI 对话、浮层 |

### 共享能力
| 文件 | 内容 |
|------|------|
| `shared/20-shared-ui-components.md` | 通用 UI 组件规范 |
| `shared/21-form-components.md` | 表单组件规范 |
| `shared/22-chart-components.md` | 图表组件规范 |
| `shared/23-feedback-components.md` | Toast、Modal、EmptyState |

---

## 6. 开发目标

### 6.1 V1 前端目标
- 高保真前端实现，mock 数据驱动
- 所有页面可交互、可导航
- 页面状态完整（空态、有数据态、待确认态）
- 动效和过渡自然流畅
- 代码结构清晰，模块边界明确

### 6.2 质量标准
- TypeScript 严格模式，零 `any`
- 所有组件有明确的 props 类型
- 样式全部引用 Design Tokens
- mock 数据覆盖所有页面状态
- 导航类型安全

### 6.3 后续对接
- mock 数据层设计为可替换结构
- API client 预留在 `src/core/api/`
- 认证 token 管理预留在 `src/core/store/globalStore.ts`
- 后端 API 就绪后，只需替换 services 层的实现
