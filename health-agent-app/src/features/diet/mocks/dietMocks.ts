// 饮食模块 Mock 数据
// 参考: docs/specs/frontend/modules/12-diet-module.md §8

import type {
  DietPageData,
  DietRecord,
  FoodCandidate,
  FoodItem,
  MealType,
} from '../types/diet.types';

const emptyMeal = (mealType: MealType): DietRecord => ({
  mealType,
  status: 'empty',
  foods: [],
  totalCalories: 0,
  nutrients: { carbs: 0, protein: 0, fat: 0 },
});

// 食物库（10+ 常见食物）
export const foodCandidates: FoodCandidate[] = [
  { id: 'f-001', name: '鸡胸肉', defaultAmount: 100, defaultUnit: 'g', caloriesPerPortion: 165, proteinPerPortion: 31, fatPerPortion: 3.6, carbsPerPortion: 0 },
  { id: 'f-002', name: '米饭', defaultAmount: 1, defaultUnit: '碗', caloriesPerPortion: 230, proteinPerPortion: 4.6, fatPerPortion: 0.5, carbsPerPortion: 51 },
  { id: 'f-003', name: '全麦面包', defaultAmount: 1, defaultUnit: '片', caloriesPerPortion: 80, proteinPerPortion: 4, fatPerPortion: 1, carbsPerPortion: 14 },
  { id: 'f-004', name: '牛奶', defaultAmount: 1, defaultUnit: '杯', caloriesPerPortion: 150, proteinPerPortion: 8, fatPerPortion: 8, carbsPerPortion: 12 },
  { id: 'f-005', name: '鸡蛋', defaultAmount: 1, defaultUnit: '个', caloriesPerPortion: 78, proteinPerPortion: 6, fatPerPortion: 5, carbsPerPortion: 0.6 },
  { id: 'f-006', name: '西兰花', defaultAmount: 100, defaultUnit: 'g', caloriesPerPortion: 34, proteinPerPortion: 2.8, fatPerPortion: 0.4, carbsPerPortion: 7 },
  { id: 'f-007', name: '牛肉面', defaultAmount: 1, defaultUnit: '碗', caloriesPerPortion: 590, proteinPerPortion: 25, fatPerPortion: 18, carbsPerPortion: 80 },
  { id: 'f-008', name: '凉拌黄瓜', defaultAmount: 1, defaultUnit: '份', caloriesPerPortion: 50, proteinPerPortion: 1.5, fatPerPortion: 2, carbsPerPortion: 6 },
  { id: 'f-009', name: '杂粮粥', defaultAmount: 1, defaultUnit: '碗', caloriesPerPortion: 180, proteinPerPortion: 5, fatPerPortion: 1.5, carbsPerPortion: 36 },
  { id: 'f-010', name: '紫菜汤', defaultAmount: 1, defaultUnit: '碗', caloriesPerPortion: 60, proteinPerPortion: 3, fatPerPortion: 1, carbsPerPortion: 10 },
  { id: 'f-011', name: '豆浆', defaultAmount: 1, defaultUnit: '杯', caloriesPerPortion: 80, proteinPerPortion: 6, fatPerPortion: 3, carbsPerPortion: 8 },
  { id: 'f-012', name: '苹果', defaultAmount: 1, defaultUnit: '个', caloriesPerPortion: 95, proteinPerPortion: 0.5, fatPerPortion: 0.3, carbsPerPortion: 25 },
  { id: 'f-013', name: '酸奶', defaultAmount: 1, defaultUnit: '杯', caloriesPerPortion: 100, proteinPerPortion: 5, fatPerPortion: 3, carbsPerPortion: 12 },
  { id: 'f-014', name: '沙拉', defaultAmount: 1, defaultUnit: '份', caloriesPerPortion: 180, proteinPerPortion: 5, fatPerPortion: 12, carbsPerPortion: 12 },
  { id: 'f-015', name: '红烧肉', defaultAmount: 100, defaultUnit: 'g', caloriesPerPortion: 360, proteinPerPortion: 14, fatPerPortion: 32, carbsPerPortion: 4 },
];

