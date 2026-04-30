# UI 设计文档体系 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate 17 UI design documents covering all V1 pages, global components, design system, official website, and asset prompts — each document structured for AI tools (Figma AI, Midjourney) to directly produce design deliverables.

**Architecture:** Each document follows a unified template (page goal, layout wireframe, component tree, states, interactions, copy, Figma AI prompt, assets). Documents reference a shared design system and component library. All content is Chinese.

**Tech Stack:** Markdown documentation only. Target platform: React Native mobile app (iOS/Android). Design tokens reference: colors, typography, spacing, border-radius defined in `01-design-system.md`.

---

## File Map

All files live under `D:\temp\nuts\我的坚果云\学习\AI\agent\health-agent\docs\prd\v1\ui-design\`.

| File | Responsibility | Status |
|------|---------------|--------|
| `00-ui-overview.md` | 总览、页面清单、文档使用指南 | Update (exists) |
| `01-design-system.md` | 配色、字体、间距、圆角、阴影、图标风格 | Create |
| `02-components.md` | 全局复用组件规范 | Create |
| `03-home-dashboard.md` | 首页 Dashboard | Create |
| `04-diet-record-page.md` | 饮食记录页 | Create |
| `05-diet-edit-page.md` | 饮食编辑详情页 | Create |
| `06-data-page.md` | 数据页（6 个 Tab） | Create |
| `07-body-edit-page.md` | 身体数据编辑详情页 | Create |
| `08-plan-list-page.md` | 计划列表页 | Create |
| `09-plan-detail-page.md` | 计划详情页 | Create |
| `10-plan-create-chat-page.md` | 计划创建对话页 | Create |
| `11-analysis-page.md` | 数据分析页 | Create |
| `12-profile-and-settings.md` | 个人中心 + 设置页 | Create |
| `13-auth-and-onboarding.md` | 登录/注册/档案填写 | Create |
| `14-ai-dialog-and-overlays.md` | AI 全屏对话 + 弹窗/浮层 | Create |
| `15-official-website.md` | 官网 Landing Page | Create |
| `16-asset-prompts.md` | Logo、插画、图标生成 prompt | Create |

---

### Task 1: Update `00-ui-overview.md`

**Files:**
- Modify: `ui-design/00-ui-overview.md`

- [ ] **Step 1: Rewrite overview to serve as index**

Replace the current content with a streamlined index document. Keep only:
1. 设计目标（3 sentences）
2. 全局视觉规范摘要（point to `01-design-system.md` for details）
3. 全局布局规范摘要（point to `02-components.md` for details）
4. 页面清单表格（file name → page name → corresponding PRD）
5. 给 AI 生成页面的统一提示模板
6. 生成素材清单（point to `16-asset-prompts.md` for details）

Remove all detailed page descriptions (those now live in individual files 03-16). Remove duplicate design system content (now in `01-design-system.md`).

- [ ] **Step 2: Verify links**

Check that every file referenced in the page list table matches the file map above.

---

### Task 2: Create `01-design-system.md`

**Files:**
- Create: `ui-design/01-design-system.md`

- [ ] **Step 1: Write design system document**

Document structure:

```markdown
# 设计系统规范

## 1. 配色
### 1.1 品牌色
- 主品牌色：珊瑚橙 #FF7A5C（用途：主按钮、Tab 高亮、进度条、强调元素）
- 主品牌深色：#E96345（用途：按钮按下态、深色文字强调）
- 主品牌浅色：#FFE7E1（用途：待确认卡片背景、浅色标签、选中态背景）

### 1.2 功能色
- 成功绿 #4CD964（用途：达标、完成、正常状态）
- 警告黄 #FFC94D（用途：接近目标、注意提示）
- 信息蓝 #5AC8FA（用途：链接、信息提示）
- 错误红 #FF5A5F（用途：超标、错误、删除）

