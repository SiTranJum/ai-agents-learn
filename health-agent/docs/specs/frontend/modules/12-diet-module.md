# 饮食模块前端实现 Spec

## 1. 模块职责

饮食记录查看、AI 对话式记录、表单式编辑、食物搜索。

## 2. 对应 UI 设计文稿

- `health-agent/docs/prd/v1/ui-design/04-diet-record-page.md`
- `health-agent/docs/prd/v1/ui-design/05-diet-edit-page.md`

## 3. 页面列表

| 页面编号 | 页面名称 | 说明 |
|---------|---------|------|
| P02 | DietRecordScreen | 饮食记录页 |
| P03 | DietEditScreen | 饮食编辑页 |

## 4. 页面详细规格

### P02 DietRecordScreen

**页面职责**：按餐次展示饮食卡片，支持查看当天饮食、营养摄入和记录进度。

**对应 UI 文稿**：`04-diet-record-page.md`

**页面结构**：

- 顶部日期切换栏（左箭头 + 日期 + 右箭头）
- 今日摄入汇总区（热量进度条 + 营养素环形图）
- 餐次卡片列表（早餐、午餐、晚餐、加餐）
- 底部常驻 AI 输入框
- 底部 Tab 导航

**页面状态**：

| 状态 | 说明 |
|------|------|
| 全部未记录 | 新用户首次进入，所有餐次为空态 |
| 部分记录 | 部分餐次有记录，部分为空 |
| 全部已记录 | 所有餐次均已完成记录 |
| 某餐待确认（pending） | AI 解析完成，等待用户确认 |
| 修改中 | 用户正在编辑某餐记录 |

**数据字段**：

```typescript
interface DietPageData {
  date: string;
  totalCalories: { current: number; target: number };
  nutrients: {
    carbs: { current: number; target: number };
    protein: { current: number; target: number };
    fat: { current: number; target: number };
  };
  meals: DietRecord[]; // 4 餐
}
```

**关键交互**：

- AI 输入自然语言 → 对应餐次卡片变为 pending
- 点击确认 → 保存，卡片变为 recorded
- 点击修改 → 跳转 DietEditScreen
- 日期切换 → 加载对应日期数据
- 删除操作 → 弹出确认对话框

**跳转关系**：

- 餐次卡片"修改" → DietEdit `{ mealType, date, recordId }`
- 餐次卡片空态点击 → DietEdit `{ mealType, date }`

---

### P03 DietEditScreen

**页面职责**：表单化饮食记录编辑，精确修改食物名称、份量和单位。

**对应 UI 文稿**：`05-diet-edit-page.md`

**页面结构**：

- 顶部导航栏（返回 + 标题）
- 餐次选择器（早餐/午餐/晚餐/加餐标签组）
- 食物列表（每个食物一行，支持增删改）
- 添加食物按钮
- 营养汇总区（实时计算）
- 底部操作栏（保存 + 取消）

**页面状态**：

| 状态 | 说明 |
|------|------|
| 编辑已有记录（预填充） | 餐次不可切换 |
| 新增记录（空表单） | 餐次可切换 |
| 食物搜索中 | 输入框下方弹出候选列表 |
| 表单校验失败 | 显示错误提示 |

**数据字段**：

```typescript
interface DietEditFormData {
  mealType: MealType;
  foods: {
    name: string;
    amount: number;
    unit: string;
    calories: number;
    protein: number;
    fat: number;
    carbs: number;
  }[];
}
```

**关键交互**：

- 修改食物名称/份量 → 热量自动重算
- 删除食物 → 列表移除，汇总重算
- 添加食物 → 新增一行
- 保存 → 返回饮食记录页
- 取消 → 有未保存修改时弹确认框
- 食物名称搜索 → 模糊搜索，点击候选项自动填充

## 5. 模块内组件

| 组件名 | 职责 |
|--------|------|
| DateSwitcher | 日期切换栏，左右箭头切换日期 |
| NutritionSummary | 营养摄入汇总，含热量进度条和营养素环形图 |
| MealCardList | 餐次卡片列表，渲染 4 餐卡片 |
| FoodSearchModal | 食物搜索弹窗，模糊搜索并选择食物 |
| FoodItemRow | 食物编辑行，单个食物的名称/份量/单位编辑 |

## 6. 模块内 Store

```typescript
interface DietStore {
  selectedDate: string;
  setSelectedDate: (date: string) => void;
}
```

## 7. 模块内 Services

```typescript
interface DietService {
  getDietByDate(date: string): Promise<DietRecord[]>;
  saveDietRecord(record: DietRecord): Promise<DietRecord>;
  deleteDietRecord(recordId: string): Promise<void>;
  confirmPendingRecord(recordId: string): Promise<DietRecord>;
  cancelPendingRecord(recordId: string): Promise<void>;
}

interface FoodService {
  searchFood(keyword: string): Promise<FoodItem[]>;
  getFoodNutrition(foodName: string, amount: number): Promise<FoodItem>;
}
```

## 8. Mock 数据要求

| Mock 场景 | 说明 |
|-----------|------|
| 有数据日期 mock | 4 餐都有记录，展示完整状态 |
| 部分数据 mock | 2 餐有记录，2 餐为空，展示混合状态 |
| 待确认 mock | 某餐 status 为 pending，展示确认交互 |
| 食物搜索 mock | 返回 10-20 种常见食物，覆盖搜索场景 |

## 9. 模块依赖

| 依赖路径 | 用途 |
|----------|------|
| `@shared/ui/Card` | 通用卡片容器 |
| `@shared/ui/MealCard` | 餐次卡片 |
| `@shared/ui/ProgressBar` | 热量进度条 |
| `@shared/ui/CircularProgress` | 营养素环形图 |
| `@shared/ui/Button` | 通用按钮 |
| `@shared/ui/AIInputBar` | AI 输入框 |
| `@shared/forms/TextInput` | 文本输入框 |
| `@shared/feedback/Toast` | 轻提示 |
| `@shared/feedback/ConfirmDialog` | 确认对话框 |
| `@shared/feedback/BottomSheet` | 底部弹出面板 |

## 10. 实现约束

- 必须参考 `04-diet-record-page.md` 和 `05-diet-edit-page.md` 文稿实现
- 没有完整视觉稿，以文稿中的 ASCII 线框图、组件树、样式描述为准
- 颜色、字体、间距遵循 `04-design-system-mapping.md`
