# 个人中心模块前端实现规格

## 1. 模块职责

个人中心模块负责：
- 展示用户完整档案信息（基础信息、饮食偏好、疾病信息）
- 提供档案编辑功能
- 应用设置管理（交互模式、通知、隐私）
- 账号操作（退出登录、删除账号、数据导出）

## 2. 对应 UI 设计文稿

- `health-agent/docs/prd/v1/ui-design/12-profile-and-settings.md`

## 3. 页面列表

- **P10 ProfileScreen** — 个人中心页
- **P11 EditProfileScreen** — 编辑档案页
- **P12 SettingsScreen** — 设置页

## 4. 页面详细规格

### P10 ProfileScreen

**页面职责**

展示用户档案概览，提供快捷入口跳转到编辑资料和设置页面。

**对应 UI 文稿**

`12-profile-and-settings.md` 个人中心部分

**页面结构**

```
┌─────────────────────────────────┐
│         个人信息卡片              │
│  ┌──────┐                       │
│  │ 头像  │  昵称                 │
│  └──────┘  基础信息摘要          │
├─────────────────────────────────┤
│         健康档案卡片              │
│  性别 · 年龄 · 身高 · 体重       │
│  目标体重 · BMI                  │
├─────────────────────────────────┤
│         饮食偏好卡片              │
│  饮食类型 · 过敏 · 忌口          │
├─────────────────────────────────┤
│         疾病信息卡片              │
│  基础疾病 · 服用药物             │
├─────────────────────────────────┤
│  编辑资料                    >   │
│  设置                        >   │
│  退出登录                        │
├─────────────────────────────────┤
│  🏠 首页  🍽 饮食  📊 数据  👤 我的 │
└─────────────────────────────────┘
```

**页面状态**

| 状态 | 说明 |
|------|------|
| 加载中 | 骨架屏展示，等待用户数据返回 |
| 正常态 | 展示完整档案信息 |

**数据字段**

```typescript
interface UserProfile {
  id: string;
  nickname: string;
  avatar?: string;
  gender: 'male' | 'female' | 'other';
  birthDate: string;          // ISO date
  height: number;             // cm
  weight: number;             // kg
  targetWeight: number;       // kg
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';
  dietType: string;           // 如"普通饮食"、"素食"等
  allergies: string[];        // 过敏食物
  restrictions: string[];     // 忌口
  dislikedFoods: string[];    // 不喜欢的食物
  diseases: string[];         // 基础疾病
  medications: string[];      // 服用药物
  medicalAdvice?: string;     // 医嘱限制
}
```

**跳转关系**

| 触发 | 目标 | 说明 |
|------|------|------|
| 点击"编辑资料" | EditProfileScreen | 进入编辑页 |
| 点击"设置" | SettingsScreen | 进入设置页 |
| 点击"退出登录" | ConfirmDialog → LoginScreen | 弹出确认对话框，确认后清除登录态，跳转登录页 |

---

### P11 EditProfileScreen

**页面职责**

编辑用户档案，包括基础信息、饮食偏好、疾病信息三个分组。

**对应 UI 文稿**

`12-profile-and-settings.md` 编辑资料部分

**页面结构**

```
┌─────────────────────────────────┐
│  ← 编辑资料                      │
├─────────────────────────────────┤
│  基础信息                        │
│  昵称         [输入框]           │
│  性别         [选择器]           │
│  出生日期     [日期选择器]       │
│  身高         [输入框] cm        │
│  体重         [输入框] kg        │
│  目标体重     [输入框] kg        │
│  活动量       [选择器]           │
├─────────────────────────────────┤
│  饮食偏好                        │
│  饮食类型     [选择器]           │
│  过敏         [多选标签]         │
│  忌口         [多选标签]         │
│  不喜欢的食物 [多选标签]         │
├─────────────────────────────────┤
│  疾病信息                        │
│  基础疾病     [多选标签]         │
│  服用药物     [多选标签]         │
│  医嘱限制     [文本域]           │
├─────────────────────────────────┤
│         [保存]                   │
└─────────────────────────────────┘
```

**页面状态**

