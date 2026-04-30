// useAuth Hook - 封装登录/注册/忘记密码/Onboarding 流程
// 参考: docs/specs/frontend/modules/10-auth-module.md

import { useState } from 'react';
import { useGlobalStore, UserProfile as GlobalUserProfile } from '@core/store/globalStore';
import { authService } from '../services/authService';
import { useAuthStore } from '../store/authStore';
import type {
  ActivityLevel,
  AuthUserProfile,
  Gender,
  OnboardingData,
} from '../types/auth.types';

// 将 Auth 模块的 UserProfile 映射到 Global UserProfile
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

  const login = async (email: string, password: string): Promise<{
    success: boolean;
    onboardingCompleted: boolean;
  }> => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await authService.login(email, password);
      const profile = toGlobalUserProfile(res.user);
      if (res.user.onboardingCompleted) {
        setUserProfile(profile);
        setToken(res.token); // 触发 RootNavigator 切换到 Main
      } else {
        // 未完成 Onboarding：暂存 token，进入 Onboarding 流程
        setUserProfile(profile);
        setPendingToken(res.token);
      }
      return { success: true, onboardingCompleted: res.user.onboardingCompleted };
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
      const res = await authService.register(email, password);
      resetOnboarding();
      setPendingToken(res.token);
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
      const profile = await authService.saveOnboarding(data);
      setUserProfile(toGlobalUserProfile(profile));
      // 写入 token 触发主导航切换
      const tokenToUse = pendingToken ?? 'mock_jwt_token_onboarding';
      setToken(tokenToUse);
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

  return {
    isLoading,
    error,
    setError,
    login,
    register,
    forgotPassword,
    submitOnboarding,
  };
}
