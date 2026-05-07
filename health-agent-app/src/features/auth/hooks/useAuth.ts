// useAuth Hook - 封装登录/注册/忘记密码/Onboarding 流程
// 参考: docs/specs/frontend/modules/10-auth-module.md
//
// 流程：
//   - login: Supabase 登录 → 拉取后端档案 → 写入 globalStore.token + userProfile
//            若用户未完成 Onboarding：暂存到 pendingToken，引导进入 Onboarding
//   - register: Supabase 注册 → 暂存 token，进入 Onboarding
//   - forgotPassword: Supabase resetPasswordForEmail
//   - submitOnboarding: 调用后端 /users/me/onboarding → 写入 globalStore

import { useState } from 'react';
import {
  useGlobalStore,
  UserProfile as GlobalUserProfile,
} from '@core/store/globalStore';
import { authService } from '../services/authService';
import { userService } from '../services/userService';
import { useAuthStore } from '../store/authStore';
import type {
  ActivityLevel,
  AuthUserProfile,
  Gender,
  OnboardingData,
} from '../types/auth.types';

function toGlobalUserProfile(p: AuthUserProfile): GlobalUserProfile {
  const activityMap: Record<ActivityLevel, GlobalUserProfile['activityLevel']> = {
    sedentary: 'sedentary',
    light: 'light',
    moderate: 'moderate',
    heavy: 'very_active',
  };
  const genderMap: Record<Gender, GlobalUserProfile['gender']> = {
    male: 'male',
    female: 'female',
  };
  return {
    id: p.id,
    email: p.email,
    nickname: p.nickname,
    gender: genderMap[p.gender],
    birthDate: p.birthDate,
    height: p.height,
    weight: p.weight,
    targetWeight: p.targetWeight ?? p.weight,
    activityLevel: activityMap[p.activityLevel],
    healthGoals: [p.goalType],
    dietPreferences: p.dietType ? [p.dietType] : [],
    allergies: p.allergies ?? [],
    restrictions: p.restrictions ?? [],
    diseases: p.diseases ?? [],
    onboardingCompleted: p.onboardingCompleted,
  };
}

export function useAuth() {
  const setToken = useGlobalStore((s) => s.setToken);
  const setUserProfile = useGlobalStore((s) => s.setUserProfile);
  const resetOnboarding = useAuthStore((s) => s.resetOnboarding);
  const setPendingToken = useAuthStore((s) => s.setPendingToken);
  const pendingToken = useAuthStore((s) => s.pendingToken);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (
    email: string,
    password: string
  ): Promise<{ success: boolean; onboardingCompleted: boolean }> => {
    setIsLoading(true);
    setError(null);
    try {
      const token = await authService.login(email, password);
      // 登录成功后查询后端档案
      let onboardingCompleted = false;
      try {
        const profile = await userService.getMe();
        onboardingCompleted = profile.onboardingCompleted;
        setUserProfile(toGlobalUserProfile(profile));
      } catch {
        // 后端档案获取失败（可能尚未创建）→ 视为未完成 Onboarding
        onboardingCompleted = false;
      }

      if (onboardingCompleted) {
        setToken(token); // 触发 RootNavigator 切换到 Main
      } else {
        setPendingToken(token);
      }
      return { success: true, onboardingCompleted };
    } catch (e) {
      const msg = e instanceof Error ? e.message : '登录失败，请重试';
      setError(msg);
      return { success: false, onboardingCompleted: false };
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    try {
      const token = await authService.register(email, password);
      resetOnboarding();
      // 若 Supabase 启用邮箱确认，token 可能为空字符串
      setPendingToken(token || null);
      return true;
    } catch (e) {
      const msg = e instanceof Error ? e.message : '注册失败，请重试';
      setError(msg);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const forgotPassword = async (email: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.forgotPassword(email);
      return true;
    } catch (e) {
      const msg = e instanceof Error ? e.message : '发送失败，请重试';
      setError(msg);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const submitOnboarding = async (data: OnboardingData): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    try {
      const profile = await userService.saveOnboarding(data);
      setUserProfile(toGlobalUserProfile(profile));
      const tokenToUse = pendingToken ?? (await authService.getSession());
      if (tokenToUse) setToken(tokenToUse);
      setPendingToken(null);
      resetOnboarding();
      return true;
    } catch (e) {
      const msg = e instanceof Error ? e.message : '保存失败，请重试';
      setError(msg);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } finally {
      useGlobalStore.getState().logout();
      resetOnboarding();
    }
  };

  return {
    isLoading,
    error,
    setError,
    login,
    register,
    forgotPassword,
    submitOnboarding,
    logout,
  };
}
