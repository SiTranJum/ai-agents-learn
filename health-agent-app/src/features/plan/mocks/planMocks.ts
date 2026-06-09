import type { PlanDetail, PlanListItem } from '../types/plan.types';

export const planListMock: PlanListItem[] = [
  {
    id: 'plan-001',
    name: '减重计划',
    type: 'weight_loss',
    status: 'active',
    progress: 72,
    startDate: '2026-03-01',
    endDate: '2026-06-01',
    currentPhase: '第 2 阶段',
  },
  {
    id: 'plan-003',
    name: '习惯养成计划',
    type: 'habit_formation',
    status: 'completed',
    progress: 100,
    startDate: '2026-01-01',
    endDate: '2026-03-31',
  },
];

export const planDetailsMock: Record<string, PlanDetail> = {
  'plan-001': {
    id: 'plan-001',
    name: '减重计划',
    type: 'weight_loss',
    status: 'active',
    targetWeight: 70,
    dailyCalorieTarget: 1600,
    duration: '12 周',
    currentPhase: '第 2 阶段',
    startDate: '2026-03-01',
    endDate: '2026-06-01',
    progress: 72,
    completedTasks: 2,
    totalTasks: 4,
    streakDays: 3,
    tasks: [
      { id: 't-1', text: '早餐控制在 450 kcal 左右', completed: true },
      { id: 't-2', text: '午餐后步行 30 分钟', completed: true },
      { id: 't-3', text: '晚餐不喝含糖饮料', completed: false },
      { id: 't-4', text: '22:30 前入睡', completed: false },
    ],
    phases: [
      {
        id: 'phase-1',
        title: '第 1 阶段',
        goal: '先建立稳定执行节奏。',
        startDate: '2026-03-01',
        endDate: '2026-04-01',
        tasks: [
          { id: 't-1', text: '早餐控制在 450 kcal 左右', completed: true },
          { id: 't-2', text: '午餐后步行 30 分钟', completed: true },
        ],
      },
      {
        id: 'phase-2',
        title: '第 2 阶段',
        goal: '保持日常节奏稳定，减少晚餐偏离。',
        startDate: '2026-04-02',
        endDate: '2026-06-01',
        tasks: [
          { id: 't-3', text: '晚餐不喝含糖饮料', completed: false },
          { id: 't-4', text: '22:30 前入睡', completed: false },
        ],
      },
    ],
    trendData: Array.from({ length: 14 }).map((_, index) => {
      const day = new Date('2026-04-30T00:00:00Z');
      day.setUTCDate(day.getUTCDate() - (13 - index));
      return {
        date: day.toISOString().slice(0, 10),
        value: 65 + (index % 4) * 10,
      };
    }),
    aiSuggestion: '晚餐执行有偏离。建议略微减少主食份量，同时保持蔬菜摄入。',
  },
  'plan-003': {
    id: 'plan-003',
    name: '习惯养成计划',
    type: 'habit_formation',
    status: 'completed',
    duration: '12 周',
    startDate: '2026-01-01',
    endDate: '2026-03-31',
    progress: 100,
    completedTasks: 0,
    totalTasks: 0,
    streakDays: 0,
    tasks: [],
    phases: [],
    trendData: [],
    aiSuggestion: '计划已完成。建议把当前节奏作为后续维持期的基础习惯。',
  },
};
