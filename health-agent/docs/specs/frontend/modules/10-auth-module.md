# 认证模块前端实现规格

> 模块编号：M10
> 模块名称：Auth Module（认证模块）
> 对应 PRD：`health-agent/docs/prd/v1/01-user-system.md`
> 对应 UI 设计：`health-agent/docs/prd/v1/ui-design/13-auth-and-onboarding.md`
> 优先级：P0
> 预计工时：3-4 天

---

## 1. 模块职责

认证模块负责用户的身份验证和初始档案建立流程，包括：

- **登录**：邮箱 + 密码登录，支持表单验证和错误处理
- **注册**：邮箱 + 密码注册，引导用户创建健康档案
- **忘记密码**：通过邮箱发送密码重置链接
- **Onboarding 引导**：分步表单收集用户基础档案、饮食偏好、疾病信息

---

## 2. 对应 UI 设计文稿

本模块实现基于以下 UI 设计文档：

- **主要文稿**：`health-agent/docs/prd/v1/ui-design/13-auth-and-onboarding.md`
- **设计系统**：`health-agent/docs/prd/v1/ui-design/01-design-system.md`
- **通用组件**：`health-agent/docs/prd/v1/ui-design/02-components.md`

---

## 3. 页面列表

| 页面编号 | 页面名称 | 路由 | 说明 |
|---------|---------|------|------|
| P13 | LoginScreen | `/login` | 登录页 |
| P14 | RegisterScreen | `/register` | 注册页 |
| P15 | ForgotPasswordScreen | `/forgot-password` | 忘记密码页 |
| P16 | OnboardingScreen | `/onboarding` | 引导页（分步表单，5 步 + 预览） |

---

## 4. 页面详细规格

### P13 LoginScreen

**页面职责**

邮箱 + 密码登录，验证用户身份后进入主应用。

**对应 UI 文稿**

`13-auth-and-onboarding.md` 页面 A：登录页

**页面结构**

```
顶部 Logo + 品牌名"健康管家"
  ↓ 40px
主标题"欢迎回来" + 副标题"像朋友一样，陪你管理健康"
  ↓ 32px
邮箱输入框（左侧邮箱图标）
  ↓ 16px
密码输入框（左侧锁图标，右侧显示/隐藏切换）
  ↓
"忘记密码？"链接（右对齐）
  ↓ 24px
登录按钮（品牌色全宽，48px 高，圆角 24px）
  ↓
"还没有账号？去注册"链接（居中）
```

**页面状态**

| 状态 | 说明 |
|------|------|
| 默认态 | 表单为空，登录按钮禁用（浅灰色） |
| 输入中 | 当前输入框边框高亮为品牌色 `#FF7A5C`，左侧图标变品牌色；两个字段都有内容时按钮激活 |
| 登录中（loading） | 按钮显示 loading + "登录中..."，不可重复点击；表单输入框不可编辑 |
| 登录失败 | 表单上方显示红色错误提示条"邮箱或密码错误，请重试"；密码框清空并自动聚焦 |

**数据字段**

```typescript
interface LoginFormData {
  email: string;
  password: string;
}
```

**表单校验**

| 字段 | 校验规则 | 错误提示 |
|------|---------|---------|
| email | 非空 + 邮箱格式（RFC 5322） | "请输入有效的邮箱地址" |
| password | 非空 | （无独立提示，登录失败统一提示） |

**跳转关系**

| 触发条件 | 目标 |
|---------|------|
| 登录成功 + 已完成 Onboarding | MainNavigator（首页） |
| 登录成功 + 未完成 Onboarding | OnboardingScreen（P16） |
| 点击"去注册" | RegisterScreen（P14） |
| 点击"忘记密码？" | ForgotPasswordScreen（P15） |

**关键交互**

- 键盘回车：邮箱框回车跳到密码框，密码框回车触发登录
- 密码显示/隐藏：点击眼睛图标切换明文/密文，图标在睁眼/闭眼之间切换
- 键盘弹起时页面内容上推，避免遮挡输入框

**页面文案**

