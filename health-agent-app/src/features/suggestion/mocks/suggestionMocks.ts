// AI 建议模块 Mock 数据

import type { DailySuggestionResponseRaw, InsightResponseRaw, MealSuggestionResponseRaw } from '../types/suggestion.types';

const now = new Date().toISOString();

export const dailySuggestionMock: DailySuggestionResponseRaw = {
  generated_at: now,
  disclaimer: '本建议仅用于日常健康管理参考，不能替代专业医疗诊断或治疗。',
  suggestions: [
    {
      id: 'suggestion-daily-1',
      type: 'proactive_insight',
      title: '今日蛋白质提醒',
      content: '今天优先保证一餐有优质蛋白，比如鸡蛋、豆腐或鸡胸肉。',
      priority: 'medium',
      created_at: now,
    },
  ],
};

export const mealSuggestionMock: MealSuggestionResponseRaw = {
  suggestion_id: 'suggestion-meal-1',
  meal_type: 'lunch',
  consumed_today: { calories: 0, protein: 0, fat: 0, carbs: 0 },
  remaining: { calories: 600, protein: 30, fat: 20, carbs: 75 },
  suggestions: ['鸡蛋', '豆腐', '绿叶蔬菜'],
  reasoning: '优先补充蛋白质和蔬菜，帮助提升饱腹感。',
  disclaimer: '本建议仅用于日常健康管理参考，不能替代专业医疗诊断或治疗。',
};

export const insightMock: InsightResponseRaw = {
  period: 'last_30_days',
  disclaimer: '本建议仅用于日常健康管理参考，不能替代专业医疗诊断或治疗。',
  insights: [
    {
      id: 'insight-1',
      dimension: 'data_completeness',
      finding: '最近记录还不够连续',
      suggestion: '建议连续记录 7 天饮食和体重，让 AI 更准确识别趋势。',
      data_support: { period: 'last_30_days' },
      generated_at: now,
    },
  ],
};

