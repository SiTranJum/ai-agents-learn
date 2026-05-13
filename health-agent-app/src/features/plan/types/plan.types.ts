// 计划模块类型定义
// 参考: docs/specs/frontend/modules/14-plan-module.md §4

export type PlanType = 'lose_weight' | 'nutrition' | 'habit';
export type PlanStatus = 'active' | 'paused' | 'completed' | 'terminated';
export type BackendPlanType = 'weight_loss' | 'nutrition_adjustment' | 'habit_formation';
export type BackendPlanStatus = 'active' | 'completed' | 'terminated';

// 计划列表项
export interface PlanListItem {
  id: string;
  name: string;
  type: PlanType;
  status: PlanStatus;
  /** 进度 0-100 */
  progress: number;
  startDate: string;
  endDate: string;
}

// 任务项
export interface PlanTask {
  id: string;
  text: string;
  completed: boolean;
}

// 趋势点
export interface PlanTrendPoint {
  date: string;
  value: number;
}

// 计划详情
export interface PlanDetail {
  id: string;
  name: string;
  type: PlanType;
  status: PlanStatus;
  targetWeight?: number;
  /** 每日热量目标 kcal */
  dailyCalorieTarget?: number;
  /** 时间周期描述（如 "3个月"） */
  duration?: string;
  /** 当前阶段（如 "第2阶段"） */
  currentPhase?: string;
  startDate: string;
  endDate: string;
  /** 进度 0-100 */
  progress: number;
  tasks: PlanTask[];
  trendData: PlanTrendPoint[];
  aiSuggestion: string;
  /** 是否连续未达标（V1 简化为标志位） */
  warning?: {
    daysMissed: number;
    description: string;
  };
}

// ===== 对话相关 =====
export type ChatRole = 'ai' | 'user';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  /** AI 提问时附带的快捷选项 */
  quickOptions?: string[];
  /** AI 最后一条消息可附带计划摘要 */
  planSummary?: PlanSummary;
  /** 末尾"操作按钮"组（如 [确认创建, 修改目标] 或 [查看计划]） */
  actionButtons?: ChatActionButton[];
}

export interface ChatActionButton {
  /** 唯一标识，用于点击回调匹配 */
  key: string;
  label: string;
  variant: 'primary' | 'secondary';
}

export interface PlanSummary {
  name: string;
  type: PlanType;
  targetWeight?: number;
  dailyCalorieTarget?: number;
  /** "3个月" / "1个月" / 自定义文案 */
  duration: string;
  /** 阶段数（如 3 个阶段） */
  phases?: number;
  keyRules: string[];
}

export interface PlanTargetRaw {
  daily_calories?: number | null;
  protein_target?: number | null;
  fat_target?: number | null;
  carbs_target?: number | null;
  weight_target?: number | null;
}

export interface PlanTaskRaw {
  id: string;
  description: string;
  frequency: string;
  time_period?: string | null;
}

// noinspection JSUnusedGlobalSymbols -- exported for service-layer backend mapping
export interface PlanResponseRaw {
  id: string;
  name: string;
  goal_description: string;
  plan_type: BackendPlanType;
  status: BackendPlanStatus;
  start_date: string;
  target_date: string;
  targets: PlanTargetRaw;
  tasks: PlanTaskRaw[];
  created_at: string;
  updated_at: string;
}

// 对话流程的步骤标识
export type ChatStep =
  | 'ask_type'
  | 'ask_target_weight'
  | 'ask_duration'
  | 'show_summary'
  | 'created';