### 1.3 中性色
- 页面背景 #F7F8FA
- 卡片背景 #FFFFFF
- 一级文字 #222222（标题、重要数值）
- 二级文字 #666666（正文、说明）
- 三级文字 #999999（辅助、placeholder）
- 分割线 #EEEEEE
- 禁用态 #CCCCCC

## 2. 字体
### 2.1 字体层级表
| 层级 | 字号 | 粗细 | 行高 | 用途 |
|------|------|------|------|------|
| 大数值 | 36px | 700 | 44px | 体重、热量等核心数值 |
| 页面标题 | 24px | 700 | 32px | 页面顶部标题 |
| 卡片标题 | 18px | 600 | 26px | 卡片内标题 |
| 正文 | 16px | 400 | 24px | 主要内容文字 |
| 辅助正文 | 14px | 400 | 20px | 次要内容、列表项 |
| 说明文字 | 13px | 400 | 18px | 辅助说明、时间戳 |
| 标签文字 | 12px | 500 | 16px | 标签、badge |

## 3. 间距系统
基础单位：4px
- xs: 4px
- sm: 8px
- md: 12px
- lg: 16px
- xl: 24px
- xxl: 32px

### 3.1 页面间距
- 页面左右边距：16px
- 卡片间距：12px
- 卡片内边距：16px
- 列表项间距：12px

## 4. 圆角
- 小按钮/标签：8px
- 卡片：12px
- 弹层/底部面板：16px
- 输入框/胶囊按钮：24px
- 头像：50%（圆形）

## 5. 阴影
- 卡片阴影：0 2px 8px rgba(0,0,0,0.06)
- 输入框阴影：0 -2px 8px rgba(0,0,0,0.04)
- 弹层阴影：0 -4px 16px rgba(0,0,0,0.1)

## 6. 图标规范
- 风格：线性图标，圆角端点
- 线宽：1.5px
- 尺寸：24×24px（导航）、20×20px（列表）、16×16px（内联）
- 颜色：默认 #999999，激活 #FF7A5C

