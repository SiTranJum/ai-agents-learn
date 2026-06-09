export type PlanType = 'weight_loss' | 'nutrition_adjustment' | 'habit_formation';
export type PlanStatus = 'active' | 'completed' | 'terminated';

export interface PlanListItem {
  id: string;
  name: string;
  type: PlanType;
  status: PlanStatus;
  progress: number;
  startDate: string;
  endDate: string;
  currentPhase?: string;
}

export interface PlanTask {
  id: string;
  text: string;
  completed: boolean;
  frequency?: string;
  timePeriod?: string | null;
}

export interface PlanPhase {
  id: string;
  title: string;
  goal: string;
  startDate: string;
  endDate: string;
  tasks: PlanTask[];
}

export interface PlanTrendPoint {
  date: string;
  value: number;
}

export interface PlanDetail {
  id: string;
  name: string;
  type: PlanType;
  status: PlanStatus;
  targetWeight?: number;
  dailyCalorieTarget?: number;
  duration?: string;
  currentPhase?: string;
  startDate: string;
  endDate: string;
  progress: number;
  completedTasks: number;
  totalTasks: number;
  streakDays: number;
  tasks: PlanTask[];
  phases: PlanPhase[];
  trendData: PlanTrendPoint[];
  aiSuggestion: string;
  warning?: {
    daysMissed: number;
    description: string;
  };
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

export interface PlanPhaseRaw {
  id: string;
  title: string;
  goal: string;
  start_date: string;
  end_date: string;
  tasks: PlanTaskRaw[];
}

export interface PlanResponseRaw {
  id: string;
  name: string;
  goal_description: string;
  plan_type: PlanType;
  status: PlanStatus;
  start_date: string;
  target_date: string;
  targets: PlanTargetRaw;
  tasks: PlanTaskRaw[];
  phases: PlanPhaseRaw[];
  created_at: string;
  updated_at: string;
}

export interface DailyExecutionRaw {
  id?: string | null;
  date: string;
  calories_consumed: number;
  calories_target: number;
  protein: number;
  fat: number;
  carbs: number;
  status: 'on_track' | 'deviation' | 'missed';
}

export interface PlanProgressRaw {
  plan_id: string;
  total_days: number;
  elapsed_days: number;
  compliance_rate: number;
  streak_days: number;
  completed_tasks: number;
  total_tasks: number;
  completed_task_ids: string[];
  daily_records: DailyExecutionRaw[];
}
