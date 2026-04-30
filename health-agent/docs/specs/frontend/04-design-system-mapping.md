# Design System TypeScript 映射

> 将设计系统 Design Tokens 映射为 TypeScript 代码结构，用于前端开发。

---

## 1. 映射规则

### 1.1 命名规范

- **Token 命名**：使用 kebab-case（如 `brand-primary`）
- **TypeScript 变量**：使用 camelCase（如 `brandPrimary`）
- **CSS 变量**：使用 `--` 前缀（如 `--brand-primary`）

### 1.2 文件组织

```
src/
├── styles/
│   ├── tokens/
│   │   ├── colors.ts          # 颜色 Token
│   │   ├── typography.ts      # 字体 Token
│   │   ├── spacing.ts         # 间距 Token
│   │   ├── radius.ts          # 圆角 Token
│   │   ├── shadow.ts          # 阴影 Token
│   │   ├── icon.ts            # 图标 Token
│   │   └── animation.ts       # 动效 Token
│   ├── theme.ts               # 主题配置（汇总所有 Token）
│   └── global.css             # 全局 CSS 变量
```

---

## 2. 颜色系统

### 2.1 TypeScript 定义

```typescript
// src/styles/tokens/colors.ts

/**
 * 品牌色
 */
export const brandColors = {
  primary: '#FF7A5C',        // 珊瑚橙 - 主按钮、Tab 高亮、进度条
  primaryDark: '#E96345',    // 深色 - 按钮按下态、深色文字强调
  primaryLight: '#FFE7E1',   // 浅色 - 待确认卡片背景、浅色标签
} as const;

/**
 * 功能色
 */
export const functionalColors = {
  success: '#4CD964',        // 达标、完成、正常状态
  warning: '#FFC94D',        // 接近目标、注意提示
  info: '#5AC8FA',           // 链接、信息提示
  error: '#FF5A5F',          // 超标、错误、删除
} as const;

/**
 * 中性色
 */
export const neutralColors = {
  bgPage: '#F7F8FA',         // 页面背景
  bgCard: '#FFFFFF',         // 卡片背景
  textPrimary: '#222222',    // 标题、重要数值
  textSecondary: '#666666',  // 正文、说明
  textTertiary: '#999999',   // 辅助文字、placeholder
  borderDivider: '#EEEEEE',  // 分割线
  disabled: '#CCCCCC',       // 禁用态文字、禁用态边框
} as const;

/**
 * 所有颜色 Token
 */
export const colors = {
  brand: brandColors,
  functional: functionalColors,
  neutral: neutralColors,
} as const;

/**
 * 颜色类型定义
 */
export type BrandColor = keyof typeof brandColors;
export type FunctionalColor = keyof typeof functionalColors;
export type NeutralColor = keyof typeof neutralColors;
```

### 2.2 CSS 变量映射

```css
/* src/styles/global.css */

:root {
  /* 品牌色 */
  --brand-primary: #FF7A5C;
  --brand-primary-dark: #E96345;
  --brand-primary-light: #FFE7E1;

  /* 功能色 */
  --color-success: #4CD964;
  --color-warning: #FFC94D;
  --color-info: #5AC8FA;
  --color-error: #FF5A5F;

  /* 中性色 */
  --bg-page: #F7F8FA;
  --bg-card: #FFFFFF;
  --text-primary: #222222;
  --text-secondary: #666666;
  --text-tertiary: #999999;
  --border-divider: #EEEEEE;
  --color-disabled: #CCCCCC;
}
```

---

## 3. 字体系统

### 3.1 TypeScript 定义