| 状态 | 说明 |
|------|------|
| 编辑中 | 表单可编辑，显示当前值 |
| 保存中 | 按钮显示 loading，表单禁用 |
| 保存成功 | Toast 提示，返回个人中心页 |
| 保存失败 | Toast 提示错误信息，保持在编辑页 |

**数据字段**

使用完整的 `UserProfile` 类型（同 P10）。

**表单校验**

| 字段 | 校验规则 |
|------|---------|
| 昵称 | 必填，1-20 字符 |
| 性别 | 必选 |
| 出生日期 | 必选，不能晚于今天 |
| 身高 | 必填，50-250 cm |
| 体重 | 必填，20-300 kg |
| 目标体重 | 必填，20-300 kg |
| 活动量 | 必选 |

**跳转关系**

| 触发 | 目标 | 说明 |
|------|------|------|
| 点击返回 | ProfileScreen | 未保存时弹出确认对话框 |
| 保存成功 | ProfileScreen | 自动返回，刷新数据 |

---

### P12 SettingsScreen

**页面职责**

应用设置管理，包括交互模式、通知、隐私、关于等功能。

**对应 UI 文稿**

`12-profile-and-settings.md` 设置部分

**页面结构**

```
┌─────────────────────────────────┐
│  ← 设置                          │
├─────────────────────────────────┤
│  交互模式                        │
│  ○ 效率模式                      │
│  ○ 确认模式                      │
│  ○ 学习模式                      │
├─────────────────────────────────┤
│  通知设置                        │
│  计划提醒     [开关]             │
│  饮食提醒     [开关]             │
├─────────────────────────────────┤
│  隐私设置                        │
│  数据导出                    >   │
│  删除账号                    >   │
├─────────────────────────────────┤
│  关于                            │
│  版本号       v1.0.0             │
│  用户协议                    >   │
│  隐私政策                    >   │
└─────────────────────────────────┘
```

**页面状态**

| 状态 | 说明 |
|------|------|
| 正常态 | 展示所有设置项 |
| 操作中 | 开关切换、导出数据等操作的 loading 状态 |

**数据字段**

```typescript
interface AppSettings {
  interactionMode: 'efficient' | 'confirm' | 'learning';
  notifications: {
    planReminder: boolean;
    dietReminder: boolean;
  };
}
```

**跳转关系**

| 触发 | 目标 | 说明 |
|------|------|------|
| 点击"数据导出" | 触发下载 | 导出 JSON 文件 |
| 点击"删除账号" | ConfirmDialog | 弹出二次确认，确认后删除账号并返回登录页 |
| 点击"用户协议" | WebView | 打开协议页面 |
| 点击"隐私政策" | WebView | 打开隐私政策页面 |

---

## 5. 模块内组件

### ProfileHeader

**职责**: 展示用户头像、昵称、基础信息摘要

**Props**:
```typescript
interface ProfileHeaderProps {
  avatar?: string;
  nickname: string;
  age: number;
  gender: string;
}
```

### ProfileInfoCard

**职责**: 展示档案信息卡片（健康档案、饮食偏好、疾病信息）

**Props**:
```typescript
interface ProfileInfoCardProps {
  title: string;
  items: Array<{ label: string; value: string | string[] }>;
}
```

### SettingsList

**职责**: 设置列表容器

**Props**:
```typescript
interface SettingsListProps {
  sections: Array<{
    title: string;
    items: SettingItem[];
  }>;
}

interface SettingItem {
  type: 'radio' | 'switch' | 'link';
  label: string;
  value?: any;
  onChange?: (value: any) => void;
  onPress?: () => void;
}
```

### InteractionModeSelector

**职责**: 交互模式选择器（单选组）

**Props**:
```typescript
interface InteractionModeSelectorProps {
  value: 'efficient' | 'confirm' | 'learning';
  onChange: (mode: 'efficient' | 'confirm' | 'learning') => void;
}
```

---

## 6. 模块内 Store

个人中心模块不需要复杂的本地状态管理，主要通过 `globalStore` 和 TanStack Query 管理数据。

```typescript
// 不需要独立的 ProfileStore
// 用户档案数据通过 TanStack Query 缓存
// 应用设置通过 globalStore 管理
```

