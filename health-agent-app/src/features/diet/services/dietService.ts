// Diet Service - Mock 实现
// 参考: docs/specs/frontend/modules/12-diet-module.md §7

import type { DietPageData, DietRecord } from '../types/diet.types';
import { partialDietMock, foodCandidates, foodItemFromCandidate } from '../mocks/dietMocks';
import type { FoodCandidate } from '../types/diet.types';

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

// 计算单餐的汇总（热量与三大营养素）
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
  saveDietRecord(record: DietRecord): Promise<DietRecord>;
  deleteDietRecord(recordId: string): Promise<void>;
  confirmPendingRecord(recordId: string): Promise<DietRecord>;
  cancelPendingRecord(recordId: string): Promise<void>;
}

export const dietService: DietService = {
  async getDietByDate(date) {
    await delay(500);
    // Mock-First：默认返回部分记录态
    return { ...partialDietMock, date };
  },

  async saveDietRecord(record) {
    await delay(600);
    const recalculated = recalcMeal(record);
    return {
      ...recalculated,
      id: record.id ?? `r-${Date.now()}`,
      status: 'recorded',
    };
  },

  async deleteDietRecord(_recordId) {
    await delay(400);
  },

  async confirmPendingRecord(recordId) {
    await delay(400);
    return {
      id: recordId,
      mealType: 'lunch',
      status: 'recorded',
      foods: [],
      totalCalories: 0,
      nutrients: { carbs: 0, protein: 0, fat: 0 },
    };
  },

  async cancelPendingRecord(_recordId) {
    await delay(300);
  },
};

// ===== Food Service =====
export interface FoodService {
  searchFood(keyword: string): Promise<FoodCandidate[]>;
  getFoodNutrition(foodName: string, amount: number, unit: string): Promise<FoodCandidate | null>;
}

export const foodService: FoodService = {
  async searchFood(keyword) {
    await delay(200);
    if (!keyword.trim()) return [];
    const kw = keyword.trim().toLowerCase();
    return foodCandidates
      .filter((f) => f.name.toLowerCase().includes(kw))
      .slice(0, 5);
  },

  async getFoodNutrition(foodName, amount, unit) {
    await delay(150);
    const candidate = foodCandidates.find((f) => f.name === foodName);
    if (!candidate) return null;
    // 单位匹配时按比例缩放，否则按默认份返回
    if (candidate.defaultUnit === unit) {
      const ratio = amount / candidate.defaultAmount;
      return {
        ...candidate,
        defaultAmount: amount,
        caloriesPerPortion: Math.round(candidate.caloriesPerPortion * ratio),
        proteinPerPortion: Math.round(candidate.proteinPerPortion * ratio * 10) / 10,
        fatPerPortion: Math.round(candidate.fatPerPortion * ratio * 10) / 10,
        carbsPerPortion: Math.round(candidate.carbsPerPortion * ratio * 10) / 10,
      };
    }
    return candidate;
  },
};

// 工具导出
export { foodItemFromCandidate };
