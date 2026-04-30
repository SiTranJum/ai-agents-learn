# 共享 UI 组件规范

> 本文档定义健康管家 AI Agent 移动端 App 的所有共享 UI 组件的详细规格，供前端开发直接使用。
> 基于：`02-components.md`（组件设计）、`01-design-system.md`（设计系统）

---

## 1. 组件清单

### 1.1 基础组件
- **Button** - 通用按钮
- **Card** - 通用卡片容器
- **Tag** - 标签
- **Avatar** - 头像
- **ProgressBar** - 进度条
- **CircularProgress** - 环形进度图

### 1.2 业务组件
- **MealCard** - 餐次卡片
- **DataRecordCard** - 身体数据记录卡片
- **PlanCard** - 计划卡片

### 1.3 交互组件
- **AIInputBar** - AI 输入框（全局常驻）
- **BottomTabs** - 底部 Tab 导航（全局）

---

## 2. 组件详细规格

### 2.1 Button

#### 用途
通用按钮，用于所有需要用户点击操作的场景。

#### Props 定义

```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'text';
  size: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  onPress: () => void;
  children: React.ReactNode;
  style?: ViewStyle;
}
```

#### 状态变体

| 状态 | 表现 |
|------|------|
| 默认 | 正常显示，可点击 |
| 按下 | 缩放至 0.95，持续 100ms |
| 禁用 | 透明度 60%，不可点击 |
| 加载中 | 显示 loading 动画，不可点击 |

#### 样式规范

**primary（主按钮）**
- 背景色：`#FF7A5C`（brand-primary）
- 文字颜色：`#FFFFFF`
- 圆角：`12px`
- 按下态背景：`#E96345`（brand-primary-dark）
- 阴影：`0 4px 12px rgba(255,122,92,0.3)`

**secondary（次按钮）**
- 背景色：`#FFFFFF`
- 边框：`1px solid #EEEEEE`
- 文字颜色：`#666666`
- 圆角：`12px`
- 按下态背景：`#F5F5F5`

**text（文字按钮）**
- 背景色：透明
- 文字颜色：`#FF7A5C`
- 无边框
- 按下态文字：`#E96345`

**尺寸规格**
- small：高度 `32px`，内边距 `12px`，字号 `13px`
- medium：高度 `44px`，内边距 `16px`，字号 `15px`
- large：高度 `52px`，内边距 `20px`，字号 `16px`

#### 使用示例

```typescript
// 主按钮
<Button variant="primary" size="medium" onPress={handleSubmit}>
  确认记录
</Button>

// 次按钮
<Button variant="secondary" size="medium" onPress={handleCancel}>
  取消
</Button>

// 文字按钮
<Button variant="text" size="small" onPress={handleEdit}>
  修改
</Button>

// 加载中
<Button variant="primary" size="medium" loading onPress={handleSubmit}>
  提交中...
</Button>
```

---

### 2.2 Card

#### 用途
通用卡片容器，用于包裹内容区域，提供统一的视觉层级。

#### Props 定义

```typescript
interface CardProps {
  children: React.ReactNode;
  onPress?: () => void;
  style?: ViewStyle;
}
```

#### 样式规范

- 背景色：`#FFFFFF`
- 圆角：`12px`
- 内边距：`16px`
- 阴影：`0 2px 8px rgba(0,0,0,0.06)`（shadow-card）
- 可点击时按下态：背景色变为 `#F5F5F5`，持续 100ms

#### 使用示例

```typescript
// 基础卡片
<Card>
  <Text>卡片内容</Text>
</Card>

// 可点击卡片
<Card onPress={handlePress}>
  <Text>点击查看详情</Text>
</Card>
```

---

### 2.3 Tag

#### 用途
标签，用于状态标识、分类标记等场景。

#### Props 定义

```typescript
interface TagProps {
  label: string;
  variant: 'default' | 'success' | 'warning' | 'error';
  size: 'small' | 'medium';
}
```

#### 样式规范

**variant 颜色方案**