| 位置 | 文案 |
|------|------|
| 品牌名 | "健康管家" |
| 主标题 | "欢迎回来" |
| 副标题 | "像朋友一样，陪你管理健康" |
| 邮箱 placeholder | "请输入邮箱" |
| 密码 placeholder | "请输入密码" |
| 忘记密码链接 | "忘记密码？" |
| 登录按钮 | "登录" |
| 登录中 | "登录中..." |
| 注册引导 | "还没有账号？去注册" |
| 邮箱格式错误 | "请输入有效的邮箱地址" |
| 登录失败 | "邮箱或密码错误，请重试" |
| 网络错误 | "网络连接失败，请检查网络后重试" |

---

### P14 RegisterScreen

**页面职责**

邮箱 + 密码注册新账号，注册成功后引导进入 Onboarding 流程。

**对应 UI 文稿**

`13-auth-and-onboarding.md` 页面 B：注册页

**页面结构**

```
← 返回箭头（左上角）
  ↓
主标题"创建你的健康档案"
  ↓ 32px
邮箱输入框（左侧邮箱图标）
  ↓ 16px
密码输入框（左侧锁图标，右侧显示/隐藏）
  ↓ 16px
确认密码输入框（左侧锁图标，右侧显示/隐藏）
  ↓ 24px
注册按钮（品牌色全宽，48px 高，圆角 24px）
  ↓
"已有账号？去登录"链接（居中）
```

**页面状态**

| 状态 | 说明 |
|------|------|
| 默认态 | 三个输入框为空，注册按钮禁用 |
| 输入中 | 当前输入框边框高亮为品牌色；密码输入框下方显示密码强度提示（弱/中/强） |
| 校验失败 | 对应输入框下方显示红色错误提示文字 |
| 注册中（loading） | 按钮显示 loading + "注册中..."，所有输入框不可编辑 |
| 注册失败 | 显示错误提示（如"该邮箱已注册，请直接登录"） |

**数据字段**

```typescript
interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
}
```

**表单校验**

| 字段 | 校验规则 | 错误提示 |
|------|---------|---------|
| email | 非空 + 邮箱格式 | "请输入有效的邮箱地址" |
| password | 非空 + 长度 >= 8 + 包含字母和数字 | "密码至少 8 位，建议包含字母和数字" |
| confirmPassword | 非空 + 与 password 一致 | "两次输入的密码不一致" |

**跳转关系**

| 触发条件 | 目标 |
|---------|------|
| 注册成功 | OnboardingScreen（P16） |
| 点击"去登录" | LoginScreen（P13） |
| 点击返回箭头 | LoginScreen（P13） |

**页面文案**

| 位置 | 文案 |
|------|------|
| 页面标题 | "创建你的健康档案" |
| 邮箱 placeholder | "请输入邮箱" |
| 密码 placeholder | "请输入密码" |
| 确认密码 placeholder | "请再次输入密码" |
| 注册按钮 | "注册" |
| 注册中 | "注册中..." |
| 登录引导 | "已有账号？去登录" |
| 邮箱格式错误 | "请输入有效的邮箱地址" |
| 密码规则提示 | "密码至少 8 位，建议包含字母和数字" |
| 密码不一致 | "两次输入的密码不一致" |
| 邮箱已注册 | "该邮箱已注册，请直接登录" |

---

### P15 ForgotPasswordScreen

**页面职责**

发送密码重置邮件，帮助用户找回账号。

**对应 UI 文稿**

`13-auth-and-onboarding.md` 页面 C：忘记密码页

**页面结构**

```
← 返回箭头（左上角）
  ↓
主标题"重置密码"
说明文案"输入你的注册邮箱，我们将发送重置密码的链接到你的邮箱。"
  ↓ 32px
邮箱输入框（左侧邮箱图标）
  ↓ 24px
发送按钮"发送重置邮件"（品牌色全宽，48px 高，圆角 24px）
  ↓
"想起密码了？去登录"链接（居中）
```

**页面状态**

| 状态 | 说明 |
|------|------|
| 默认态 | 邮箱输入框为空，发送按钮禁用 |
| 发送中 | 按钮显示 loading + "发送中..." |
| 发送成功 | 页面内容替换为：绿色勾选图标 + "重置邮件已发送" + "请查看你的邮箱 xxx@email.com"；按钮变为"重新发送"，60 秒倒计时后可再次点击 |
| 邮箱不存在 | 邮箱输入框下方显示红色提示"该邮箱未注册" |

**数据字段**

```typescript
interface ForgotPasswordFormData {
  email: string;
}
```

**表单校验**

| 字段 | 校验规则 | 错误提示 |
|------|---------|---------|
| email | 非空 + 邮箱格式 | "请输入有效的邮箱地址" |

