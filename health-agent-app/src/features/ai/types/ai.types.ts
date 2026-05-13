// AI 对话模块类型
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §5

export type ChatRole = 'ai' | 'assistant' | 'user' | 'system';
export type BackendChatRole = 'assistant' | 'user' | 'system';

export interface ChatAction {
  /** 唯一标识，用于点击回调匹配 */
  key: string;
  label: string;
  /** 操作类型 */
  action: 'navigate' | 'confirm' | 'cancel' | 'show_nutrition';
  /** 跳转目标 / 附加参数 */
  params?: Record<string, unknown>;
  variant?: 'primary' | 'secondary';
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  actions?: ChatAction[];
  cards?: ChatCard[];
}

export type DataSource = 'local_db' | 'database' | 'api' | 'ai_estimate' | 'llm_estimate';

export interface ParsedFoodPayload {
  name: string;
  amount: number;
  unit: string;
  amount_grams: number;
  cooking_method?: string | null;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  fiber?: number | null;
  sodium?: number | null;
  data_source: 'database' | 'api' | 'llm_estimate';
  food_id?: string | null;
}

export interface DietParseCardPayload {
  foods: ParsedFoodPayload[];
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack' | null;
  confidence: number;
  nutrition_summary?: {
    total_calories: number;
    total_protein: number;
    total_fat: number;
    total_carbs: number;
    total_fiber?: number | null;
    total_sodium?: number | null;
  };
  suggested_date?: string;
}

export interface ChatCardActionRaw {
  kind: 'confirm_create_diet_record' | 'edit_diet_items' | string;
  label?: string | null;
}

export interface DietParseCard {
  type: 'diet_parse';
  payload: DietParseCardPayload;
  actions: ChatCardActionRaw[];
}

export type ChatCard = DietParseCard | {
  type: string;
  payload: Record<string, unknown>;
  actions: ChatCardActionRaw[];
};

export interface ChatRequest {
  session_id?: string | null;
  message: string;
  context?: {
    image_url?: string | null;
    referenced_date?: string | null;
    [key: string]: unknown;
  };
}

export interface ChatResponseMessageRaw {
  id?: string | null;
  role: BackendChatRole;
  content: string;
  cards?: ChatCard[];
  created_at?: string | null;
}

export interface ChatResponseRaw {
  session_id: string;
  messages: ChatResponseMessageRaw[];
  intent?: AIIntent | string | null;
}

export interface NutritionData {
  foodName: string;
  amount: number;
  unit: string;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  dataSource: DataSource;
}

/** AI 意图（用于 mock 路由） */
export type AIIntent =
  | 'diet'
  | 'body'
  | 'plan'
  | 'memory'
  | 'suggestion'
  | 'general';
