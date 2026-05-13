// Profile Service - 对接后端 /users/me 系列接口
// 契约: docs/specs/shared/api-contract.md §3
// 策略:
//   - getUserProfile → GET /users/me（嵌套结构拍平为前端 UserProfile）
//   - updateUserProfile → 按字段分散调 PUT /users/me/profile + /preferences + /health-info
//   - getAppSettings → GET /users/me 取 settings.interaction_mode + AsyncStorage 取 notifications
//   - updateAppSettings → PUT /users/me/settings + AsyncStorage
//   - deleteAccount / exportData → V1 mock

import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiClient } from '@core/api/client';
import type { AppSettings, InteractionMode, UserProfile } from '../types/profile.types';

// ===== 后端响应裸类型 =====

interface BackendUserFull {
  id: string;
  email: string;
  onboarding_completed: boolean;
  profile: {
    nickname: string | null;
    gender: string | null;
    birth_date: string | null;
    height: number | null;
    current_weight: number | null;
    target_weight: number | null;
    activity_level: string | null;
    goal_type: string | null;
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

// ===== 映射 =====

function mapBackendToProfile(raw: BackendUserFull): UserProfile {
  return {
    id: raw.id,
    email: raw.email,
    nickname: raw.profile.nickname ?? '',
    gender: (raw.profile.gender as UserProfile['gender']) ?? 'male',
    birthDate: raw.profile.birth_date ?? '',
    height: raw.profile.height ?? 0,
    weight: raw.profile.current_weight ?? 0,
    targetWeight: raw.profile.target_weight ?? 0,
    activityLevel:
      (raw.profile.activity_level as UserProfile['activityLevel']) ?? 'moderate',
    goalType: raw.profile.goal_type ?? undefined,
    dailyCalorieTarget: raw.profile.daily_calorie_target ?? undefined,
    dietType: raw.preferences.diet_type ?? '',
    allergies: raw.preferences.allergies,
    restrictions: raw.preferences.forbidden_foods,
    dislikedFoods: raw.preferences.disliked_foods,
    diseases: raw.health_info.diseases,
    medications: raw.health_info.medications ?? '',
    medicalAdvice: raw.health_info.medical_restrictions ?? undefined,
  };
}

function mapBackendToSettings(raw: BackendUserFull): Pick<AppSettings, 'interactionMode'> {
  return {
    interactionMode: (raw.settings.interaction_mode as InteractionMode) ?? 'confirmation',
  };
}

// ===== AsyncStorage keys =====
const NOTIFICATIONS_KEY = '@health_agent/notifications';

async function getNotifications(): Promise<AppSettings['notifications']> {
  try {
    const json = await AsyncStorage.getItem(NOTIFICATIONS_KEY);
    if (json) return JSON.parse(json);
  } catch { /* ignore */ }
  return { planReminder: true, dietReminder: true };
}

async function saveNotifications(n: AppSettings['notifications']): Promise<void> {
  await AsyncStorage.setItem(NOTIFICATIONS_KEY, JSON.stringify(n));
}

// ===== Service =====

export interface ProfileService {
  getUserProfile(): Promise<UserProfile>;
  updateUserProfile(data: Partial<UserProfile>): Promise<UserProfile>;
  deleteAccount(): Promise<void>;
  exportData(): Promise<string>;
  getAppSettings(): Promise<AppSettings>;
  updateAppSettings(settings: Partial<AppSettings>): Promise<AppSettings>;
}

export const profileService: ProfileService = {
  async getUserProfile() {
    const raw = await apiClient.get<BackendUserFull>('/users/me');
    return mapBackendToProfile(raw);
  },

  async updateUserProfile(data) {
    // 按字段归属分散到 3 个端点
    const profileFields: Record<string, unknown> = {};
    const prefFields: Record<string, unknown> = {};
    const healthFields: Record<string, unknown> = {};

    if (data.nickname !== undefined) profileFields.nickname = data.nickname;
    if (data.gender !== undefined) profileFields.gender = data.gender;
    if (data.birthDate !== undefined) profileFields.birth_date = data.birthDate;
    if (data.height !== undefined) profileFields.height = data.height;
    if (data.weight !== undefined) profileFields.current_weight = data.weight;
    if (data.targetWeight !== undefined) profileFields.target_weight = data.targetWeight;
    if (data.activityLevel !== undefined) profileFields.activity_level = data.activityLevel;
    if (data.goalType !== undefined) profileFields.goal_type = data.goalType;
    if (data.dailyCalorieTarget !== undefined)
      profileFields.daily_calorie_target = data.dailyCalorieTarget;

    if (data.dietType !== undefined) prefFields.diet_type = data.dietType;
    if (data.allergies !== undefined) prefFields.allergies = data.allergies;
    if (data.restrictions !== undefined) prefFields.forbidden_foods = data.restrictions;
    if (data.dislikedFoods !== undefined) prefFields.disliked_foods = data.dislikedFoods;

    if (data.diseases !== undefined) healthFields.diseases = data.diseases;
    if (data.medications !== undefined) healthFields.medications = data.medications;
    if (data.medicalAdvice !== undefined)
      healthFields.medical_restrictions = data.medicalAdvice;

    // 并行调用有变更的端点
    const calls: Promise<unknown>[] = [];
    if (Object.keys(profileFields).length > 0)
      calls.push(apiClient.put('/users/me/profile', profileFields));
    if (Object.keys(prefFields).length > 0)
      calls.push(apiClient.put('/users/me/preferences', prefFields));
    if (Object.keys(healthFields).length > 0)
      calls.push(apiClient.put('/users/me/health-info', healthFields));

    await Promise.all(calls);

    // 重新拉取完整档案返回
    return this.getUserProfile();
  },

  async deleteAccount() {
    // V1 mock：后端暂无 delete account 端点
    await new Promise((r) => setTimeout(r, 500));
  },

  async exportData() {
    // V1：前端本地打包 JSON
    const profile = await this.getUserProfile();
    const settings = await this.getAppSettings();
    return JSON.stringify(
      { profile, settings, exportedAt: new Date().toISOString() },
      null,
      2
    );
  },

  async getAppSettings() {
    const raw = await apiClient.get<BackendUserFull>('/users/me');
    const { interactionMode } = mapBackendToSettings(raw);
    const notifications = await getNotifications();
    return { interactionMode, notifications };
  },

  async updateAppSettings(settings) {
    const calls: Promise<unknown>[] = [];

    if (settings.interactionMode !== undefined) {
      calls.push(
        apiClient.put('/users/me/settings', {
          interaction_mode: settings.interactionMode,
        })
      );
    }

    if (settings.notifications !== undefined) {
      calls.push(saveNotifications(settings.notifications));
    }

    await Promise.all(calls);
    return this.getAppSettings();
  },
};

// 重置本地缓存（退出登录时调用）
export async function resetLocalProfileCache() {
  await AsyncStorage.removeItem(NOTIFICATIONS_KEY);
}