```typescript
// src/styles/tokens/typography.ts

/**
 * 字体家族
 */
export const fontFamilies = {
  ios: {
    chinese: 'PingFang SC',
    english: 'SF Pro',
    numeric: 'DIN Alternate',  // 核心数值专用
  },
  android: {
    chinese: 'Noto Sans CJK SC',
    english: 'Roboto',
    numeric: 'Roboto Mono',    // 核心数值专用
  },
} as const;

/**
 * 字体层级
 */
export const typography = {
  hero: {
    fontSize: '36px',
    fontWeight: 700,          // Bold
    lineHeight: '44px',
    letterSpacing: '-0.5px',
    usage: '核心数值展示',
  },
  pageTitle: {
    fontSize: '24px',
    fontWeight: 700,          // Bold
    lineHeight: '32px',
    letterSpacing: '0',
    usage: '页面顶部标题',
  },
  cardTitle: {
    fontSize: '18px',
    fontWeight: 600,          // SemiBold
    lineHeight: '26px',
    letterSpacing: '0',
    usage: '卡片内标题',
  },
  body: {
    fontSize: '16px',
    fontWeight: 400,          // Regular
    lineHeight: '24px',
    letterSpacing: '0.2px',
    usage: '主要内容文字',
  },
  bodySm: {
    fontSize: '14px',
    fontWeight: 400,          // Regular
    lineHeight: '20px',
    letterSpacing: '0.1px',
    usage: '次要内容',
  },
  caption: {
    fontSize: '13px',
    fontWeight: 400,          // Regular
    lineHeight: '18px',
    letterSpacing: '0.1px',
    usage: '辅助说明',
  },
  tag: {
    fontSize: '12px',
    fontWeight: 500,          // Medium
    lineHeight: '16px',
    letterSpacing: '0.2px',
    usage: '标签、badge',
  },
} as const;

/**
 * 字体类型定义
 */
export type TypographyLevel = keyof typeof typography;
```

### 3.2 CSS 变量映射

```css
/* src/styles/global.css */

:root {
  /* 字体层级 */
  --font-hero-size: 36px;
  --font-hero-weight: 700;
  --font-hero-line-height: 44px;
  --font-hero-letter-spacing: -0.5px;

  --font-page-title-size: 24px;
  --font-page-title-weight: 700;
  --font-page-title-line-height: 32px;
  --font-page-title-letter-spacing: 0;

  --font-card-title-size: 18px;
  --font-card-title-weight: 600;
  --font-card-title-line-height: 26px;
  --font-card-title-letter-spacing: 0;

  --font-body-size: 16px;
  --font-body-weight: 400;
  --font-body-line-height: 24px;
  --font-body-letter-spacing: 0.2px;

  --font-body-sm-size: 14px;
  --font-body-sm-weight: 400;
  --font-body-sm-line-height: 20px;
  --font-body-sm-letter-spacing: 0.1px;

  --font-caption-size: 13px;
  --font-caption-weight: 400;
  --font-caption-line-height: 18px;
  --font-caption-letter-spacing: 0.1px;

  --font-tag-size: 12px;
  --font-tag-weight: 500;
  --font-tag-line-height: 16px;
  --font-tag-letter-spacing: 0.2px;
}
```

---

## 4. 间距系统

### 4.1 TypeScript 定义

```typescript
// src/styles/tokens/spacing.ts

/**
 * 间距 Token（基础单位 4px）
 */
export const spacing = {
  xs: '4px',    // 图标与文字间距、紧凑元素内间距
  sm: '8px',    // 标签内边距、紧凑列表项间距、区域标题与内容间距
  md: '12px',   // 卡片间距、列表项间距
  lg: '16px',   // 页面左右边距、卡片内边距、区域间距
  xl: '24px',   // 大区域间距、页面顶部留白
  xxl: '32px',  // 页面底部留白、大区域分隔
} as const;

/**
 * 页面布局常量
 */
export const layout = {
  pageHorizontalPadding: '16px',  // 页面左右边距
  cardPadding: '16px',            // 卡片内边距
  cardGap: '12px',                // 卡片间距
  bottomSafeArea: '116px',        // 底部安全区（Tab 60px + 输入框 56px）
  tabBarHeight: '60px',           // 底部 Tab 导航高度
  aiInputHeight: '56px',          // AI 输入框高度
} as const;

/**
 * 间距类型定义
 */
export type SpacingSize = keyof typeof spacing;
```

### 4.2 CSS 变量映射

