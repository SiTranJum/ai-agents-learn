// Home Service - 前端组合调用多个后端接口
// 契约: docs/specs/shared/api-contract.md（不存在独立的 /home 端点）
// 组合策略:
//   - 热量/营养/餐次聚合：GET /diet/daily-summary
//   - 饮水/睡眠/运动/排便卡片：GET /body/today
//   - 当前活跃计划：Phase 8 未完成 → 暂返回 null
//   - AI 洞察：Phase 9 未完成 → 暂使用 mock 文案

import type {
  AuxiliaryItemType,
  HomeAuxiliary,
  HomeData,
  HomeMeal,
  HomePlan,
  MealType,
} from '../types/home.types';
import { dietService } from '@features/diet/services/dietService';
import { dataService } from '@features/data/services/dataService';
import type { DietPageData, DietRecord } from '@features/diet/types/diet.types';
import type { TodayRecords } from '@features/data/types/data.types';

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

function pad2(n: number): string {
  return n < 10 ? `0${n}` : `${n}`;
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
 */
export function assembleHomeData(
  date: string,
  diet: DietPageData,
  today: TodayRecords,
  plan: HomePlan | null,
  aiInsight: string
): HomeData {
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
    meals: diet.meals.map(dietRecordToHomeMeal),
    aiInsight,
    plan,
    auxiliary: mapAuxiliary(today),
  };
}

// ===== 临时 placeholder（Phase 8/9 完成后替换） =====

/** TODO(Phase 8): 改为 planService.listActive() */
async function fetchActivePlan(): Promise<HomePlan | null> {
  return null;
}

/** TODO(Phase 9): 改为 aiService.getDailyInsight() 或 suggestionService.getDailyTip() */
async function fetchAIInsight(): Promise<string> {
  return '记得多喝水、均衡饮食、保持运动。';
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

// 类型导出给 hook 侧可能使用
export type { AuxiliaryItemType };
