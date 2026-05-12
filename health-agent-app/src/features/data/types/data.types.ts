// 数据模块类型定义
// 参考: docs/specs/frontend/modules/13-data-module.md §4

export type DataTabType =
  | 'weight'
  | 'measurement'
  | 'sleep'
  | 'exercise'
  | 'water'
  | 'bowel';

export type TimeRange = '7d' | '30d' | '90d' | '365d';

export type RecordStatus = 'empty' | 'pending' | 'recorded';

// ===== 6 类记录 =====
export interface WeightRecord {
  id: string;
  date: string;
  weight: number;
  bmi: number | null;
  /** 与昨日体重差值（kg） */
  change: number;
  note?: string;
  anomalyWarning?: string | null;
  createdAt?: string;
  updatedAt?: string;
}

export interface MeasurementRecord {
  id: string;
  date: string;
  waist?: number;
  hip?: number;
  thigh?: number;
  arm?: number;
  note?: string;
  anomalyWarning?: string | null;
  createdAt?: string;
  updatedAt?: string;
}

export type SleepQuality = 'excellent' | 'good' | 'fair' | 'poor';

export interface SleepRecord {
  id: string;
  date: string;
  /** 入睡时间 HH:mm */
  bedTime: string;
  /** 起床时间 HH:mm */
  wakeTime: string;
  /** 时长（分钟） */
  duration: number;
  quality: SleepQuality;
  note?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface ExerciseRecord {
  id: string;
  date: string;
  /** 运动类型，如 "跑步" */
  type: string;
  /** 时长（分钟） */
  duration: number;
  /** 估算消耗 kcal */
  calories: number;
  note?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface WaterRecord {
  id: string;
  date: string;
  /** 已喝（ml） */
  amount: number;
  /** 目标（ml） */
  target: number;
  createdAt?: string;
  updatedAt?: string;
}

export type BowelStatus = 'normal' | 'constipation' | 'diarrhea';

export interface BowelRecord {
  id: string;
  date: string;
  /** 时间 HH:mm */
  time: string;
  status: BowelStatus;
  note?: string;
  createdAt?: string;
  updatedAt?: string;
}

export type BodyRecord =
  | WeightRecord
  | MeasurementRecord
  | SleepRecord
  | ExerciseRecord
  | WaterRecord
  | BowelRecord;

// ===== 趋势数据 =====
export interface TrendPoint {
  date: string;
  value: number;
}

// 今日各类型记录的统一容器
export interface TodayRecords {
  weight: WeightRecord | null;
  measurement: MeasurementRecord | null;
  sleep: SleepRecord | null;
  exercise: ExerciseRecord | null;
  water: WaterRecord | null;
  bowel: BowelRecord | null;
}

// ===== 分析数据 =====
export interface AnalysisInsight {
  type: 'calorie' | 'nutrition' | 'weight' | 'habit' | 'achievement';
  title: string;
  description: string;
}

export interface AnalysisData {
  timeRange: TimeRange;
  caloriesTrend: { date: string; intake: number; target: number }[];
  nutritionDistribution: {
    carbs: number;
    protein: number;
    fat: number;
    carbsPercent: number;
    proteinPercent: number;
    fatPercent: number;
  };
  weightTrend: { date: string; weight: number }[];
  currentWeight: number;
  targetWeight: number;
  planCompletion: {
    totalDays: number;
    completedDays: number;
    completionRate: number;
  };
  insights: AnalysisInsight[];
}

// ===== 编辑表单数据 =====
export interface WeightFormData {
  date: string;
  weight: number;
  note?: string;
}

export interface MeasurementFormData {
  date: string;
  waist?: number;
  hip?: number;
  thigh?: number;
  arm?: number;
  note?: string;
}

export interface SleepFormData {
  date: string;
  bedTime: string;
  wakeTime: string;
  quality: SleepQuality;
  note?: string;
}

export interface ExerciseFormData {
  date: string;
  type: string;
  duration: number;
  note?: string;
}

export type BodyFormData =
  | WeightFormData
  | MeasurementFormData
  | SleepFormData
  | ExerciseFormData;