**跳转关系**

| 触发条件 | 目标 |
|---------|------|
| 发送成功 → 停留在提示页面 | 当前页面（成功态） |
| 点击"去登录" | LoginScreen（P13） |
| 点击返回箭头 | LoginScreen（P13） |

**页面文案**

| 位置 | 文案 |
|------|------|
| 页面标题 | "重置密码" |
| 说明文案 | "输入你的注册邮箱，我们将发送重置密码的链接到你的邮箱。" |
| 邮箱 placeholder | "请输入注册邮箱" |
| 发送按钮 | "发送重置邮件" |
| 发送中 | "发送中..." |
| 发送成功标题 | "重置邮件已发送" |
| 发送成功说明 | "请查看你的邮箱 {email}" |
| 重新发送 | "重新发送（{countdown}s）" |
| 邮箱格式错误 | "请输入有效的邮箱地址" |
| 邮箱未注册 | "该邮箱未注册" |
| 登录引导 | "想起密码了？去登录" |

---

### P16 OnboardingScreen

**页面职责**

分步表单收集用户基础健康档案、饮食偏好、疾病信息。注册成功后自动进入，也可从个人中心"完善档案"入口进入。

**对应 UI 文稿**

`13-auth-and-onboarding.md` 页面 D：基础档案填写页（分步表单）

**页面结构**

```
← 返回箭头（第 1 步时隐藏或返回登录页）
  ↓
进度条（5 段）+ "第 N 步，共 5 步"
  ↓
步骤标题 + 副标题
  ↓ 24px
表单内容区（随步骤切换，左右滑动动画）
  ↓
底部固定操作栏：[上一步] [跳过] [下一步 →]
```

**步骤详情**

#### Step 1：基础信息

| 属性 | 值 |
|------|------|
| 标题 | "先认识一下你" |
| 副标题 | "这些信息帮助 AI 更好地了解你" |

| 字段 | 组件类型 | 校验规则 |
|------|---------|---------|
| 昵称 | TextInput | 必填，2-20 字符 |
| 性别 | SelectionCards（男/女） | 必选 |
| 出生日期 | DatePicker | 必填，有效日期 |

#### Step 2：身体信息

| 属性 | 值 |
|------|------|
| 标题 | "你的身体数据" |
| 副标题 | "用于计算每日营养需求" |

| 字段 | 组件类型 | 校验规则 |
|------|---------|---------|
| 身高 (cm) | SliderInput | 必填，100-250 |
| 体重 (kg) | SliderInput | 必填，30-300 |
| 活动量 | SelectionCards（久坐/轻度/中度/重度） | 必选，默认"中度" |

#### Step 3：健康目标

| 属性 | 值 |
|------|------|
| 标题 | "你的健康目标是什么？" |
| 副标题 | "设定目标帮助 AI 给你更精准的建议" |

| 字段 | 组件类型 | 校验规则 |
|------|---------|---------|
| 目标类型 | SelectionCards（减脂/增肌/维持/健康饮食） | 必选 |
| 目标体重 (kg) | NumberInput | 选填，30-300 |
| 每日热量目标 (kcal) | NumberInput（可自动计算） | 选填 |

#### Step 4：饮食偏好

| 属性 | 值 |
|------|------|
| 标题 | "你的饮食习惯" |
| 副标题 | "帮助 AI 推荐适合你的食物" |

| 字段 | 组件类型 | 校验规则 |
|------|---------|---------|
| 偏好类型 | SelectionCards（均衡/低碳水/高蛋白/素食/地中海） | 选填 |
| 过敏原 | MultiSelectTags（海鲜/花生/牛奶/鸡蛋/大豆/小麦/其他） | 选填 |
| 忌口 | MultiSelectTags（猪肉/牛肉/辣椒/其他） | 选填 |

#### Step 5：疾病信息（可选）

| 属性 | 值 |
|------|------|
| 标题 | "健康状况（选填）" |
| 副标题 | "如有慢性病，AI 会特别注意饮食禁忌" |

| 字段 | 组件类型 | 校验规则 |
|------|---------|---------|
| 基础疾病 | MultiSelectTags（高血压/糖尿病/高血脂/痛风/其他） | 选填 |
| 服用药物 | TextInput | 选填 |
| 医嘱限制 | TextInput | 选填 |

#### 完成后：预览页