| variant | 背景色 | 文字颜色 | 使用场景 |
|---------|--------|----------|---------|
| default | `#F7F8FA` | `#666666` | 普通标签 |
| success | `rgba(76,217,100,0.1)` | `#4CD964` | 达标、完成 |
| warning | `rgba(255,201,77,0.1)` | `#FFC94D` | 接近目标、注意 |
| error | `rgba(255,90,95,0.1)` | `#FF5A5F` | 超标、错误 |

**尺寸规格**
- small：高度 `24px`，内边距 `8px 12px`，字号 `12px`
- medium：高度 `32px`，内边距 `10px 16px`，字号 `13px`

**通用样式**
- 圆角：`999px`（radius-full）
- 字重：Medium (500)

#### 使用示例

```typescript
// 成功标签
<Tag label="已达标" variant="success" size="small" />

// 警告标签
<Tag label="待确认" variant="warning" size="medium" />

// 错误标签
<Tag label="超标" variant="error" size="small" />
```

---

### 2.4 Avatar

#### 用途
头像，用于用户头像展示。

#### Props 定义

```typescript
interface AvatarProps {
  uri?: string;
  name: string; // 用于生成默认头像
  size: number;
}
```

#### 样式规范

- 形状：圆形
- 边框：无
- 默认头像：品牌色背景 `#FF7A5C` + 白色首字母
- 首字母字号：`size * 0.4`
- 首字母字重：SemiBold (600)

#### 使用示例

```typescript
// 有图片的头像
<Avatar uri="https://example.com/avatar.jpg" name="张三" size={48} />

// 默认头像（显示首字母）
<Avatar name="张三" size={48} />

// 小尺寸头像
<Avatar name="李四" size={32} />
```

---

### 2.5 ProgressBar

#### 用途
进度条，用于展示线性进度（如热量摄入、营养素摄入等）。

#### Props 定义

```typescript
interface ProgressBarProps {
  current: number;
  target: number;
  color?: string;
  height?: number;
  showLabel?: boolean;
}
```

#### 样式规范

- 高度：默认 `10px`
- 圆角：`999px`（radius-full）
- 轨道背景：`#F0F0F0`
- 填充颜色：默认 `#FF7A5C`（brand-primary），可自定义
- 超标处理：超过 100% 时，超出部分使用 `#FF5A5F`（color-error）
- 标签字号：`14px`
- 标签颜色：`#666666`（text-secondary）

#### 使用示例

```typescript
// 基础进度条
<ProgressBar current={1280} target={1800} />

// 自定义颜色
<ProgressBar current={45} target={60} color="#4CD964" />

// 带标签
<ProgressBar
  current={1280}
  target={1800}
  showLabel
/>
// 显示：1280 / 1800 kcal

// 超标情况
<ProgressBar current={2100} target={1800} />
// 进度条会显示超出部分为红色
```

---

### 2.6 CircularProgress

#### 用途
环形进度图，主要用于热量展示（首页核心数据）。

#### Props 定义

```typescript
interface CircularProgressProps {
  current: number;
  target: number;
  size: number;
  strokeWidth: number;
  showCenter?: boolean;
}
```

#### 样式规范

- 轨道颜色：`#F0F0F0`
- 填充颜色：`#FF7A5C`（brand-primary）
- 超标颜色：`#FF5A5F`（color-error）
- 中心文字字号：`size * 0.25`
- 中心文字字重：Bold (700)
- 中心文字颜色：`#222222`（text-primary）
- 单位字号：`size * 0.12`
- 单位颜色：`#999999`（text-tertiary）

#### 使用示例

```typescript
// 热量环形图
<CircularProgress
  current={1280}
  target={1800}
  size={160}
  strokeWidth={16}
  showCenter
/>
// 中心显示：1280 / 1800 kcal

// 小尺寸
<CircularProgress
  current={65}
  target={100}
  size={80}
  strokeWidth={8}
/>
```

---

### 2.7 MealCard

#### 用途
餐次卡片，用于饮食记录页面，展示早餐、午餐、晚餐、加餐等餐次的记录状态。

#### Props 定义

