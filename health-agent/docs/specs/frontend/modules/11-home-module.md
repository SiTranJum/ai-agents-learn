# 首页模块 (Home Module)

## 1. 模块职责

首页 Dashboard，展示今日健康概览、快捷操作、饮食时间轴、AI 洞察、计划进度、辅助记录。作为用户打开 App 后的第一个页面，承担信息聚合和快捷入口的核心职责。

## 2. 对应 UI 设计文稿

- `health-agent/docs/prd/v1/ui-design/03-home-dashboard.md`

## 3. 页面列表

| 页面 ID | 页面名称 | 说明 |
|---------|---------|------|
| P01 | HomeScreen | 首页 Dashboard |

## 4. 页面详细规格

### P01 HomeScreen

**页面职责**：展示今日健康概览、快捷记录入口、AI 洞察和计划进度。

**对应 UI 文稿**：`03-home-dashboard.md`

#### 页面结构（从上到下）

| 区域 | 名称 | 说明 |
|------|------|------|
| A | 顶部标题区 | "今天" + 日期，如"今天 · 4月29日 周二" |
| B | 今日概览大卡片 | 热量环形图 + 三大营养素进度条 + 右侧插画 |
| C | 快捷操作区 | 3 个按钮横排 |
| D | 今日饮食时间轴卡片 | 4 餐时间轴 |
| E | AI 洞察卡片 | 一句话建议 |
| F | 计划进度卡片 | 计划名称 + 进度 |
| G | 辅助记录小卡片区 | 2×2 网格 |
| H | AI 输入框 | 常驻底部，全局组件 |
| I | 底部 Tab 导航 | 全局组件 |

**A. 顶部标题区**

- 显示格式："今天 · {M}月{D}日 周{X}"
- 示例："今天 · 4月29日 周二"

**B. 今日概览大卡片**

- 左侧：热量环形图 + 三大营养素进度条
  - 热量：已摄入/目标（如 1250/1800 kcal），环形图展示百分比
  - 碳水：进度条 + 数值（g）
  - 蛋白质：进度条 + 数值（g）
  - 脂肪：进度条 + 数值（g）
- 右侧：插画图片（`assets/images/illustrations/home-person.png`）

**C. 快捷操作区**

3 个按钮横排，等宽分布：

| 按钮 | 图标 | 文字 | 跳转 |
|------|------|------|------|
| 1 | 餐具图标 | 记录饮食 | → DietTab |
| 2 | 体重秤图标 | 记录体重 | → BodyEdit { recordType: 'weight' } |
| 3 | 计划图标 | 查看计划 | → PlanList |

**D. 今日饮食时间轴卡片**

4 餐时间轴，纵向排列：

| 餐次 | 说明 |
|------|------|
| 早餐 | 餐次名称 + 时间 + 食物摘要 + 热量 |
| 午餐 | 同上 |
| 晚餐 | 同上 |
| 加餐 | 同上 |

每餐三种状态：

| 状态 | 显示 |
|------|------|
| `empty` | 显示"未记录"，引导点击添加 |
| `pending` | AI 解析完成但未确认，卡片高亮 + 确认按钮 |
| `recorded` | 显示食物摘要和热量 |

**E. AI 洞察卡片**

- 标题："AI 洞察"
- 内容：一句话建议（如"今天蛋白质摄入偏低，晚餐建议加个鸡蛋"）
- 可点击查看详情 → 跳转 Analysis

**F. 计划进度卡片**

- 有计划时：计划名称 + 进度条 + 完成数/总数（如"3/7 天"）
- 无计划时：显示"创建计划"引导按钮
- 点击 → PlanDetail { planId }

**G. 辅助记录小卡片区**

2×2 网格布局：

| 位置 | 类型 | 显示 |
|------|------|------|
| 左上 | 饮水 | 已喝/目标 ml（如 1200/2000 ml） |
| 右上 | 睡眠 | 时长（如 7h 30min） |
| 左下 | 运动 | 时长（如 45min） |
| 右下 | 排便 | 状态（如"正常"） |

点击任意卡片 → DataTab { tab: type }

**H. AI 输入框**

- 全局 shared 组件 `AIInputBar`，常驻底部
- 不属于本模块，由全局布局挂载

**I. 底部 Tab 导航**

- 全局导航组件 `BottomTabs`，不属于本模块

#### 页面状态

