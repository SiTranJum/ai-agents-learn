# 素材管理规范

> 本文档定义"健康管家"前端项目的素材组织方式、命名规范和引用方式。

---

## 1. 素材目录结构

```
health-agent-app/
├── assets/
│   ├── images/
│   │   ├── logo/
│   │   │   ├── app-icon.png           # 1024x1024 App 图标
│   │   │   └── app-icon.svg           # 矢量版本（可选）
│   │   ├── illustrations/
│   │   │   ├── home-person.png        # 240x240 首页健康人物插画
│   │   │   ├── water-cup.png          # 80x80 饮水卡片插画
│   │   │   ├── exercise.png           # 80x80 运动卡片插画
│   │   │   ├── sleep.png              # 80x80 睡眠卡片插画
│   │   │   └── login-hero.png         # 240x240 登录页品牌插画
│   │   ├── empty-states/
│   │   │   ├── empty-diet.png         # 200x200 未记录饮食
│   │   │   ├── empty-plan.png         # 200x200 无计划
│   │   │   └── empty-data.png         # 200x200 无数据
│   │   └── mockups/
│   │       └── hero-phone.png         # 600x1200 官网 Hero 区手机 mockup
│   └── fonts/                          # 自定义字体（如需要）
│       └── (暂无)
└── src/
    └── constants/
        └── assets.ts                   # 素材路径常量定义
```

---

## 2. 图标方案

### 2.1 推荐方案：使用 @expo/vector-icons

**选择理由：**
- Expo 内置，无需额外安装
- 包含多个图标库（Feather、Ionicons、MaterialIcons 等）
- 矢量渲染，自动适配各分辨率
- 支持自定义颜色和尺寸

**安装（Expo 项目已内置）：**

```bash
npx expo install @expo/vector-icons
```

**统一使用 Feather 图标库**，风格简洁、线性、现代，与产品视觉语言一致。

### 2.2 引用方式

```tsx
import { Feather } from '@expo/vector-icons';

// 基本用法
<Feather name="home" size={24} color="#FF7A5C" />

// 在 Tab 导航中使用
<Feather name="home" size={24} color={focused ? '#FF7A5C' : '#999999'} />
```

### 2.3 Tab 导航图标映射

| Tab 名称 | 图标名称 | 默认态颜色 | 选中态颜色 |
|---------|---------|-----------|-----------|
| 首页 | `home` | #999999 | #FF7A5C |
| 饮食 | `coffee` | #999999 | #FF7A5C |
| 数据 | `bar-chart-2` | #999999 | #FF7A5C |
| 我的 | `user` | #999999 | #FF7A5C |

### 2.4 功能图标映射

| 功能 | 图标名称 | 尺寸 | 使用场景 |
|------|---------|------|---------|
| 拍照 | `camera` | 24 | AI 输入框左侧 |
| 语音 | `mic` | 24 | AI 输入框左侧 |
| 发送 | `send` | 24 | AI 输入框右侧 |
| 编辑 | `edit-2` | 20 | 卡片操作按钮 |
| 删除 | `trash-2` | 20 | 卡片操作按钮 |
| 确认 | `check` | 24 | 待确认卡片 |
| 取消 | `x` | 24 | 待确认卡片 |
| 添加 | `plus` | 24 | 新增记录入口 |
| 返回 | `arrow-left` | 24 | 页面顶部导航 |
| 设置 | `settings` | 24 | 个人中心 |
| 日历 | `calendar` | 20 | 日期选择器 |
| 时钟 | `clock` | 20 | 时间选择器 |
| 搜索 | `search` | 24 | 食物搜索 |
| 更多 | `more-horizontal` | 24 | 更多操作 |
| 信息 | `info` | 20 | 提示信息 |

### 2.5 图标尺寸规范