- 居中绿色勾选图标 + "档案已完成！"
- 白底圆角卡片展示所有填写信息摘要（分区：基础信息、身体信息、健康目标、饮食偏好、疾病信息）
- 跳过的步骤显示"未填写"灰色文字
- 底部"开始使用健康管家"按钮（品牌色全宽）+ "返回修改"链接

**页面状态**

| 状态 | 说明 |
|------|------|
| 各步骤默认态 | 表单字段为空或显示推荐默认值（如活动量默认"中度"） |
| 步骤切换 | 下一步：当前内容向左滑出，新内容从右侧滑入；上一步：反向 |
| 跳过态 | 该步骤字段保持为空，进度条该段标记为灰色虚线 |
| 预览态 | 所有步骤完成后展示预览页 |
| 提交中 | "开始使用健康管家"按钮显示 loading |

**数据字段**

```typescript
interface OnboardingData {
  // Step 1: 基础信息
  nickname: string;
  gender: 'male' | 'female';
  birthDate: string; // ISO date

  // Step 2: 身体信息
  height: number; // cm
  weight: number; // kg
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'heavy';

  // Step 3: 健康目标
  goalType: 'lose_fat' | 'gain_muscle' | 'maintain' | 'healthy_diet';
  targetWeight?: number; // kg
  dailyCalorieTarget?: number; // kcal

  // Step 4: 饮食偏好
  dietType?: 'balanced' | 'low_carb' | 'high_protein' | 'vegetarian' | 'mediterranean';
  allergies?: string[];
  restrictions?: string[];

  // Step 5: 疾病信息（可选）
  diseases?: string[];
  medications?: string;
  medicalAdvice?: string;
}
```

**跳转关系**

| 触发条件 | 目标 |
|---------|------|
| 预览页点击"开始使用健康管家" | 保存档案 → MainNavigator（首页） |
| 预览页点击"返回修改" | 返回 Step 1，可重新编辑 |
| 第 1 步点击返回箭头 | 返回 LoginScreen 或 RegisterScreen |

**关键交互**

- 选择卡片点击：选中态边框变品牌色，背景变 `#FFE7E1`
- 多选标签点击：选中态背景变 `#FFE7E1`，文字变品牌色
- 身高/体重滑块拖动：实时更新数值显示
- 步骤切换动画：300ms ease-in-out 左右滑动
- "下一步"点击：校验当前步骤必填项 → 通过则切换 → 进度条更新
- "跳过"点击：跳过当前步骤，直接进入下一步
- 最后一步"完成"：提交所有数据 → 显示预览页

**页面文案**

| 位置 | 文案 |
|------|------|
| 进度提示 | "第 {n} 步，共 5 步" |
| 上一步按钮 | "上一步" |
| 下一步按钮 | "下一步" |
| 跳过按钮 | "跳过" |
| 完成按钮 | "完成" |
| 预览成功标题 | "档案已完成！" |
| 开始使用按钮 | "开始使用健康管家" |
| 返回修改链接 | "返回修改" |
| 未填写提示 | "未填写" |

---

## 5. 模块内组件

本模块需要实现以下内部组件（不在共享组件库中）：

### OnboardingStep

**职责**：单步表单容器，包裹每个步骤的表单内容

**Props**

```typescript
interface OnboardingStepProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}
```

**样式**

- 标题：`font-page-title`（24px Bold），颜色 `text-primary`
- 副标题：`font-body-sm`（14px Regular），颜色 `text-secondary`
- 标题与副标题间距：`space-xs`（4px）
- 副标题与表单内容间距：`space-xl`（24px）

---

### OnboardingProgress

**职责**：顶部进度条，显示当前步骤和完成进度

**Props**

```typescript
interface OnboardingProgressProps {
  totalSteps: number;
  currentStep: number;
  skippedSteps: number[];
}
```

**样式**

- 5 段圆角条，每段宽度相等，间距 `space-xs`（4px）
- 已完成段：品牌色 `#FF7A5C` 填充
- 当前段：品牌色 `#FF7A5C` 填充
- 未完成段：浅灰色 `#F0F0F0` 填充
- 跳过段：灰色虚线边框 `#CCCCCC`，无填充
- 进度条下方显示"第 N 步，共 5 步"（`font-caption`，颜色 `text-tertiary`）

---

### GenderSelector

**职责**：性别选择器（选择卡片样式）

**Props**

