export type ChatRole = 'ai' | 'assistant' | 'user' | 'system';
export type BackendChatRole = 'assistant' | 'user' | 'system';

export interface ChatAction {
  key: string;
  label: string;
  action: 'navigate' | 'confirm' | 'cancel' | 'show_nutrition';
  params?: Record<string, unknown>;
  variant?: 'primary' | 'secondary';
}

export interface ChoiceOption {
  value: string;
  label: string;
  description?: string;
}

export interface ChoicePrompt {
  prompt_id: string;
  question?: string;
  options: ChoiceOption[];
  allow_free_text?: boolean;
}

export interface ToolCallState {
  tool: string;
  label: string;
  summary?: string;
  state: 'pending' | 'done';
}

export interface ChatCardActionRaw {
  kind: string;
  label?: string | null;
}

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
  operation?: 'append' | 'replace';
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

export interface DietParseCard {
  type: 'diet_parse';
  payload: DietParseCardPayload;
  actions: ChatCardActionRaw[];
}

export type BodyRecordKind = 'water' | 'sleep' | 'exercise' | 'bowel';

export interface BodyParseCardPayload {
  record_type: BodyRecordKind;
  operation?: 'append' | 'replace';
  confidence?: number;
  water_amount?: number | null;
  sleep_bed_time?: string | null;
  sleep_wake_time?: string | null;
  sleep_quality?: 'excellent' | 'good' | 'fair' | 'poor' | null;
  exercise_type?: string | null;
  exercise_duration?: number | null;
  bowel_time?: string | null;
  bowel_status?: 'normal' | 'constipation' | 'diarrhea' | null;
  suggested_date?: string;
}

export interface BodyParseCard {
  type: 'body_parse';
  payload: BodyParseCardPayload;
  actions: ChatCardActionRaw[];
}

export interface PlanTaskCardPayload {
  id: string;
  description: string;
  frequency: string;
  time_period?: string | null;
}

export interface PlanPhaseCardPayload {
  id: string;
  title: string;
  goal: string;
  start_date: string;
  end_date: string;
  tasks: PlanTaskCardPayload[];
}

export interface PlanDraftCardPayload {
  draft: {
    name: string;
    goal_description: string;
    plan_type: string;
    start_date: string;
    target_date: string;
    targets: {
      daily_calories?: number | null;
      protein_target?: number | null;
      fat_target?: number | null;
      carbs_target?: number | null;
      weight_target?: number | null;
    };
    tasks: PlanTaskCardPayload[];
    phases: PlanPhaseCardPayload[];
  };
  violations?: string[];
}

export interface PlanDraftCard {
  type: 'plan_draft';
  payload: PlanDraftCardPayload;
  actions: ChatCardActionRaw[];
}

export interface PlanSavedCard {
  type: 'plan_saved';
  payload: {
    plan_id: string;
    plan: Record<string, unknown>;
  };
  actions: ChatCardActionRaw[];
}

export interface PlanProgressCard {
  type: 'plan_progress';
  payload: {
    plan_id: string;
    plan_name: string;
    status: string;
    completed_tasks: number;
    total_tasks: number;
    compliance_rate: number;
    streak_days: number;
    current_phase?: string | null;
  };
  actions: ChatCardActionRaw[];
}

export type ChatCard =
  | DietParseCard
  | BodyParseCard
  | PlanDraftCard
  | PlanSavedCard
  | PlanProgressCard
  | {
      type: string;
      payload: Record<string, unknown>;
      actions: ChatCardActionRaw[];
    };

export type MessageSegment =
  | { kind: 'text'; content: string }
  | { kind: 'card'; card: ChatCard }
  | { kind: 'choice'; prompt: ChoicePrompt; selectedValue?: string; freeText?: string };

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  actions?: ChatAction[];
  cards?: ChatCard[];
  segments?: MessageSegment[];
  status?: string | null;
  tools?: ToolCallState[];
  isStreaming?: boolean;
  error?: { code: string; message: string };
}

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

export type DataSource = 'local_db' | 'database' | 'api' | 'ai_estimate' | 'llm_estimate';

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

export type AIIntent = 'diet' | 'body' | 'plan' | 'memory' | 'suggestion' | 'general';
