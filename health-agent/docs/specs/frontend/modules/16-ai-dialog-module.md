# AI 对话模块前端实现规格

## 1. 模块职责

AI 全屏对话、营养查询结果浮层、确认对话框、跨页面 AI 交互。

负责：
- AI 多轮对话的全屏展示和交互
- 营养查询结果的浮层展示
- 全局确认对话框和 Toast 提示
- 跨页面的 AI 交互状态管理

## 2. 对应 UI 设计文稿

- `health-agent/docs/prd/v1/ui-design/14-ai-dialog-and-overlays.md`
- `health-agent/docs/prd/v1/ui-design/02-components.md`

## 3. 页面列表

- **P17 AIDialogScreen** — AI 全屏对话页

## 4. 浮层/弹窗列表

- **O01 NutritionBottomSheet** — 营养查询结果浮层
- **O02 ConfirmDialog** — 确认对话框（全局）
- **O03 Toast** — Toast 提示（全局）

## 5. 页面详细规格

### P17 AIDialogScreen

**页面职责**

多轮 AI 对话（超过 2 轮自动切换到此页面）。

**对应 UI 文稿**

`14-ai-dialog-and-overlays.md` AI 全屏对话部分

**页面结构**

- 顶部导航栏（返回 + "AI 助手"）
- 中间全屏对话流（可滚动）
  - AI 消息气泡（左对齐，#F2F3F5 背景）
  - 用户消息气泡（右对齐，#FFE7E1 背景）
  - 系统消息（居中，灰色小字）
- 底部 AI 输入框（56px 高）

**页面状态**

- 对话进行中（消息流增长）
- AI 思考中（三个点跳动动画）
- 对话完成（显示操作按钮）

**数据字段**

```typescript
interface ChatMessage {
  id: string;
  role: 'ai' | 'user' | 'system';
  content: string;
  timestamp: string;
  actions?: ChatAction[]; // AI 消息可能带操作按钮
}

interface ChatAction {
  label: string;
  action: 'navigate' | 'confirm' | 'cancel';
  params?: any;
}
```

**关键交互**

- 点击返回 → 返回上一页面，保留对话历史
- 输入文字并发送 → 用户消息气泡出现，触发 AI 回复
- AI 思考中 → 三个点跳动动画
- 点击操作按钮 → 执行对应操作（跳转、确认等）

---

### O01 NutritionBottomSheet

**浮层职责**

展示食物营养查询结果。

**对应 UI 文稿**

`14-ai-dialog-and-overlays.md` 营养查询浮层部分

**浮层结构**

- 顶部拖拽条（36×4px）
- 食物名称（18px SemiBold）
- 热量大数值（36px Bold）
- 三大营养素（碳水、蛋白质、脂肪）
- 数据来源标签
- 操作按钮（"记录到饮食" + "关闭"）

**浮层状态**

- 展开
- 收起
- 关闭

**数据字段**

```typescript
interface NutritionData {
  foodName: string;
  amount: number;
  unit: string;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  dataSource: 'local_db' | 'api' | 'ai_estimate';
}
```

**关键交互**

- 向下拖拽 → 关闭浮层
- 点击"记录到饮食" → 跳转到饮食编辑页，预填充数据
- 点击"关闭" → 关闭浮层

---

### O02 ConfirmDialog

**对话框职责**

确认操作（删除、退出、终止等）。

**对应 UI 文稿**

`02-components.md` 确认对话框部分

**对话框结构**

- 标题（18px SemiBold）
- 内容文案（14px Regular）
- 按钮组（次要按钮 + 主要按钮）

**对话框状态**

- 显示
- 隐藏

**数据字段**

```typescript
interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmText?: string; // 默认"确认"
  cancelText?: string; // 默认"取消"
  onConfirm: () => void;
  onCancel: () => void;
  variant?: 'default' | 'danger'; // 危险操作用红色
}
```

---

### O03 Toast

**Toast 职责**

操作反馈提示。

**对应 UI 文稿**

`02-components.md` Toast 提示部分

**Toast 结构**

- 图标（成功/失败/信息）
- 文案（14px Regular）

**Toast 状态**

- 显示
- 隐藏

**Toast 类型**

- success
- error
- info

**数据字段**

```typescript
interface ToastProps {
  type: 'success' | 'error' | 'info';
  message: string;
  duration?: number; // 默认 2000ms
}
```

## 6. 模块内组件

| 组件 | 职责 | 使用位置 |
|------|------|---------|
| ChatMessageList | 对话消息列表，渲染 AI/用户/系统消息气泡 | P17 AIDialogScreen |
| ChatInput | 对话输入框，发送消息 | P17 AIDialogScreen |
| ConfirmDialog | 确认对话框（全局） | 全局使用 |
| NutritionBottomSheet | 营养查询结果浮层 | AI 对话中触发 |
| Toast | Toast 提示（全局） | 全局使用 |

## 7. 模块内 Store

```typescript
interface AIStore {
  chatMessages: ChatMessage[];
  isAIThinking: boolean;
  addMessage: (message: ChatMessage) => void;
  setAIThinking: (thinking: boolean) => void;
  clearChat: () => void;
}
```

## 8. 模块内 Services

```typescript
interface AIService {
  sendMessage(message: string, context?: any): Promise<ChatMessage>;
  queryNutrition(foodName: string, amount: number): Promise<NutritionData>;
}
```

## 9. Mock 数据要求

- **AI 回复 mock**：模拟不同意图的回复（饮食记录确认、营养查询结果、健康建议等）
- **营养查询 mock**：返回食物营养数据（热量、三大营养素、数据来源）

## 10. 模块依赖

| 依赖 | 用途 |
|------|------|
| `@shared/ui/Button` | 操作按钮 |
| `@shared/ui/AIInputBar` | AI 输入框组件 |
| `@shared/feedback/BottomSheet` | 底部浮层基础组件 |
| `@shared/feedback/Modal` | 模态对话框基础组件 |
| `@shared/feedback/Toast` | Toast 提示基础组件 |

## 11. 实现约束

- 必须参考 `14-ai-dialog-and-overlays.md` 和 `02-components.md` 文稿实现
- 对话气泡样式：AI 左对齐灰底（#F2F3F5）、用户右对齐浅橙底（#FFE7E1）
- BottomSheet 使用 `@gorhom/bottom-sheet` 库
- Toast 使用全局单例模式
- 颜色、字体、间距遵循 `04-design-system-mapping.md`
