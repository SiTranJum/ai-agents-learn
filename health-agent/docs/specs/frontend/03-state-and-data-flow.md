# 状态管理与数据流

> 定义应用的状态管理策略、数据流向、mock 数据组织方式。
> 实现依据：`02-app-framework.md`、各模块 PRD。

---

## 1. 状态分层

### 1.1 全局状态（Zustand globalStore）

存储跨模块共享的数据：

```typescript
interface GlobalState {
  // 用户认证
  isAuthenticated: boolean;
  token: string | null;

  // 用户档案
  userProfile: UserProfile | null;

  // 交互模式
  interactionMode: 'efficiency' | 'confirm' | 'learn';

  // 当前活跃计划
  activePlanId: string | null;

  // Actions
  setToken: (token: string | null) => void;
  setUserProfile: (profile: UserProfile) => void;
  setInteractionMode: (mode: InteractionMode) => void;
  logout: () => void;
}
```

### 1.2 模块状态（Zustand 模块 store）

每个模块可以有自己的 store，存储模块内状态：

| 模块 | Store | 内容 |
|------|-------|------|
| diet | dietStore | 当前选中日期、当前编辑的餐次 |
| data | dataStore | 当前选中的 Tab、当前时间范围 |
| plan | planStore | 当前对话消息列表 |
| ai | aiStore | AI 对话历史、输入状态 |

### 1.3 服务端状态（TanStack Query）

所有从"服务端"获取的数据（V1 阶段为 mock 数据）通过 TanStack Query 管理：

| 数据 | Query Key | 说明 |
|------|-----------|------|
| 今日饮食 | `['diet', date]` | 按日期查询饮食记录 |
| 今日身体数据 | `['bodyData', date, type]` | 按日期和类型查询 |
| 体重趋势 | `['weightTrend', range]` | 按时间范围查询 |
| 计划列表 | `['plans']` | 所有计划 |
| 计划详情 | `['plan', planId]` | 单个计划 |
| 用户档案 | `['userProfile']` | 用户信息 |
| 首页数据 | `['homeData', date]` | 首页聚合数据 |
| 分析数据 | `['analysis', range]` | 分析页数据 |

### 1.4 表单状态（React Hook Form）

表单数据通过 React Hook Form 管理，不进入 Zustand：

| 表单 | 使用场景 |
|------|---------|
| 登录表单 | LoginScreen |
| 注册表单 | RegisterScreen |
| Onboarding 表单 | OnboardingScreen |
| 饮食编辑表单 | DietEditScreen |
| 身体数据编辑表单 | BodyEditScreen |
| 编辑档案表单 | EditProfileScreen |

### 1.5 UI 状态（组件内 useState）

纯 UI 状态留在组件内部：
- Modal 开关
- 下拉展开/收起
- 动画状态
- 输入框焦点

---

## 2. 数据流向

### 2.1 读取数据流

```
Screen
  ↓ useQuery(queryKey)
TanStack Query
  ↓ queryFn()
Service 层
  ↓ V1: 返回 mock 数据 / 未来: 调用 API
Mock 数据 / API
```

### 2.2 写入数据流

```
Screen（用户操作）
  ↓ useMutation()
TanStack Query Mutation
  ↓ mutationFn()
Service 层
  ↓ V1: 更新 mock 数据 / 未来: 调用 API
Mock 数据 / API
  ↓ onSuccess
invalidateQueries() → 自动刷新相关数据
```

### 2.3 跨模块数据流

```
模块 A（触发操作）
  ↓ 方式 1: navigation.navigate(Screen, params)
模块 B（接收参数）

  ↓ 方式 2: globalStore.setState()
模块 B（useGlobalStore 订阅）

  ↓ 方式 3: queryClient.invalidateQueries()
TanStack Query 自动刷新相关模块的数据
```