| 场景 | 尺寸 | 说明 |
|------|------|------|
| 标准 | 24px | Tab 图标、主要操作按钮 |
| 小 | 20px | 卡片内操作、辅助信息 |
| 大 | 28px | 强调性操作、空状态引导 |

---

## 3. 插画引用方式

### 3.1 路径常量定义

在 `src/constants/assets.ts` 中统一管理所有素材路径：

```ts
// src/constants/assets.ts

export const Images = {
  logo: {
    appIcon: require('../../assets/images/logo/app-icon.png'),
  },
  illustrations: {
    homePerson: require('../../assets/images/illustrations/home-person.png'),
    waterCup: require('../../assets/images/illustrations/water-cup.png'),
    exercise: require('../../assets/images/illustrations/exercise.png'),
    sleep: require('../../assets/images/illustrations/sleep.png'),
    loginHero: require('../../assets/images/illustrations/login-hero.png'),
  },
  emptyStates: {
    diet: require('../../assets/images/empty-states/empty-diet.png'),
    plan: require('../../assets/images/empty-states/empty-plan.png'),
    data: require('../../assets/images/empty-states/empty-data.png'),
  },
  mockups: {
    heroPhone: require('../../assets/images/mockups/hero-phone.png'),
  },
} as const;
```

### 3.2 组件中引用

```tsx
import { Image } from 'react-native';
import { Images } from '@/constants/assets';

// 插画引用
<Image source={Images.illustrations.homePerson} style={{ width: 120, height: 120 }} />

// 空状态引用
<Image source={Images.emptyStates.diet} style={{ width: 200, height: 200 }} />
```

### 3.3 插画尺寸与导出规范

所有插画导出 PNG 格式，提供 @2x 和 @3x 两个倍率：

| 素材 | 设计尺寸 | @2x 文件 | @3x 文件 |
|------|---------|---------|---------|
| 首页人物 | 240x240 | 480x480px | 720x720px |
| 饮水杯 | 80x80 | 160x160px | 240x240px |
| 运动 | 80x80 | 160x160px | 240x240px |
| 睡眠 | 80x80 | 160x160px | 240x240px |
| 登录插画 | 240x240 | 480x480px | 720x720px |

React Native 自动根据设备分辨率选择对应倍率文件，命名方式：

```
home-person.png      # @1x（可省略）
home-person@2x.png   # @2x
home-person@3x.png   # @3x
```

---

## 4. 空状态图

### 4.1 空状态素材清单

| 素材名称 | 文件名 | 尺寸 | 使用页面 | 配文 |
|---------|--------|------|---------|------|
| 未记录饮食 | `empty-diet.png` | 200x200 | 饮食记录页 | "还没有今天的饮食记录，和我聊聊吃了什么吧" |
| 无计划 | `empty-plan.png` | 200x200 | 计划列表页 | "还没有健康计划，让我帮你制定一个吧" |
| 无数据 | `empty-data.png` | 200x200 | 数据分析页 | "开始记录后就能看到数据分析啦" |

### 4.2 空状态组件封装

```tsx
// src/components/EmptyState.tsx
import { View, Image, Text, ImageSourcePropType, StyleSheet } from 'react-native';

interface EmptyStateProps {
  image: ImageSourcePropType;
  message: string;
}

export function EmptyState({ image, message }: EmptyStateProps) {
  return (
    <View style={styles.container}>
      <Image source={image} style={styles.image} resizeMode="contain" />
      <Text style={styles.message}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
  },
  image: {
    width: 200,
    height: 200,
    marginBottom: 16,
  },
  message: {
    fontSize: 14,
    color: '#999999',
    textAlign: 'center',
    lineHeight: 20,
  },
});
```

### 4.3 空状态设计原则

- 插画风格：扁平、圆润、积极正面，不使用负面情绪元素
- 配文语气：鼓励引导，像朋友对话，避免"你还没做 XX"的指责感
- 颜色：以品牌珊瑚橙 #FF7A5C 为主色调，搭配浅灰

