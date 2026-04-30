# 图表组件规范

## 1. 图表库选择

### 推荐方案

**V1 推荐：`react-native-chart-kit`**

- **优势**：
  - 轻量级，打包体积小
  - 配置简单，上手快
  - 支持 React Native 和 Web（通过 react-native-web）
  - 内置常用图表类型
  - 样式可定制

- **备选方案：`victory-native`**
  - 功能更强大，交互更丰富
  - 学习曲线较陡
  - 适合复杂图表需求

### 安装

```bash
npm install react-native-chart-kit react-native-svg
```

## 2. 组件清单

| 组件 | 用途 | 使用场景 |
|------|------|---------|
| `LineChart` | 折线图 | 体重趋势、热量趋势、营养素趋势 |
| `BarChart` | 柱状图 | 营养素对比、每日热量对比 |
| `PieChart` | 饼图 | 营养素分布（碳水/蛋白质/脂肪） |
| `CircularProgress` | 环形进度图 | 热量进度、营养素目标进度 |

## 3. 组件详细规格

### 3.1 LineChart（折线图）

**用途**：展示趋势数据（体重、热量、营养素随时间变化）

**Props 定义**：

```typescript
interface LineChartProps {
  data: {
    labels: string[]; // X 轴标签，如 ["周一", "周二", "周三"]
    datasets: {
      data: number[]; // Y 轴数据点
      color?: string; // 线条颜色（可选）
      strokeWidth?: number; // 线条宽度（可选，默认 2）
    }[];
  };
  width: number; // 图表宽度（px）
  height: number; // 图表高度（px）
  yAxisSuffix?: string; // Y 轴单位，如 "kg"、"kcal"
  showGrid?: boolean; // 是否显示网格线（默认 true）
  showLegend?: boolean; // 是否显示图例（默认 false）
}
```

**样式规范**：

- **线条颜色**：品牌色 `#007AFF`（默认），或自定义颜色
- **线条宽度**：2px
- **网格线颜色**：`#EEEEEE`
- **标签字体**：12px Regular，颜色 `#666666`
- **数据点**：圆形，半径 4px
- **背景**：透明或白色

**使用示例**：

```typescript
<LineChart
  data={{
    labels: ["周一", "周二", "周三", "周四", "周五"],
    datasets: [{
      data: [65.2, 65.0, 64.8, 64.9, 64.7],
      color: "#007AFF",
      strokeWidth: 2
    }]
  }}
  width={350}
  height={220}
  yAxisSuffix=" kg"
  showGrid={true}
/>
```

### 3.2 BarChart（柱状图）

**用途**：展示对比数据（营养素对比、每日热量对比）

**Props 定义**：

```typescript
interface BarChartProps {
  data: {
    labels: string[]; // X 轴标签，如 ["碳水", "蛋白质", "脂肪"]
    datasets: {
      data: number[]; // 柱子高度数据
      colors?: string[]; // 每个柱子的颜色（可选）
    }[];
  };
  width: number; // 图表宽度（px）
  height: number; // 图表高度（px）
  yAxisSuffix?: string; // Y 轴单位，如 "g"
}
```

**样式规范**：

- **柱子颜色**：
  - 碳水化合物：`#5AC8FA`（蓝色）
  - 蛋白质：`#4CD964`（绿色）
  - 脂肪：`#FFC94D`（黄色）
- **柱子圆角**：顶部 4px 圆角
- **柱子间距**：8px
- **标签字体**：12px Regular，颜色 `#666666`

**使用示例**：

```typescript
<BarChart
  data={{
    labels: ["碳水", "蛋白质", "脂肪"],
    datasets: [{
      data: [180, 85, 45],
      colors: ["#5AC8FA", "#4CD964", "#FFC94D"]
    }]
  }}
  width={350}
  height={220}
  yAxisSuffix=" g"
/>
```

### 3.3 PieChart（饼图）

**用途**：展示分布数据（营养素分布）

**Props 定义**：

```typescript
interface PieChartProps {
  data: {
    name: string; // 数据项名称，如 "碳水化合物"
    value: number; // 数据项数值
    color: string; // 扇形颜色
    legendFontColor?: string; // 图例文字颜色（可选）
    legendFontSize?: number; // 图例文字大小（可选）
  }[];
  width: number; // 图表宽度（px）
  height: number; // 图表高度（px）
  showLegend?: boolean; // 是否显示图例（默认 true）
}
```

**样式规范**：

- **颜色方案**：
  - 碳水化合物：`#5AC8FA`（蓝色）
  - 蛋白质：`#4CD964`（绿色）
  - 脂肪：`#FFC94D`（黄色）
- **图例位置**：右侧或底部（根据空间自适应）
- **图例字体**：12px Regular，颜色 `#333333`
- **扇形间隙**：无间隙（紧密拼接）

**使用示例**：

```typescript
<PieChart
  data={[
    { name: "碳水", value: 180, color: "#5AC8FA" },
    { name: "蛋白质", value: 85, color: "#4CD964" },
    { name: "脂肪", value: 45, color: "#FFC94D" }
  ]}
  width={350}
  height={220}
  showLegend={true}
/>
```

### 3.4 CircularProgress（环形进度图）

**用途**：展示进度数据（热量进度、营养素目标进度）

**Props 定义**：

```typescript
interface CircularProgressProps {
  current: number; // 当前值
  target: number; // 目标值
  size: number; // 圆环直径（px）
  strokeWidth: number; // 圆环宽度（px）
  color?: string; // 填充颜色（可选，默认品牌色）
  showLabel?: boolean; // 是否显示中心文字（默认 true）
  unit?: string; // 单位，如 "kcal"
}
```

