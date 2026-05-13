// Profile 模块 Mock 数据
// 参考: docs/specs/frontend/modules/15-profile-module.md §8

import type { AppSettings, UserProfile } from '../types/profile.types';

export const userProfileMock: UserProfile = {
  id: 'user-001',
  email: 'xiaoming@email.com',
  nickname: '小明',
  gender: 'male',
  birthDate: '1995-06-15',
  height: 175,
  weight: 74.5,
  targetWeight: 68,
  activityLevel: 'moderate',
  goalType: '减脂',
  dailyCalorieTarget: 2100,
  dietType: '均衡饮食',
  allergies: ['海鲜', '花生'],
  restrictions: [],
  dislikedFoods: ['香菜'],
  diseases: ['高血压'],
  medications: '氨氯地平 5mg/日',
  medicalAdvice: '低盐饮食，每日盐摄入不超过 6g',
};

export const appSettingsMock: AppSettings = {
  interactionMode: 'confirmation',
  notifications: {
    planReminder: true,
    dietReminder: true,
  },
};

// ===== 选项常量 =====
export const GENDER_OPTIONS = [
  { label: '男', value: 'male' },
  { label: '女', value: 'female' },
  { label: '其他', value: 'other' },
] as const;

export const ACTIVITY_LEVEL_OPTIONS = [
  { label: '久坐（基本不运动）', value: 'sedentary' },
  { label: '轻度活动（每周 1-3 次）', value: 'light' },
  { label: '中度活动（每周 3-5 次）', value: 'moderate' },
  { label: '高强度活动（每周 6 次以上）', value: 'heavy' },
] as const;

export const ACTIVITY_LEVEL_LABEL: Record<string, string> = {
  sedentary: '久坐',
  light: '轻度',
  moderate: '中度',
  heavy: '高强度',
};

export const GOAL_TYPE_OPTIONS = [
  { label: '减脂', value: '减脂' },
  { label: '增肌', value: '增肌' },
  { label: '保持体重', value: '保持体重' },
  { label: '改善习惯', value: '改善习惯' },
];

export const DIET_TYPE_OPTIONS = [
  { label: '均衡饮食', value: '均衡饮食' },
  { label: '低碳饮食', value: '低碳饮食' },
  { label: '高蛋白', value: '高蛋白' },
  { label: '素食', value: '素食' },
  { label: '生酮', value: '生酮' },
];

export const ALLERGY_OPTIONS = [
  { label: '海鲜', value: '海鲜' },
  { label: '花生', value: '花生' },
  { label: '牛奶', value: '牛奶' },
  { label: '鸡蛋', value: '鸡蛋' },
  { label: '坚果', value: '坚果' },
  { label: '麸质', value: '麸质' },
  { label: '大豆', value: '大豆' },
];

export const RESTRICTION_OPTIONS = [
  { label: '猪肉', value: '猪肉' },
  { label: '牛肉', value: '牛肉' },
  { label: '辛辣', value: '辛辣' },
  { label: '油炸', value: '油炸' },
  { label: '甜食', value: '甜食' },
];

export const DISLIKED_FOOD_OPTIONS = [
  { label: '香菜', value: '香菜' },
  { label: '芹菜', value: '芹菜' },
  { label: '苦瓜', value: '苦瓜' },
  { label: '茄子', value: '茄子' },
  { label: '内脏', value: '内脏' },
];

export const DISEASE_OPTIONS = [
  { label: '高血压', value: '高血压' },
  { label: '糖尿病', value: '糖尿病' },
  { label: '高血脂', value: '高血脂' },
  { label: '痛风', value: '痛风' },
  { label: '甲状腺异常', value: '甲状腺异常' },
];

export const MEDICATION_OPTIONS = [
  { label: '氨氯地平 5mg/日', value: '氨氯地平 5mg/日' },
  { label: '二甲双胍', value: '二甲双胍' },
  { label: '阿司匹林', value: '阿司匹林' },
  { label: '他汀类', value: '他汀类' },
];
