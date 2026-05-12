// Data Service - Mock 实现
// 参考: docs/specs/frontend/modules/13-data-module.md §7

import type {
  AnalysisData,
  BodyRecord,
  DataTabType,
  ExerciseRecord,
  MeasurementRecord,
  SleepRecord,
  TimeRange,
  TodayRecords,
  WaterRecord,
  WeightRecord,
  TrendPoint,
} from '../types/data.types';
import {
  analysisDataMock,
  bowelTrend7,
  exerciseTrend7,
  getWeightTrendByRange,
  measurementTrend30,
  sleepTrend7,
  todayRecordsMock,
} from '../mocks/dataMocks';

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

// MET 值表（运动消耗估算）
const MET_VALUES: Record<string, number> = {
  跑步: 8.0,
  游泳: 7.0,
  瑜伽: 3.0,
  力量训练: 6.0,
  骑行: 7.5,
  篮球: 8.0,
  羽毛球: 5.5,
  快走: 4.0,
  其他: 5.0,
};

export const EXERCISE_TYPES = Object.keys(MET_VALUES);

/**
 * 计算睡眠时长（分钟），支持跨天
 * @param bedTime "HH:mm"
 * @param wakeTime "HH:mm"
 */
export function calculateSleepDuration(bedTime: string, wakeTime: string): number {
  const [bh, bm] = bedTime.split(':').map(Number);
  const [wh, wm] = wakeTime.split(':').map(Number);
  if ([bh, bm, wh, wm].some((n) => Number.isNaN(n))) return 0;
  let diff = wh * 60 + wm - (bh * 60 + bm);
  if (diff <= 0) diff += 24 * 60; // 跨天
  return diff;
}

/**
 * 估算运动消耗 kcal
 * 公式: kcal = MET × 体重(kg) × 时长(小时)
 */
export function calculateExerciseCalories(
  type: string,
  durationMinutes: number,
  weightKg: number
): number {
  const met = MET_VALUES[type] ?? 5.0;
  return Math.round(met * weightKg * (durationMinutes / 60));
}

// ===== 趋势数据 =====
export interface WeightTrendData {
  records: WeightRecord[];
  avgWeight: number;
  totalChange: number;
}

export interface MeasurementTrendData {
  records: MeasurementRecord[];
  avgWaist?: number;
  avgHip?: number;
}

export interface SleepTrendData {
  records: SleepRecord[];
  avgDuration: number;
  qualityDistribution: { excellent: number; good: number; fair: number; poor: number };
}

export interface ExerciseTrendData {
  records: ExerciseRecord[];
  totalDuration: number;
  totalCalories: number;
  typeDistribution: Record<string, number>;
}

// 从体重 / 围度等记录提取折线点
export function trendPointsFromWeight(records: WeightRecord[]): TrendPoint[] {
  return records.map((r) => ({ date: r.date, value: r.weight }));
}
export function trendPointsFromSleep(records: SleepRecord[]): TrendPoint[] {
  return records.map((r) => ({
    date: r.date,
    value: Math.round((r.duration / 60) * 10) / 10,
  }));
}
export function trendPointsFromExercise(records: ExerciseRecord[]): TrendPoint[] {
  return records.map((r) => ({ date: r.date, value: r.duration }));
}
export function trendPointsFromMeasurement(records: MeasurementRecord[]): TrendPoint[] {
  return records
    .filter((r) => typeof r.waist === 'number')
    .map((r) => ({ date: r.date, value: r.waist! }));
}
export function trendPointsFromBowel(records: BodyRecord[]): TrendPoint[] {
  // 排便趋势用"次数/天"作占位（mock 简化为每天 0/1）
  return records.map((r) => ({ date: (r as { date: string }).date, value: 1 }));
}

// ===== Service =====
export interface DataService {
  getTodayRecords(): Promise<TodayRecords>;
  getWeightTrend(range: TimeRange): Promise<WeightTrendData>;
  getMeasurementTrend(range: TimeRange): Promise<MeasurementTrendData>;
  getSleepTrend(range: TimeRange): Promise<SleepTrendData>;
  getExerciseTrend(range: TimeRange): Promise<ExerciseTrendData>;
  getWaterRecord(date: string): Promise<WaterRecord>;
  addWaterAmount(date: string, amount: number): Promise<WaterRecord>;
  saveBodyData(type: DataTabType, record: Partial<BodyRecord>): Promise<BodyRecord>;
  getAnalysisData(range: TimeRange): Promise<AnalysisData>;
}