// ===== 1. 部分记录 mock（默认） =====
export const partialDietMock: DietPageData = {
  date: '2026-04-29',
  totalCalories: { current: 930, target: 1800 },
  nutrients: {
    carbs: { current: 110, target: 225 },
    protein: { current: 50, target: 90 },
    fat: { current: 28, target: 60 },
  },
  meals: [
    {
      id: 'r-001',
      mealType: 'breakfast',
      status: 'recorded',
      time: '08:15',
      foods: [
        { id: 'fi-1', name: '豆浆', amount: 1, unit: '杯', calories: 80, protein: 6, fat: 3, carbs: 8 },
        { id: 'fi-2', name: '鸡蛋', amount: 1, unit: '个', calories: 78, protein: 6, fat: 5, carbs: 0.6 },
        { id: 'fi-3', name: '全麦面包', amount: 2, unit: '片', calories: 160, protein: 8, fat: 2, carbs: 28 },
      ],
      totalCalories: 318,
      nutrients: { carbs: 36.6, protein: 20, fat: 10 },
    },
    {
      id: 'r-002',
      mealType: 'lunch',
      status: 'recorded',
      time: '12:30',
      foods: [
        { id: 'fi-4', name: '鸡胸肉', amount: 100, unit: 'g', calories: 165, protein: 31, fat: 3.6, carbs: 0 },
        { id: 'fi-5', name: '米饭', amount: 1, unit: '碗', calories: 230, protein: 4.6, fat: 0.5, carbs: 51 },
        { id: 'fi-6', name: '西兰花', amount: 100, unit: 'g', calories: 34, protein: 2.8, fat: 0.4, carbs: 7 },
      ],
      totalCalories: 429,
      nutrients: { carbs: 58, protein: 38.4, fat: 4.5 },
    },
    emptyMeal('dinner'),
    emptyMeal('snack'),
  ],
};

// ===== 2. 全部记录 mock =====
export const fullDietMock: DietPageData = {
  ...partialDietMock,
  totalCalories: { current: 1720, target: 1800 },
  nutrients: {
    carbs: { current: 210, target: 225 },
    protein: { current: 85, target: 90 },
    fat: { current: 55, target: 60 },
  },
  meals: [
    partialDietMock.meals[0],
    partialDietMock.meals[1],
    {
      id: 'r-003',
      mealType: 'dinner',
      status: 'recorded',
      time: '18:45',
      foods: [
        { id: 'fi-7', name: '杂粮粥', amount: 1, unit: '碗', calories: 180, protein: 5, fat: 1.5, carbs: 36 },
        { id: 'fi-8', name: '凉拌黄瓜', amount: 1, unit: '份', calories: 50, protein: 1.5, fat: 2, carbs: 6 },
      ],
      totalCalories: 230,
      nutrients: { carbs: 42, protein: 6.5, fat: 3.5 },
    },
    {
      id: 'r-004',
      mealType: 'snack',
      status: 'recorded',
      time: '15:30',
      foods: [
        { id: 'fi-9', name: '苹果', amount: 1, unit: '个', calories: 95, protein: 0.5, fat: 0.3, carbs: 25 },
      ],
      totalCalories: 95,
      nutrients: { carbs: 25, protein: 0.5, fat: 0.3 },
    },
  ],
};

// ===== 3. 全部未记录 mock =====
export const emptyDietMock: DietPageData = {
  date: '2026-04-29',
  totalCalories: { current: 0, target: 1800 },
  nutrients: {
    carbs: { current: 0, target: 225 },
    protein: { current: 0, target: 90 },
    fat: { current: 0, target: 60 },
  },
  meals: [
    emptyMeal('breakfast'),
    emptyMeal('lunch'),
    emptyMeal('dinner'),
    emptyMeal('snack'),
  ],
};

// ===== 4. 待确认 mock =====
export const pendingDietMock: DietPageData = {
  ...partialDietMock,
  meals: [
    partialDietMock.meals[0],
    {
      id: 'r-pending',
      mealType: 'lunch',
      status: 'pending',
      foods: [
        { id: 'fi-p1', name: '鸡胸肉', amount: 100, unit: 'g', calories: 165, protein: 31, fat: 3.6, carbs: 0 },
        { id: 'fi-p2', name: '米饭', amount: 1, unit: '碗', calories: 230, protein: 4.6, fat: 0.5, carbs: 51 },
      ],
      totalCalories: 395,
      nutrients: { carbs: 51, protein: 35.6, fat: 4.1 },
    },
    emptyMeal('dinner'),
    emptyMeal('snack'),
  ],
};

// 工具：克隆食物条目并生成新 ID
let foodSeq = 1000;
export const nextFoodItemId = (): string => `fi-${++foodSeq}`;

// 工具：从食物库构造 FoodItem
export function foodItemFromCandidate(c: FoodCandidate): FoodItem {
  return {
    id: nextFoodItemId(),
    name: c.name,
    amount: c.defaultAmount,
    unit: c.defaultUnit,
    calories: c.caloriesPerPortion,
    protein: c.proteinPerPortion,
    fat: c.fatPerPortion,
    carbs: c.carbsPerPortion,
  };
}
