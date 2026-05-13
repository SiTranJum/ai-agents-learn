// 饮食模块 - 后端 snake_case ↔ 前端 camelCase 映射层
// 契约: docs/specs/shared/api-contract.md §5

import type {
  DietPageData,
  DietRecord,
  FoodCandidate,
  FoodItem,
  MealType,
  NutritionDataSource,
} from '../types/diet.types';

// ========== 后端响应裸类型（snake_case） ==========

export interface BackendFoodItem {
  id: string;
  name: string;
  amount: number;
  unit: string;
  amount_grams: number | null;
  cooking_method: string | null;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  fiber: number | null;
  sodium: number | null;
  data_source: 'database' | 'api' | 'llm_estimate';
  food_id: string | null;
}

export interface BackendNutritionSummary {
  total_calories: number;
  total_protein: number;
  total_fat: number;
  total_carbs: number;
  total_fiber: number | null;
  total_sodium: number | null;
}

export interface BackendDietRecord {
  id: string;
  meal_type: MealType;
  date: string;
  foods: BackendFoodItem[];
  nutrition_summary: BackendNutritionSummary;
  created_at: string;
  updated_at: string;
}

export interface BackendDailySummary {
  date: string;
  meals: {
    breakfast: BackendDietRecord[];
    lunch: BackendDietRecord[];
    dinner: BackendDietRecord[];
    snack: BackendDietRecord[];
  };
  total_nutrition: BackendNutritionSummary;
  target_nutrition: BackendNutritionSummary | null;
  completion_rate: Record<string, number>;
}

export interface BackendFoodSearchItem {
  id: string;
  name: string;
  aliases: string[];
  category: string;
  calories_per_100g: number;
  match_score: number;
}

// ========== 默认目标值（target_nutrition 为 null 时使用） ==========
const DEFAULT_TARGET = {
  calories: 1800,
  carbs: 225,
  protein: 90,
  fat: 60,
} as const;

// ========== 映射：后端 -> 前端 ==========

export function mapFoodItem(f: BackendFoodItem): FoodItem {
  return {
    id: f.id,
    name: f.name,
    amount: f.amount,
    unit: f.unit,
    amountGrams: f.amount_grams ?? undefined,
    cookingMethod: f.cooking_method ?? undefined,
    calories: f.calories,
    protein: f.protein,
    fat: f.fat,
    carbs: f.carbs,
    fiber: f.fiber ?? undefined,
    sodium: f.sodium ?? undefined,
    dataSource: f.data_source as NutritionDataSource,
    foodId: f.food_id ?? undefined,
  };
}

/** 取 ISO 时间的 HH:mm（用于 DietRecord.time 展示） */
function extractHHmm(iso: string): string | undefined {
  const m = /T(\d{2}:\d{2})/.exec(iso);
  return m?.[1];
}

/**
 * 把同一 mealType 下的多条后端记录合并为一张前端卡片。
 * - 取首条记录的 id 作为卡片 id（编辑时用它做 PUT 目标，多余记录由 service 层删除）
 * - foods 合并、totalCalories/nutrients 重新汇总
 * - time 取最早记录的 created_at HH:mm
 */
export function mergeRecordsToCard(
  records: BackendDietRecord[],
  mealType: MealType
): DietRecord {
  if (records.length === 0) {
    return {
      mealType,
      status: 'empty',
      foods: [],
      totalCalories: 0,
      nutrients: { carbs: 0, protein: 0, fat: 0 },
    };
  }
  // 后端通常已按时间升序，但保险再排一次
  const sorted = [...records].sort((a, b) =>
    a.created_at.localeCompare(b.created_at)
  );
  const head = sorted[0];
  const allFoods = sorted.flatMap((r) => r.foods.map(mapFoodItem));
  const totalCalories = sorted.reduce(
    (s, r) => s + r.nutrition_summary.total_calories,
    0
  );
  const totalCarbs = sorted.reduce(
    (s, r) => s + r.nutrition_summary.total_carbs,
    0
  );
  const totalProtein = sorted.reduce(
    (s, r) => s + r.nutrition_summary.total_protein,
    0
  );
  const totalFat = sorted.reduce(
    (s, r) => s + r.nutrition_summary.total_fat,
    0
  );
  return {
    id: head.id,
    mealType,
    status: 'recorded',
    foods: allFoods,
    totalCalories: Math.round(totalCalories),
    nutrients: {
      carbs: Math.round(totalCarbs * 10) / 10,
      protein: Math.round(totalProtein * 10) / 10,
      fat: Math.round(totalFat * 10) / 10,
    },
    time: extractHHmm(head.created_at),
  };
}

const MEAL_ORDER: MealType[] = ['breakfast', 'lunch', 'dinner', 'snack'];

export function mapDailySummary(s: BackendDailySummary): DietPageData {
  const target = s.target_nutrition ?? null;
  const meals = MEAL_ORDER.map((mt) => mergeRecordsToCard(s.meals[mt], mt));
  return {
    date: s.date,
    totalCalories: {
      current: Math.round(s.total_nutrition.total_calories),
      target: Math.round(target?.total_calories ?? DEFAULT_TARGET.calories),
    },
    nutrients: {
      carbs: {
        current: Math.round(s.total_nutrition.total_carbs * 10) / 10,
        target: Math.round(target?.total_carbs ?? DEFAULT_TARGET.carbs),
      },
      protein: {
        current: Math.round(s.total_nutrition.total_protein * 10) / 10,
        target: Math.round(target?.total_protein ?? DEFAULT_TARGET.protein),
      },
      fat: {
        current: Math.round(s.total_nutrition.total_fat * 10) / 10,
        target: Math.round(target?.total_fat ?? DEFAULT_TARGET.fat),
      },
    },
    meals,
  };
}

/** 食物搜索 → FoodCandidate（D1 方案：默认 100g 份量） */
export function mapFoodSearchItem(b: BackendFoodSearchItem): FoodCandidate {
  return {
    id: b.id,
    name: b.name,
    defaultAmount: 100,
    defaultUnit: 'g',
    caloriesPerPortion: b.calories_per_100g,
    proteinPerPortion: 0,
    fatPerPortion: 0,
    carbsPerPortion: 0,
  };
}

// ========== 映射：前端 -> 后端请求体 ==========

export function toFoodInputPayload(f: FoodItem) {
  return {
    name: f.name,
    amount: f.amount,
    unit: f.unit,
    amount_grams: f.amountGrams ?? null,
    cooking_method: f.cookingMethod ?? null,
    calories: f.calories,
    protein: f.protein,
    fat: f.fat,
    carbs: f.carbs,
    fiber: f.fiber ?? null,
    sodium: f.sodium ?? null,
    data_source: f.dataSource ?? null,
    food_id: f.foodId ?? null,
  };
}

export function toDietRecordPayload(record: DietRecord, date: string) {
  return {
    meal_type: record.mealType,
    date,
    foods: record.foods.map(toFoodInputPayload),
  };
}
