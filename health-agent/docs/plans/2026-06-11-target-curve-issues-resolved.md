# 计划目标曲线问题排查与修复

## 本次排查的问题

### 问题 :目标曲线"前 6 天和体重线重合,最后一天突降到 0"

**现象**:数据页的体重趋势图,目标曲线(虚线)前 6 天跟实际体重线(实线)完全重合,06-11 这天突然跳到真正的目标值 65kg,视觉上像"断崖式下跌到 0"。

**数据库验证**:
```
Active plan: 3a20acb0..., start=2026-06-11, end=2026-07-08
plan_daily_targets (28 rows):
  2026-06-11: 65.0
  2026-06-12: 65.037
  ...
  2026-07-08: 66.0

body_weight_records (最近):
  2026-06-11: 68.7
  2026-06-10: 68.9
  ...
  2026-06-02: 69.9
```

数据完全正常。问题在**前端展示逻辑**。

**根因分析**:
`health-agent-app/src/features/data/components/TrendChart.tsx:128-147`

横轴是**体重记录的日期**(06-02 ~ 06-11,共 10 天)。计划 06-11 才开始,前 9 天目标曲线没有值(null)。

旧 `fillForward` 逻辑:
```typescript
function fillForward(values: Array<number | null>, fallback: number[]): number[] {
  const out: number[] = [];
  let last: number | null = null;
  for (let i = 0; i < values.length; i += 1) {
    const v = values[i];
    if (v !== null) {
      last = v;
      out.push(v);
    } else {
      out.push(last ?? fallback[i] ?? 0);  // ← 问题在这
    }
  }
  return out;
}
```

当开头是 null 时,用 `fallback[i]`(=实际体重值)兜底 → **目标线前 9 天复制了实际体重(69.9 → 68.7)** → 06-11 才"突然"跳到真目标值 65,视觉像断崖。

**修复**:
```typescript
function fillForward(values: Array<number | null>, fallback: number[]): number[] {
  const firstValid = values.find((v): v is number => v !== null);  // 找第一个未来有效值
  const out: number[] = [];
  let last: number | null = null;
  for (let i = 0; i < values.length; i += 1) {
    const v = values[i];
    if (v !== null) {
      last = v;
      out.push(v);
    } else if (last !== null) {
      out.push(last);  // 中间空缺:用前一个有效值填充
    } else if (firstValid !== undefined) {
      // 开头空缺:用第一个未来有效目标值水平延伸,避免与实际曲线重叠
      out.push(firstValid);
    } else {
      out.push(fallback[i] ?? 0);
    }
  }
  return out;
}
```

**效果**:
- 前 9 天(06-02 ~ 06-10):目标线显示为"未来计划起点的水平线"(65kg)
- 06-11 开始:目标线正常显示 65 → 66 的渐进曲线
- 不再有"和实际体重重合"或"突然跳跃"

---

## 三、计划目标曲线接口与数据流

### 后端接口

**获取目标曲线**:
```
GET /api/v1/plans/{plan_id}/daily-targets
    ?dimension=weight
    &start_date=2026-06-01
    &end_date=2026-07-31
```

**响应结构**:
```json
[
  {
    "plan_id": "3a20acb0-...",
    "sub_plan_id": "e24e7a3b-...",
    "dimension": "weight",
    "unit": "kg",
    "points": [
      {"date": "2026-06-11", "target_value": 65.0, "unit": "kg", "dimension": "weight"},
      {"date": "2026-06-12", "target_value": 65.037, "unit": "kg", "dimension": "weight"},
      ...
    ]
  }
]
```

**实现位置**:
- 路由:`health-agent/backend/app/api/v1/plans.py:294-309`
- Service:`health-agent/backend/app/services/plan_service.py:605-650`
- Repository:`health-agent/backend/app/db/repositories/plan_repo.py:231-253`

### 前端消费

**Hook**:
`health-agent-app/src/features/data/hooks/usePlanData.ts:69-83`
```typescript
export function useActivePlanTargetCurve(dimension?: PlanDimension) {
  const { data: plan } = useActivePlan();
  return useQuery({
    queryKey: ['active-plan-target-curve', dimension],
    queryFn: async () => {
      if (!plan?.id) return null;
      const curves = await planService.getDailyTargetCurves(plan.id, dimension);
      return curves.find((c) => c.dimension === dimension) || null;
    },
    enabled: !!plan?.id && !!dimension,
  });
}
```