```css
/* src/styles/global.css */

:root {
  /* 间距 */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-lg: 16px;
  --space-xl: 24px;
  --space-xxl: 32px;

  /* 布局常量 */
  --page-horizontal-padding: 16px;
  --card-padding: 16px;
  --card-gap: 12px;
  --bottom-safe-area: 116px;
  --tab-bar-height: 60px;
  --ai-input-height: 56px;
}
```

---

## 5. 圆角系统

### 5.1 TypeScript 定义

```typescript
// src/styles/tokens/radius.ts

/**
 * 圆角 Token
 */
export const radius = {
  sm: '8px',      // 小按钮、标签
  md: '12px',     // 卡片
  lg: '16px',     // 弹层、底部面板（仅顶部圆角）
  pill: '24px',   // 输入框、胶囊按钮
  full: '999px',  // 头像、圆形按钮
} as const;

/**
 * 圆角类型定义
 */
export type RadiusSize = keyof typeof radius;
```

### 5.2 CSS 变量映射

```css
/* src/styles/global.css */

:root {
  /* 圆角 */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-pill: 24px;
  --radius-full: 999px;
}
```

---

## 6. 阴影系统

### 6.1 TypeScript 定义

```typescript
// src/styles/tokens/shadow.ts

/**
 * 阴影 Token
 */
export const shadow = {
  card: '0 2px 8px rgba(0, 0, 0, 0.06)',           // 卡片 - 轻阴影
  input: '0 -2px 8px rgba(0, 0, 0, 0.04)',         // AI 输入框 - 向上阴影
  modal: '0 -4px 16px rgba(0, 0, 0, 0.1)',         // 弹层、浮层 - 较重阴影
  brandButton: '0 4px 12px rgba(255, 122, 92, 0.3)', // 主按钮悬浮态 - 品牌色阴影
} as const;

/**
 * 阴影类型定义
 */
export type ShadowType = keyof typeof shadow;
```

### 6.2 CSS 变量映射

```css
/* src/styles/global.css */

:root {
  /* 阴影 */
  --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.06);
  --shadow-input: 0 -2px 8px rgba(0, 0, 0, 0.04);
  --shadow-modal: 0 -4px 16px rgba(0, 0, 0, 0.1);
  --shadow-brand-button: 0 4px 12px rgba(255, 122, 92, 0.3);
}
```

---

## 7. 图标系统

### 7.1 TypeScript 定义

```typescript
// src/styles/tokens/icon.ts

/**
 * 图标尺寸
 */
export const iconSize = {
  nav: '24px',      // 底部 Tab 导航
  list: '20px',     // 列表项前缀图标
  inline: '16px',   // 文字内嵌图标
  action: '28px',   // AI 输入框内的拍照、语音按钮
} as const;

/**
 * 图标点击热区
 */
export const iconHitArea = {
  nav: '44px',      // 底部 Tab 导航
  list: '36px',     // 列表项前缀图标
  action: '44px',   // AI 输入框内的拍照、语音按钮
} as const;

/**
 * 图标样式配置
 */
export const iconStyle = {
  strokeWidth: '1.5px',           // 线宽
  defaultColor: '#999999',        // 默认颜色（text-tertiary）
  activeColor: '#FF7A5C',         // 激活/选中颜色（brand-primary）
  style: 'outline',               // 风格：线性图标
  cap: 'round',                   // 端点：圆角
  join: 'round',                  // 连接：圆角
} as const;

/**
 * Tab 导航图标配置
 */
export const tabIcons = {
  home: {
    name: 'Home',
    description: '房子轮廓',
  },
  diet: {
    name: 'ForkKnife',
    description: '餐盘 + 刀叉轮廓',
  },
  data: {
    name: 'ChartBar',
    description: '柱状图轮廓',
  },
  profile: {
    name: 'User',
    description: '人物轮廓',
  },
} as const;

/**
 * 图标类型定义
 */
export type IconSize = keyof typeof iconSize;
export type TabIconName = keyof typeof tabIcons;
```

### 7.2 CSS 变量映射

