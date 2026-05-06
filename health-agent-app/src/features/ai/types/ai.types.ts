// AI 对话模块类型
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §5

export type ChatRole = 'ai' | 'user' | 'system';

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
}

export type DataSource = 'local_db' | 'api' | 'ai_estimate';

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
  | 'greeting'
  | 'nutrition_query'
  | 'health_advice'
  | 'plan_suggestion'
  | 'general';