---

## 5. Mockup 图

### 5.1 官网 Hero 区手机 Mockup

| 属性 | 值 |
|------|------|
| 文件名 | `hero-phone.png` |
| 尺寸 | 600x1200px |
| 用途 | 官网首屏主视觉 |
| 风格 | iPhone 14 Pro 真实感渲染，倾斜 15 度，带阴影 |
| 屏幕内容 | 健康管家首页 Dashboard 界面 |

### 5.2 Mockup 使用场景

- 官网 Hero 区展示
- App Store / Google Play 商店截图
- 社交媒体宣传素材

> 注：Mockup 图仅用于 Web 官网和营销场景，不打包进 App 内。

---

## 6. 字体加载

### 6.1 当前方案：使用系统默认字体

V1 版本使用系统默认字体栈，无需加载自定义字体：

```ts
// 字体栈定义
const fontFamily = {
  ios: 'System',           // San Francisco
  android: 'Roboto',       // Android 默认
};
```

### 6.2 后续扩展：自定义字体加载

如后续需要自定义字体（如品牌字体），使用 `expo-font` 加载：

```tsx
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';

// 防止启动页在字体加载前消失
SplashScreen.preventAutoHideAsync();

export default function App() {
  const [fontsLoaded] = useFonts({
    'Brand-Regular': require('./assets/fonts/Brand-Regular.ttf'),
    'Brand-Medium': require('./assets/fonts/Brand-Medium.ttf'),
    'Brand-Bold': require('./assets/fonts/Brand-Bold.ttf'),
  });

  if (!fontsLoaded) return null;

  // 字体加载完成后隐藏启动页
  SplashScreen.hideAsync();

  return <RootNavigator />;
}
```

### 6.3 字体文件存放

```
assets/
└── fonts/
    ├── Brand-Regular.ttf
    ├── Brand-Medium.ttf
    └── Brand-Bold.ttf
```

> V1 暂不使用自定义字体，此目录预留。

---

## 7. 素材命名规范

### 7.1 通用规则

| 规则 | 说明 | 示例 |
|------|------|------|
| 小写字母 | 文件名全部小写 | `home-person.png` |
| 连字符分隔 | 多个单词用 `-` 连接 | `empty-diet.png` |
| 语义化命名 | 名称反映内容或用途 | `water-cup.png`（非 `img01.png`） |
| 前缀分类 | 空状态图统一 `empty-` 前缀 | `empty-plan.png` |
| 倍率后缀 | 多倍率文件用 `@2x` `@3x` | `home-person@2x.png` |
| 禁止空格 | 文件名不含空格 | `login-hero.png`（非 `login hero.png`） |
| 禁止中文 | 文件名不使用中文字符 | `sleep.png`（非 `睡眠.png`） |

### 7.2 目录命名

| 目录 | 命名规则 | 说明 |
|------|---------|------|
| `logo/` | 品牌标识 | App 图标、Logo |
| `illustrations/` | 插画素材 | 页面装饰性插画 |
| `empty-states/` | 空状态图 | 各页面空态展示 |
| `mockups/` | 展示用 Mockup | 官网、商店截图 |
| `fonts/` | 字体文件 | 自定义字体 |

### 7.3 常量命名（TypeScript）

```ts
// 使用 camelCase，按类别分组
Images.illustrations.homePerson   // 插画 - 首页人物
Images.emptyStates.diet           // 空状态 - 饮食
Images.logo.appIcon               // Logo - App 图标
```

---

## 8. 素材清单

### 8.1 Logo

| # | 素材名称 | 文件名 | 尺寸 | 格式 | 用途 |
|---|---------|--------|------|------|------|
| 1 | App 图标 | `app-icon.png` | 1024x1024 | PNG | App 图标、启动页 |

### 8.2 插画