```css
/* src/styles/global.css */

:root {
  /* 图标尺寸 */
  --icon-nav-size: 24px;
  --icon-list-size: 20px;
  --icon-inline-size: 16px;
  --icon-action-size: 28px;

  /* 图标点击热区 */
  --icon-nav-hit-area: 44px;
  --icon-list-hit-area: 36px;
  --icon-action-hit-area: 44px;

  /* 图标样式 */
  --icon-stroke-width: 1.5px;
  --icon-default-color: #999999;
  --icon-active-color: #FF7A5C;
}
```

---

## 8. 动效系统

### 8.1 TypeScript 定义

```typescript
// src/styles/tokens/animation.ts

/**
 * 基础动效配置
 */
export const animation = {
  pageTransition: {
    duration: '300ms',
    easing: 'ease-in-out',
    description: '页面切换 - 左右滑动过渡',
  },
  cardStateChange: {
    duration: '200ms',
    easing: 'ease',
    description: '卡片状态变化 - 背景色、边框色渐变过渡',
  },
  modalShow: {
    duration: '250ms',
    easing: 'ease-out',
    description: '弹窗出现 - 从底部滑入 + 背景蒙层渐显',
  },
  modalHide: {
    duration: '200ms',
    easing: 'ease-in',
    description: '弹窗消失 - 向下滑出 + 背景蒙层渐隐',
  },
  toastShow: {
    duration: '200ms',
    easing: 'ease-out',
    description: 'Toast 出现 - 从顶部滑入',
  },
  toastHide: {
    duration: '300ms',
    easing: 'ease-in',
    description: 'Toast 消失 - 向上滑出 + 透明度渐变',
  },
  numberChange: {
    duration: '400ms',
    easing: 'ease-out',
    description: '数值变化 - 数字滚动动画',
  },
  progressFill: {
    duration: '500ms',
    easing: 'ease-out',
    description: '进度条填充 - 从 0 到目标值的填充动画',
  },
} as const;

/**
 * 交互反馈配置
 */
export const interaction = {
  buttonClick: {
    scale: 0.95,
    duration: '100ms',
    description: '按钮点击 - 缩放反馈',
  },
  cardClick: {
    backgroundColor: '#F5F5F5',
    duration: '100ms',
    description: '卡片点击 - 背景色变浅',
  },
  longPress: {
    scale: 0.98,
    duration: '200ms',
    description: '长按 - 缩放 + 阴影加深',
  },
  aiThinking: {
    duration: '300ms',
    description: 'AI 思考中 - 三个点依次跳动',
  },
} as const;

/**
 * 动效类型定义
 */
export type AnimationType = keyof typeof animation;
export type InteractionType = keyof typeof interaction;
```

### 8.2 CSS 变量映射

```css
/* src/styles/global.css */

:root {
  /* 基础动效 */
  --animation-page-transition-duration: 300ms;
  --animation-page-transition-easing: ease-in-out;

  --animation-card-state-duration: 200ms;
  --animation-card-state-easing: ease;

  --animation-modal-show-duration: 250ms;
  --animation-modal-show-easing: ease-out;

  --animation-modal-hide-duration: 200ms;
  --animation-modal-hide-easing: ease-in;

  --animation-toast-show-duration: 200ms;
  --animation-toast-show-easing: ease-out;

  --animation-toast-hide-duration: 300ms;
  --animation-toast-hide-easing: ease-in;

  --animation-number-change-duration: 400ms;
  --animation-number-change-easing: ease-out;

  --animation-progress-fill-duration: 500ms;
  --animation-progress-fill-easing: ease-out;

  /* 交互反馈 */
  --interaction-button-click-scale: 0.95;
  --interaction-button-click-duration: 100ms;

  --interaction-card-click-bg: #F5F5F5;
  --interaction-card-click-duration: 100ms;

  --interaction-long-press-scale: 0.98;
  --interaction-long-press-duration: 200ms;

  --interaction-ai-thinking-duration: 300ms;
}
```

---

## 9. 响应式规则

### 9.1 TypeScript 定义

