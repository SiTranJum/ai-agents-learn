import { create } from 'zustand';

export interface UserProfile {
  id: string;
  email: string;
  nickname: string;
  gender: 'male' | 'female' | 'other';
  birthDate: string;
  height: number;
  weight: number;
  targetWeight: number;
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';
  healthGoals: string[];
  dietPreferences: string[];
  allergies: string[];
  restrictions: string[];
  diseases: string[];
  onboardingCompleted: boolean;
}

export type InteractionMode = 'efficiency' | 'confirm' | 'learn';

interface GlobalState {
  // 用户认证
  isAuthenticated: boolean;
  token: string | null;

  // 用户档案
  userProfile: UserProfile | null;

  // 交互模式
  interactionMode: InteractionMode;

  // 当前活跃计划
  activePlanId: string | null;

  // Actions
  setToken: (token: string | null) => void;
  setUserProfile: (profile: UserProfile | null) => void;
  setInteractionMode: (mode: InteractionMode) => void;
  setActivePlanId: (id: string | null) => void;
  logout: () => void;
}

export const useGlobalStore = create<GlobalState>((set) => ({
  isAuthenticated: false,
  token: null,
  userProfile: null,
  interactionMode: 'confirm',
  activePlanId: null,

  setToken: (token) =>
    set({ token, isAuthenticated: token !== null }),

  setUserProfile: (profile) =>
    set({ userProfile: profile }),

  setInteractionMode: (mode) =>
    set({ interactionMode: mode }),

  setActivePlanId: (id) =>
    set({ activePlanId: id }),

  logout: () =>
    set({
      isAuthenticated: false,
      token: null,
      userProfile: null,
      activePlanId: null,
    }),
}));