| # | 素材名称 | 文件名 | 设计尺寸 | 格式 | 用途 |
|---|---------|--------|---------|------|------|
| 2 | 首页健康人物 | `home-person.png` | 240x240 | PNG @2x/@3x | 首页概览卡片右侧装饰 |
| 3 | 饮水杯 | `water-cup.png` | 80x80 | PNG @2x/@3x | 饮水记录卡片装饰 |
| 4 | 运动人物 | `exercise.png` | 80x80 | PNG @2x/@3x | 运动记录卡片装饰 |
| 5 | 睡眠月亮 | `sleep.png` | 80x80 | PNG @2x/@3x | 睡眠记录卡片装饰 |
| 6 | 登录页品牌插画 | `login-hero.png` | 240x240 | PNG @2x/@3x | 登录/注册页顶部装饰 |

### 8.3 空状态图

| # | 素材名称 | 文件名 | 设计尺寸 | 格式 | 用途 |
|---|---------|--------|---------|------|------|
| 7 | 未记录饮食 | `empty-diet.png` | 200x200 | PNG @2x/@3x | 饮食页空态 |
| 8 | 无计划 | `empty-plan.png` | 200x200 | PNG @2x/@3x | 计划列表空态 |
| 9 | 无数据 | `empty-data.png` | 200x200 | PNG @2x/@3x | 数据分析空态 |

### 8.4 Mockup

| # | 素材名称 | 文件名 | 尺寸 | 格式 | 用途 |
|---|---------|--------|------|------|------|
| 10 | 手机 Mockup | `hero-phone.png` | 600x1200 | PNG | 官网 Hero 区主视觉 |

### 8.5 图标（使用 @expo/vector-icons/Feather，无需图片文件）

| # | 图标名称 | Feather name | 尺寸 | 使用场景 |
|---|---------|-------------|------|---------|
| 11 | 首页 Tab | `home` | 24 | 底部导航 |
| 12 | 饮食 Tab | `coffee` | 24 | 底部导航 |
| 13 | 数据 Tab | `bar-chart-2` | 24 | 底部导航 |
| 14 | 我的 Tab | `user` | 24 | 底部导航 |
| 15 | 拍照 | `camera` | 24 | AI 输入框 |
| 16 | 语音 | `mic` | 24 | AI 输入框 |
| 17 | 发送 | `send` | 24 | AI 输入框 |
| 18 | 编辑 | `edit-2` | 20 | 卡片操作 |
| 19 | 删除 | `trash-2` | 20 | 卡片操作 |
| 20 | 确认 | `check` | 24 | 待确认卡片 |
| 21 | 取消 | `x` | 24 | 待确认卡片 |
| 22 | 添加 | `plus` | 24 | 新增记录 |
| 23 | 返回 | `arrow-left` | 24 | 顶部导航 |
| 24 | 设置 | `settings` | 24 | 个人中心 |
| 25 | 日历 | `calendar` | 20 | 日期选择 |
| 26 | 时钟 | `clock` | 20 | 时间选择 |
| 27 | 搜索 | `search` | 24 | 食物搜索 |
| 28 | 更多 | `more-horizontal` | 24 | 更多操作 |
| 29 | 信息 | `info` | 20 | 提示信息 |

### 8.6 素材总览

| 类别 | 数量 | 需要生成 | 说明 |
|------|------|---------|------|
| Logo | 1 | 是 | AI 生成，参考 16-asset-prompts.md |
| 插画 | 5 | 是 | AI 生成，参考 16-asset-prompts.md |
| 空状态图 | 3 | 是 | AI 生成，参考 16-asset-prompts.md |
| Mockup | 1 | 是 | AI 生成或截图合成 |
| 图标 | 19 | 否 | 使用 @expo/vector-icons/Feather |
| **合计** | **29** | **10 个需生成** | |

> 所有需要生成的素材，其 AI 生成 Prompt 详见 `health-agent/docs/prd/v1/ui-design/16-asset-prompts.md`。