| 状态 | 说明 |
|------|------|
| 新用户空态 | 各项显示 0 或"未记录"，AI 洞察显示欢迎语（如"欢迎使用健康管家，开始记录你的第一餐吧"） |
| 有数据态 | 显示实际数据 |
| 局部待确认态 | 某餐 AI 解析完成但未确认，对应餐次卡片高亮显示确认按钮 |

#### 数据字段

```typescript
// 餐次类型
type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

// 首页聚合数据
interface HomeData {
  date: string;                          // 日期，格式 YYYY-MM-DD
  calories: {
    current: number;                     // 今日已摄入热量 kcal
    target: number;                      // 目标热量 kcal
  };
  nutrients: {
    carbs: { current: number; target: number };     // 碳水 g
    protein: { current: number; target: number };   // 蛋白质 g
    fat: { current: number; target: number };       // 脂肪 g
  };
  meals: {
    type: MealType;                      // 餐次类型
    status: 'empty' | 'pending' | 'recorded';  // 记录状态
    foods: string;                       // 食物摘要文本
    calories: number;                    // 该餐热量 kcal
    time?: string;                       // 记录时间，如 "08:30"
  }[];
  aiInsight: string;                     // AI 洞察文本
  plan: {
    id: string;                          // 计划 ID
    name: string;                        // 计划名称
    progress: number;                    // 进度百分比 0-100
    completedTasks: number;              // 已完成任务数
    totalTasks: number;                  // 总任务数
  } | null;                              // null 表示无计划
  auxiliary: {
    water: { current: number; target: number };       // 饮水 ml
    sleep: { duration: string } | null;               // 睡眠时长，如 "7h 30min"
    exercise: { duration: string } | null;            // 运动时长，如 "45min"
    bowel: { status: string } | null;                 // 排便状态，如 "正常"
  };
}
```

#### Mock 数据要求

**新用户 mock**：所有字段为 0 或空。

```typescript
const emptyMock: HomeData = {
  date: '2026-04-29',
  calories: { current: 0, target: 1800 },
  nutrients: {
    carbs: { current: 0, target: 225 },
    protein: { current: 0, target: 90 },
    fat: { current: 0, target: 60 },
  },
  meals: [
    { type: 'breakfast', status: 'empty', foods: '', calories: 0 },
    { type: 'lunch', status: 'empty', foods: '', calories: 0 },
    { type: 'dinner', status: 'empty', foods: '', calories: 0 },
    { type: 'snack', status: 'empty', foods: '', calories: 0 },
  ],
  aiInsight: '欢迎使用健康管家，开始记录你的第一餐吧 🍽️',
  plan: null,
  auxiliary: {
    water: { current: 0, target: 2000 },
    sleep: null,
    exercise: null,
    bowel: null,
  },
};
```

**有数据 mock**：模拟真实一天的数据。

```typescript
const dataMock: HomeData = {
  date: '2026-04-29',
  calories: { current: 1250, target: 1800 },
  nutrients: {
    carbs: { current: 150, target: 225 },
    protein: { current: 55, target: 90 },
    fat: { current: 38, target: 60 },
  },
  meals: [
    { type: 'breakfast', status: 'recorded', foods: '全麦面包、牛奶、鸡蛋', calories: 380, time: '08:15' },
    { type: 'lunch', status: 'recorded', foods: '米饭、西兰花炒鸡胸、紫菜汤', calories: 550, time: '12:30' },
    { type: 'dinner', status: 'recorded', foods: '杂粮粥、凉拌黄瓜', calories: 320, time: '18:45' },
    { type: 'snack', status: 'empty', foods: '', calories: 0 },
  ],
  aiInsight: '今天蛋白质摄入偏低，晚餐建议加个鸡蛋或豆腐补充一下',
  plan: {
    id: 'plan-001',
    name: '30天减脂计划',
    progress: 43,
    completedTasks: 3,
    totalTasks: 7,
  },
  auxiliary: {
    water: { current: 1200, target: 2000 },
    sleep: { duration: '7h 30min' },
    exercise: { duration: '45min' },
    bowel: { status: '正常' },
  },
};
```

**待确认 mock**：某餐 status 为 pending。

```typescript
const pendingMock: HomeData = {
  ...dataMock,
  meals: [
    { type: 'breakfast', status: 'recorded', foods: '全麦面包、牛奶、鸡蛋', calories: 380, time: '08:15' },
    { type: 'lunch', status: 'pending', foods: '牛肉面、卤蛋（AI 识别中）', calories: 620, time: '12:20' },
    { type: 'dinner', status: 'empty', foods: '', calories: 0 },
    { type: 'snack', status: 'empty', foods: '', calories: 0 },
  ],
};
```