---

## 7. 模块内 Services

```typescript
interface ProfileService {
  /**
   * 获取用户档案
   * @returns 完整的用户档案信息
   */
  getUserProfile(): Promise<UserProfile>;

  /**
   * 更新用户档案
   * @param data 要更新的字段（部分更新）
   * @returns 更新后的完整档案
   */
  updateUserProfile(data: Partial<UserProfile>): Promise<UserProfile>;

  /**
   * 删除账号
   * 删除用户所有数据，不可恢复
   */
  deleteAccount(): Promise<void>;

  /**
   * 导出用户数据
   * @returns JSON 格式的用户数据文件
   */
  exportData(): Promise<Blob>;

  /**
   * 获取应用设置
   * @returns 应用设置对象
   */
  getAppSettings(): Promise<AppSettings>;

  /**
   * 更新应用设置
   * @param settings 要更新的设置项
   * @returns 更新后的完整设置
   */
  updateAppSettings(settings: Partial<AppSettings>): Promise<AppSettings>;
}
```

---

## 8. Mock 数据要求

### 用户档案 Mock

```typescript
const mockUserProfile: UserProfile = {
  id: 'user-001',
  nickname: '小明',
  avatar: 'https://example.com/avatar.jpg',
  gender: 'male',
  birthDate: '1990-05-15',
  height: 175,
  weight: 70,
  targetWeight: 65,
  activityLevel: 'moderate',
  dietType: '普通饮食',
  allergies: ['花生', '海鲜'],
  restrictions: ['猪肉'],
  dislikedFoods: ['香菜', '芹菜'],
  diseases: ['高血压'],
  medications: ['降压药'],
  medicalAdvice: '低盐饮食，每日盐摄入不超过6g'
};
```

### 应用设置 Mock

```typescript
const mockAppSettings: AppSettings = {
  interactionMode: 'confirm',
  notifications: {
    planReminder: true,
    dietReminder: true
  }
};
```

### 更新档案 Mock

```typescript
// POST /api/profile
// Request: Partial<UserProfile>
// Response: 返回更新后的完整 UserProfile
```

---

## 9. 模块依赖

### UI 组件
- `@shared/ui/Card` — 卡片容器
- `@shared/ui/Avatar` — 头像组件
- `@shared/ui/Button` — 按钮组件
- `@shared/ui/Divider` — 分割线

### 表单组件
- `@shared/forms/TextInput` — 文本输入框
- `@shared/forms/DatePicker` — 日期选择器
- `@shared/forms/Picker` — 下拉选择器
- `@shared/forms/MultiSelectTags` — 多选标签
- `@shared/forms/Switch` — 开关组件
- `@shared/forms/TextArea` — 多行文本输入

### 反馈组件
- `@shared/feedback/Toast` — 轻提示
- `@shared/feedback/ConfirmDialog` — 确认对话框
- `@shared/feedback/Loading` — 加载状态

### 状态管理
- `@core/store/globalStore` — 全局状态（用户信息、应用设置）
- `@tanstack/react-query` — 数据请求和缓存

### 导航
- `@react-navigation/native` — 页面导航

---

## 10. 实现约束

1. **必须参考 UI 文稿**: 严格按照 `12-profile-and-settings.md` 中的结构、文案、交互说明实现
2. **没有完整视觉稿**: 以文稿中的描述为准，颜色、字体、间距遵循 `04-design-system-mapping.md`
3. **表单校验**: 所有输入字段必须进行前端校验，提供清晰的错误提示
4. **数据持久化**: 档案更新和设置更改必须立即同步到后端
5. **退出登录**: 清除本地缓存、Token、用户状态，跳转到登录页
6. **删除账号**: 必须二次确认，删除后清除所有本地数据并返回登录页
7. **数据导出**: 导出 JSON 格式文件，包含用户所有数据（档案、饮食记录、计划等）
8. **交互模式**:
   - 效率模式：最少确认，快速操作
   - 确认模式：关键操作需要确认
   - 学习模式：提供操作提示和引导
9. **响应式布局**: 适配不同屏幕尺寸
10. **无障碍支持**: 所有交互元素必须支持屏幕阅读器
