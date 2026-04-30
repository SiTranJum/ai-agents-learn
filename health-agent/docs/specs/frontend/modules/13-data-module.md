# 数据模块前端实现规格

## 1. 模块职责

数据模块负责身体数据的记录、展示和分析，包括：
- 体重、围度、睡眠、运动、饮水、排便等 6 类身体数据的记录
- 各类数据的趋势可视化（折线图、柱状图、环形图）
- 数据分析与 AI 洞察（热量趋势、营养分布、体重变化、计划达成率）
- 多时间范围切换（7天/30天/90天/365天）
- 表单化数据编辑与自动计算（睡眠时长、运动消耗）

## 2. 对应 UI 设计文稿

- `health-agent/docs/prd/v1/ui-design/06-data-page.md` — 数据页（6 个 Tab）
- `health-agent/docs/prd/v1/ui-design/07-body-edit-page.md` — 身体数据编辑页
- `health-agent/docs/prd/v1/ui-design/11-analysis-page.md` — 数据分析页

## 3. 页面列表

| 页面 ID | 页面名称 | 路由 | 对应文稿 |
|---------|---------|------|---------|
| P04 | DataScreen | `/data` | `06-data-page.md` |
| P05 | BodyEditScreen | `/data/edit` | `07-body-edit-page.md` |
| P09 | AnalysisScreen | `/data/analysis` | `11-analysis-page.md` |

## 4. 页面详细规格

### P04 DataScreen

**页面职责**

展示体重、围度、睡眠、运动、饮水、排便等身体数据的记录与趋势，支持多时间范围切换和 AI 对话式记录。

**对应 UI 文稿**

`06-data-page.md`

**页面结构**

- 顶部标题区："数据"
- 趋势折线图组件（高度 200px）
- 时间范围切换（7天/30天/90天/365天）
- Tab 切换栏（体重/围度/睡眠/运动/饮水/排便，可横向滚动）
- 今日记录卡片（根据 Tab 动态切换）
- 历史记录列表
- AI 输入框（常驻）
- 底部 Tab 导航

**页面状态**

每个 Tab 都有三种状态：
- `empty`：无任何记录，显示空状态插画 + 引导文案
- `pending`：今日未记录，显示"手动记录"按钮
- `recorded`：今日已记录，显示数据卡片 + "修改"按钮

**6 个 Tab 的卡片结构**

1. **体重 Tab**：今日体重（kg）+ 比昨天变化（+0.5kg / -0.3kg）+ BMI 值
2. **围度 Tab**：腰围、臀围、大腿围、上臂围（cm）
3. **睡眠 Tab**：睡眠时长 + 入睡/起床时间 + 睡眠质量（优秀/良好/一般/较差）
4. **运动 Tab**：运动类型 + 时长 + 预估消耗（kcal）
5. **饮水 Tab**：已喝/目标 ml + 进度条 + 快捷按钮（+250ml / +500ml）
6. **排便 Tab**：时间 + 状态（正常/便秘/腹泻）

**数据字段**

根据 Tab 类型动态变化：

```typescript
type DataTabType = 'weight' | 'measurement' | 'sleep' | 'exercise' | 'water' | 'bowel';

interface WeightRecord {
  id: string; date: string; weight: number; bmi: number; change: number; note?: string;
}
interface MeasurementRecord {
  id: string; date: string; waist?: number; hip?: number; thigh?: number; arm?: number; note?: string;
}
interface SleepRecord {
  id: string; date: string; bedTime: string; wakeTime: string;
  duration: number; // 分钟
  quality: 'excellent' | 'good' | 'fair' | 'poor'; note?: string;
}
interface ExerciseRecord {
  id: string; date: string; type: string; duration: number; calories: number; note?: string;
}
interface WaterRecord {
  id: string; date: string; amount: number; target: number; // ml
}
interface BowelRecord {
  id: string; date: string; time: string;
  status: 'normal' | 'constipation' | 'diarrhea'; note?: string;
}
```

**跳转关系**

- 今日卡片"手动记录"按钮 → `BodyEditScreen { recordType }`
- 今日卡片"修改"按钮 → `BodyEditScreen { recordType, recordId }`
- "数据分析"入口 → `AnalysisScreen`

---

### P05 BodyEditScreen

**页面职责**

表单化身体数据编辑，支持新增和修改记录，提供自动计算功能。

**对应 UI 文稿**

`07-body-edit-page.md`

**页面结构**

- 顶部导航栏（返回 + 动态标题）
- 日期选择器
- 动态表单区（根据 recordType 展示不同字段）
- 底部操作栏（保存 + 取消）

**4 种表单类型**

