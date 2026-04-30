# 反馈组件规范

> 本文档定义健康管家 AI Agent 移动端 App 的所有反馈类 UI 组件的详细规格，供前端开发直接使用。
> 基于：`02-components.md`（组件设计）、`01-design-system.md`（设计系统）

---

## 1. 组件清单

| 组件 | 用途 | 全局管理 |
|------|------|---------|
| **Toast** | 轻提示，操作反馈 | 全局单例 |
| **Modal** | 模态框，承载自定义内容 | 否 |
| **ConfirmDialog** | 确认对话框，二次确认操作 | 全局单例 |
| **BottomSheet** | 底部弹层，承载列表/表单等 | 否 |
| **EmptyState** | 空状态，无数据时的占位展示 | 否 |
| **LoadingSpinner** | 加载指示器 | 否 |
| **Skeleton** | 骨架屏，内容加载占位 | 否 |

---

## 2. 组件详细规格

### 2.1 Toast

#### 用途

操作反馈提示，用于告知用户操作结果（成功、失败、信息提示）。轻量级、自动消失，不打断用户操作流。

#### Props 定义

```typescript
interface ToastProps {
  /** 提示类型：成功、失败、信息 */
  type: 'success' | 'error' | 'info';
  /** 提示文案 */
  message: string;
  /** 显示时长，单位 ms，默认 2000 */
  duration?: number;
  /** 显示位置，默认 'top' */
  position?: 'top' | 'center' | 'bottom';
}
```

#### 样式规范

**位置与尺寸**
- 位置：顶部居中（top），距离顶部安全区 `16px`
- 宽度：屏宽 - `32px`（左右各 `16px` 边距）
- 最小高度：`44px`
- 内边距：`12px 16px`
- 圆角：`12px`

**类型颜色方案**

| 类型 | 背景色 | 文字颜色 | 图标 |
|------|--------|----------|------|
| success | `rgba(76,217,100,0.95)` | `#FFFFFF` | ✓ 对勾 |
| error | `rgba(255,90,95,0.95)` | `#FFFFFF` | ✗ 叉号 |
| info | `rgba(90,200,250,0.95)` | `#FFFFFF` | ⓘ 信息 |

**文字规范**
- 字号：`15px`
- 字重：Medium (500)
- 行高：`20px`
- 最多显示 2 行，超出省略

**动效**
- 入场：从顶部下滑 `20px` + 淡入，持续 `300ms`，缓动函数 `ease-out`
- 停留：默认 `2000ms`
- 离场：上移 `20px` + 淡出，持续 `200ms`，缓动函数 `ease-in`

**阴影**
- `0 4px 12px rgba(0,0,0,0.15)`

#### 使用方式

全局单例模式，通过静态方法调用：

```typescript
// 成功提示
Toast.show({ type: 'success', message: '保存成功' });

// 失败提示
Toast.show({ type: 'error', message: '网络连接失败，请重试' });

// 信息提示
Toast.show({ type: 'info', message: '数据已同步' });

// 自定义时长
Toast.show({
  type: 'success',
  message: '操作成功',
  duration: 3000
});

// 底部显示
Toast.show({
  type: 'info',
  message: '已复制到剪贴板',
  position: 'bottom'
});
```

---

### 2.2 Modal

#### 用途

模态框，用于承载自定义内容（表单、详情、选择器等），需要用户关注并完成操作后才能返回。

#### Props 定义

```typescript
interface ModalProps {
  /** 是否可见 */
  visible: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 模态框内容 */
  children: React.ReactNode;
  /** 动画类型，默认 'slide' */
  animationType?: 'slide' | 'fade';
  /** 是否显示关闭按钮，默认 true */
  showCloseButton?: boolean;
  /** 点击遮罩是否关闭，默认 true */
  closeOnMaskPress?: boolean;
}
```

#### 样式规范

**遮罩层**
- 背景色：`rgba(0,0,0,0.4)`
- 覆盖全屏
- 点击遮罩默认关闭 Modal

**内容区**
- 背景色：`#FFFFFF`
- 圆角：`16px`（仅顶部圆角，底部贴边）
- 最大高度：屏高 `90%`
- 内边距：`20px`
- 阴影：`0 -4px 16px rgba(0,0,0,0.12)`

**关闭按钮**
- 位置：右上角，距离边缘 `12px`
- 尺寸：`32×32px`
- 图标：✗ 叉号，`20×20px`
- 颜色：`#999999`
- 热区：`44×44px`

**动效**
- slide：从底部滑入，持续 `300ms`，缓动函数 `ease-out`
- fade：淡入，持续 `200ms`

