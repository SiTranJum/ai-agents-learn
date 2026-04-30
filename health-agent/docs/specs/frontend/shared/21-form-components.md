# 表单组件规范

## 1. 组件清单

本文档定义了健康管家应用中所有表单组件的规范，包括：

- **TextInput** - 文本输入框
- **PasswordInput** - 密码输入框
- **DatePicker** - 日期选择器
- **Picker** - 下拉选择器
- **MultiSelectTags** - 多选标签
- **Slider** - 滑块
- **Switch** - 开关

所有组件遵循 `01-design-system.md` 中定义的设计规范，并与 `02-components.md` 中的 UI 组件保持一致的视觉风格。

## 2. 组件详细规格

### 2.1 TextInput

**用途**：通用文本输入框，支持单行和多行输入。

**Props 定义**：

```typescript
interface TextInputProps {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  disabled?: boolean;
  multiline?: boolean;
  maxLength?: number;
  autoFocus?: boolean;
  keyboardType?: 'default' | 'email-address' | 'numeric' | 'phone-pad';
}
```

**样式规范**：

- **高度**：48px（单行），multiline 时自动扩展
- **背景色**：`#F7F8FA`（默认态），`#FFFFFF`（聚焦态）
- **圆角**：12px
- **内边距**：水平 16px，垂直 12px
- **字体**：16px，Regular，`#1A1A1A`
- **占位符**：16px，Regular，`#999999`
- **边框**：
  - 默认：无边框
  - 聚焦：1.5px `#4CAF50`（品牌色）
  - 错误：1.5px `#F44336`
- **Label**：14px，Medium，`#666666`，距离输入框 8px
- **错误提示**：12px，Regular，`#F44336`，距离输入框 4px
- **禁用态**：背景色 `#F0F0F0`，文字 `#CCCCCC`

**交互行为**：

- 点击聚焦，显示光标
- 超过 maxLength 时阻止输入
- multiline 时支持换行

---

### 2.2 PasswordInput

**用途**：密码输入框，支持密码显示/隐藏切换。

**Props 定义**：

```typescript
interface PasswordInputProps extends Omit<TextInputProps, 'multiline' | 'keyboardType'> {
  showToggle?: boolean; // 是否显示密码可见性切换按钮，默认 true
}
```

**样式规范**：

- 继承 TextInput 所有样式规范
- **右侧图标区域**：宽度 48px，居中对齐
- **眼睛图标**：24x24px，颜色 `#999999`
  - 密码隐藏时：闭眼图标
  - 密码可见时：睁眼图标
- **图标点击区域**：最小 44x44px（无障碍要求）

**交互行为**：

- 默认隐藏密码（显示圆点）
- 点击眼睛图标切换密码可见性
- 不支持 multiline

---

### 2.3 DatePicker

**用途**：日期选择器，用于选择出生日期、目标日期等场景。

**Props 定义**：

```typescript
interface DatePickerProps {
  value: Date;
  onChange: (date: Date) => void;
  label?: string;
  error?: string;
  minimumDate?: Date;
  maximumDate?: Date;
  placeholder?: string;
  disabled?: boolean;
}
```

**样式规范**：

- 触发器样式同 TextInput（高度 48px，背景 `#F7F8FA`，圆角 12px）
- **右侧日历图标**：24x24px，颜色 `#999999`
- **日期显示格式**：`YYYY-MM-DD`
- **日历面板**：
  - 背景：`#FFFFFF`
  - 圆角：16px
  - 阴影：`0 4px 20px rgba(0, 0, 0, 0.1)`
  - 选中日期：品牌色圆形背景，白色文字
  - 今天：品牌色文字，无背景
  - 不可选日期：`#CCCCCC`

**交互行为**：

- 点击触发器弹出日历面板
- 选择日期后自动关闭面板
- 超出 minimumDate/maximumDate 范围的日期不可选

---

### 2.4 Picker

**用途**：下拉选择器，用于性别、活动量等单选场景。

**Props 定义**：

```typescript
interface PickerProps {
  value: string;
  onChange: (value: string) => void;
  options: { label: string; value: string }[];
  label?: string;
  error?: string;
  placeholder?: string;
  disabled?: boolean;
}
```

**样式规范**：