```typescript
interface GenderSelectorProps {
  value: 'male' | 'female' | null;
  onChange: (value: 'male' | 'female') => void;
}
```

**样式**

- 两个并排卡片：男 / 女
- 未选中：白底 `bg-card`，浅灰边框 `#EEEEEE`，圆角 `radius-md`（12px）
- 选中：品牌色边框 `#FF7A5C`，浅橙背景 `#FFE7E1`
- 卡片内边距：`space-lg`（16px）
- 卡片间距：`space-md`（12px）
- 文字：`font-body`（16px），未选中 `text-secondary`，选中 `brand-primary`

---

### ActivityLevelSelector

**职责**：活动量选择器（选择卡片样式）

**Props**

```typescript
interface ActivityLevelSelectorProps {
  value: 'sedentary' | 'light' | 'moderate' | 'heavy' | null;
  onChange: (value: 'sedentary' | 'light' | 'moderate' | 'heavy') => void;
}
```

**选项**

| 值 | 显示文案 | 说明 |
|------|---------|------|
| sedentary | 久坐 | 办公室工作，很少运动 |
| light | 轻度 | 每周运动 1-3 次 |
| moderate | 中度 | 每周运动 3-5 次 |
| heavy | 重度 | 每周运动 6-7 次或体力劳动 |

**样式**

- 四个卡片，2×2 网格布局
- 样式同 GenderSelector
- 卡片内显示主文案（如"久坐"）+ 小字说明（如"办公室工作，很少运动"）

---

## 6. 模块内 Store

使用 Zustand 管理认证模块状态。

```typescript
interface AuthStore {
  // 登录状态
  isLoading: boolean;
  error: string | null;

  // Onboarding 状态
  onboardingStep: number; // 当前步骤 1-5
  onboardingData: Partial<OnboardingData>;
  skippedSteps: number[]; // 跳过的步骤编号

  // Actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setOnboardingStep: (step: number) => void;
  updateOnboardingData: (data: Partial<OnboardingData>) => void;
  skipStep: (step: number) => void;
  resetOnboarding: () => void;
}
```

**Store 实现示例**

```typescript
import { create } from 'zustand';

export const useAuthStore = create<AuthStore>((set) => ({
  isLoading: false,
  error: null,
  onboardingStep: 1,
  onboardingData: {},
  skippedSteps: [],

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setOnboardingStep: (step) => set({ onboardingStep: step }),
  updateOnboardingData: (data) =>
    set((state) => ({
      onboardingData: { ...state.onboardingData, ...data }
    })),
  skipStep: (step) =>
    set((state) => ({
      skippedSteps: [...state.skippedSteps, step]
    })),
  resetOnboarding: () =>
    set({
      onboardingStep: 1,
      onboardingData: {},
      skippedSteps: []
    }),
}));
```

---

## 7. 模块内 Services

**重要架构决策**：前端直接使用 Supabase Auth SDK，不通过后端 API。

### 7.1 Supabase 客户端配置

```typescript
// src/core/supabase/client.ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.EXPO_PUBLIC_SUPABASE_URL!,
  process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY!
)
```

### 7.2 AuthService 接口

```typescript
interface AuthService {
  /**
   * 登录
   * @param email 邮箱
   * @param password 密码
   * @returns 返回 access_token
   */
  login(email: string, password: string): Promise<string>;

  /**
   * 注册
   * @param email 邮箱
   * @param password 密码
   * @returns 返回 access_token
   */
  register(email: string, password: string): Promise<string>;

  /**
   * 忘记密码
   * @param email 邮箱
   * @returns 发送成功无返回值
   */
  forgotPassword(email: string): Promise<void>;

  /**
   * 登出
   */
  logout(): Promise<void>;

  /**
   * 获取当前 session
   */
  getSession(): Promise<string | null>;
}
```

### 7.3 AuthService 实现

```typescript
// src/features/auth/services/authService.ts
import { supabase } from '@core/supabase/client'

export const authService: AuthService = {
  async login(email: string, password: string): Promise<string> {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) throw new Error(error.message)
    if (!data.session) throw new Error('登录失败')

    return data.session.access_token
  },

  async register(email: string, password: string): Promise<string> {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    })

    if (error) throw new Error(error.message)
    if (!data.session) throw new Error('注册失败')

    return data.session.access_token
  },

  async forgotPassword(email: string): Promise<void> {
    const { error } = await supabase.auth.resetPasswordForEmail(email)
    if (error) throw new Error(error.message)
  },

  async logout(): Promise<void> {
    const { error } = await supabase.auth.signOut()
    if (error) throw new Error(error.message)
  },

  async getSession(): Promise<string | null> {
    const { data } = await supabase.auth.getSession()
    return data.session?.access_token ?? null
  },
}
```

