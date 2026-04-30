// Auth Mock 数据
// 参考: docs/specs/frontend/modules/10-auth-module.md §8

import type {
  AuthUserProfile,
  LoginResponse,
  RegisterResponse,
} from '../types/auth.types';

export const mockLoginSuccess: LoginResponse = {
  token: 'mock_jwt_token_12345',
  user: {
    id: 'user_001',
    email: 'test@example.com',
    nickname: '小明',
    gender: 'male',
    birthDate: '1995-06-15',
    height: 175,
    weight: 74.5,
    activityLevel: 'moderate',
    goalType: 'lose_fat',
    targetWeight: 68,
    dailyCalorieTarget: 2100,
    dietType: 'balanced',
    allergies: ['海鲜', '花生'],
    restrictions: [],
    diseases: [],
    medications: '',
    medicalAdvice: '',
    onboardingCompleted: true,
    createdAt: '2026-04-01T10:00:00Z',
    updatedAt: '2026-04-29T15:30:00Z',
  },
};

export const mockRegisterSuccess: RegisterResponse = {
  token: 'mock_jwt_token_67890',
};

export const mockOnboardingSaveSuccess: AuthUserProfile = {
  id: 'user_002',
  email: 'newuser@example.com',
  nickname: '小红',
  gender: 'female',
  birthDate: '1998-03-20',
  height: 165,
  weight: 58,
  activityLevel: 'light',
  goalType: 'maintain',
  targetWeight: 58,
  dailyCalorieTarget: 1800,
  dietType: 'vegetarian',
  allergies: ['牛奶'],
  restrictions: ['猪肉', '牛肉'],
  diseases: [],
  medications: '',
  medicalAdvice: '',
  onboardingCompleted: true,
  createdAt: '2026-04-29T16:00:00Z',
  updatedAt: '2026-04-29T16:05:00Z',
};

// 测试预置邮箱
export const TEST_EMAIL = 'test@example.com';
export const TEST_PASSWORD = 'password123';