#### 使用示例

```typescript
// 基础用法
<Modal visible={isVisible} onClose={handleClose}>
  <Text style={styles.title}>标题</Text>
  <Text style={styles.content}>这是模态框内容</Text>
  <Button onPress={handleConfirm}>确认</Button>
</Modal>

// 淡入动画
<Modal
  visible={isVisible}
  onClose={handleClose}
  animationType="fade"
>
  <View>{/* 内容 */}</View>
</Modal>

// 禁止点击遮罩关闭
<Modal
  visible={isVisible}
  onClose={handleClose}
  closeOnMaskPress={false}
>
  <View>{/* 内容 */}</View>
</Modal>
```

---

### 2.3 ConfirmDialog

#### 用途

确认对话框，用于二次确认操作（删除、退出、放弃等），防止误操作。

#### Props 定义

```typescript
interface ConfirmDialogProps {
  /** 是否可见 */
  visible: boolean;
  /** 标题 */
  title: string;
  /** 描述文案 */
  message: string;
  /** 确认按钮文案，默认 '确认' */
  confirmText?: string;
  /** 取消按钮文案，默认 '取消' */
  cancelText?: string;
  /** 确认回调 */
  onConfirm: () => void;
  /** 取消回调 */
  onCancel: () => void;
  /** 样式变体，默认 'default' */
  variant?: 'default' | 'danger';
}
```

#### 样式规范

**对话框容器**
- 宽度：屏宽 `78%`~`84%`（最大 `320px`）
- 背景色：`#FFFFFF`
- 圆角：`16px`
- 内边距：`20px`
- 阴影：`0 8px 24px rgba(0,0,0,0.2)`
- 居中显示

**遮罩层**
- 背景色：`rgba(0,0,0,0.4)`

**标题**
- 字号：`17px`
- 字重：SemiBold (600)
- 颜色：`#222222`
- 行高：`24px`
- 底部间距：`8px`

**描述文案**
- 字号：`15px`
- 字重：Regular (400)
- 颜色：`#666666`
- 行高：`22px`
- 底部间距：`20px`

**按钮区域**
- 布局：水平排列，等宽
- 按钮高度：`44px`
- 按钮圆角：`12px`
- 按钮间距：`12px`

**按钮样式（default 变体）**
- 取消按钮：背景 `#F7F8FA`，文字 `#666666`
- 确认按钮：背景 `#FF7A5C`，文字 `#FFFFFF`

**按钮样式（danger 变体）**
- 取消按钮：背景 `#F7F8FA`，文字 `#666666`
- 确认按钮：背景 `#FF5A5F`，文字 `#FFFFFF`

**动效**
- 入场：缩放从 `0.9` 到 `1.0` + 淡入，持续 `200ms`
- 离场：缩放从 `1.0` 到 `0.9` + 淡出，持续 `150ms`

#### 使用方式

全局单例模式，通过静态方法调用：

```typescript
// 基础确认
ConfirmDialog.show({
  title: '确认删除',
  message: '删除后无法恢复，确定要删除这条记录吗？',
  onConfirm: () => {
    // 执行删除
  },
  onCancel: () => {
    // 取消操作
  }
});

// 危险操作
ConfirmDialog.show({
  title: '退出登录',
  message: '退出后需要重新登录才能使用',
  confirmText: '退出',
  cancelText: '再想想',
  variant: 'danger',
  onConfirm: handleLogout,
  onCancel: () => {}
});

// 自定义按钮文案
ConfirmDialog.show({
  title: '放弃编辑',
  message: '当前内容尚未保存，确定要放弃吗？',
  confirmText: '放弃',
  cancelText: '继续编辑',
  onConfirm: handleDiscard,
  onCancel: () => {}
});
```

---

### 2.4 BottomSheet

#### 用途

底部弹层，用于承载列表选择、表单输入、筛选器等内容，支持拖拽交互和多档位高度。

#### Props 定义

```typescript
interface BottomSheetProps {
  /** 是否可见 */
  visible: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 弹层内容 */
  children: React.ReactNode;
  /** 停靠点位置，如 ['25%', '50%', '90%']，默认 ['50%', '90%'] */
  snapPoints?: string[];
  /** 初始停靠点索引，默认 0 */
  initialSnapIndex?: number;
  /** 是否启用拖拽，默认 true */
  enablePanDownToClose?: boolean;
}
```

#### 样式规范

**容器**
- 背景色：`#FFFFFF`
- 顶部圆角：`16px`
- 底部：贴边，包含安全区
- 阴影：`0 -4px 16px rgba(0,0,0,0.12)`

