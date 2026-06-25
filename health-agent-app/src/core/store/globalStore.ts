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
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'heavy';
  healthGoals: string[];
  dietPreferences: string[];
  allergies: string[];
  restrictions: string[];
  diseases: string[];
  onboardingCompleted: boolean;
}

export type InteractionMode = 'efficiency' | 'confirmation' | 'learning';

interface GlobalState {
  // 用户认证
  isAuthenticated: boolean;
  token: string | null;

  // 密码恢复模式：用户从重置邮件链接进来时为 true。
  // 此时即使 Supabase 建立了临时 session，也不能把用户直接放进主页，
  // 而要停在「设置新密码」页。setToken 在该模式下不会翻 isAuthenticated。
  isRecoveringPassword: boolean;

  // 用户档案
  userProfile: UserProfile | null;

  // 交互模式
  interactionMode: InteractionMode;

  // 当前活跃计划
  activePlanId: string | null;

  // Actions
  setToken: (token: string | null) => void;
  setRecoveringPassword: (recovering: boolean) => void;
  setUserProfile: (profile: UserProfile | null) => void;
  setInteractionMode: (mode: InteractionMode) => void;
  setActivePlanId: (id: string | null) => void;
  logout: () => void;
}

export const useGlobalStore = create<GlobalState>((set, get) => ({
  isAuthenticated: false,
  token: null,
  isRecoveringPassword: false,
  userProfile: null,
  interactionMode: 'confirmation',
  activePlanId: null,

  setToken: (token) =>
    // 恢复密码期间，保存 token 但不触发已登录（避免越过设密页直接进主页）
    set({
      token,
      isAuthenticated: token !== null && !get().isRecoveringPassword,
    }),

  setRecoveringPassword: (recovering) =>
    set({ isRecoveringPassword: recovering }),

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
      isRecoveringPassword: false,
      userProfile: null,
      activePlanId: null,
    }),
}));
