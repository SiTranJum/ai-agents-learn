// Profile 模块类型
// 参考: docs/specs/frontend/modules/15-profile-module.md §4
// 2026-05: 枚举与后端 api-contract §2 对齐；medications 改为 string

export type Gender = 'male' | 'female' | 'other';
/** 与后端 api-contract §2.2 对齐 */
export type ActivityLevel = 'sedentary' | 'light' | 'moderate' | 'heavy';
/** 与后端 api-contract §2.5 对齐 */
export type InteractionMode = 'efficiency' | 'confirmation' | 'learning';

export interface UserProfile {
  id: string;
  email: string;
  nickname: string;
  /** 头像 URL；V1 前端本地化，不落库 */
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
  /** 服用药物（后端 health_info.medications 是单字段多行文本） */
  medications: string;
  medicalAdvice?: string;
}

/**
 * App 层设置。
 * - interactionMode 落后端（PUT /users/me/settings）
 * - notifications V1 仅存前端 AsyncStorage（后端没有对应端点）
 */
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
  /** 服用药物（单字符串） */
  medications: string;
  medicalAdvice: string;
}