export const dataService: DataService = {
  async getTodayRecords() {
    await delay(400);
    return todayRecordsMock;
  },

  async getWeightTrend(range) {
    await delay(400);
    const records = getWeightTrendByRange(range);
    const avgWeight =
      records.length > 0
        ? Math.round(
            (records.reduce((s, r) => s + r.weight, 0) / records.length) * 10
          ) / 10
        : 0;
    const totalChange =
      records.length > 1
        ? Math.round((records[records.length - 1].weight - records[0].weight) * 10) / 10
        : 0;
    return { records, avgWeight, totalChange };
  },

  async getMeasurementTrend(_range) {
    await delay(400);
    const records = measurementTrend30;
    const avgWaist =
      records.reduce((s, r) => s + (r.waist ?? 0), 0) / Math.max(1, records.length);
    const avgHip =
      records.reduce((s, r) => s + (r.hip ?? 0), 0) / Math.max(1, records.length);
    return {
      records,
      avgWaist: Math.round(avgWaist * 10) / 10,
      avgHip: Math.round(avgHip * 10) / 10,
    };
  },

  async getSleepTrend(_range) {
    await delay(400);
    const records = sleepTrend7;
    const avgDuration =
      records.reduce((s, r) => s + r.duration, 0) / Math.max(1, records.length);
    const dist = { excellent: 0, good: 0, fair: 0, poor: 0 };
    records.forEach((r) => {
      dist[r.quality] += 1;
    });
    return { records, avgDuration: Math.round(avgDuration), qualityDistribution: dist };
  },

  async getExerciseTrend(_range) {
    await delay(400);
    const records = exerciseTrend7;
    const totalDuration = records.reduce((s, r) => s + r.duration, 0);
    const totalCalories = records.reduce((s, r) => s + r.calories, 0);
    const typeDistribution: Record<string, number> = {};
    records.forEach((r) => {
      typeDistribution[r.type] = (typeDistribution[r.type] ?? 0) + r.duration;
    });
    return { records, totalDuration, totalCalories, typeDistribution };
  },

  async getWaterRecord(date) {
    await delay(200);
    return { ...todayRecordsMock.water!, date };
  },

  async addWaterAmount(date, amount) {
    await delay(300);
    const current = todayRecordsMock.water ?? {
      id: `wa-${date}`,
      date,
      amount: 0,
      target: 2000,
    };
    const next = { ...current, amount: current.amount + amount };
    todayRecordsMock.water = next; // mock 持久化
    return next;
  },

  async saveBodyData(type, record) {
    await delay(500);
    const id = (record as { id?: string }).id ?? `${type}-${Date.now()}`;
    const saved = { ...record, id } as BodyRecord;
    // 同步更新 todayRecordsMock，便于演示
    if (type === 'weight') todayRecordsMock.weight = saved as WeightRecord;
    if (type === 'measurement') todayRecordsMock.measurement = saved as MeasurementRecord;
    if (type === 'sleep') todayRecordsMock.sleep = saved as SleepRecord;
    if (type === 'exercise') todayRecordsMock.exercise = saved as ExerciseRecord;
    if (type === 'bowel') todayRecordsMock.bowel = saved as import('../types/data.types').BowelRecord;
    return saved;
  },

  async getAnalysisData(range) {
    await delay(600);
    return { ...analysisDataMock, timeRange: range };
  },
};

// 历史记录（仅获取最近 N 天，不含今日）
export async function getRecentRecords(
  type: DataTabType,
  limit: number = 7
): Promise<BodyRecord[]> {
  await delay(200);
  switch (type) {
    case 'weight':
      return getWeightTrendByRange('30d').slice(-limit - 1, -1).reverse();
    case 'measurement':
      return measurementTrend30.slice(0, limit);
    case 'sleep':
      return sleepTrend7.slice(0, -1).reverse().slice(0, limit);
    case 'exercise':
      return exerciseTrend7.slice(0, -1).reverse().slice(0, limit);
    case 'water': {
      // 饮水按天构造历史
      return Array.from({ length: limit }).map((_, idx) => {
        const d = new Date(`${todayRecordsMock.water?.date ?? new Date().toISOString().slice(0, 10)}T00:00:00`);
        d.setDate(d.getDate() - (idx + 1));
        const dateStr = d.toISOString().slice(0, 10);
        return {
          id: `wa-${dateStr}`,
          date: dateStr,
          amount: 1500 + Math.round(Math.sin(idx) * 300),
          target: 2000,
        } as WaterRecord;
      });
    }
    case 'bowel':
      return bowelTrend7.slice(0, -1).reverse().slice(0, limit);
  }
}