**拖拽条**
- 宽度：`36px`
- 高度：`4px`
- 圆角：`2px`
- 颜色：`#D9D9D9`
- 位置：顶部居中，距离顶部 `8px`
- 热区：`60×20px`

**内容区**
- 内边距：`16px`（顶部留出拖拽条空间，实际为 `28px`）
- 可滚动

**遮罩层**
- 背景色：`rgba(0,0,0,0.4)`
- 点击遮罩关闭

**动效**
- 入场：从底部滑入，持续 `300ms`，缓动函数 `ease-out`
- 拖拽：跟手，带阻尼
- 停靠：自动吸附到最近的 snapPoint，持续 `200ms`

#### 依赖库

使用 `@gorhom/bottom-sheet`：

```bash
npm install @gorhom/bottom-sheet@^4
```

#### 使用示例

```typescript
import BottomSheet from '@gorhom/bottom-sheet';

// 基础用法
<BottomSheet
  visible={isVisible}
  onClose={handleClose}
  snapPoints={['50%', '90%']}
>
  <View>
    <Text>底部弹层内容</Text>
  </View>
</BottomSheet>

// 单一高度
<BottomSheet
  visible={isVisible}
  onClose={handleClose}
  snapPoints={['60%']}
>
  <ScrollView>
    {/* 列表内容 */}
  </ScrollView>
</BottomSheet>

// 禁用拖拽关闭
<BottomSheet
  visible={isVisible}
  onClose={handleClose}
  snapPoints={['90%']}
  enablePanDownToClose={false}
>
  <View>{/* 表单内容 */}</View>
</BottomSheet>
```

---

### 2.5 EmptyState

#### 用途

空状态占位，用于列表、搜索结果、数据页面等无内容时的展示，引导用户进行操作。

#### Props 定义

```typescript
interface EmptyStateProps {
  /** 插画图片 */
  image: ImageSourcePropType;
  /** 标题文案 */
  title: string;
  /** 描述文案，可选 */
  description?: string;
  /** 操作按钮文案，可选 */
  actionText?: string;
  /** 操作按钮回调，可选 */
  onAction?: () => void;
}
```

#### 样式规范

**布局**
- 整体居中排布（水平 + 垂直）
- 内边距：`32px`

**插画**
- 尺寸：`200×200px`
- 底部间距：`24px`
- 内容模式：`contain`

**标题**
- 字号：`16px`
- 字重：SemiBold (600)
- 颜色：`#222222`
- 行高：`24px`
- 底部间距：`8px`

**描述文案**
- 字号：`14px`
- 字重：Regular (400)
- 颜色：`#666666`
- 行高：`20px`
- 底部间距：`24px`
- 最大宽度：`260px`
- 文本居中

**操作按钮**
- 高度：`44px`
- 圆角：`22px`
- 背景色：`#FF7A5C`（brand-primary）
- 文字颜色：`#FFFFFF`
- 字号：`15px`
- 字重：Medium (500)
- 内边距：`0 32px`
- 按下态背景：`#E96345`

#### 使用示例

```typescript
// 无数据
<EmptyState
  image={require('@/assets/images/empty-data.png')}
  title="暂无记录"
  description="开始记录你的第一餐吧"
  actionText="去记录"
  onAction={handleAddRecord}
/>

// 搜索无结果
<EmptyState
  image={require('@/assets/images/empty-search.png')}
  title="未找到相关食物"
  description="换个关键词试试"
/>

// 无网络
<EmptyState
  image={require('@/assets/images/empty-network.png')}
  title="网络连接失败"
  description="请检查网络设置后重试"
  actionText="重试"
  onAction={handleRetry}
/>
```

---

### 2.6 LoadingSpinner

#### 用途

加载指示器，用于数据加载、操作处理等等待场景。

#### Props 定义

```typescript
interface LoadingSpinnerProps {
  /** 尺寸，默认 'large' */
  size?: 'small' | 'large';
  /** 颜色，默认品牌色 */
  color?: string;
  /** 是否显示加载文案 */
  text?: string;
}
```

#### 样式规范

**尺寸**
- small：`20×20px`，用于按钮内、行内加载
- large：`36×36px`，用于页面级加载

**颜色**
- 默认：`#FF7A5C`（brand-primary）
- 可自定义

**加载文案**
- 字号：`14px`
- 颜色：`#999999`
- 与 Spinner 间距：`12px`
- 位于 Spinner 下方

**动效**
- 旋转动画：`360°` 循环，持续 `800ms`，线性缓动
- 使用 `react-native-reanimated` 实现

