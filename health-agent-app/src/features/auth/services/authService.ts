// Auth Service - Mock 实现
// 参考: docs/specs/frontend/modules/10-auth-module.md §7-8

import type {
  AuthUserProfile,
  LoginResponse,
  OnboardingData,
  RegisterResponse,
} from '../types/auth.types';
import {
  TEST_EMAIL,
  TEST_PASSWORD,
  mockLoginSuccess,
  mockOnboardingSaveSuccess,
  mockRegisterSuccess,
} from '../mocks/authMocks';

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export interface AuthService {
  login(email: string, password: string): Promise<LoginResponse>;
  register(email: string, password: string): Promise<RegisterResponse>;
  forgotPassword(email: string): Promise<void>;
  saveOnboarding(data: OnboardingData): Promise<AuthUserProfile>;
  checkOnboardingStatus(): Promise<boolean>;
}

export const authService: AuthService = {
  async login(email, password) {
    await delay(1000);
    if (email === TEST_EMAIL && password === TEST_PASSWORD) {
      return mockLoginSuccess;
    }
    throw new Error('邮箱或密码错误，请重试');
  },

  async register(email, _password) {
    await delay(1000);
    if (email === TEST_EMAIL) {
      throw new Error('该邮箱已注册，请直接登录');
    }
    return mockRegisterSuccess;
  },

  async forgotPassword(_email) {
    await delay(1000);
    // 成功无返回值
  },

  async saveOnboarding(data) {
    await delay(1500);
    return {
      ...mockOnboardingSaveSuccess,
      ...data,
      id: mockOnboardingSaveSuccess.id,
      email: mockOnboardingSaveSuccess.email,
      onboardingCompleted: true,
      createdAt: mockOnboardingSaveSuccess.createdAt,
      updatedAt: new Date().toISOString(),
    };
  },

  async checkOnboardingStatus() {
    await delay(500);
    return false;
  },
};
