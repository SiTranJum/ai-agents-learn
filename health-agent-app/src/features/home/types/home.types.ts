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
  /** pending 态写入语义：append=追加到已保存记录 / replace=替换。用于卡片标签提示 */
  pendingOperation?: 'append' | 'replace';
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
  /** AI 解析后待确认的辅助记录预览（按类型）。有值则首页卡片显示「待确认」态 */
  pending?: {
    water?: AuxiliaryPending;
    sleep?: AuxiliaryPending;
    exercise?: AuxiliaryPending;
    bowel?: AuxiliaryPending;
  };
}

/** 辅助记录的 pending 预览：summary 用于卡片展示，operation 用于标签 */
export interface AuxiliaryPending {
  /** 卡片上展示的预览文本，如 "+250 ml"、"23:00–07:00 良好"、"跑步 30 分钟" */
  summary: string;
  operation?: 'append' | 'replace';
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
