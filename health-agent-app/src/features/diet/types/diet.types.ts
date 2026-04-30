// 饮食模块类型定义
// 参考: docs/specs/frontend/modules/12-diet-module.md §4

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';
export type DietRecordStatus = 'empty' | 'pending' | 'recorded' | 'editing';

// 食物条目
export interface FoodItem {
  /** 食物条目 ID（前端临时 ID 或服务端 ID） */
  id: string;
  /** 食物名称 */
  name: string;
  /** 份量数值 */
  amount: number;
  /** 单位（g、碗、个、片、杯、勺、份） */
  unit: string;
  /** 该食物条目的热量（kcal） */
  calories: number;
  /** 蛋白质（g） */
  protein: number;
  /** 脂肪（g） */
  fat: number;
  /** 碳水（g） */
  carbs: number;
}

// 单餐记录
export interface DietRecord {
  /** 记录 ID（empty 状态可为空） */
  id?: string;
  /** 餐次类型 */
  mealType: MealType;
  /** 卡片状态 */
  status: DietRecordStatus;
  /** 食物条目 */
  foods: FoodItem[];
  /** 该餐总热量 */
  totalCalories: number;
  /** 营养素汇总 */
  nutrients: {
    carbs: number;
    protein: number;
    fat: number;
  };
  /** 记录时间，如 "12:30" */
  time?: string;
  /** 修改前的原记录（仅 editing 状态使用） */
  originalRecord?: DietRecord;
}

// 饮食页聚合数据
export interface DietPageData {
  /** 日期 YYYY-MM-DD */
  date: string;
  /** 当日总热量目标 */
  totalCalories: { current: number; target: number };
  /** 三大营养素汇总（g） */
  nutrients: {
    carbs: { current: number; target: number };
    protein: { current: number; target: number };
    fat: { current: number; target: number };
  };
  /** 4 餐记录（顺序：早/午/晚/加餐） */
  meals: DietRecord[];
}

// 编辑表单数据
export interface DietEditFormData {
  mealType: MealType;
  foods: FoodItem[];
}

// 食物搜索候选项（食物库条目）
export interface FoodCandidate {
  id: string;
  name: string;
  /** 默认份量 */
  defaultAmount: number;
  /** 默认单位 */
  defaultUnit: string;
  /** 每"默认份量×默认单位"对应的营养信息 */
  caloriesPerPortion: number;
  proteinPerPortion: number;
  fatPerPortion: number;
  carbsPerPortion: number;
}
