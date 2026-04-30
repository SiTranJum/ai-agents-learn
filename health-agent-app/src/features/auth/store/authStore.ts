// Auth Store - Zustand
// 参考: docs/specs/frontend/modules/10-auth-module.md §6

import { create } from 'zustand';
import type { OnboardingData } from '../types/auth.types';

interface AuthStore {
  // 登录状态
  isLoading: boolean;
  error: string | null;

  // Onboarding 状态
  onboardingStep: number; // 1-5
  onboardingData: Partial<OnboardingData>;
  skippedSteps: number[];

  // 注册/登录后但 Onboarding 未完成时的暂存 token
  pendingToken: string | null;

  // Actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setOnboardingStep: (step: number) => void;
  updateOnboardingData: (data: Partial<OnboardingData>) => void;
  skipStep: (step: number) => void;
  resetOnboarding: () => void;
  setPendingToken: (token: string | null) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  isLoading: false,
  error: null,
  onboardingStep: 1,
  onboardingData: {},
  skippedSteps: [],
  pendingToken: null,

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setOnboardingStep: (step) => set({ onboardingStep: step }),
  updateOnboardingData: (data) =>
    set((state) => ({
      onboardingData: { ...state.onboardingData, ...data },
    })),
  skipStep: (step) =>
    set((state) =>
      state.skippedSteps.includes(step)
        ? state
        : { skippedSteps: [...state.skippedSteps, step] }
    ),
  resetOnboarding: () =>
    set({
      onboardingStep: 1,
      onboardingData: {},
      skippedSteps: [],
      pendingToken: null,
    }),
  setPendingToken: (token) => set({ pendingToken: token }),
}));