```typescript
type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';
type MealStatus = 'empty' | 'pending' | 'recorded';

interface MealData {
  foods: Array<{
    name: string;
    amount: string;
    calories: number;
  }>;
  totalCalories: number;
  recordTime?: string;
}

interface MealCardProps {
  mealType: MealType;
  status: MealStatus;
  data?: MealData;
  onConfirm?: () => void;
  onEdit?: () => void;
  onCancel?: () => void;
  onPress?: () => void;
}
```

#### 三种状态

**empty（未记录）**
- 背景：`#F7F8FA`
- 内容：显示 `+ 点击记录` 或 `告诉 AI 你吃了什么`
- 交互：点击进入输入或拍照记录

**pending（待确认）**
- 背景：`#FFFFFF`
- 边框：`1px solid #FFE7E1`（brand-primary-light）
- 顶部提示条：浅橙色 `#FFE7E1`，高度 `4px`
- 内容：显示 AI 解析出的食物内容
- 操作按钮：`✓ 确认`、`✏️ 修改`、`✗ 取消`

**recorded（已记录）**
- 背景：`#FFFFFF`
- 内容：显示食物列表、份量、总热量
- 交互：点击进入详情页

#### 样式规范

- 卡片圆角：`12px`
- 内边距：`16px`
- 餐次名称字号：`16px`，SemiBold (600)
- 时间段字号：`13px`，颜色 `#999999`
- 食物列表字号：`14px`
- 热量字号：`15px`，SemiBold (600)
- 操作按钮高度：`32px`
- 操作按钮圆角：`16px`
- 操作按钮间距：`8px`

#### 使用示例

```typescript
// 未记录状态
<MealCard
  mealType="breakfast"
  status="empty"
  onPress={handleAddMeal}
/>

// 待确认状态
<MealCard
  mealType="lunch"
  status="pending"
  data={{
    foods: [
      { name: '鸡胸肉沙拉', amount: '1份', calories: 320 },
      { name: '玉米', amount: '半根', calories: 80 },
      { name: '无糖酸奶', amount: '1杯', calories: 60 }
    ],
    totalCalories: 460
  }}
  onConfirm={handleConfirm}
  onEdit={handleEdit}
  onCancel={handleCancel}
/>

// 已记录状态
<MealCard
  mealType="dinner"
  status="recorded"
  data={{
    foods: [
      { name: '三文鱼', amount: '150g', calories: 280 },
      { name: '西兰花', amount: '100g', calories: 34 },
      { name: '糙米饭', amount: '1碗', calories: 216 }
    ],
    totalCalories: 530,
    recordTime: '18:30'
  }}
  onPress={handleViewDetail}
/>
```

---

### 2.8 DataRecordCard

#### 用途
身体数据记录卡片，用于数据页面，展示体重、围度、睡眠、运动、饮水、排便等记录。

#### Props 定义

```typescript
type BodyRecordType = 'weight' | 'measurement' | 'sleep' | 'exercise' | 'water' | 'bowel';
type RecordStatus = 'empty' | 'pending' | 'recorded';

interface BodyRecordData {
  // 体重
  weight?: {
    value: number;
    unit: string;
    change?: number;
  };
  // 围度
  measurement?: {
    waist?: number;
    hip?: number;
    chest?: number;
  };
  // 睡眠
  sleep?: {
    duration: string;
    bedTime: string;
    wakeTime: string;
    quality?: string;
  };
  // 运动
  exercise?: {
    type: string;
    duration: number;
    calories: number;
  };
  // 饮水
  water?: {
    current: number;
    target: number;
  };
  // 排便
  bowel?: {
    count: number;
    time: string;
    status: string;
  };
}

interface DataRecordCardProps {
  recordType: BodyRecordType;
  status: RecordStatus;
  data?: BodyRecordData;
  onConfirm?: () => void;
  onEdit?: () => void;
  onCancel?: () => void;
  onPress?: () => void;
  onQuickAdd?: (amount: number) => void; // 用于饮水快捷添加
}
```

#### 样式规范

参考 MealCard 的基础样式，根据不同 recordType 展示不同内容：

