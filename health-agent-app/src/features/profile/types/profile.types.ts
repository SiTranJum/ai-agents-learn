// Profile 模块类型
// 参考: docs/specs/frontend/modules/15-profile-module.md §4

export type Gender = 'male' | 'female' | 'other';
export type ActivityLevel =
  | 'sedentary'
  | 'light'
  | 'moderate'
  | 'active'
  | 'very_active';
/** 与 globalStore 保持一致的交互模式枚举 */
export type InteractionMode = 'efficiency' | 'confirm' | 'learn';

export interface UserProfile {
  id: string;
  email: string;
  nickname: string;
  avatar?: string;
  gender: Gender;
  birthDate: string; // YYYY-MM-DD
  height: number; // cm
  weight: number; // kg
  targetWeight: number; // kg
  activityLevel: ActivityLevel;
  /** 健康目标类型：减脂 / 增肌 / 保持 / 改善习惯 */
  goalType?: string;
  dailyCalorieTarget?: number;
  dietType: string; // 普通饮食 / 素食 / 低碳 / ...
  allergies: string[];
  restrictions: string[];
  dislikedFoods: string[];
  diseases: string[];
  medications: string[];
  medicalAdvice?: string;
}

export interface AppSettings {
  interactionMode: InteractionMode;
  notifications: {
    planReminder: boolean;
    dietReminder: boolean;
  };
}

// 编辑表单类型 — 由 RHF 直接使用
export interface EditProfileFormData {
  nickname: string;
  gender: Gender;
  birthDate: string;
  height: string; // 表单中存字符串，提交时 parseFloat
  weight: string;
  targetWeight: string;
  activityLevel: ActivityLevel;
  goalType: string;
  dailyCalorieTarget: string;
  dietType: string;
  allergies: string[];
  restrictions: string[];
  dislikedFoods: string[];
  diseases: string[];
  medications: string[];
  medicalAdvice: string;
}