#### 使用示例

```typescript
// 页面级加载
<LoadingSpinner size="large" />

// 带文案
<LoadingSpinner size="large" text="加载中..." />

// 按钮内加载
<LoadingSpinner size="small" color="#FFFFFF" />

// 自定义颜色
<LoadingSpinner size="large" color="#4CD964" />
```

---

### 2.7 Skeleton

#### 用途

骨架屏，用于内容加载时的占位展示，提供视觉连续性，减少用户等待焦虑。

#### Props 定义

```typescript
interface SkeletonProps {
  /** 宽度，支持数字（px）或字符串（百分比） */
  width: number | string;
  /** 高度，单位 px */
  height: number;
  /** 圆角，默认 8 */
  borderRadius?: number;
  /** 是否启用动画，默认 true */
  animated?: boolean;
}
```

#### 样式规范

**基础样式**
- 背景色：`#F0F0F0`
- 默认圆角：`8px`

**动画效果**
- 类型：渐变扫过（shimmer）
- 渐变色：从 `#F0F0F0` → `#E0E0E0` → `#F0F0F0`
- 动画方向：从左到右
- 动画周期：`1500ms`
- 缓动函数：`ease-in-out`
- 使用 `react-native-reanimated` 实现

#### 预设组合

```typescript
// 文本行骨架
<Skeleton width="80%" height={16} borderRadius={4} />

// 头像骨架
<Skeleton width={48} height={48} borderRadius={24} />

// 卡片骨架
<Skeleton width="100%" height={120} borderRadius={12} />

// 组合示例：MealCard 骨架
const MealCardSkeleton = () => (
  <View style={styles.card}>
    <View style={styles.header}>
      <Skeleton width={80} height={20} borderRadius={4} />
      <Skeleton width={40} height={16} borderRadius={4} />
    </View>
    <Skeleton width="100%" height={16} borderRadius={4} />
    <Skeleton width="60%" height={16} borderRadius={4} />
    <View style={styles.footer}>
      <Skeleton width={100} height={32} borderRadius={16} />
    </View>
  </View>
);
```

---

## 3. 全局管理

Toast 和 ConfirmDialog 使用全局单例模式，避免在每个页面重复挂载组件。

### 3.1 Provider 注册

```typescript
// App.tsx
import { ToastProvider } from '@/components/shared/Toast';
import { ConfirmDialogProvider } from '@/components/shared/ConfirmDialog';

export default function App() {
  return (
    <ToastProvider>
      <ConfirmDialogProvider>
        <NavigationContainer>
          {/* 路由 */}
        </NavigationContainer>
      </ConfirmDialogProvider>
    </ToastProvider>
  );
}
```

### 3.2 全局调用方式

```typescript
import { Toast, ConfirmDialog } from '@/components';

// Toast 调用
Toast.show({ type: 'success', message: '保存成功' });
Toast.show({ type: 'error', message: '操作失败' });
Toast.show({ type: 'info', message: '数据已更新' });

// ConfirmDialog 调用
ConfirmDialog.show({
  title: '确认删除',
  message: '删除后无法恢复',
  variant: 'danger',
  confirmText: '删除',
  onConfirm: () => {
    deleteRecord(id);
    Toast.show({ type: 'success', message: '删除成功' });
  },
  onCancel: () => {}
});
```

### 3.3 实现原理

使用 React Context + Ref 实现全局单例：

```typescript
// Toast 实现思路
const toastRef = React.createRef<ToastHandle>();

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <>
      {children}
      <ToastComponent ref={toastRef} />
    </>
  );
};

export const Toast = {
  show: (props: ToastProps) => {
    toastRef.current?.show(props);
  },
  hide: () => {
    toastRef.current?.hide();
  }
};
```

---

## 4. 组件开发规范

### 4.1 TypeScript 类型定义

所有组件必须有完整的 TypeScript 类型定义：

```typescript
// ✅ 正确：使用联合类型和明确的函数签名
interface ToastProps {
  type: 'success' | 'error' | 'info';
  message: string;
  duration?: number;
  position?: 'top' | 'center' | 'bottom';
}

// ❌ 错误：使用 string、any、Function
interface ToastProps {
  type: string;
  message: any;
  onDismiss: Function;
}
```

### 4.2 样式分离

样式必须分离到 `.styles.ts` 文件：