- 触发器样式同 TextInput（高度 48px，背景 `#F7F8FA`，圆角 12px）
- **右侧箭头图标**：24x24px，颜色 `#999999`，展开时旋转 180°
- **选项列表**：
  - 背景：`#FFFFFF`
  - 圆角：16px
  - 阴影：`0 4px 20px rgba(0, 0, 0, 0.1)`
  - 选项高度：48px
  - 选中项：品牌色文字 + 右侧勾选图标
  - 悬停/按压：背景 `#F7F8FA`

**交互行为**：

- 点击触发器弹出选项列表
- 选择选项后自动关闭列表
- 已选中的选项显示勾选标记

---

### 2.5 MultiSelectTags

**用途**：多选标签，用于健康目标、饮食偏好等多选场景。

**Props 定义**：

```typescript
interface MultiSelectTagsProps {
  value: string[];
  onChange: (value: string[]) => void;
  options: string[];
  label?: string;
  maxSelect?: number; // 最多可选数量
  minSelect?: number; // 最少可选数量
  error?: string;
}
```

**样式规范**：

- **标签容器**：flex wrap，间距 8px
- **单个标签**：
  - 高度：32-36px
  - 圆角：999px（完全圆角）
  - 内边距：水平 16px，垂直 8px
  - 字体：14px，Medium
  - **默认态**：
    - 背景：`#FFFFFF`
    - 边框：1px `#E0E0E0`
    - 文字：`#666666`
  - **选中态**：
    - 背景：`#4CAF50`（品牌色）
    - 边框：无
    - 文字：`#FFFFFF`
  - **禁用态**：
    - 背景：`#F0F0F0`
    - 文字：`#CCCCCC`
- **Label**：14px，Medium，`#666666`，距离标签容器 8px

**交互行为**：

- 点击标签切换选中状态
- 达到 maxSelect 时，未选中的标签变为禁用态
- 选中数量少于 minSelect 时，显示错误提示

---

### 2.6 Slider

**用途**：滑块，用于体重、身高、目标体重等数值输入。

**Props 定义**：

```typescript
interface SliderProps {
  value: number;
  onChange: (value: number) => void;
  minimumValue: number;
  maximumValue: number;
  step?: number; // 步进值，默认 1
  label?: string;
  unit?: string; // 单位，如 "kg"、"cm"
  showValue?: boolean; // 是否显示当前值，默认 true
}
```

**样式规范**：

- **轨道**：
  - 高度：4px
  - 背景：`#F0F0F0`
  - 圆角：2px
- **填充轨道**：
  - 背景：`#4CAF50`（品牌色）
- **滑块（Thumb）**：
  - 尺寸：24x24px
  - 背景：`#4CAF50`（品牌色）
  - 阴影：`0 2px 4px rgba(0, 0, 0, 0.2)`
  - 按压时：放大到 28x28px
- **数值显示**：
  - 位置：滑块上方或右侧
  - 字体：16px，Medium，`#1A1A1A`
  - 单位：14px，Regular，`#666666`
- **Label**：14px，Medium，`#666666`

**交互行为**：

- 拖动滑块改变数值
- 点击轨道跳转到对应数值
- 按 step 步进

---

### 2.7 Switch

**用途**：开关，用于提醒开关、隐私设置等二元选择。

**Props 定义**：

```typescript
interface SwitchProps {
  value: boolean;
  onChange: (value: boolean) => void;
  label?: string;
  disabled?: boolean;
}
```

**样式规范**：

- **轨道**：
  - 尺寸：51x31px
  - 圆角：999px
  - **关闭态**：背景 `#E0E0E0`
  - **开启态**：背景 `#4CAF50`（品牌色）
  - **禁用态**：背景 `#F0F0F0`
- **滑块（Thumb）**：
  - 尺寸：27x27px
  - 背景：`#FFFFFF`
  - 阴影：`0 2px 4px rgba(0, 0, 0, 0.2)`
  - **关闭态**：左侧（距离左边 2px）
  - **开启态**：右侧（距离右边 2px）
  - 过渡动画：200ms ease
- **Label**：
  - 字体：16px，Regular，`#1A1A1A`
  - 位置：开关左侧，间距 12px

**交互行为**：

- 点击切换开关状态
- 滑块平滑过渡到目标位置
- 禁用时不响应点击

---

## 3. React Hook Form 集成

所有表单组件都支持 React Hook Form 的 `Controller` 组件进行集成，实现表单状态管理和校验。

### 基本用法