1. **weight（体重）**：体重输入框（kg，小数点后 1 位）+ 备注（可选）
2. **measurement（围度）**：腰围、臀围、大腿围、上臂围（cm，均可选）+ 备注
3. **sleep（睡眠）**：入睡/起床时间选择器 + 睡眠时长（自动计算）+ 质量选择器 + 备注
4. **exercise（运动）**：运动类型选择器 + 时长输入框 + 预估消耗（自动计算）+ 备注

**页面状态**

- **编辑已有记录**：预填充数据，日期锁定（不可切换）
- **新增记录**：空表单，日期可切换（默认今天）
- **表单校验失败**：显示错误提示（必填项未填、数值超出范围等）

**关键交互**

- 选择入睡/起床时间 → 自动计算睡眠时长（跨天计算支持）
- 选择运动类型/输入时长 → 自动估算消耗（基于 MET 值）
- 保存 → 返回数据页，卡片更新为 `recorded` 状态
- 取消 → 有未保存修改时弹确认框："确定放弃修改吗？"

**自动计算规则**

```typescript
// 睡眠时长计算（支持跨天）
function calculateSleepDuration(bedTime: string, wakeTime: string): number {
  // 返回分钟数，例如：23:00 → 06:30 = 450 分钟（7.5 小时）
}

// 运动消耗估算（基于 MET 值）
const MET_VALUES = {
  '跑步': 8.0, '游泳': 7.0, '瑜伽': 3.0, '力量训练': 6.0,
  '骑行': 7.5, '篮球': 8.0, '羽毛球': 5.5, '其他': 5.0,
};

function calculateCalories(type: string, duration: number, weight: number): number {
  // 消耗（kcal）= MET × 体重（kg）× 时长（小时）
  const met = MET_VALUES[type] || 5.0;
  return Math.round(met * weight * (duration / 60));
}
```

---

### P09 AnalysisScreen

**页面职责**

展示热量趋势、营养分布、体重变化、计划执行情况，并用 AI 输出阶段性洞察。

**对应 UI 文稿**

`11-analysis-page.md`

**页面结构**

- 顶部导航栏（返回 + "数据分析"）
- 时间范围切换（7天/30天/90天/365天）
- 热量趋势卡片（折线图：摄入/目标双折线）
- 营养分布卡片（环形图 + 柱状图）
- 体重变化卡片（折线图 + 当前/目标体重）
- 计划达成率卡片（进度条 + 完成度）
- AI 洞察总结卡片（2-3 条洞察）
- AI 输入框（常驻）
- 底部 Tab 导航

**页面状态**

- **空状态（数据不足）**：显示空状态插画 + 引导文案："记录 7 天以上数据后，即可查看分析报告"
- **有数据态**：显示所有图表和洞察
- **加载中**：骨架屏

**数据字段**

```typescript
interface AnalysisData {
  timeRange: '7d' | '30d' | '90d' | '365d';
  caloriesTrend: { date: string; intake: number; target: number; }[];
  nutritionDistribution: {
    carbs: number; protein: number; fat: number;
    carbsPercent: number; proteinPercent: number; fatPercent: number;
  };
  weightTrend: { date: string; weight: number; }[];
  currentWeight: number; targetWeight: number;
  planCompletion: { totalDays: number; completedDays: number; completionRate: number; };
  insights: {
    type: 'calorie' | 'nutrition' | 'weight' | 'habit' | 'achievement';
    title: string; description: string;
  }[];
}
```

**AI 洞察类型**

1. **热量趋势**：摄入是否稳定、是否超标、波动原因
2. **营养均衡**：三大营养素比例是否合理、缺乏/过量提示
3. **体重变化**：减重/增重进度、速度是否健康、预测达标时间
4. **饮食规律**：记录频率、遗漏天数、记录时间规律
5. **达标情况**：计划完成度、坚持天数、鼓励/建议

---

## 5. 模块内组件

| 组件名 | 职责 | 使用页面 |
|--------|------|---------|
| TrendChart | 趋势折线图（单/双折线） | P04, P09 |
| DataRecordList | 历史记录列表 | P04 |
| DataTabBar | Tab 切换栏（6 个 Tab，可横向滚动） | P04 |
| WeightCard | 体重今日卡片 | P04 |
| MeasurementCard | 围度今日卡片 | P04 |
| SleepCard | 睡眠今日卡片 | P04 |
| ExerciseCard | 运动今日卡片 | P04 |
| WaterCard | 饮水今日卡片（含快捷按钮） | P04 |
| BowelCard | 排便今日卡片 | P04 |
| TimeRangeSelector | 时间范围切换按钮组 | P04, P09 |
| NutritionAnalysisCard | 营养分布卡片（环形图 + 柱状图） | P09 |
| AIInsightSummaryCard | AI 洞察总结卡片 | P09 |

