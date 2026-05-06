// Profile Service - Mock 实现
// 参考: docs/specs/frontend/modules/15-profile-module.md §7

import { appSettingsMock, userProfileMock } from '../mocks/profileMocks';
import type { AppSettings, UserProfile } from '../types/profile.types';

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

let CURRENT_PROFILE: UserProfile = { ...userProfileMock };
let CURRENT_SETTINGS: AppSettings = {
  ...appSettingsMock,
  notifications: { ...appSettingsMock.notifications },
};

export interface ProfileService {
  getUserProfile(): Promise<UserProfile>;
  updateUserProfile(data: Partial<UserProfile>): Promise<UserProfile>;
  deleteAccount(): Promise<void>;
  /** Mock：返回 JSON 字符串而不是 Blob，避免 RN 环境兼容问题 */
  exportData(): Promise<string>;
  getAppSettings(): Promise<AppSettings>;
  updateAppSettings(settings: Partial<AppSettings>): Promise<AppSettings>;
}

export const profileService: ProfileService = {
  async getUserProfile() {
    await delay(300);
    return { ...CURRENT_PROFILE };
  },

  async updateUserProfile(data) {
    await delay(500);
    CURRENT_PROFILE = { ...CURRENT_PROFILE, ...data };
    return { ...CURRENT_PROFILE };
  },

  async deleteAccount() {
    await delay(500);
    // mock：不真的删除数据，留给上层清理本地态
  },

  async exportData() {
    await delay(400);
    return JSON.stringify(
      {
        profile: CURRENT_PROFILE,
        settings: CURRENT_SETTINGS,
        exportedAt: new Date().toISOString(),
      },
      null,
      2
    );
  },

  async getAppSettings() {
    await delay(200);
    return {
      ...CURRENT_SETTINGS,
      notifications: { ...CURRENT_SETTINGS.notifications },
    };
  },

  async updateAppSettings(settings) {
    await delay(300);
    CURRENT_SETTINGS = {
      ...CURRENT_SETTINGS,
      ...settings,
      notifications: {
        ...CURRENT_SETTINGS.notifications,
        ...(settings.notifications ?? {}),
      },
    };
    return {
      ...CURRENT_SETTINGS,
      notifications: { ...CURRENT_SETTINGS.notifications },
    };
  },
};

// 重置 mock 数据（用于退出登录 / 删除账号）
export function resetMockProfile() {
  CURRENT_PROFILE = { ...userProfileMock };
  CURRENT_SETTINGS = {
    ...appSettingsMock,
    notifications: { ...appSettingsMock.notifications },
  };
}
