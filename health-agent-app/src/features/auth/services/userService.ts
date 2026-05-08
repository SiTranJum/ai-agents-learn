// UserService - 调用后端 API 处理用户档案 / Onboarding
// 契约真相源: docs/specs/shared/api-contract.md §3
// 后端实现: backend/app/api/v1/users.py

import { apiClient } from '@core/api/client';
import type { AuthUserProfile, GoalType, OnboardingData } from '../types/auth.types';

export interface UserService {
  /** 提交 Onboarding 数据 → 写入后端用户档案 */
  saveOnboarding(data: OnboardingData): Promise<AuthUserProfile>;
  /** 检查当前用户是否已完成 Onboarding */
  checkOnboardingStatus(): Promise<boolean>;
  /** 获取当前用户完整档案（GET /users/me） */
  getMe(): Promise<AuthUserProfile>;
}

/**
 * 后端 GET /users/me 的聚合响应（snake_case）。
 * 对齐 docs/specs/shared/api-contract.md §3.2.5。
 * 注意：apiClient 已自动剥离 { data } 信封，此处直接是 data 内容。
 */
interface UserFullResponseRaw {
  id: string;
  email: string;
  onboarding_completed: boolean;
  profile: {
    nickname: string | null;
    gender: 'male' | 'female' | 'other' | null;
    birth_date: string | null;
    height: number | null;
    current_weight: number | null;
    target_weight: number | null;
    activity_level: 'sedentary' | 'light' | 'moderate' | 'heavy' | null;
    goal_type: GoalType | null;
    daily_calorie_target: number | null;
    profile_completeness: number;
  };
  preferences: {
    diet_type: string | null;
    allergies: string[];
    forbidden_foods: string[];
    disliked_foods: string[];
  };
  health_info: {
    diseases: string[];
    medications: string | null;
    medical_restrictions: string | null;
  };
  settings: {
    interaction_mode: string;
  };
  created_at: string | null;
  updated_at: string | null;
}

function mapBackendToAuthProfile(raw: UserFullResponseRaw): AuthUserProfile {
  return {
    id: raw.id,
    email: raw.email,
    nickname: raw.profile.nickname ?? '',
    gender: (raw.profile.gender ?? 'male') as AuthUserProfile['gender'],
    birthDate: raw.profile.birth_date ?? '',
    height: raw.profile.height ?? 0,
    weight: raw.profile.current_weight ?? 0,
    activityLevel: (raw.profile.activity_level ?? 'moderate') as AuthUserProfile['activityLevel'],
    goalType: raw.profile.goal_type ?? 'maintain',
    targetWeight: raw.profile.target_weight ?? undefined,
    dailyCalorieTarget: raw.profile.daily_calorie_target ?? undefined,
    dietType: raw.preferences.diet_type ?? undefined,
    allergies: raw.preferences.allergies,
    restrictions: raw.preferences.forbidden_foods,
    diseases: raw.health_info.diseases,
    medications: raw.health_info.medications ?? undefined,
    medicalAdvice: raw.health_info.medical_restrictions ?? undefined,
    onboardingCompleted: raw.onboarding_completed,
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
      goal_type: data.goalType,
      daily_calorie_target: data.dailyCalorieTarget,
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
    return raw.onboarding_completed;
  },

  async getMe() {
    const raw = await apiClient.get<UserFullResponseRaw>('/users/me');
    return mapBackendToAuthProfile(raw);
  },
};