### 7.4 用户档案服务（调用后端 API）

```typescript
// src/features/auth/services/userService.ts
interface UserService {
  /**
   * 保存 Onboarding 数据
   * @param data 用户档案数据
   * @returns 返回完整用户档案
   */
  saveOnboarding(data: OnboardingData): Promise<UserProfile>;

  /**
   * 检查用户是否完成 Onboarding
   * @returns 返回是否完成
   */
  checkOnboardingStatus(): Promise<boolean>;
}

export const userService: UserService = {
  async saveOnboarding(data: OnboardingData): Promise<UserProfile> {
    // 调用后端 API: POST /api/v1/users/me/onboarding
    const response = await apiClient.post('/users/me/onboarding', data)
    return response.data
  },

  async checkOnboardingStatus(): Promise<boolean> {
    // 调用后端 API: GET /api/v1/users/me
    const response = await apiClient.get('/users/me')
    return response.data.onboardingCompleted
  },
}
```

**类型定义**

```typescript
interface LoginResponse {
  token: string;
  user: UserProfile;
}

interface RegisterResponse {
  token: string;
}

interface UserProfile {
  id: string;
  email: string;
  nickname: string;
  gender: 'male' | 'female';
  birthDate: string;
  height: number;
  weight: number;
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'heavy';
  goalType: 'lose_fat' | 'gain_muscle' | 'maintain' | 'healthy_diet';
  targetWeight?: number;
  dailyCalorieTarget?: number;
  dietType?: string;
  allergies?: string[];
  restrictions?: string[];
  diseases?: string[];
  medications?: string;
  medicalAdvice?: string;
  onboardingCompleted: boolean;
  createdAt: string;
  updatedAt: string;
}
```

---

## 8. Mock 数据要求

开发阶段使用 Mock 数据，模拟 API 响应。

### 登录成功 Mock

```typescript
const mockLoginSuccess: LoginResponse = {
  token: 'mock_jwt_token_12345',
  user: {
    id: 'user_001',
    email: 'test@example.com',
    nickname: '小明',
    gender: 'male',
    birthDate: '1995-06-15',
    height: 175,
    weight: 74.5,
    activityLevel: 'moderate',
    goalType: 'lose_fat',
    targetWeight: 68,
    dailyCalorieTarget: 2100,
    dietType: 'balanced',
    allergies: ['海鲜', '花生'],
    restrictions: [],
    diseases: [],
    medications: '',
    medicalAdvice: '',
    onboardingCompleted: true,
    createdAt: '2026-04-01T10:00:00Z',
    updatedAt: '2026-04-29T15:30:00Z',
  },
};
```

### 登录失败 Mock

```typescript
const mockLoginError = {
  code: 'AUTH_FAILED',
  message: '邮箱或密码错误，请重试',
};
```

### 注册成功 Mock

```typescript
const mockRegisterSuccess: RegisterResponse = {
  token: 'mock_jwt_token_67890',
};
```

### 注册失败 Mock（邮箱已存在）

```typescript
const mockRegisterError = {
  code: 'EMAIL_EXISTS',
  message: '该邮箱已注册，请直接登录',
};
```

### Onboarding 保存成功 Mock

```typescript
const mockOnboardingSaveSuccess: UserProfile = {
  id: 'user_002',
  email: 'newuser@example.com',
  nickname: '小红',
  gender: 'female',
  birthDate: '1998-03-20',
  height: 165,
  weight: 58,
  activityLevel: 'light',
  goalType: 'maintain',
  targetWeight: 58,
  dailyCalorieTarget: 1800,
  dietType: 'vegetarian',
  allergies: ['牛奶'],
  restrictions: ['猪肉', '牛肉'],
  diseases: [],
  medications: '',
  medicalAdvice: '',
  onboardingCompleted: true,
  createdAt: '2026-04-29T16:00:00Z',
  updatedAt: '2026-04-29T16:05:00Z',
};
```

### Mock Service 实现示例