---

## 6. 模块内 Store

```typescript
interface DataStore {
  // 当前选中的 Tab
  selectedTab: DataTabType;
  setSelectedTab: (tab: DataTabType) => void;

  // 当前选中的时间范围
  selectedTimeRange: '7d' | '30d' | '90d' | '365d';
  setSelectedTimeRange: (range: '7d' | '30d' | '90d' | '365d') => void;

  // 今日各类型数据记录
  todayWeightRecord: WeightRecord | null;
  todayMeasurementRecord: MeasurementRecord | null;
  todaySleepRecord: SleepRecord | null;
  todayExerciseRecord: ExerciseRecord | null;
  todayWaterRecord: WaterRecord | null;
  todayBowelRecord: BowelRecord | null;

  // 趋势数据
  weightTrendData: WeightRecord[];
  measurementTrendData: MeasurementRecord[];
  sleepTrendData: SleepRecord[];
  exerciseTrendData: ExerciseRecord[];

  // 分析数据
  analysisData: AnalysisData | null;

  // 加载状态
  isLoading: boolean;
  error: string | null;

  // 操作方法
  fetchTodayRecords: () => Promise<void>;
  fetchTrendData: (type: DataTabType, range: string) => Promise<void>;
  fetchAnalysisData: (range: string) => Promise<void>;
  saveBodyRecord: (type: DataTabType, record: any) => Promise<void>;
  addWaterQuick: (amount: number) => Promise<void>;
}
```

---

## 7. 模块内 Services

```typescript
interface DataService {
  // 获取指定日期的身体数据
  getBodyDataByDate(date: string, type: BodyRecordType): Promise<BodyRecord>;

  // 保存身体数据
  saveBodyData(record: BodyRecord): Promise<BodyRecord>;

  // 获取体重趋势数据
  getWeightTrend(range: string): Promise<WeightTrendData>;

  // 获取围度趋势数据
  getMeasurementTrend(range: string): Promise<MeasurementTrendData>;

  // 获取睡眠趋势数据
  getSleepTrend(range: string): Promise<SleepTrendData>;

  // 获取运动趋势数据
  getExerciseTrend(range: string): Promise<ExerciseTrendData>;

  // 获取饮水记录
  getWaterRecord(date: string): Promise<WaterRecord>;

  // 快捷添加饮水量
  addWaterAmount(date: string, amount: number): Promise<WaterRecord>;

  // 获取分析数据
  getAnalysisData(range: string): Promise<AnalysisData>;
}

type BodyRecordType = 'weight' | 'measurement' | 'sleep' | 'exercise' | 'water' | 'bowel';
type BodyRecord = WeightRecord | MeasurementRecord | SleepRecord | ExerciseRecord | WaterRecord | BowelRecord;

interface WeightTrendData {
  records: WeightRecord[];
  avgWeight: number;
  totalChange: number;
}

interface MeasurementTrendData {
  records: MeasurementRecord[];
  avgWaist?: number;
  avgHip?: number;
}

interface SleepTrendData {
  records: SleepRecord[];
  avgDuration: number;
  qualityDistribution: { excellent: number; good: number; fair: number; poor: number; };
}

interface ExerciseTrendData {
  records: ExerciseRecord[];
  totalDuration: number;
  totalCalories: number;
  typeDistribution: { [type: string]: number };
}
```

---

## 8. Mock 数据要求

### 体重趋势 Mock

- **7 天数据**：每天一条记录，体重在 65-68kg 波动
- **30 天数据**：每天一条记录，体重呈下降趋势（70kg → 66kg）
- **90 天数据**：每 3 天一条记录，体重呈稳定下降趋势
- **365 天数据**：每周一条记录，体重呈阶梯式下降

### 围度趋势 Mock

- **30 天数据**：每 3 天一条记录，腰围、臀围、大腿围、上臂围均有记录
- 腰围：85cm → 80cm（下降趋势）
- 臀围：95cm → 92cm（下降趋势）

### 睡眠记录 Mock

- **7 天数据**：每天一条记录
- 睡眠时长：6.5-8 小时波动
- 睡眠质量：优秀 2 天、良好 3 天、一般 2 天

### 运动记录 Mock

- **7 天数据**：5 天有记录，2 天无记录
- 运动类型：跑步、游泳、瑜伽、力量训练混合
- 时长：30-60 分钟
- 消耗：200-500 kcal

### 饮水记录 Mock

