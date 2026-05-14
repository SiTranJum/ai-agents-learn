// AI 建议模块类型

export type SuggestionType = 'diet_advice' | 'goal_advice' | 'trend_advice' | 'proactive_insight';
export type SuggestionPriority = 'high' | 'medium' | 'low';
export type FeedbackRating = 'helpful' | 'not_helpful' | 'dismissed';

export interface SuggestionItemRaw {
  id: string;
  type: SuggestionType;
  title: string;
  content: string;
  basis?: string | null;
  priority: SuggestionPriority;
  expires_at?: string | null;
  created_at: string;
}

export interface DailySuggestionResponseRaw {
  suggestions: SuggestionItemRaw[];
  generated_at: string;
  disclaimer: string;
}

export interface NutritionSummaryRaw {
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
}

export interface MealSuggestionResponseRaw {
  suggestion_id: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  consumed_today: NutritionSummaryRaw;
  remaining: NutritionSummaryRaw;
  suggestions: string[];
  reasoning: string;
  disclaimer: string;
}

export interface InsightItemRaw {
  id: string;
  dimension: string;
  finding: string;
  suggestion: string;
  data_support: Record<string, unknown>;
  generated_at: string;
}

export interface InsightResponseRaw {
  insights: InsightItemRaw[];
  period: string;
  disclaimer: string;
}

export interface DailySuggestion {
  id: string;
  title: string;
  content: string;
  priority: SuggestionPriority;
}