- 卡片圆角：`12px`
- 内边距：`16px`
- 标题字号：`15px`，SemiBold (600)
- 主数值字号：`28px`~`36px`，Bold (700)
- 副信息字号：`13px`~`14px`
- 快捷按钮高度：`28px`~`32px`

#### 使用示例

```typescript
// 体重卡片 - 已记录
<DataRecordCard
  recordType="weight"
  status="recorded"
  data={{
    weight: {
      value: 65.8,
      unit: 'kg',
      change: 0.3
    }
  }}
  onPress={handleViewDetail}
/>

// 饮水卡片 - 已记录
<DataRecordCard
  recordType="water"
  status="recorded"
  data={{
    water: {
      current: 1200,
      target: 2000
    }
  }}
  onQuickAdd={handleQuickAdd}
/>

// 睡眠卡片 - 待确认
<DataRecordCard
  recordType="sleep"
  status="pending"
  data={{
    sleep: {
      duration: '7h 35m',
      bedTime: '23:48',
      wakeTime: '07:23',
      quality: '睡得不错'
    }
  }}
  onConfirm={handleConfirm}
  onEdit={handleEdit}
/>

// 空状态
<DataRecordCard
  recordType="exercise"
  status="empty"
  onPress={handleAddRecord}
/>
```

---

### 2.9 PlanCard

#### 用途
计划卡片，用于计划列表页面，展示健康计划的目标、进度和状态。

#### Props 定义

```typescript
type PlanStatus = 'active' | 'paused' | 'completed';

interface PlanListItem {
  id: string;
  name: string;
  progress: number; // 0-100
  startDate: string;
  targetDate: string;
  status: PlanStatus;
}

interface PlanCardProps {
  plan: PlanListItem;
  onPress: () => void;
}
```

#### 样式规范

- 背景色：`#FFFFFF`
- 圆角：`12px`
- 内边距：`16px`
- 计划名称字号：`16px`，SemiBold (600)
- 进度条高度：`8px`
- 进度条圆角：`999px`
- 日期字号：`13px`，颜色 `#999999`
- 状态标签高度：`24px`
- 状态标签圆角：`12px`

**状态标签颜色**

| 状态 | 背景色 | 文字颜色 |
|------|--------|----------|
| active（进行中） | `rgba(76,217,100,0.1)` | `#4CD964` |
| paused（已暂停） | `rgba(255,201,77,0.1)` | `#FFC94D` |
| completed（已完成） | `rgba(90,200,250,0.1)` | `#5AC8FA` |

#### 使用示例

```typescript
<PlanCard
  plan={{
    id: '1',
    name: '30 天减脂计划',
    progress: 62,
    startDate: '2026-04-01',
    targetDate: '2026-04-30',
    status: 'active'
  }}
  onPress={handleViewPlan}
/>
```

---

### 2.10 AIInputBar

#### 用途
AI 输入框，全局常驻在页面底部，承担文字输入、拍照输入、语音输入和发送操作。

#### Props 定义

```typescript
interface AIInputBarProps {
  onSend: (message: string) => void;
  onCamera: () => void;
  onVoice: () => void;
  placeholder?: string;
  disabled?: boolean;
}
```

#### 样式规范

- 整体高度：`56px`
- 背景色：`#FFFFFF`
- 顶部阴影：`0 -2px 12px rgba(34,34,34,0.06)`（shadow-input）
- 左右内边距：`12px`
- 上下内边距：`8px`
- 左侧按钮尺寸：`28x28px`
- 左侧两个按钮间距：`8px`
- 中间输入胶囊高度：`40px`
- 中间输入胶囊圆角：`24px`（radius-pill）
- 输入胶囊背景：`#F7F8FA`
- Placeholder 颜色：`#999999`
- 发送按钮热区：最小 `44x44px`
- 发送按钮图标：`20x20px`

#### 状态

| 状态 | 表现 |
|------|------|
| 默认 | 显示 placeholder，发送按钮弱化 |
| 输入中 | 键盘弹起，输入框获得焦点，组件整体上移到键盘上方 |
| 录音中 | 语音按钮变红 `#FF5A5F`，按钮周围出现脉冲光圈 |
| 发送中 | 发送按钮替换为 loading 动画 |
| 禁用 | 整体透明度降至 60%，按钮不可点 |