- **今日数据**：已喝 1500ml，目标 2000ml，进度 75%

### 排便记录 Mock

- **7 天数据**：每天一条记录
- 状态：正常 5 天、便秘 1 天、腹泻 1 天

### 分析数据 Mock

```typescript
const mockAnalysisData: AnalysisData = {
  timeRange: '30d',
  caloriesTrend: [
    // 30 天数据，每天摄入在 1500-2000 kcal，目标 1800 kcal
  ],
  nutritionDistribution: {
    carbs: 180, protein: 90, fat: 60,
    carbsPercent: 50, proteinPercent: 25, fatPercent: 25,
  },
  weightTrend: [
    // 30 天体重数据，70kg → 66kg
  ],
  currentWeight: 66, targetWeight: 60,
  planCompletion: {
    totalDays: 30, completedDays: 25, completionRate: 83.3,
  },
  insights: [
    { type: 'calorie', title: '热量控制良好', description: '近 30 天平均摄入 1750 kcal，略低于目标，有助于减重。' },
    { type: 'weight', title: '体重稳步下降', description: '30 天减重 4kg，平均每周 1kg，速度健康合理。' },
    { type: 'achievement', title: '坚持记录 25 天', description: '计划完成度 83.3%，继续保持！' },
  ],
};
```

---

## 9. 模块依赖

### 共享 UI 组件

- `@shared/ui/Card` — 卡片容器
- `@shared/ui/ProgressBar` — 进度条（饮水、计划达成率）
- `@shared/ui/DataRecordCard` — 历史记录卡片
- `@shared/ui/Button` — 按钮（手动记录、修改、保存、取消）
- `@shared/ui/EmptyState` — 空状态插画

### 共享图表组件

- `@shared/charts/LineChart` — 折线图（体重、热量、睡眠趋势）
- `@shared/charts/BarChart` — 柱状图（营养分布）
- `@shared/charts/PieChart` — 环形图（营养分布）

### 共享表单组件

- `@shared/forms/TextInput` — 文本输入框（体重、围度、时长）
- `@shared/forms/DatePicker` — 日期选择器
- `@shared/forms/TimePicker` — 时间选择器（入睡/起床时间）
- `@shared/forms/Picker` — 选择器（运动类型、睡眠质量）

### 共享反馈组件

- `@shared/feedback/Toast` — 轻提示（保存成功、快捷添加饮水）
- `@shared/feedback/Dialog` — 对话框（取消确认）
- `@shared/feedback/Skeleton` — 骨架屏

### 共享导航组件

- `@shared/navigation/TabBar` — 底部 Tab 导航
- `@shared/navigation/TopBar` — 顶部导航栏

---

## 10. 实现约束

### UI 文稿遵循

- 必须参考 `06-data-page.md`、`07-body-edit-page.md`、`11-analysis-page.md` 文稿实现
- 没有完整视觉稿，以文稿中的 ASCII 线框图、组件树、样式描述为准
- 页面结构、组件层级、交互逻辑必须与文稿一致

### 设计系统映射

- 颜色、字体、间距遵循 `04-design-system-mapping.md`
- 主色：`#4CAF50`（绿色，健康主题）
- 辅助色：`#FF9800`（橙色，警告/提示）
- 文本色：`#212121`（深灰）、`#757575`（中灰）、`#BDBDBD`（浅灰）
- 圆角：卡片 12px，按钮 8px
- 间距：8px 基准，16px 标准，24px 大间距

### 图表库选择

- **推荐**：`react-native-chart-kit`（轻量、易用、样式可定制）
- **备选**：`victory-native`（功能强大、交互丰富，但体积较大）
- 折线图：支持双折线（摄入/目标）、网格线、数据点标记
- 柱状图：支持分组柱状图（营养素对比）
- 环形图：支持百分比标签、图例

### 性能优化

- 趋势图表数据量大时（365 天），使用数据抽样或分页加载
- 历史记录列表使用虚拟滚动（`FlatList` 的 `windowSize` 优化）
- 图表组件使用 `React.memo` 避免不必要的重渲染
- 分析数据计算放在 Service 层，避免在组件中重复计算

### 数据校验

- 体重：20-200 kg，小数点后 1 位
- 围度：20-200 cm，整数
- 睡眠时长：0-24 小时，自动计算
- 运动时长：1-300 分钟，整数
- 饮水量：0-10000 ml，整数
- 日期：不能选择未来日期

### 错误处理

- 网络请求失败：显示 Toast 提示，支持重试
- 数据为空：显示空状态插画 + 引导文案
- 表单校验失败：字段下方显示红色错误提示
- 自动计算异常：显示默认值或提示用户手动输入