```typescript
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { TextInput, Picker, MultiSelectTags } from '@/components/form';

const MyForm = () => {
  const { control, handleSubmit } = useForm({
    resolver: zodResolver(schema),
  });

  return (
    <View>
      {/* TextInput 集成 */}
      <Controller
        control={control}
        name="nickname"
        render={({ field, fieldState }) => (
          <TextInput
            value={field.value}
            onChangeText={field.onChange}
            label="昵称"
            placeholder="请输入昵称"
            error={fieldState.error?.message}
          />
        )}
      />

      {/* Picker 集成 */}
      <Controller
        control={control}
        name="gender"
        render={({ field, fieldState }) => (
          <Picker
            value={field.value}
            onChange={field.onChange}
            label="性别"
            options={[
              { label: '男', value: 'male' },
              { label: '女', value: 'female' },
            ]}
            error={fieldState.error?.message}
          />
        )}
      />

      {/* MultiSelectTags 集成 */}
      <Controller
        control={control}
        name="healthGoals"
        render={({ field, fieldState }) => (
          <MultiSelectTags
            value={field.value}
            onChange={field.onChange}
            label="健康目标"
            options={['减脂', '增肌', '保持健康', '改善睡眠']}
            maxSelect={3}
            error={fieldState.error?.message}
          />
        )}
      />
    </View>
  );
};
```

### 集成要点

- 所有组件通过 `value` / `onChange`（或 `onChangeText`）与 Controller 对接
- 校验错误通过 `fieldState.error?.message` 传递给组件的 `error` 属性
- 组件内部不管理表单状态，完全受控

---

## 4. Zod 校验集成

表单组件的 `error` 属性接收 Zod 校验错误信息，通过 `@hookform/resolvers/zod` 桥接。

### 校验 Schema 示例

```typescript
import { z } from 'zod';

const profileSchema = z.object({
  nickname: z
    .string()
    .min(2, '昵称至少 2 个字符')
    .max(20, '昵称最多 20 个字符'),
  gender: z.enum(['male', 'female'], {
    required_error: '请选择性别',
  }),
  birthday: z.date({
    required_error: '请选择出生日期',
  }),
  height: z
    .number()
    .min(100, '身高不能低于 100cm')
    .max(250, '身高不能超过 250cm'),
  weight: z
    .number()
    .min(30, '体重不能低于 30kg')
    .max(300, '体重不能超过 300kg'),
  healthGoals: z
    .array(z.string())
    .min(1, '请至少选择一个健康目标')
    .max(3, '最多选择 3 个健康目标'),
  enableReminder: z.boolean(),
});

type ProfileFormData = z.infer<typeof profileSchema>;
```

### 错误展示规则

- 校验错误在字段失焦（onBlur）或提交（onSubmit）时触发
- 错误信息显示在对应组件下方
- 修正输入后错误信息实时清除

---

## 5. 组件开发规范

### TypeScript 类型

- 所有组件必须有完整的 TypeScript 类型定义
- Props 接口导出，方便外部引用
- 使用泛型支持灵活的数据类型（如 Picker 的 value 类型）

### 样式分离

- 样式定义在独立的 `.styles.ts` 文件中
- 使用 `StyleSheet.create()` 创建样式
- 文件命名：`TextInput.styles.ts`、`Picker.styles.ts`

```
components/
  form/
    TextInput/
      TextInput.tsx
      TextInput.styles.ts
      index.ts
    Picker/
      Picker.tsx
      Picker.styles.ts
      index.ts
    index.ts          # 统一导出
```

### Design Tokens

- 所有颜色、间距、字体大小必须使用 Design Tokens，不允许硬编码
- 引用方式：`import { colors, spacing, typography } from '@/theme/tokens'`
- 品牌色：`colors.primary`（`#4CAF50`）
- 错误色：`colors.error`（`#F44336`）
- 背景色：`colors.inputBackground`（`#F7F8FA`）

### Ref 转发

- 所有组件必须支持 `React.forwardRef`，允许父组件获取内部引用
- TextInput / PasswordInput 转发到原生 TextInput 的 ref

```typescript
const TextInput = React.forwardRef<RNTextInput, TextInputProps>((props, ref) => {
  // ...
});
```

### 无障碍支持

- 所有组件必须设置 `accessibilityLabel`
- 输入框设置 `accessibilityHint` 描述预期输入
- 错误状态设置 `accessibilityState={{ error: true }}`
- Switch 设置 `accessibilityRole="switch"`
- 可点击区域最小 44x44px
