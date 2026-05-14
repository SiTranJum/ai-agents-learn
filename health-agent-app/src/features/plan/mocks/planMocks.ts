// 计划模块 Mock 数据
// 参考: docs/specs/frontend/modules/14-plan-module.md §8

import type {
  PlanDetail,
  PlanListItem,
  PlanSummary,
} from '../types/plan.types';

// ===== 计划列表 mock：1 进行中 / 1 已完成 =====
export const planListMock: PlanListItem[] = [
  {
    id: 'plan-001',
    name: '减脂计划',
    type: 'weight_loss',
    status: 'active',
    progress: 72,
    startDate: '2026-03-01',
    endDate: '2026-06-01',
  },
  {
    id: 'plan-003',
    name: '增肌计划',
    type: 'habit_formation',
    status: 'completed',
    progress: 100,
    startDate: '2026-01-01',
    endDate: '2026-03-31',
  },
];

// ===== 计划详情 mock =====
export const planDetailsMock: Record<string, PlanDetail> = {
  'plan-001': {
    id: 'plan-001',
    name: '减脂计划',
    type: 'weight_loss',
    status: 'active',
    targetWeight: 70,
    dailyCalorieTarget: 1600,
    duration: '3个月',
    currentPhase: '第2阶段',
    startDate: '2026-03-01',
    endDate: '2026-06-01',
    progress: 72,
    tasks: [
      { id: 't-1', text: '早餐控制在 450 kcal 内', completed: true },
      { id: 't-2', text: '午后步行 30 分钟', completed: true },
      { id: 't-3', text: '晚餐不喝含糖饮料', completed: false },
      { id: 't-4', text: '22:30 前入睡', completed: false },
    ],
    trendData: Array.from({ length: 14 }).map((_, i) => {
      const d = new Date('2026-04-30T00:00:00');
      d.setDate(d.getDate() - (13 - i));
      return {
        date: d.toISOString().slice(0, 10),
        value: Math.round((73.5 - i * 0.18 + Math.sin(i * 0.7) * 0.2) * 10) / 10,
      };
    }),
    aiSuggestion:
      '你最近 3 天晚餐热量偏高，建议把晚餐主食减少 1/4，并增加蔬菜比例。',
  },
  'plan-003': {
    id: 'plan-003',
    name: '增肌计划',
    type: 'habit_formation',
    status: 'completed',
    duration: '3个月',
    startDate: '2026-01-01',
    endDate: '2026-03-31',
    progress: 100,
    tasks: [],
    trendData: [],
    aiSuggestion: '计划已完成！平均蛋白质摄入提升 30%，恭喜达成目标',
  },
};

// ===== 默认计划摘要 mock（对话流第 4 步生成） =====
export function buildDefaultSummary(
  type: 'weight_loss' | 'nutrition_adjustment' | 'habit_formation' = 'weight_loss',
  targetWeight: number = 70,
  duration: string = '3个月'
): PlanSummary {
  const NAME_MAP = {
    weight_loss: '减重计划',
    nutrition_adjustment: '营养调整计划',
    habit_formation: '习惯养成计划',
  } as const;
  return {
    name: NAME_MAP[type],
    type,
    targetWeight: type === 'weight_loss' ? targetWeight : undefined,
    dailyCalorieTarget: type === 'weight_loss' ? 1600 : 1800,
    duration,
    phases: 3,
    keyRules:
      type === 'weight_loss'
        ? [
            '每日热量控制在 1600 kcal 以内',
            '每周至少 3 次有氧运动',
            '22:30 前入睡',
          ]
        : type === 'nutrition_adjustment'
        ? ['蛋白质 ≥ 80g/天', '蔬菜每餐 ≥ 1 份', '减少加工食品']
        : ['每日步数 ≥ 8000', '每天饮水 2000ml', '规律作息'],
  };
}

// 对话快捷选项常量
export const TYPE_OPTIONS = ['减重计划', '营养调整', '习惯养成'];
export const DURATION_OPTIONS = ['1个月', '3个月', '6个月'];