**展示位置**:
`health-agent-app/src/features/data/screens/DataScreen.tsx:130,319-320`
```tsx
const targetCurveQuery = useActivePlanTargetCurve(planDimension);

<TrendChart
  targetPoints={selectedTab === 'bowel' ? undefined : targetCurveQuery.data?.points}
/>
```

**图表渲染**:
`health-agent-app/src/features/data/components/TrendChart.tsx:30-60`
```typescript
const { targetPoints } = props;
const hasTarget = !!targetPoints && targetPoints.length > 0;
const targetValues = hasTarget
  ? sampled.map((p) => nearestTargetValue(targetPoints!, p.date))
  : [];
const showTarget = hasTarget && targetValues.some((v) => v !== null);

// 传给 LineChart
datasets: [
  { data: sampled.map((p) => p.value), color: theme.colors.primary },
  ...(showTarget ? [{
    data: fillForward(targetValues, sampled.map((p) => p.value)),
    color: theme.colors.secondary,
    strokeDashArray: [5, 3],
  }] : []),
]
```

### 数据库表

**`plan_daily_targets`**:
```sql
CREATE TABLE plan_daily_targets (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  plan_id UUID NOT NULL,
  sub_plan_id UUID NOT NULL,
  dimension TEXT NOT NULL,  -- 'weight' / 'water' / 'sleep' / ...
  date DATE NOT NULL,
  target_value NUMERIC NOT NULL,
  unit TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(sub_plan_id, date)
);
```

**写入时机**:
1. AI 对话确认创建计划 → `create_plan_from_draft` → `_derive_weight_sub_plan`
2. 如果 LLM 给了 `weight_anchors` 且校验通过 → `build_curve_from_anchors`(插值)
3. 否则 → `generate_curve`(线性 current_weight → target_weight)
4. `replace_daily_targets` 批量写入(先删旧再插新)

---

## 四、当前遗留问题

### 问题:曲线完全不显示

**上下文**:
- 用户反馈:"你改完后曲线完全不显示了"
- 修复前:曲线显示但前 6 天和体重线重合、最后一天突降
- 修复后:曲线不显示(可能是 `fillForward` 逻辑 bug 或前端渲染条件变化)

**需要排查**:
1. `fillForward` 的 `firstValid` 是否正确找到了 65.0?
2. `showTarget` 条件:`targetValues.some((v) => v !== null)` 是否通过?
3. 如果全部 `targetValues` 都是 65(开头空缺用 firstValid 填充),`some(v !== null)` 应该是 true,为什么不显示?

**可能原因猜测**:
- `firstValid` 是 undefined(目标点数组为空或全是 null)?
- 或者 `fillForward` 返回的数组长度不对,导致 `LineChart` 渲染异常?
- 或者前端缓存未刷新,还在用旧数据?

**建议下一步**:
1. 前端加 console.log 看 `targetValues` 和 `fillForward` 返回值
2. 或者回滚 `fillForward` 修改,先恢复显示再调整逻辑

---

## 五、提交记录

**5145a1b** - feat(plan): LLM-driven weight target curve via anchors
后端方案 C:LLM 输出锚点 + 后端插值,解决方案 B 超时。增加锚点校验(单调性 / 速率 / 端点匹配)。

**f75c009** - fix(ui): hide card_action user bubble; stop target curve overlap with actual
前端两个 UI 修复:
1. `useStreamingChat`:跳过 card_action 的用户消息气泡
2. `TrendChart fillForward`:开头 null 用未来第一个有效目标值兜底,不再用实际体重

---

## 六、相关文档

- 计划模块设计:`health-agent/docs/plans/2026-06-09-plan-module-design.md`
- 方案 C 锚点插值:`§5.3 每日目标曲线 + §六 下一步行动第4项`
- 前端目标曲线叠加:`docs/prd/v1/ui-design/06-data-page.md §3`