```typescript
// src/styles/tokens/breakpoints.ts

/**
 * 响应式断点
 */
export const breakpoints = {
  mobile: '375px',      // 移动端基准（iPhone SE）
  tablet: '768px',      // 平板
  desktop: '1024px',    // 桌面端
} as const;

/**
 * 设备类型判断
 */
export const deviceQuery = {
  mobile: `(max-width: ${breakpoints.tablet})`,
  tablet: `(min-width: ${breakpoints.tablet}) and (max-width: ${breakpoints.desktop})`,
  desktop: `(min-width: ${breakpoints.desktop})`,
} as const;

/**
 * 响应式类型定义
 */
export type Breakpoint = keyof typeof breakpoints;
export type DeviceType = keyof typeof deviceQuery;
```

### 9.2 CSS 媒体查询

```css
/* src/styles/global.css */

/* 移动端优先（默认样式） */
:root {
  /* 移动端基准尺寸 */
  --viewport-width: 375px;
}

/* 平板适配 */
@media (min-width: 768px) {
  :root {
    --page-horizontal-padding: 24px;
    --card-padding: 20px;
  }
}

/* 桌面端适配 */
@media (min-width: 1024px) {
  :root {
    --page-horizontal-padding: 32px;
    --card-padding: 24px;
  }
}
```

---

## 10. 主题配置汇总

### 10.1 TypeScript 主题对象

```typescript
// src/styles/theme.ts

import { colors } from './tokens/colors';
import { typography } from './tokens/typography';
import { spacing, layout } from './tokens/spacing';
import { radius } from './tokens/radius';
import { shadow } from './tokens/shadow';
import { iconSize, iconHitArea, iconStyle, tabIcons } from './tokens/icon';
import { animation, interaction } from './tokens/animation';
import { breakpoints, deviceQuery } from './tokens/breakpoints';

/**
 * 完整主题配置
 */
export const theme = {
  colors,
  typography,
  spacing,
  layout,
  radius,
  shadow,
  icon: {
    size: iconSize,
    hitArea: iconHitArea,
    style: iconStyle,
    tab: tabIcons,
  },
  animation,
  interaction,
  breakpoints,
  deviceQuery,
} as const;

/**
 * 主题类型定义
 */
export type Theme = typeof theme;

/**
 * 默认导出
 */
export default theme;
```

---

## 11. 使用示例

### 11.1 在 React 组件中使用

```typescript
import { theme } from '@/styles/theme';

// 示例：主按钮组件
const PrimaryButton = styled.button`
  background-color: ${theme.colors.brand.primary};
  color: ${theme.colors.neutral.bgCard};
  font-size: ${theme.typography.body.fontSize};
  font-weight: ${theme.typography.body.fontWeight};
  padding: ${theme.spacing.sm} ${theme.spacing.lg};
  border-radius: ${theme.radius.sm};
  box-shadow: ${theme.shadow.brandButton};
  transition: transform ${theme.interaction.buttonClick.duration};

  &:active {
    transform: scale(${theme.interaction.buttonClick.scale});
  }
`;
```

### 11.2 在 CSS 中使用变量

```css
/* 示例：卡片样式 */
.card {
  background-color: var(--bg-card);
  padding: var(--card-padding);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  margin-bottom: var(--card-gap);
}

/* 示例：页面标题 */
.page-title {
  font-size: var(--font-page-title-size);
  font-weight: var(--font-page-title-weight);
  line-height: var(--font-page-title-line-height);
  color: var(--text-primary);
  margin-bottom: var(--space-xl);
}
```

---

## 12. 注意事项

### 12.1 命名一致性

- TypeScript 变量使用 camelCase
- CSS 变量使用 kebab-case
- 保持两者语义一致，便于查找和维护

### 12.2 类型安全

- 所有 Token 使用 `as const` 确保类型推断
- 导出类型定义，供组件使用
- 避免硬编码值，统一使用 Token

### 12.3 扩展性

- 新增 Token 时，同步更新 TypeScript 和 CSS
- 保持文件结构清晰，按类别组织
- 主题配置集中管理，便于切换（如深色模式）

### 12.4 性能优化

- CSS 变量在运行时可动态修改
- TypeScript 常量在编译时优化
- 优先使用 CSS 变量实现主题切换
