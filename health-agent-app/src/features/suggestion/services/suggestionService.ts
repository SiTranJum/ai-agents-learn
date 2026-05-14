// AI 建议 Service - 优先调用后端 API，失败回退 mock

import { apiClient } from '@core/api/client';
import { dailySuggestionMock, insightMock, mealSuggestionMock } from '../mocks/suggestionMocks';
import type {
  DailySuggestionResponseRaw,
  FeedbackRating,
  InsightResponseRaw,
  MealSuggestionResponseRaw,
} from '../types/suggestion.types';

export interface SuggestionService {
  getDailySuggestions(): Promise<DailySuggestionResponseRaw>;
  getMealSuggestions(mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack'): Promise<MealSuggestionResponseRaw>;
  getInsights(): Promise<InsightResponseRaw>;
  submitFeedback(suggestionId: string, rating: FeedbackRating): Promise<void>;
  getDailyInsightText(): Promise<string>;
}

// noinspection JSUnusedGlobalSymbols -- imported by homeService and future suggestion screens
export const suggestionService: SuggestionService = {
  async getDailySuggestions() {
    try {
      return await apiClient.get<DailySuggestionResponseRaw>('/suggestions/daily');
    } catch {
      return dailySuggestionMock;
    }
  },

  async getMealSuggestions(mealType) {
    try {
      return await apiClient.get<MealSuggestionResponseRaw>(`/suggestions/meal?meal_type=${mealType}`);
    } catch {
      return { ...mealSuggestionMock, meal_type: mealType };
    }
  },

  async getInsights() {
    try {
      return await apiClient.get<InsightResponseRaw>('/suggestions/insights');
    } catch {
      return insightMock;
    }
  },

  async submitFeedback(suggestionId, rating) {
    try {
      await apiClient.post<void>(`/suggestions/${suggestionId}/feedback`, { rating });
    } catch {
      // mock fallback: ignore
    }
  },

  async getDailyInsightText() {
    const data = await this.getDailySuggestions();
    return data.suggestions[0]?.content ?? '记得多喝水、均衡饮食、保持运动。';
  },
};


