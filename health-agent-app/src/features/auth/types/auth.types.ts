// Auth 模块类型定义
// 参考: docs/specs/frontend/modules/10-auth-module.md

// ============ 表单数据类型 ============

export interface LoginFormData {
  email: string;
  password: string;
}

export interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
}

export interface ForgotPasswordFormData {
  email: string;
}

export type Gender = 'male' | 'female';
export type ActivityLevel = 'sedentary' | 'light' | 'moderate' | 'heavy';
export type GoalType = 'lose_fat' | 'gain_muscle' | 'maintain' | 'healthy_diet';
export type DietType =
  | 'balanced'
  | 'low_carb'
  | 'high_protein'
  | 'vegetarian'
  | 'mediterranean';

export interface OnboardingData {
  // Step 1
  nickname: string;
  gender: Gender;
  birthDate: string; // ISO date

  // Step 2
  height: number; // cm
  weight: number; // kg
  activityLevel: ActivityLevel;

  // Step 3
  goalType: GoalType;
  targetWeight?: number;
  dailyCalorieTarget?: number;

  // Step 4
  dietType?: DietType;
  allergies?: string[];
  restrictions?: string[];

  // Step 5
  diseases?: string[];
  medications?: string;
  medicalAdvice?: string;
}

// ============ API 响应类型 ============

export interface AuthUserProfile {
  id: string;
  email: string;
  nickname: string;
  gender: Gender;
  birthDate: string;
  height: number;
  weight: number;
  activityLevel: ActivityLevel;
  goalType: GoalType;
  targetWeight?: number;
  dailyCalorieTarget?: number;
  dietType?: string;
  allergies?: string[];
  restrictions?: string[];
  diseases?: string[];
  medications?: string;
  medicalAdvice?: string;
  onboardingCompleted: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface LoginResponse {
  token: string;
  user: AuthUserProfile;
}

export interface RegisterResponse {
  token: string;
}
