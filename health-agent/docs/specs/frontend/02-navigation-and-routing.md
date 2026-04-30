# 导航与路由

> 定义应用的导航层级、路由配置、页面跳转映射和导航类型。
> 实现依据：`02-app-framework.md`、各页面 UI 设计文稿。

---

## 1. 导航层级

```
RootNavigator
├── AuthNavigator (Stack)
│   ├── Login                    → P13 登录页
│   ├── Register                 → P14 注册页
│   ├── ForgotPassword           → P15 忘记密码页
│   └── Onboarding               → P16 引导页
│
└── MainNavigator (Stack)
    ├── TabNavigator (Bottom Tabs)
    │   ├── HomeTab               → P01 首页 Dashboard
    │   ├── DietTab               → P02 饮食记录页
    │   ├── DataTab               → P04 数据页
    │   └── ProfileTab            → P10 个人中心页
    │
    ├── DietEdit                  → P03 饮食编辑页
    ├── BodyEdit                  → P05 身体数据编辑页
    ├── PlanList                  → P06 计划列表页
    ├── PlanDetail                → P07 计划详情页
    ├── PlanCreateChat            → P08 计划创建对话页
    ├── Analysis                  → P09 数据分析页
    ├── EditProfile               → P11 编辑档案页
    ├── Settings                  → P12 设置页
    └── AIDialog                  → P17 AI 全屏对话页
```

---

## 2. 导航类型定义

### 2.1 RootStackParamList

```typescript
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
};
```

### 2.2 AuthStackParamList

```typescript
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  Onboarding: undefined;
};
```

### 2.3 MainStackParamList

```typescript
export type MainStackParamList = {
  Tabs: undefined;
  DietEdit: { mealType: MealType; date: string; recordId?: string };
  BodyEdit: { recordType: BodyRecordType; recordId?: string };
  PlanList: undefined;
  PlanDetail: { planId: string };
  PlanCreateChat: undefined;
  Analysis: undefined;
  EditProfile: undefined;
  Settings: undefined;
  AIDialog: { initialMessage?: string };
};
```

### 2.4 TabParamList

```typescript
export type TabParamList = {
  HomeTab: undefined;
  DietTab: { date?: string };
  DataTab: { tab?: DataTabType };
  ProfileTab: undefined;
};
```

### 2.5 辅助类型

```typescript
export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

export type BodyRecordType = 'weight' | 'measurement' | 'sleep' | 'exercise' | 'water' | 'bowel';

export type DataTabType = 'weight' | 'measurement' | 'sleep' | 'exercise' | 'water' | 'bowel';
```

---

## 3. Bottom Tabs 配置

### 3.1 Tab 结构

| Tab | 图标 (Feather) | 标签 | 对应页面 |
|-----|---------------|------|---------|
| HomeTab | `home` | 首页 | HomeScreen |
| DietTab | `coffee` | 饮食 | DietRecordScreen |
| DataTab | `bar-chart-2` | 数据 | DataScreen |
| ProfileTab | `user` | 我的 | ProfileScreen |

### 3.2 Tab 样式

参考 `02-components.md` 底部 Tab 导航规范：
- 高度：60px（不含底部安全区）
- 图标：24×24px，上下结构
- 文字：12px Medium
- 默认色：`#999999`
- 选中色：`#FF7A5C`（品牌色）
- 按下色：`#E96345`
- 背景：`#FFFFFF`
- 顶部分割线：`#EEEEEE`

---

## 4. 页面跳转映射表

### 4.1 首页跳转

| 触发元素 | 目标页面 | 参数 |
|---------|---------|------|
| 快捷操作"记录饮食" | DietTab | `{ date: today }` |
| 快捷操作"记录体重" | BodyEdit | `{ recordType: 'weight' }` |
| 快捷操作"查看计划" | PlanList | - |
| 饮食时间轴卡片 | DietTab | `{ date: today }` |
| AI 洞察卡片 | Analysis | - |
| 计划进度卡片 | PlanDetail | `{ planId }` |
| 辅助记录卡片（饮水） | DataTab | `{ tab: 'water' }` |
| 辅助记录卡片（睡眠） | DataTab | `{ tab: 'sleep' }` |
| 辅助记录卡片（运动） | DataTab | `{ tab: 'exercise' }` |
| 辅助记录卡片（排便） | DataTab | `{ tab: 'bowel' }` |

### 4.2 饮食页跳转

| 触发元素 | 目标页面 | 参数 |
|---------|---------|------|
| 餐次卡片"修改"按钮 | DietEdit | `{ mealType, date, recordId }` |
| 餐次卡片空态点击 | DietEdit | `{ mealType, date }` |

### 4.3 数据页跳转

| 触发元素 | 目标页面 | 参数 |
|---------|---------|------|
| 今日卡片"手动记录" | BodyEdit | `{ recordType }` |
| 今日卡片"修改"按钮 | BodyEdit | `{ recordType, recordId }` |
| "数据分析"入口 | Analysis | - |

### 4.4 计划页跳转

| 触发元素 | 目标页面 | 参数 |
|---------|---------|------|
| 计划卡片点击 | PlanDetail | `{ planId }` |
| "+ 新建"按钮 | PlanCreateChat | - |
| 计划详情"修改计划" | PlanCreateChat | - |
| 创建完成"查看计划" | PlanDetail | `{ planId }` |

### 4.5 个人中心跳转

| 触发元素 | 目标页面 | 参数 |
|---------|---------|------|
| "编辑资料" | EditProfile | - |
| "设置" | Settings | - |

### 4.6 全局跳转（AI 输入框触发）

| 意图 | 目标页面 | 条件 |
|------|---------|------|
| 记录饮食 | 当前页面内更新 | 在首页或饮食页时 |
| 记录体重 | DataTab | 跨页面跳转 |
| 查询营养 | 弹出 BottomSheet | 不跳转 |
| 制定计划 | PlanCreateChat | 跳转 |
| 多轮对话（>2轮） | AIDialog | 自动切换 |

---

## 5. 导航动效

参考 `01-design-system.md` 动效规范：
- 页面切换：300ms ease-in-out
- Stack push：从右侧滑入
- Stack pop：向右侧滑出
- Modal：从底部滑入，250ms ease-out
- Tab 切换：无动画，即时切换

---

## 6. 导航守卫

### 6.1 认证守卫

```
App 启动
  ↓
检查 token（expo-secure-store）
  ↓
有 token → MainNavigator
无 token → AuthNavigator
```

### 6.2 Onboarding 守卫

```
注册成功
  ↓
检查是否完成 Onboarding
  ↓
未完成 → Onboarding 页面
已完成 → MainNavigator
```

### 6.3 返回拦截

以下页面需要拦截返回操作：
- DietEdit（有未保存修改时）→ 弹出确认对话框
- BodyEdit（有未保存修改时）→ 弹出确认对话框
- PlanCreateChat（对话进行中）→ 弹出确认对话框

---

## 7. 深链接（V1 预留）

V1 不实现深链接，但导航结构设计时预留支持：
- 所有路由名称使用字符串常量
- 路由参数可序列化
- 未来可通过 Expo Linking 配置
