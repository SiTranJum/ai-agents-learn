// UserService - 调用后端 API 处理用户档案 / Onboarding
// 参考: docs/specs/frontend/modules/10-auth-module.md §7.4
//       docs/specs/backend/01-core-modules/user-system.md

import { apiClient } from '@core/api/client';
import type { AuthUserProfile, OnboardingData } from '../types/auth.types';

export interface UserService {
  /** 提交 Onboarding 数据 → 写入后端用户档案 */
  saveOnboarding(data: OnboardingData): Promise<AuthUserProfile>;
  /** 检查当前用户是否已完成 Onboarding */
  checkOnboardingStatus(): Promise<boolean>;
  /** 获取当前用户完整档案（GET /users/me） */
  getMe(): Promise<AuthUserProfile>;
}

/** 后端 GET /users/me 的聚合响应（snake_case） */
interface UserFullResponseRaw {
  id: string;
  email: string;
  profile: {
    nickname: string;
    gender: 'male' | 'female';
    birth_date: string;
    height: number;
    current_weight: number;
    target_weight?: number;
    activity_level: 'sedentary' | 'light' | 'moderate' | 'heavy';
    profile_completeness: number;
  };
  preferences: {
    diet_type?: string;
    allergies: string[];
    forbidden_foods: string[];
    disliked_foods: string[];
  };
  health_info: {
    diseases: string[];
    medications?: string;
    medical_restrictions?: string;
  };
  // goal_type / daily_calorie_target 暂未在后端 schema 中暴露，
  // 由前端基于 profile 推断或后续扩展。
  goal_type?: AuthUserProfile['goalType'];
  daily_calorie_target?: number;
  onboarding_completed?: boolean;
  created_at?: string;
  updated_at?: string;
}

function mapBackendToAuthProfile(raw: UserFullResponseRaw): AuthUserProfile {
  return {
    id: raw.id,
    email: raw.email,
    nickname: raw.profile.nickname,
    gender: raw.profile.gender,
    birthDate: raw.profile.birth_date,
    height: raw.profile.height,
    weight: raw.profile.current_weight,
    activityLevel: raw.profile.activity_level,
    goalType: raw.goal_type ?? 'maintain',
    targetWeight: raw.profile.target_weight,
    dailyCalorieTarget: raw.daily_calorie_target,
    dietType: raw.preferences.diet_type,
    allergies: raw.preferences.allergies,
    restrictions: raw.preferences.forbidden_foods,
    diseases: raw.health_info.diseases,
    medications: raw.health_info.medications,
    medicalAdvice: raw.health_info.medical_restrictions,
    onboardingCompleted:
      raw.onboarding_completed ??
      (raw.profile.profile_completeness >= 1),
    createdAt: raw.created_at ?? new Date().toISOString(),
    updatedAt: raw.updated_at ?? new Date().toISOString(),
  };
}

/** 前端 OnboardingData → 后端 onboarding 请求体（camelCase → snake_case） */
function toOnboardingPayload(data: OnboardingData): Record<string, unknown> {
  return {
    profile: {
      nickname: data.nickname,
      gender: data.gender,
      birth_date: data.birthDate,
      height: data.height,
      current_weight: data.weight,
      target_weight: data.targetWeight,
      activity_level: data.activityLevel,
    },
    preferences: {
      diet_type: data.dietType,
      allergies: data.allergies ?? [],
      forbidden_foods: data.restrictions ?? [],
      disliked_foods: [],
    },
    health_info: {
      diseases: data.diseases ?? [],
      medications: data.medications,
      medical_restrictions: data.medicalAdvice,
    },
    goal_type: data.goalType,
    daily_calorie_target: data.dailyCalorieTarget,
  };
}

export const userService: UserService = {
  async saveOnboarding(data) {
    const raw = await apiClient.post<UserFullResponseRaw>(
      '/users/me/onboarding',
      toOnboardingPayload(data)
    );
    return mapBackendToAuthProfile(raw);
  },

  async checkOnboardingStatus() {
    const raw = await apiClient.get<UserFullResponseRaw>('/users/me');
    return (
      raw.onboarding_completed ??
      raw.profile.profile_completeness >= 1
    );
  },

  async getMe() {
    const raw = await apiClient.get<UserFullResponseRaw>('/users/me');
    return mapBackendToAuthProfile(raw);
  },
};
