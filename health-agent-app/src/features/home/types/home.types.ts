// 首页模块类型定义
// 参考: docs/specs/frontend/modules/11-home-module.md §4

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';
export type MealStatus = 'empty' | 'pending' | 'recorded';

export interface HomeMeal {
  type: MealType;
  status: MealStatus;
  foods: string; // 食物摘要文本
  calories: number;
  time?: string; // 如 "08:30"
}

export interface NutrientValue {
  current: number;
  target: number;
}

export interface HomePlan {
  id: string;
  name: string;
  progress: number; // 0-100
  completedTasks: number;
  totalTasks: number;
}

export interface HomeAuxiliary {
  water: { current: number; target: number };
  sleep: { duration: string } | null;
  exercise: { duration: string } | null;
  bowel: { status: string } | null;
}

export interface HomeData {
  date: string; // YYYY-MM-DD
  calories: { current: number; target: number };
  nutrients: {
    carbs: NutrientValue;
    protein: NutrientValue;
    fat: NutrientValue;
  };
  meals: HomeMeal[];
  aiInsight: string;
  plan: HomePlan | null;
  auxiliary: HomeAuxiliary;
}

export type AuxiliaryItemType = 'water' | 'sleep' | 'exercise' | 'bowel';