#### 使用示例

```typescript
<AIInputBar
  onSend={handleSend}
  onCamera={handleCamera}
  onVoice={handleVoice}
  placeholder="说点什么..."
/>

// 禁用状态
<AIInputBar
  onSend={handleSend}
  onCamera={handleCamera}
  onVoice={handleVoice}
  disabled
/>
```

---

### 2.11 BottomTabs

#### 用途
底部 Tab 导航，全局固定在主框架页面底部，用于一级信息架构切换。

#### Props

由 React Navigation 管理，通常不需要手动传递 props。

```typescript
// 在 React Navigation 中配置
<Tab.Navigator
  screenOptions={{
    tabBarStyle: {
      height: 60,
      backgroundColor: '#FFFFFF',
      borderTopWidth: 1,
      borderTopColor: '#EEEEEE',
    },
    tabBarActiveTintColor: '#FF7A5C',
    tabBarInactiveTintColor: '#999999',
  }}
>
  <Tab.Screen name="Home" component={HomeScreen} />
  <Tab.Screen name="Diet" component={DietScreen} />
  <Tab.Screen name="Data" component={DataScreen} />
  <Tab.Screen name="Profile" component={ProfileScreen} />
</Tab.Navigator>
```

#### 样式规范

- 容器高度：`60px`（不含底部安全区）
- 安全区补偿：`env(safe-area-inset-bottom)`，最小按 `16px` 预留
- 背景色：`#FFFFFF`
- 顶部分割线：`1px #EEEEEE`
- 单个 Tab 宽度：`25%` 等分
- 图标尺寸：`24x24px`
- 图标与文字间距：`4px`
- 文字字号：`12px`，Medium (500)
- 默认态颜色：`#999999`
- 选中态颜色：`#FF7A5C`
- 按下反馈颜色：`#E96345`

**Tab 图标**

| Tab | 图标描述 | 默认态 | 选中态 |
|-----|---------|--------|--------|
| 首页 | 房子轮廓（Home） | `#999999` 线性 | `#FF7A5C` 线性 |
| 饮食 | 餐盘 + 刀叉轮廓（Fork Knife） | `#999999` 线性 | `#FF7A5C` 线性 |
| 数据 | 柱状图轮廓（Chart Bar） | `#999999` 线性 | `#FF7A5C` 线性 |
| 我的 | 人物轮廓（User） | `#999999` 线性 | `#FF7A5C` 线性 |

---

## 3. 组件开发规范

### 3.1 TypeScript 类型定义

所有组件必须有完整的 TypeScript 类型定义：

```typescript
// ✅ 正确
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'text';
  size: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  onPress: () => void;
  children: React.ReactNode;
  style?: ViewStyle;
}

// ❌ 错误
interface ButtonProps {
  variant: string; // 应该使用联合类型
  size: any; // 不应该使用 any
  onPress: Function; // 应该明确函数签名
}
```

### 3.2 样式分离

样式必须分离到 `.styles.ts` 文件：

```typescript
// Button.tsx
import { styles } from './Button.styles';

export const Button: React.FC<ButtonProps> = ({ variant, size, children }) => {
  return (
    <TouchableOpacity style={[styles.base, styles[variant], styles[size]]}>
      <Text>{children}</Text>
    </TouchableOpacity>
  );
};

// Button.styles.ts
import { StyleSheet } from 'react-native';
import { tokens } from '@/design-tokens';

export const styles = StyleSheet.create({
  base: {
    borderRadius: tokens.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primary: {
    backgroundColor: tokens.color.brandPrimary,
  },
  secondary: {
    backgroundColor: tokens.color.bgCard,
    borderWidth: 1,
    borderColor: tokens.color.borderDivider,
  },
  // ...
});
```

### 3.3 使用 Design Tokens

禁止硬编码颜色、尺寸等值，必须使用 Design Tokens：