#### 组件组成

| 组件 | 来源 | 说明 |
|------|------|------|
| HealthOverviewCard | 模块内 | 热量环形图 + 营养素进度条 + 插画 |
| QuickActionBar | 模块内 | 3 个快捷操作按钮 |
| MealTimelineCard | 复用 `@shared/ui/MealCard` | 饮食时间轴卡片 |
| AIInsightCard | 模块内 | AI 洞察卡片 |
| PlanProgressCard | 模块内 | 计划进度卡片 |
| AuxiliaryRecordGrid | 模块内 | 2×2 辅助记录网格 |
| AIInputBar | 全局 `@shared` 组件 | 底部 AI 输入框 |
| BottomTabs | 全局导航组件 | 底部 Tab 导航 |

#### 跳转关系

| 触发元素 | 目标页面 | 参数 |
|---------|---------|------|
| 快捷操作"记录饮食" | DietTab | — |
| 快捷操作"记录体重" | BodyEdit | `{ recordType: 'weight' }` |
| 快捷操作"查看计划" | PlanList | — |
| 饮食卡片点击 | DietTab | — |
| AI 洞察点击 | Analysis | — |
| 计划进度点击 | PlanDetail | `{ planId }` |
| 辅助记录卡片点击 | DataTab | `{ tab: type }` |

## 5. 模块内组件

| 组件 | Props | 说明 |
|------|-------|------|
| HealthOverviewCard | `calories`, `nutrients` | 热量环形图（CircularProgress）+ 三大营养素进度条（ProgressBar）+ 右侧插画 |
| QuickActionBar | `onRecordDiet`, `onRecordWeight`, `onViewPlan` | 3 个快捷操作按钮，横排等宽分布，每个按钮包含图标 + 文字 |
| AIInsightCard | `insight`, `onPress` | AI 洞察卡片，显示一句话建议，点击跳转详情 |
| PlanProgressCard | `plan`, `onPress`, `onCreatePlan` | 计划进度卡片，有计划时显示进度条，无计划时显示创建引导 |
| AuxiliaryRecordGrid | `auxiliary`, `onItemPress` | 2×2 网格，饮水/睡眠/运动/排便四个小卡片 |

## 6. 模块内 Store

```typescript
// 首页不需要复杂的本地状态管理
// 数据通过 TanStack Query 管理服务端状态
// Query Key: ['home', date]

interface HomeStore {
  // 预留：如果后续需要本地 UI 状态（如展开/折叠），在此扩展
}
```

TanStack Query 用法：

```typescript
// 首页数据查询
const useHomeData = (date: string) => {
  return useQuery({
    queryKey: ['home', date],
    queryFn: () => homeService.getHomeData(date),
  });
};
```

## 7. 模块内 Services

```typescript
interface HomeService {
  /**
   * 获取首页聚合数据
   * @param date - 日期字符串，格式 YYYY-MM-DD
   * @returns 首页所需的全部聚合数据
   */
  getHomeData(date: string): Promise<HomeData>;
}
```

说明：`getHomeData` 是一个聚合接口，后端将饮食记录、营养计算、计划进度、辅助记录等数据合并返回，避免首页发起多个请求。

## 8. 模块依赖

| 依赖 | 用途 |
|------|------|
| `@shared/ui/Card` | 卡片容器组件 |
| `@shared/ui/ProgressBar` | 营养素进度条 |
| `@shared/ui/CircularProgress` | 热量环形图 |
| `@shared/ui/MealCard` | 饮食时间轴卡片（复用） |
| `@shared/ui/AIInputBar` | 底部 AI 输入框（全局） |
| `@shared/feedback/Toast` | 轻提示（操作反馈） |

## 9. 实现约束

- 必须参考 `03-home-dashboard.md` 文稿实现，以文稿中的 ASCII 线框图、组件树、样式描述为准
- 没有完整视觉稿，不要自行发挥视觉设计，严格按文稿描述
- 插画使用 `assets/images/illustrations/home-person.png`
- 颜色、字体、间距遵循 `04-design-system-mapping.md` 中的设计系统规范
- 首页作为高频页面，注意性能优化：
  - 环形图和进度条避免不必要的重渲染
  - 列表项使用合适的 key
  - 图片资源做好缓存
- 页面需支持下拉刷新（Pull to Refresh）