**样式规范**：

- **轨道颜色**：`#F0F0F0`（浅灰色）
- **填充颜色**：品牌色 `#007AFF`（默认），或自定义颜色
- **中心文字**：
  - 主文字：`current/target`，如 "1500/2000"
  - 字体：16px Semibold，颜色 `#333333`
  - 副文字：单位，如 "kcal"
  - 字体：12px Regular，颜色 `#999999`
- **进度超标**：当 `current > target` 时，填充颜色变为警告色 `#FF3B30`

**使用示例**：

```typescript
<CircularProgress
  current={1500}
  target={2000}
  size={120}
  strokeWidth={12}
  color="#007AFF"
  showLabel={true}
  unit="kcal"
/>
```

## 4. 图表交互

### 4.1 Web 端交互

- **鼠标悬停**：显示具体数值的 Tooltip
  - 位置：鼠标上方或数据点上方
  - 样式：白色背景，阴影，圆角 4px
  - 内容：标签 + 数值 + 单位
- **点击数据点**：显示详情弹窗或跳转到详情页
- **缩放和拖拽**：长时间范围数据支持缩放和拖拽（如 30 天以上）

### 4.2 移动端交互

- **触摸高亮**：触摸数据点时高亮显示
- **长按**：显示详情信息
- **双指缩放**：支持图表缩放（可选）

## 5. 响应式设计

### 5.1 宽度自适应

- 图表宽度根据容器自适应
- 使用 `Dimensions.get('window').width` 获取屏幕宽度
- 预留左右边距（16px）

```typescript
import { Dimensions } from 'react-native';

const screenWidth = Dimensions.get('window').width;
const chartWidth = screenWidth - 32; // 左右各 16px 边距
```

### 5.2 高度设置

- **固定高度**：220px（默认）
- **按比例**：宽度的 60%（可选）

### 5.3 标签处理

- **标签过多**：自动旋转 45° 或隐藏部分标签
- **标签过长**：截断并显示省略号
- **自适应字体**：根据图表宽度调整字体大小

## 6. 性能优化

### 6.1 数据采样

- **数据点过多**：超过 50 个数据点时自动采样
- **采样策略**：
  - 保留首尾数据点
  - 中间数据点按间隔采样
  - 保留极值点（最大值、最小值）

```typescript
function sampleData(data: number[], maxPoints: number = 50): number[] {
  if (data.length <= maxPoints) return data;

  const step = Math.ceil(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
}
```

### 6.2 避免重复渲染

- 使用 `React.memo` 包裹图表组件
- 使用 `useMemo` 缓存图表数据

```typescript
const MemoizedLineChart = React.memo(LineChart);

const chartData = useMemo(() => ({
  labels: labels,
  datasets: [{ data: data }]
}), [labels, data]);
```

### 6.3 懒加载

- 图表库按需加载，不在首屏加载
- 使用 `React.lazy` 和 `Suspense`

```typescript
const LineChart = React.lazy(() => import('./charts/LineChart'));

<Suspense fallback={<LoadingSpinner />}>
  <LineChart data={chartData} />
</Suspense>
```

### 6.4 虚拟化

- 长列表中的图表使用虚拟化渲染
- 只渲染可见区域的图表

## 7. 无障碍支持

- **语义化标签**：为图表添加 `accessibilityLabel`
- **屏幕阅读器**：提供数据摘要描述
- **键盘导航**：支持键盘切换数据点（Web 端）

```typescript
<LineChart
  accessibilityLabel="体重趋势图，显示最近 7 天的体重变化"
  data={chartData}
/>
```

## 8. 错误处理

### 8.1 数据异常

- **空数据**：显示空状态提示
- **数据格式错误**：显示错误提示
- **数据缺失**：用占位符或虚线表示

### 8.2 渲染失败

- 使用 Error Boundary 捕获渲染错误
- 显示降级 UI（如表格或文字描述）

```typescript
<ErrorBoundary fallback={<ChartErrorFallback />}>
  <LineChart data={chartData} />
</ErrorBoundary>
```

## 9. 主题支持

### 9.1 浅色主题（默认）

- 背景：白色或透明
- 文字：深色（`#333333`、`#666666`）
- 网格线：浅灰色（`#EEEEEE`）

### 9.2 深色主题

- 背景：深色（`#1C1C1E`）
- 文字：浅色（`#FFFFFF`、`#CCCCCC`）
- 网格线：深灰色（`#3A3A3C`）

```typescript
const chartConfig = {
  backgroundColor: theme === 'dark' ? '#1C1C1E' : '#FFFFFF',
  color: (opacity = 1) => theme === 'dark'
    ? `rgba(255, 255, 255, ${opacity})`
    : `rgba(0, 0, 0, ${opacity})`,
  labelColor: (opacity = 1) => theme === 'dark'
    ? `rgba(204, 204, 204, ${opacity})`
    : `rgba(102, 102, 102, ${opacity})`,
};
```

## 10. 测试建议

### 10.1 单元测试

- 测试数据转换逻辑
- 测试采样算法
- 测试边界情况（空数据、单点数据）

### 10.2 快照测试

- 对图表组件进行快照测试
- 确保样式一致性

### 10.3 视觉回归测试

- 使用 Storybook 展示不同状态的图表
- 使用 Chromatic 进行视觉回归测试

---

**相关文档**：
- UI 组件规范：`02-components.md`
- 数据页面规范：`06-data-page.md`
- 分析页面规范：`11-analysis-page.md`
- 设计系统：`01-design-system.md`
