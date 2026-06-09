// Home Service - 前端组合调用多个后端接口
// 契约: docs/specs/shared/api-contract.md（不存在独立的 /home 端点）
// 组合策略:
//   - 热量/营养/餐次聚合：GET /diet/daily-summary
//   - 饮水/睡眠/运动/排便卡片：GET /body/today
//   - 当前活跃计划：Phase 8 未完成 → 暂返回 null
//   - AI 洞察：GET /suggestions/daily

import type {
  AuxiliaryItemType,
  HomeAuxiliary,
  HomeData,
  HomeMeal,
  HomePlan,
  MealType,
} from '../types/home.types';
import { apiClient } from '@core/api/client';
import { dietService } from '@features/diet/services/dietService';
import { dataService } from '@features/data/services/dataService';
import { suggestionService } from '@features/suggestion/services/suggestionService';
import { useDietStore } from '@features/diet/store/dietStore';
import { useBodyPendingStore } from '@features/data/store/bodyPendingStore';
import type { PendingBodyRecord } from '@features/data/store/bodyPendingStore';
import type { DietPageData, DietRecord } from '@features/diet/types/diet.types';
import type { TodayRecords } from '@features/data/types/data.types';
import type { AuxiliaryPending } from '../types/home.types';
import type { PlanProgressRaw, PlanResponseRaw } from '@features/plan/types/plan.types';

export interface HomeService {
  /**
   * 获取首页聚合数据
   * @param date - YYYY-MM-DD
   */
  getHomeData(date: string): Promise<HomeData>;
}

// ===== 辅助映射 =====

function foodsSummary(foods: DietRecord['foods']): string {
  if (foods.length === 0) return '';
  const names = foods.map((f) => f.name).filter(Boolean);
  if (names.length === 0) return '';
  if (names.length === 1) return names[0];
  if (names.length === 2) return names.join('、');
  return `${names.slice(0, 2).join('、')}等 ${names.length} 项`;
}

function dietRecordToHomeMeal(r: DietRecord): HomeMeal {
  return {
    type: r.mealType as MealType,
    status: r.status === 'editing' ? 'recorded' : r.status,
    foods: foodsSummary(r.foods),
    calories: r.totalCalories,
    time: r.time,
  };
}

function formatSleepDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m} 分钟`;
  if (m === 0) return `${h} 小时`;
  return `${h} 小时 ${m} 分`;
}

const BOWEL_LABEL: Record<'normal' | 'constipation' | 'diarrhea', string> = {
  normal: '正常',
  constipation: '便秘',
  diarrhea: '腹泻',
};

function mapAuxiliary(today: TodayRecords): HomeAuxiliary {
  return {
    water: today.water
      ? { current: today.water.amount, target: today.water.target }
      : { current: 0, target: 2000 },
    sleep: today.sleep
      ? { duration: formatSleepDuration(today.sleep.duration) }
      : null,
    exercise: today.exercise
      ? { duration: `${today.exercise.duration} 分钟` }
      : null,
    bowel: today.bowel
      ? { status: BOWEL_LABEL[today.bowel.status] ?? today.bowel.status }
      : null,
  };
}

/**
 * 由 DietPageData + TodayRecords 组装首页数据。
 * plan / aiInsight 暂用默认值（Phase 8/9 完成后替换）。
 *
 * 会合并 dietStore 中的 pending 记录：
 * - 如果某个餐次有 pending 记录，优先显示 pending 状态
 * - pending 记录包含 AI 解析的食物列表和热量
 */
export function assembleHomeData(
  date: string,
  diet: DietPageData,
  today: TodayRecords,
  plan: HomePlan | null,
  aiInsight: string
): HomeData {
  // 获取当前日期的所有 pending 记录
  const pendingRecords = useDietStore.getState().pendingRecords;

  // 将 diet.meals 转换为 HomeMeal，并检查是否有 pending 覆盖
  const meals: HomeMeal[] = diet.meals.map((r) => {
    const mealType = r.mealType as MealType;
    const pending = pendingRecords[`${date}_${mealType}`];

    // 如果有 pending 记录，优先显示 pending 状态
    if (pending) {
      // append：预览 = 已保存食物 + 本次新增（所见即所得，确认后即此结果）
      // replace：预览 = 仅本次食物（会替换掉已保存的）
      const previewFoods =
        pending.operation === 'append'
          ? [...r.foods, ...pending.foods]
          : pending.foods;
      const pendingCalories = previewFoods.reduce((sum, f) => sum + f.calories, 0);
      return {
        type: mealType,
        status: 'pending',
        foods: foodsSummary(previewFoods),
        calories: pendingCalories,
        time: r.time,
        pendingOperation: pending.operation ?? 'replace',
      };
    }

    // 否则使用后端返回的记录
    return dietRecordToHomeMeal(r);
  });

  return {
    date,
    calories: {
      current: diet.totalCalories.current,
      target: diet.totalCalories.target,
    },
    nutrients: {
      carbs: diet.nutrients.carbs,
      protein: diet.nutrients.protein,
      fat: diet.nutrients.fat,
    },
    meals,
    aiInsight,
    plan,
    auxiliary: mapAuxiliary(today),
  };
}

// ===== 临时 placeholder（Phase 8/9 完成后替换） =====

/** TODO(Phase 8): 改为 planService.listActive() */
async function fetchActivePlan(): Promise<HomePlan | null> {
  const listed = await apiClient.getPaginated<PlanResponseRaw>('/plans?status=active&page=1&page_size=1');
  const active = listed.data[0];
  if (!active) {
    return null;
  }
  const progress = await apiClient.get<PlanProgressRaw>(`/plans/${active.id}/progress`);
  const today = new Date().toISOString().slice(0, 10);
  const currentPhase =
    active.phases.find((phase) => phase.start_date <= today && phase.end_date >= today)?.title ??
    active.phases[0]?.title;
  return {
    id: active.id,
    name: active.name,
    progress: Math.round(progress.compliance_rate * 100),
    currentPhase,
    completedTasks: progress.completed_tasks,
    totalTasks: progress.total_tasks,
  };
}

const DEFAULT_INSIGHT = '记得多喝水、均衡饮食、保持运动。';

/** 带超时保护的 AI 洞察获取（5 秒超时用默认文案，不阻塞首页） */
async function fetchAIInsight(): Promise<string> {
  try {
    const result = await Promise.race([
      suggestionService.getDailyInsightText(),
      new Promise<string>((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), 5000)
      ),
    ]);
    return result || DEFAULT_INSIGHT;
  } catch {
    return DEFAULT_INSIGHT;
  }
}

// ===== Service 实现 =====

export const homeService: HomeService = {
  async getHomeData(date) {
    // 并行拉取，互不阻塞
    const [diet, today, plan, aiInsight] = await Promise.all([
      dietService.getDietByDate(date),
      dataService.getTodayRecords(date),
      fetchActivePlan(),
      fetchAIInsight(),
    ]);
    return assembleHomeData(date, diet, today, plan, aiInsight);
  },
};

// ===== 独立查询（供拆分后的 hooks 使用） =====

/** 饮食日汇总：热量 + 营养 + 餐次 */
export async function fetchDietSummary(date: string) {
  const diet = await dietService.getDietByDate(date);

  // 获取当前日期的所有 pending 记录
  const pendingRecords = useDietStore.getState().pendingRecords;

  // 将 diet.meals 转换为 HomeMeal，并检查是否有 pending 覆盖
  const meals: HomeMeal[] = diet.meals.map((r) => {
    const mealType = r.mealType as MealType;
    const pending = pendingRecords[`${date}_${mealType}`];

    // 如果有 pending 记录，优先显示 pending 状态
    if (pending) {
      // append：预览 = 已保存食物 + 本次新增（所见即所得，确认后即此结果）
      // replace：预览 = 仅本次食物（会替换掉已保存的）
      const previewFoods =
        pending.operation === 'append'
          ? [...r.foods, ...pending.foods]
          : pending.foods;
      const pendingCalories = previewFoods.reduce((sum, f) => sum + f.calories, 0);
      return {
        type: mealType,
        status: 'pending',
        foods: foodsSummary(previewFoods),
        calories: pendingCalories,
        time: r.time,
        pendingOperation: pending.operation ?? 'replace',
      };
    }

    // 否则使用后端返回的记录
    return dietRecordToHomeMeal(r);
  });

  return {
    calories: { current: diet.totalCalories.current, target: diet.totalCalories.target },
    nutrients: { carbs: diet.nutrients.carbs, protein: diet.nutrients.protein, fat: diet.nutrients.fat },
    meals,
  };
}

/** 辅助记录：饮水/睡眠/运动/排便 */
export async function fetchBodyToday(date: string): Promise<HomeAuxiliary> {
  const today = await dataService.getTodayRecords(date);
  const aux = mapAuxiliary(today);
  return mergeBodyPending(aux, date);
}

const SLEEP_QUALITY_LABEL: Record<string, string> = {
  excellent: '极佳',
  good: '良好',
  fair: '一般',
  poor: '较差',
};

/** 把单条 pending 记录转成首页卡片展示用的预览文本 */
function pendingSummary(p: PendingBodyRecord): string {
  switch (p.recordType) {
    case 'water':
      return p.operation === 'append'
        ? `+${p.waterAmount ?? 0} ml`
        : `${p.waterAmount ?? 0} ml`;
    case 'sleep': {
      const range =
        p.sleepBedTime && p.sleepWakeTime
          ? `${p.sleepBedTime}–${p.sleepWakeTime}`
          : '睡眠';
      const q = p.sleepQuality ? ` ${SLEEP_QUALITY_LABEL[p.sleepQuality] ?? ''}` : '';
      return `${range}${q}`.trim();
    }
    case 'exercise': {
      const t = p.exerciseType ?? '运动';
      const d = p.exerciseDuration ? ` ${p.exerciseDuration} 分钟` : '';
      return `${t}${d}`;
    }
    case 'bowel':
      return BOWEL_LABEL[p.bowelStatus ?? 'normal'] ?? '已记录';
  }
}

/** 合并 bodyPendingStore：某类型有 pending 时，给 aux.pending 填充预览 */
function mergeBodyPending(aux: HomeAuxiliary, date: string): HomeAuxiliary {
  const records = useBodyPendingStore.getState().pendingRecords;
  const pending: NonNullable<HomeAuxiliary['pending']> = {};
  (['water', 'sleep', 'exercise', 'bowel'] as const).forEach((rt) => {
    const p = records[`${date}_${rt}`];
    if (p) {
      const item: AuxiliaryPending = {
        summary: pendingSummary(p),
        operation: p.operation,
      };
      pending[rt] = item;
    }
  });
  return Object.keys(pending).length > 0 ? { ...aux, pending } : aux;
}

/** AI 每日洞察（带 5s 超时保护） */
export { fetchAIInsight };

/** 当前活跃计划 */
export { fetchActivePlan };

// 类型导出给 hook 侧可能使用
export type { AuxiliaryItemType };
