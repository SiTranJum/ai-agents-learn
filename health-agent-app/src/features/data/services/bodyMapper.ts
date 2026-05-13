// 身体数据模块 - 后端 snake_case ↔ 前端 camelCase 映射层
// 契约: docs/specs/shared/api-contract.md §6

import type {
  BowelRecord,
  ExerciseRecord,
  MeasurementRecord,
  SleepRecord,
  TrendPoint,
  WaterRecord,
  WeightRecord,
} from '../types/data.types';

// ========== 后端响应裸类型（snake_case）==========

export interface BackendWeightRecord {
  id: string;
  date: string;
  weight: number;
  bmi: number | null;
  change: number | null;
  note: string | null;
  anomaly_warning: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendMeasurementRecord {
  id: string;
  date: string;
  waist: number | null;
  hip: number | null;
  thigh: number | null;
  arm: number | null;
  note: string | null;
  anomaly_warning: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendSleepRecord {
  id: string;
  date: string;
  bed_time: string;
  wake_time: string;
  duration: number;
  quality: 'excellent' | 'good' | 'fair' | 'poor';
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendExerciseRecord {
  id: string;
  date: string;
  type: string;
  duration: number;
  calories: number;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendWaterRecord {
  id: string;
  date: string;
  amount: number;
  target: number;
  created_at: string;
  updated_at: string;
}

export interface BackendBowelRecord {
  id: string;
  date: string;
  time: string;
  status: 'normal' | 'constipation' | 'diarrhea';
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendTodayRecords {
  weight: BackendWeightRecord | null;
  measurement: BackendMeasurementRecord | null;
  sleep: BackendSleepRecord | null;
  exercise: BackendExerciseRecord | null;
  water: BackendWaterRecord | null;
  bowel: BackendBowelRecord | null;
}

export interface BackendTrendResponse {
  type: string;
  period: string;
  metric: string;
  data_points: { date: string; value: number }[];
  statistics: {
    min: number | null;
    max: number | null;
    average: number | null;
    latest: number | null;
    change: number | null;
  };
  target: number | null;
}

// ========== 映射函数：后端 -> 前端 ==========

export function mapWeightRecord(r: BackendWeightRecord): WeightRecord {
  return {
    id: r.id,
    date: r.date,
    weight: r.weight,
    bmi: r.bmi,
    change: r.change ?? 0,
    note: r.note ?? undefined,
    anomalyWarning: r.anomaly_warning,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

export function mapMeasurementRecord(
  r: BackendMeasurementRecord
): MeasurementRecord {
  return {
    id: r.id,
    date: r.date,
    waist: r.waist ?? undefined,
    hip: r.hip ?? undefined,
    thigh: r.thigh ?? undefined,
    arm: r.arm ?? undefined,
    note: r.note ?? undefined,
    anomalyWarning: r.anomaly_warning,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

export function mapSleepRecord(r: BackendSleepRecord): SleepRecord {
  return {
    id: r.id,
    date: r.date,
    bedTime: r.bed_time,
    wakeTime: r.wake_time,
    duration: r.duration,
    quality: r.quality,
    note: r.note ?? undefined,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

export function mapExerciseRecord(r: BackendExerciseRecord): ExerciseRecord {
  return {
    id: r.id,
    date: r.date,
    type: r.type,
    duration: r.duration,
    calories: r.calories,
    note: r.note ?? undefined,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

export function mapWaterRecord(r: BackendWaterRecord): WaterRecord {
  return {
    id: r.id,
    date: r.date,
    amount: r.amount,
    target: r.target,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

export function mapBowelRecord(r: BackendBowelRecord): BowelRecord {
  return {
    id: r.id,
    date: r.date,
    time: r.time,
    status: r.status,
    note: r.note ?? undefined,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

// ========== 映射函数：前端 -> 后端请求体 ==========

export function toWeightPayload(r: Partial<WeightRecord>) {
  return {
    date: r.date,
    weight: r.weight,
    note: r.note ?? null,
  };
}

export function toMeasurementPayload(r: Partial<MeasurementRecord>) {
  return {
    date: r.date,
    waist: r.waist ?? null,
    hip: r.hip ?? null,
    thigh: r.thigh ?? null,
    arm: r.arm ?? null,
    note: r.note ?? null,
  };
}

export function toSleepPayload(r: Partial<SleepRecord>) {
  return {
    date: r.date,
    bed_time: r.bedTime,
    wake_time: r.wakeTime,
    quality: r.quality,
    note: r.note ?? null,
  };
}

export function toExercisePayload(r: Partial<ExerciseRecord>) {
  return {
    date: r.date,
    type: r.type,
    duration: r.duration,
    calories: r.calories,
    note: r.note ?? null,
  };
}

export function toWaterPayload(r: Partial<WaterRecord>) {
  return {
    date: r.date,
    amount: r.amount,
    target: r.target,
  };
}

export function toBowelPayload(r: Partial<BowelRecord>) {
  return {
    date: r.date,
    time: r.time,
    status: r.status,
    note: r.note ?? null,
  };
}

// 从后端 trend 响应取 data_points，转 camelCase
export function mapTrendPoints(r: BackendTrendResponse): TrendPoint[] {
  return r.data_points.map((p) => ({ date: p.date, value: p.value }));
}