```typescript
export const mockAuthService: AuthService = {
  async login(email: string, password: string) {
    await new Promise((resolve) => setTimeout(resolve, 1000)); // 模拟网络延迟

    if (email === 'test@example.com' && password === 'password123') {
      return mockLoginSuccess;
    }

    throw new Error('邮箱或密码错误，请重试');
  },

  async register(email: string, password: string) {
    await new Promise((resolve) => setTimeout(resolve, 1000));

    if (email === 'test@example.com') {
      throw new Error('该邮箱已注册，请直接登录');
    }

    return mockRegisterSuccess;
  },

  async forgotPassword(email: string) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    // 成功无返回值
  },

  async saveOnboarding(data: OnboardingData) {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    return mockOnboardingSaveSuccess;
  },

  async checkOnboardingStatus() {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return false; // 模拟未完成 Onboarding
  },
};
```

---

## 9. 模块依赖

### 共享 UI 组件

| 组件 | 路径 | 用途 |
|------|------|------|
| Button | `@shared/ui/Button` | 登录、注册、发送等主要操作按钮 |
| TextInput | `@shared/forms/TextInput` | 邮箱、昵称、药物等文本输入 |
| PasswordInput | `@shared/forms/PasswordInput` | 密码输入框（带显示/隐藏切换） |
| DatePicker | `@shared/forms/DatePicker` | 出生日期选择 |
| SliderInput | `@shared/forms/SliderInput` | 身高、体重滑块输入 |
| NumberInput | `@shared/forms/NumberInput` | 目标体重、每日热量输入 |
| MultiSelectTags | `@shared/forms/MultiSelectTags` | 过敏原、忌口、疾病多选标签 |
| Toast | `@shared/feedback/Toast` | 错误提示、成功提示 |
| Loading | `@shared/feedback/Loading` | 加载状态指示器 |

### 全局 Store

| Store | 路径 | 用途 |
|------|------|------|
| globalStore | `@core/store/globalStore` | 存储 token、用户信息等全局状态 |

### 工具函数

| 函数 | 路径 | 用途 |
|------|------|------|
| validateEmail | `@utils/validation` | 邮箱格式验证 |
| validatePassword | `@utils/validation` | 密码强度验证 |
| formatDate | `@utils/date` | 日期格式化 |

---

## 10. 实现约束

### 必须遵循的规范

1. **UI 设计文稿为准**
   - 所有页面必须参考 `13-auth-and-onboarding.md` 文稿实现
   - 没有完整视觉稿，以文稿中的结构、文案、交互说明为准
   - 颜色、字体、间距严格遵循 `01-design-system.md`

2. **设计系统映射**
   - 所有颜色使用 Design Token（如 `brand-primary`、`text-secondary`）
   - 所有字体使用 Font Token（如 `font-page-title`、`font-body`）
   - 所有间距使用 Space Token（如 `space-lg`、`space-md`）
   - 所有圆角使用 Radius Token（如 `radius-md`、`radius-pill`）

3. **表单验证**
   - 实时验证，错误提示即时显示
   - 错误提示文案清晰友好，避免技术术语
   - 必填项未填写时，提交按钮禁用

4. **无障碍支持**
   - 所有输入框必须有 `label` 或 `aria-label`
   - 错误提示使用 `aria-describedby` 关联到输入框
   - 按钮禁用态使用 `aria-disabled`
   - 键盘导航支持（Tab 键切换焦点，Enter 提交）

5. **响应式适配**
   - 优先适配移动端（iPhone 14/15 尺寸：390×844）
   - 键盘弹起时页面内容上推，避免遮挡输入框
   - 底部安全区预留（iOS Safe Area）

6. **动效规范**
   - 页面切换：300ms ease-in-out 左右滑动
   - 按钮点击：100ms 缩放至 0.95
   - 步骤切换：300ms ease-in-out 左右滑动
   - 错误提示：200ms ease-out 从顶部滑入

7. **错误处理**
   - 网络错误：显示"网络连接失败，请检查网络后重试"
   - 服务器错误：显示"服务异常，请稍后重试"
   - 业务错误：显示后端返回的具体错误信息

8. **安全要求**
   - 密码输入框默认密文显示
   - 登录/注册成功后立即存储 token 到安全存储（如 SecureStore）
   - 敏感信息（密码）不在日志中输出

---

## 11. 开发建议

### 开发顺序

