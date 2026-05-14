// AI 建议 Service - 调用后端 API

import { apiClient } from '@core/api/client';
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
    return await apiClient.get<DailySuggestionResponseRaw>('/suggestions/daily');
  },

  async getMealSuggestions(mealType) {
    return await apiClient.get<MealSuggestionResponseRaw>(`/suggestions/meal?meal_type=${mealType}`);
  },

  async getInsights() {
    return await apiClient.get<InsightResponseRaw>('/suggestions/insights');
  },

  async submitFeedback(suggestionId, rating) {
    await apiClient.post<void>(`/suggestions/${suggestionId}/feedback`, { rating });
  },

  async getDailyInsightText() {
    const data = await this.getDailySuggestions();
    return data.suggestions[0]?.content ?? '记得多喝水、均衡饮食、保持运动。';
  },
};


