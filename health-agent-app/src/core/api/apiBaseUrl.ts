// API Base URL 动态配置（开发期辅助工具）
//
// 设计：
// - 启动时从 AsyncStorage 读取覆盖值，没有则用 EXPO_PUBLIC_API_BASE_URL
// - 用一个 in-memory 变量 `currentBaseUrl` 缓存当前值，apiClient 每次请求时读取
// - 提供 setBaseUrl / resetBaseUrl 给设置页调用
//
// 上线前删除：
// 1. 删除本文件
// 2. apiClient 改回直接读 process.env.EXPO_PUBLIC_API_BASE_URL
// 3. 删除 src/features/profile/screens/DevApiSettingsScreen.tsx
// 4. 删除 SettingsScreen 里的"开发者：API 地址"入口

import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = '@health_agent/dev_api_base_url';

const ENV_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

let currentBaseUrl: string = ENV_BASE_URL;

/** 应用启动时调用一次，把 storage 里的覆盖值加载到内存。 */
export async function initApiBaseUrl(): Promise<void> {
  try {
    const stored = await AsyncStorage.getItem(STORAGE_KEY);
    if (stored && stored.trim()) {
      currentBaseUrl = stored.trim();
    }
  } catch {
    // 忽略 storage 读失败，使用 env 默认值
  }
}

/** apiClient 每次请求时读取当前 baseUrl */
export function getApiBaseUrl(): string {
  return currentBaseUrl;
}

/** 获取 env 默认值（用于 UI 上展示原值 / 重置） */
export function getEnvApiBaseUrl(): string {
  return ENV_BASE_URL;
}

/** 设置自定义 baseUrl 并持久化 */
export async function setApiBaseUrl(url: string): Promise<void> {
  const normalized = url.trim().replace(/\/$/, ''); // 去尾部斜杠
  currentBaseUrl = normalized || ENV_BASE_URL;
  if (normalized) {
    await AsyncStorage.setItem(STORAGE_KEY, normalized);
  } else {
    await AsyncStorage.removeItem(STORAGE_KEY);
  }
}

/** 重置为 env 默认值 */
export async function resetApiBaseUrl(): Promise<void> {
  currentBaseUrl = ENV_BASE_URL;
  await AsyncStorage.removeItem(STORAGE_KEY);
}