1. **第一阶段**：基础页面（2 天）
   - P13 LoginScreen
   - P14 RegisterScreen
   - P15 ForgotPasswordScreen
   - 使用 Mock Service 测试

2. **第二阶段**：Onboarding 流程（1.5 天）
   - P16 OnboardingScreen（5 个步骤 + 预览页）
   - 实现步骤切换动画
   - 实现进度条组件

3. **第三阶段**：集成与优化（0.5 天）
   - 集成真实 API
   - 错误处理完善
   - 无障碍测试
   - 性能优化

### 技术栈建议

- **框架**：React Native（移动端）或 React（Web 端）
- **状态管理**：Zustand
- **表单管理**：React Hook Form
- **路由**：React Navigation（移动端）或 React Router（Web 端）
- **样式**：Tailwind CSS 或 Styled Components
- **动画**：Framer Motion 或 React Native Reanimated

### 测试要点

- 表单验证逻辑（邮箱格式、密码强度、两次密码一致性）
- 步骤切换逻辑（上一步、下一步、跳过）
- 进度条状态更新
- 错误提示显示与隐藏
- 键盘操作（Enter 提交、Tab 切换）
- 网络异常处理

---

## 12. 附录：完整类型定义

```typescript
// ============ 表单数据类型 ============

interface LoginFormData {
  email: string;
  password: string;
}

interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
}

interface ForgotPasswordFormData {
  email: string;
}

interface OnboardingData {
  // Step 1: 基础信息
  nickname: string;
  gender: 'male' | 'female';
  birthDate: string; // ISO date

  // Step 2: 身体信息
  height: number; // cm
  weight: number; // kg
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'heavy';

  // Step 3: 健康目标
  goalType: 'lose_fat' | 'gain_muscle' | 'maintain' | 'healthy_diet';
  targetWeight?: number; // kg
  dailyCalorieTarget?: number; // kcal

  // Step 4: 饮食偏好
  dietType?: 'balanced' | 'low_carb' | 'high_protein' | 'vegetarian' | 'mediterranean';
  allergies?: string[];
  restrictions?: string[];

  // Step 5: 疾病信息（可选）
  diseases?: string[];
  medications?: string;
  medicalAdvice?: string;
}

// ============ API 响应类型 ============

interface LoginResponse {
  token: string;
  user: UserProfile;
}

interface RegisterResponse {
  token: string;
}

interface UserProfile {
  id: string;
  email: string;
  nickname: string;
  gender: 'male' | 'female';
  birthDate: string;
  height: number;
  weight: number;
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'heavy';
  goalType: 'lose_fat' | 'gain_muscle' | 'maintain' | 'healthy_diet';
  targetWeight?: number;
  dailyCalorieTarget?: number;
  dietType?: string;
  allergies?: string[];
  restrictions?: string[];
  diseases?: string[];
  medications?: string;
  medicalAdvice?: string;
  onboardingCompleted: boolean;
  createdAt: string;
  updatedAt: string;
}

// ============ Store 类型 ============

interface AuthStore {
  isLoading: boolean;
  error: string | null;
  onboardingStep: number;
  onboardingData: Partial<OnboardingData>;
  skippedSteps: number[];

  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setOnboardingStep: (step: number) => void;
  updateOnboardingData: (data: Partial<OnboardingData>) => void;
  skipStep: (step: number) => void;
  resetOnboarding: () => void;
}

// ============ Service 类型 ============

interface AuthService {
  login(email: string, password: string): Promise<LoginResponse>;
  register(email: string, password: string): Promise<RegisterResponse>;
  forgotPassword(email: string): Promise<void>;
  saveOnboarding(data: OnboardingData): Promise<UserProfile>;
  checkOnboardingStatus(): Promise<boolean>;
}

// ============ 组件 Props 类型 ============

interface OnboardingStepProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}

interface OnboardingProgressProps {
  totalSteps: number;
  currentStep: number;
  skippedSteps: number[];
}

interface GenderSelectorProps {
  value: 'male' | 'female' | null;
  onChange: (value: 'male' | 'female') => void;
}

interface ActivityLevelSelectorProps {
  value: 'sedentary' | 'light' | 'moderate' | 'heavy' | null;
  onChange: (value: 'sedentary' | 'light' | 'moderate' | 'heavy') => void;
}
```

---

**文档版本**：v1.0
**最后更新**：2026-04-29
**维护者**：前端开发团队
