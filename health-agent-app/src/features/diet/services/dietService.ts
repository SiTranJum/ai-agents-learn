// Diet Service - 对接后端 /diet/* 与 /knowledge/foods/*
// 契约: docs/specs/shared/api-contract.md §5、§10

import { apiClient } from '@core/api/client';
import { todayStr } from '@shared/utils/date';
import type {
  DietPageData,
  DietRecord,
  FoodCandidate,
  MealType,
} from '../types/diet.types';
import {
  BackendDailySummary,
  BackendDietRecord,
  BackendFoodSearchItem,
  mapDailySummary,
  mapFoodSearchItem,
  mapFoodItem,
  mergeRecordsToCard,
  toDietRecordPayload,
} from './dietMapper';

// 兼容 editing 态的 Record 容器
interface SaveableRecord extends Omit<DietRecord, 'status'> {
  status: DietRecord['status'];
}

/**
 * 重算单餐的热量与三大营养素（编辑页即时预览用）
 * 保存时后端会自己再算一次，前端结果仅用于展示，不会写入后端。
 */
export function recalcMeal(meal: DietRecord): DietRecord {
  const total = meal.foods.reduce(
    (acc, f) => ({
      calories: acc.calories + f.calories,
      protein: acc.protein + f.protein,
      fat: acc.fat + f.fat,
      carbs: acc.carbs + f.carbs,
    }),
    { calories: 0, protein: 0, fat: 0, carbs: 0 }
  );
  return {
    ...meal,
    totalCalories: Math.round(total.calories),
    nutrients: {
      carbs: Math.round(total.carbs * 10) / 10,
      protein: Math.round(total.protein * 10) / 10,
      fat: Math.round(total.fat * 10) / 10,
    },
  };
}

export interface DietService {
  getDietByDate(date: string): Promise<DietPageData>;
  /**
   * 新增/更新饮食记录。
   * - 无 id → POST /diet/records 新建
   * - 有 id → PUT /diet/records/{id} 更新
   *
   * 注：若同日同 mealType 存在多条记录，getDietByDate 已把它们合并到一张卡（id 取首条）。
   * 保存时只更新首条记录，**不会**自动删除冗余记录（避免误删）。V2 再考虑 upsert。
   */
  saveDietRecord(record: SaveableRecord, date?: string): Promise<DietRecord>;
  deleteDietRecord(recordId: string): Promise<void>;
  /** 确认 pending 卡片 = 直接调用 saveDietRecord 创建 recorded */
  confirmPendingRecord(record: SaveableRecord, date?: string): Promise<DietRecord>;
  /** pending 取消纯前端本地，不调后端 */
  cancelPendingRecord(_recordId?: string): Promise<void>;
}

export const dietService: DietService = {
  async getDietByDate(date) {
    const raw = await apiClient.get<BackendDailySummary>(
      `/diet/daily-summary?date=${encodeURIComponent(date)}`
    );
    return mapDailySummary(raw);
  },

  async saveDietRecord(record, date) {
    const effectiveDate = date ?? todayStr();
    const payload = toDietRecordPayload(record as DietRecord, effectiveDate);
    // 统一走 upsert：按 date + meal_type 替换为 1 条记录，彻底避免幽灵记录
    const raw = await apiClient.put<BackendDietRecord>(
      '/diet/records/upsert',
      payload
    );
    return mergeRecordsToCard([raw], record.mealType);
  },

  async deleteDietRecord(recordId) {
    await apiClient.delete<null>(`/diet/records/${recordId}`);
  },

  async confirmPendingRecord(record, date) {
    // pending 是前端 UI 态，确认 = 新建一条后端记录
    const { id: _omit, ...rest } = record;
    return dietService.saveDietRecord({ ...rest } as SaveableRecord, date);
  },

  async cancelPendingRecord() {
    // noop：pending 仅存在于前端 state，调用方直接清除即可
  },
};

// ===== Food Service =====

export interface FoodService {
  /**
   * 食物搜索。
   * - 调用 /knowledge/foods/search，返回候选列表（仅含每 100g 热量）
   * - 用户选中后，前端按默认 100g 提交，用户可再修改份量
   *   （蛋白质/脂肪/碳水按每 100g 比例自动填充为 0，等用户输入或由后端 RAG 补全）
   */
  searchFood(keyword: string): Promise<FoodCandidate[]>;
  /**
   * 获取食物详情（详情页/编辑页选中后按实际份量推算营养素）
   * - 调用 /knowledge/foods/{id}
   * - V1 暂不使用（D1 方案：选中后用户手动输入份量）
   */
  getFoodDetail(foodId: string): Promise<FoodDetailRaw>;
}

export interface FoodDetailRaw {
  id: string;
  name: string;
  aliases: string[];
  category: string;
  nutrition_per_100g: {
    calories: number;
    protein: number;
    fat: number;
    carbs: number;
    fiber?: number | null;
    sodium?: number | null;
  };
  common_portions: Array<{
    name: string;
    amount: number;
    unit: string;
    amount_grams: number;
  }>;
  data_source: string;
}

export const foodService: FoodService = {
  async searchFood(keyword) {
    const kw = keyword.trim();
    if (!kw) return [];
    const raw = await apiClient.get<BackendFoodSearchItem[]>(
      `/knowledge/foods/search?q=${encodeURIComponent(kw)}&limit=10`
    );
    return raw.map(mapFoodSearchItem);
  },

  async getFoodDetail(foodId) {
    return apiClient.get<FoodDetailRaw>(`/knowledge/foods/${foodId}`);
  },
};

// ===== 工具：从 FoodCandidate 构造新的 FoodItem =====

// V1 前端 FoodItem 本地临时 ID 生成器（保存后由后端 ID 替换）
let LOCAL_FOOD_SEQ = Date.now();
export function nextFoodItemId(): string {
  return `local-${++LOCAL_FOOD_SEQ}`;
}

/**
 * 从搜索候选构造 FoodItem。
 * V1 方案（D1）：默认按 100g 生成，caloriesPerPortion 直接用作热量，
 * 其他营养素先置 0，等用户手动输入或保存时由后端 RAG 补全。
 */
export function foodItemFromCandidate(c: FoodCandidate) {
  return {
    id: nextFoodItemId(),
    name: c.name,
    amount: c.defaultAmount,
    unit: c.defaultUnit,
    amountGrams: c.defaultUnit === 'g' ? c.defaultAmount : undefined,
    calories: c.caloriesPerPortion,
    protein: c.proteinPerPortion,
    fat: c.fatPerPortion,
    carbs: c.carbsPerPortion,
    dataSource: 'database' as const,
    foodId: c.id,
  };
}

// 导出 mapFoodItem 给 AI 对话模块复用（diet_parse 卡片里的食物项）
export { mapFoodItem };