```typescript
// ✅ 正确
backgroundColor: tokens.color.brandPrimary,
fontSize: tokens.font.body.size,
padding: tokens.space.lg,

// ❌ 错误
backgroundColor: '#FF7A5C',
fontSize: 16,
padding: 16,
```

### 3.4 Ref 转发

需要支持 ref 的组件必须使用 `forwardRef`：

```typescript
export const Button = React.forwardRef<TouchableOpacity, ButtonProps>(
  ({ variant, size, children, ...props }, ref) => {
    return (
      <TouchableOpacity ref={ref} {...props}>
        <Text>{children}</Text>
      </TouchableOpacity>
    );
  }
);

Button.displayName = 'Button';
```

### 3.5 默认 Props

组件必须有合理的默认 props：

```typescript
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  children,
  onPress,
  style,
}) => {
  // ...
};
```

### 3.6 DisplayName

所有组件必须设置 displayName，便于调试：

```typescript
Button.displayName = 'Button';
MealCard.displayName = 'MealCard';
AIInputBar.displayName = 'AIInputBar';
```

---

## 4. 组件测试要求（V1 可选）

### 4.1 快照测试

```typescript
import { render } from '@testing-library/react-native';
import { Button } from './Button';

describe('Button', () => {
  it('matches snapshot - primary variant', () => {
    const { toJSON } = render(
      <Button variant="primary" size="medium" onPress={() => {}}>
        确认
      </Button>
    );
    expect(toJSON()).toMatchSnapshot();
  });
});
```

### 4.2 Props 测试

```typescript
it('renders with correct variant styles', () => {
  const { getByText } = render(
    <Button variant="secondary" size="medium" onPress={() => {}}>
      取消
    </Button>
  );
  const button = getByText('取消').parent;
  expect(button).toHaveStyle({ backgroundColor: '#FFFFFF' });
});
```

### 4.3 交互测试

```typescript
it('calls onPress when pressed', () => {
  const onPress = jest.fn();
  const { getByText } = render(
    <Button variant="primary" size="medium" onPress={onPress}>
      确认
    </Button>
  );
  fireEvent.press(getByText('确认'));
  expect(onPress).toHaveBeenCalledTimes(1);
});

it('does not call onPress when disabled', () => {
  const onPress = jest.fn();
  const { getByText } = render(
    <Button variant="primary" size="medium" disabled onPress={onPress}>
      确认
    </Button>
  );
  fireEvent.press(getByText('确认'));
  expect(onPress).not.toHaveBeenCalled();
});
```

---

## 附录：组件文件结构

```
src/
├── components/
│   ├── shared/
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.styles.ts
│   │   │   ├── Button.test.tsx
│   │   │   └── index.ts
│   │   ├── Card/
│   │   │   ├── Card.tsx
│   │   │   ├── Card.styles.ts
│   │   │   └── index.ts
│   │   ├── Tag/
│   │   ├── Avatar/
│   │   ├── ProgressBar/
│   │   ├── CircularProgress/
│   │   ├── MealCard/
│   │   ├── DataRecordCard/
│   │   ├── PlanCard/
│   │   ├── AIInputBar/
│   │   └── BottomTabs/
│   └── index.ts  // 统一导出
├── design-tokens/
│   ├── colors.ts
│   ├── typography.ts
│   ├── spacing.ts
│   ├── radius.ts
│   ├── shadows.ts
│   └── index.ts
└── types/
    └── components.ts  // 共享类型定义
```

统一导出示例：

```typescript
// src/components/index.ts
export { Button } from './shared/Button';
export { Card } from './shared/Card';
export { Tag } from './shared/Tag';
export { Avatar } from './shared/Avatar';
export { ProgressBar } from './shared/ProgressBar';
export { CircularProgress } from './shared/CircularProgress';
export { MealCard } from './shared/MealCard';
export { DataRecordCard } from './shared/DataRecordCard';
export { PlanCard } from './shared/PlanCard';
export { AIInputBar } from './shared/AIInputBar';
export { BottomTabs } from './shared/BottomTabs';

// 使用时
import { Button, Card, MealCard } from '@/components';
```