## 7. 插画规范
- 风格：扁平插画 + 轻微拟人
- 色调：与品牌色系一致，柔和暖色
- 线条：圆润，无尖角
- 场景：健康、饮食、运动、习惯养成
```

---

### Task 3: Create `02-components.md`

**Files:**
- Create: `ui-design/02-components.md`

- [ ] **Step 1: Write global components document**

Document the following reusable components, each with: 描述、尺寸、状态、ASCII 线框、Figma AI prompt。

**Components to document:**

1. **底部 Tab 导航**
   - 4 Tab：首页/饮食/数据/我的
   - 高度 60px
   - 状态：默认、选中

2. **AI 输入框**
   - 高度 56px
   - 元素：拍照按钮、语音按钮、输入框、发送按钮
   - 状态：默认、输入中、录音中、发送中

3. **餐次卡片**
   - 状态：empty、pending、recorded
   - pending 状态显示操作按钮

4. **数据记录卡片**
   - 体重卡片、围度卡片、睡眠卡片、运动卡片、饮水卡片、排便卡片
   - 状态：empty、pending、recorded

5. **计划卡片**
   - 显示：计划名、进度条、状态标签、日期

6. **趋势图组件**
   - 折线图 + 时间范围切换
   - 时间范围：7天/30天/90天/365天

7. **确认对话框**
   - 标题、文案、主按钮、次按钮
   - 半透明遮罩

8. **浮层卡片**
   - 营养查询结果
   - 从底部弹出

9. **Toast 提示**
   - 成功/失败/信息
   - 顶部弹出，2 秒自动消失

10. **进度条/环形图**
    - 热量进度条
    - 营养素环形图

11. **表单组件**
    - 输入框、选择器、日期选择器、多选标签

12. **空状态组件**
    - 插画 + 提示文案 + 操作按钮

---

### Task 4: Create `03-home-dashboard.md`

**Files:**
- Create: `ui-design/03-home-dashboard.md`

- [ ] **Step 1: Write home dashboard page document**

Follow the unified template. Key content:

- **页面目标：** 今日健康概览，快捷操作入口
- **页面入口：** 底部 Tab "首页"
- **页面布局：** ASCII 线框图，从上到下：
  1. 今日概览大卡片（热量环形图 + 营养素）
  2. 快捷操作区（记录饮食、记录体重、查看计划）
  3. 今日饮食时间轴卡片（早/中/晚/加餐）
  4. AI 洞察卡片
  5. 计划进度卡片
  6. 辅助记录小卡片区（饮水、睡眠、运动、排便）
- **组件树：** 列出所有引用的组件
- **页面状态：** 新用户空态、有数据态
- **关键交互：** 点击快捷操作、点击卡片跳转
- **页面文案：** 所有标题、提示文案
- **Figma AI 生成描述：** 完整自然语言段落
- **相关素材：** 首页健康人物插画

---

### Task 5: Create `04-diet-record-page.md`

**Files:**
- Create: `ui-design/04-diet-record-page.md`

- [ ] **Step 1: Write diet record page document**

Key content from PRD 03-diet-recording:

- **页面布局：** 顶部日期切换 + 今日汇总 → 餐次卡片列表 → AI 输入框
- **卡片三种状态：** empty / pending / recorded（含 ASCII 线框）
- **pending 状态：** 高亮边框 + [✓ 确认] [✏️ 修改] [✗ 取消]
- **页面状态：** 空态（新用户）、部分记录、全部记录、待确认
- **关键交互：** AI 输入记录 → 卡片更新 → 确认/修改/取消
- **Figma AI 生成描述**

---

### Task 6: Create `05-diet-edit-page.md`

**Files:**
- Create: `ui-design/05-diet-edit-page.md`

- [ ] **Step 1: Write diet edit page document**

Key content:
- **页面目标：** 编辑饮食记录（表单式修改）
- **页面入口：** 饮食记录页点击 [✏️ 修改]
- **页面布局：** 顶部标题 → 食物列表表单 → 添加/删除食物 → 餐次选择 → 保存/取消
- **表单字段：** 食物名称、份量、单位、热量（自动计算）
- **Figma AI 生成描述**

---

### Task 7: Create `06-data-page.md`

**Files:**
- Create: `ui-design/06-data-page.md`

- [ ] **Step 1: Write data page document**

Key content from PRD 04-body-tracking:

- **页面布局：** 顶部趋势图 → 时间范围切换 → Tab 切换 → 今日记录卡片 → 历史列表
- **6 个 Tab 的内容：** 体重、围度、睡眠、运动、饮水、排便
- **每个 Tab 的卡片设计和状态**
- **趋势图设计：** 7/30/90/365 天
- **饮水快捷按钮：** +250ml / +500ml
- **Figma AI 生成描述**

---

### Task 8: Create `07-body-edit-page.md`

**Files:**
- Create: `ui-design/07-body-edit-page.md`

- [ ] **Step 1: Write body data edit page document**

Key content:
- **页面目标：** 编辑体重/围度/睡眠等记录
- **动态表单：** 根据记录类型展示不同字段
- **Figma AI 生成描述**

---

### Task 9: Create `08-plan-list-page.md`

**Files:**
- Create: `ui-design/08-plan-list-page.md`

- [ ] **Step 1: Write plan list page document**

Key content from PRD 07-plan-system:
- **页面布局：** 顶部标题 + 新建按钮 → 计划卡片列表
- **计划卡片：** 名称、进度条、日期、状态标签
- **状态：** 进行中/已暂停/已完成
- **空态设计**
- **Figma AI 生成描述**

---

### Task 10: Create `09-plan-detail-page.md`

**Files:**
- Create: `ui-design/09-plan-detail-page.md`

- [ ] **Step 1: Write plan detail page document**

Key content:
- **页面布局：** 计划标题 + 状态 → 目标信息 → 今日任务 → 执行趋势 → AI 建议 → 操作按钮
- **操作按钮：** 修改计划、终止计划
- **Figma AI 生成描述**

---

### Task 11: Create `10-plan-create-chat-page.md`

**Files:**
- Create: `ui-design/10-plan-create-chat-page.md`

- [ ] **Step 1: Write plan creation chat page document**

Key content:
- **页面目标：** 多轮对话创建计划（全屏对话页）
- **页面布局：** 顶部返回 + 标题 → 对话消息流 → 底部输入框
- **消息气泡：** AI 左对齐浅灰、用户右对齐品牌浅色
- **Figma AI 生成描述**

---

### Task 12: Create `11-analysis-page.md`

**Files:**
- Create: `ui-design/11-analysis-page.md`

- [ ] **Step 1: Write data analysis page document**

Key content from PRD 09-data-analysis:
- **页面布局：** 热量趋势图 → 营养分布 → 体重变化 → 计划达成率 → AI 洞察
- **图表卡片为主**
- **Figma AI 生成描述**

---

### Task 13: Create `12-profile-and-settings.md`

**Files:**
- Create: `ui-design/12-profile-and-settings.md`

- [ ] **Step 1: Write profile and settings pages document**

Two pages in one document:

**个人中心页：**
- 头像 + 昵称 → 档案摘要 → 饮食偏好 → 疾病信息 → 设置入口 → 退出

**设置页：**
- 交互模式切换（效率/确认/学习）
- 隐私设置
- 通知设置（预留）
- 关于我们

**编辑档案页：**
- 表单分组编辑

- **Figma AI 生成描述**

---

### Task 14: Create `13-auth-and-onboarding.md`

**Files:**
- Create: `ui-design/13-auth-and-onboarding.md`

- [ ] **Step 1: Write auth and onboarding pages document**

Four pages in one document:

**登录页：** Logo + 标题 + 邮箱密码表单 + 登录按钮 + 忘记密码 + 注册入口
**注册页：** 标题 + 邮箱密码确认密码 + 注册按钮 + 登录入口
**忘记密码页：** 邮箱输入 + 发送重置邮件
**基础档案填写页：** 分步表单（5 步）+ 进度条 + 下一步/上一步

- **Figma AI 生成描述**

---

### Task 15: Create `14-ai-dialog-and-overlays.md`

**Files:**
- Create: `ui-design/14-ai-dialog-and-overlays.md`

- [ ] **Step 1: Write AI dialog and overlay pages document**

Three components/pages:

**AI 多轮全屏对话页：** 返回按钮 + 对话流 + 输入框
**跨页面确认弹窗：** 遮罩 + 对话框 + 按钮
**营养查询浮层卡片：** 底部弹出 + 营养数据 + 操作按钮

- **Figma AI 生成描述**

---

### Task 16: Create `15-official-website.md`

**Files:**
- Create: `ui-design/15-official-website.md`

- [ ] **Step 1: Write official website landing page document**

Sections:
1. Hero 区：主标题 + 副标题 + CTA + App mockup
2. 核心价值区：4 个价值点卡片
3. 产品展示区：3-4 张手机 mockup
4. AI 能力介绍区
5. 用户场景区
6. 底部 CTA

- **Figma AI 生成描述**
- **相关素材：** Hero 插画、手机 mockup

---

### Task 17: Create `16-asset-prompts.md`

**Files:**
- Create: `ui-design/16-asset-prompts.md`

- [ ] **Step 1: Write asset generation prompts document**

For each asset, provide:
- 素材名称
- 用途
- 尺寸
- Midjourney / DALL-E prompt（英文）
- 风格参考

**Assets to cover:**
1. App Logo
2. 首页健康人物插画
3. 饮水卡片水杯插画
4. 运动卡片插画
5. 睡眠卡片插画
6. 空状态插画（未记录）
7. 空状态插画（无计划）
8. 空状态插画（无数据）
9. 官网 Hero 区插画
10. 官网手机 mockup 模板
11. Tab 导航图标集（4 个）
12. 功能图标集（拍照、语音、发送、编辑、删除、确认、取消等）