```typescript
// Toast.tsx
import { styles } from './Toast.styles';

// Toast.styles.ts
import { StyleSheet } from 'react-native';
import { tokens } from '@/design-tokens';

export const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: tokens.space.lg,
    alignSelf: 'center',
    borderRadius: tokens.radius.md,
    paddingVertical: tokens.space.sm,
    paddingHorizontal: tokens.space.lg,
    minHeight: 44,
  },
  success: {
    backgroundColor: 'rgba(76,217,100,0.95)',
  },
  error: {
    backgroundColor: 'rgba(255,90,95,0.95)',
  },
  info: {
    backgroundColor: 'rgba(90,200,250,0.95)',
  },
  message: {
    color: tokens.color.textInverse,
    fontSize: tokens.font.body.size,
    fontWeight: '500',
  },
});
```

### 4.3 使用 Design Tokens

禁止硬编码颜色、尺寸等值，必须使用 Design Tokens：

```typescript
// ✅ 正确
backgroundColor: tokens.color.brandPrimary,
borderRadius: tokens.radius.lg,
padding: tokens.space.lg,

// ❌ 错误
backgroundColor: '#FF7A5C',
borderRadius: 16,
padding: 16,
```

### 4.4 动效使用 react-native-reanimated

所有动效统一使用 `react-native-reanimated`，保证 60fps 流畅度：

```typescript
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSpring,
  Easing,
} from 'react-native-reanimated';

// Toast 入场动画示例
const translateY = useSharedValue(-20);
const opacity = useSharedValue(0);

const animatedStyle = useAnimatedStyle(() => ({
  transform: [{ translateY: translateY.value }],
  opacity: opacity.value,
}));

const show = () => {
  translateY.value = withTiming(0, {
    duration: 300,
    easing: Easing.out(Easing.ease),
  });
  opacity.value = withTiming(1, { duration: 300 });
};
```

### 4.5 无障碍支持

所有反馈组件必须支持无障碍属性：

```typescript
// Toast
<View
  accessible
  accessibilityRole="alert"
  accessibilityLiveRegion="assertive"
  accessibilityLabel={`${type}提示：${message}`}
>
  <Text>{message}</Text>
</View>

// ConfirmDialog
<View
  accessible
  accessibilityRole="alert"
  accessibilityLabel={`确认对话框：${title}`}
>
  <TouchableOpacity
    accessibilityRole="button"
    accessibilityLabel={cancelText}
  />
  <TouchableOpacity
    accessibilityRole="button"
    accessibilityLabel={confirmText}
  />
</View>

// Modal
<View accessibilityViewIsModal>
  {children}
</View>
```

---

## 附录：组件文件结构

```
src/
├── components/
│   ├── shared/
│   │   ├── Toast/
│   │   │   ├── Toast.tsx
│   │   │   ├── Toast.styles.ts
│   │   │   ├── ToastProvider.tsx
│   │   │   ├── Toast.test.tsx
│   │   │   └── index.ts
│   │   ├── Modal/
│   │   │   ├── Modal.tsx
│   │   │   ├── Modal.styles.ts
│   │   │   ├── Modal.test.tsx
│   │   │   └── index.ts
│   │   ├── ConfirmDialog/
│   │   │   ├── ConfirmDialog.tsx
│   │   │   ├── ConfirmDialog.styles.ts
│   │   │   ├── ConfirmDialogProvider.tsx
│   │   │   ├── ConfirmDialog.test.tsx
│   │   │   └── index.ts
│   │   ├── BottomSheet/
│   │   │   ├── BottomSheet.tsx
│   │   │   ├── BottomSheet.styles.ts
│   │   │   ├── BottomSheet.test.tsx
│   │   │   └── index.ts
│   │   ├── EmptyState/
│   │   │   ├── EmptyState.tsx
│   │   │   ├── EmptyState.styles.ts
│   │   │   ├── EmptyState.test.tsx
│   │   │   └── index.ts
│   │   ├── LoadingSpinner/
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── LoadingSpinner.styles.ts
│   │   │   ├── LoadingSpinner.test.tsx
│   │   │   └── index.ts
│   │   └── Skeleton/
│   │       ├── Skeleton.tsx
│   │       ├── Skeleton.styles.ts
│   │       ├── Skeleton.test.tsx
│   │       └── index.ts
```

统一导出：

```typescript
// src/components/index.ts（追加）
export { Toast } from './shared/Toast';
export { Modal } from './shared/Modal';
export { ConfirmDialog } from './shared/ConfirmDialog';
export { BottomSheet } from './shared/BottomSheet';
export { EmptyState } from './shared/EmptyState';
export { LoadingSpinner } from './shared/LoadingSpinner';
export { Skeleton } from './shared/Skeleton';
```
