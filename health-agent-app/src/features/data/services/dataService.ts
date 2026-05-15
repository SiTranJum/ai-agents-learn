// Data Service - 对接后端 /body/* 与 /diet/weekly-summary
// 契约: docs/specs/shared/api-contract.md §6

import { apiClient } from '@core/api/client';
import { todayStr } from '@shared/utils/date';
import type {
  AnalysisData,
  BodyRecord,
  BowelRecord,
  DataTabType,
  ExerciseRecord,
  MeasurementRecord,
  SleepRecord,
  TimeRange,
  TodayRecords,
  TrendPoint,
  WaterRecord,
  WeightRecord,
} from '../types/data.types';
import {
  BackendBowelRecord,
  BackendExerciseRecord,
  BackendMeasurementRecord,
  BackendSleepRecord,
  BackendTodayRecords,
  BackendTrendResponse,
  BackendWaterRecord,
  BackendWeightRecord,
  mapBowelRecord,
  mapExerciseRecord,
  mapMeasurementRecord,
  mapSleepRecord,
  mapTrendPoints,
  mapWaterRecord,
  mapWeightRecord,
  toBowelPayload,
  toExercisePayload,
  toMeasurementPayload,
  toSleepPayload,
  toWaterPayload,
  toWeightPayload,
} from './bodyMapper';

// ===== 分析页后端响应类型 =====
interface BackendWeeklySummary {
  start_date: string;
  end_date: string;
  daily_summaries: Array<{
    date: string;
    total_nutrition: { total_calories: number; total_protein: number; total_fat: number; total_carbs: number };
    target_nutrition: { total_calories: number } | null;
  }>;
  total_nutrition: { total_calories: number; total_protein: number; total_fat: number; total_carbs: number };
}
interface BackendPlanListRaw {
  data?: Array<{ id: string }>;
  [key: string]: unknown;
}
interface BackendInsightsRaw {
  insights: Array<{ dimension: string; finding: string; suggestion: string }>;
}

/** 后端 insight dimension → 前端 AnalysisInsight.type */
function mapInsightDimension(dim: string): 'calorie' | 'nutrition' | 'weight' | 'habit' | 'achievement' {
  const map: Record<string, 'calorie' | 'nutrition' | 'weight' | 'habit' | 'achievement'> = {
    calorie: 'calorie',
    nutrition: 'nutrition',
    weight: 'weight',
    habit: 'habit',
    achievement: 'achievement',
    diet: 'calorie',
    exercise: 'habit',
    sleep: 'habit',
  };
  return map[dim] ?? 'nutrition';
}

// ===== MET 值表（运动消耗即时估算，UI 本地使用，非后端逻辑）=====
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
 * 编辑页预填/预览使用；保存时后端也会自算一次。
 */
export function calculateSleepDuration(bedTime: string, wakeTime: string): number {
  const [bh, bm] = bedTime.split(':').map(Number);
  const [wh, wm] = wakeTime.split(':').map(Number);
  if ([bh, bm, wh, wm].some((n) => Number.isNaN(n))) return 0;
  let diff = wh * 60 + wm - (bh * 60 + bm);
  if (diff <= 0) diff += 24 * 60;
  return diff;
}

/** 估算运动消耗 kcal（编辑页预览使用） */
export function calculateExerciseCalories(
  type: string,
  durationMinutes: number,
  weightKg: number
): number {
  const met = MET_VALUES[type] ?? 5.0;
  return Math.round(met * weightKg * (durationMinutes / 60));
}

// ===== 趋势数据聚合类型（前端视图需要的形态）=====
export interface WeightTrendData {
  points: TrendPoint[];
  statistics: {
    min: number | null;
    max: number | null;
    average: number | null;
    latest: number | null;
    change: number | null;
  };
  target: number | null;
}
export interface MeasurementTrendData {
  points: TrendPoint[];
  metric: 'waist' | 'hip' | 'thigh' | 'arm';
  statistics: WeightTrendData['statistics'];
}
export interface SleepTrendData {
  points: TrendPoint[];
  statistics: WeightTrendData['statistics'];
}
export interface ExerciseTrendData {
  points: TrendPoint[];
  statistics: WeightTrendData['statistics'];
}

// ===== 通用工具 =====

function buildQuery(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== ''
  );
  if (entries.length === 0) return '';
  const qs = entries.map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join('&');
  return `?${qs}`;
}

/** 从 today 聚合结果里派生 TrendPoint（当前值作为最后一个点）— 预留工具 */
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
  return records.map((r) => ({ date: (r as { date: string }).date, value: 1 }));
}

// ===== Service =====
export interface DataService {
  getTodayRecords(date?: string): Promise<TodayRecords>;
  getWeightTrend(range: TimeRange): Promise<WeightTrendData>;
  getMeasurementTrend(
    range: TimeRange,
    metric?: MeasurementTrendData['metric']
  ): Promise<MeasurementTrendData>;
  getSleepTrend(range: TimeRange): Promise<SleepTrendData>;
  getExerciseTrend(range: TimeRange): Promise<ExerciseTrendData>;
  getWaterRecord(date: string): Promise<WaterRecord | null>;
  addWaterAmount(date: string, amount: number, target?: number): Promise<WaterRecord>;
  saveBodyData(type: DataTabType, record: Partial<BodyRecord>): Promise<BodyRecord>;
  getAnalysisData(range: TimeRange): Promise<AnalysisData>;
}

export const dataService: DataService = {
  async getTodayRecords(date) {
    const d = date ?? todayStr();
    const raw = await apiClient.get<BackendTodayRecords>(`/body/today?date=${d}`);
    return {
      weight: raw.weight ? mapWeightRecord(raw.weight) : null,
      measurement: raw.measurement ? mapMeasurementRecord(raw.measurement) : null,
      sleep: raw.sleep ? mapSleepRecord(raw.sleep) : null,
      exercise: raw.exercise ? mapExerciseRecord(raw.exercise) : null,
      water: raw.water ? mapWaterRecord(raw.water) : null,
      bowel: raw.bowel ? mapBowelRecord(raw.bowel) : null,
    };
  },

  async getWeightTrend(range) {
    const raw = await apiClient.get<BackendTrendResponse>(
      `/body/trends?type=weight&period=${range}`
    );
    return {
      points: mapTrendPoints(raw),
      statistics: raw.statistics,
      target: raw.target,
    };
  },

  async getMeasurementTrend(range, metric = 'waist') {
    const raw = await apiClient.get<BackendTrendResponse>(
      `/body/trends?type=measurement&period=${range}&metric=${metric}`
    );
    return {
      points: mapTrendPoints(raw),
      metric,
      statistics: raw.statistics,
    };
  },

  async getSleepTrend(range) {
    const raw = await apiClient.get<BackendTrendResponse>(
      `/body/trends?type=sleep&period=${range}`
    );
    return { points: mapTrendPoints(raw), statistics: raw.statistics };
  },

  async getExerciseTrend(range) {
    const raw = await apiClient.get<BackendTrendResponse>(
      `/body/trends?type=exercise&period=${range}`
    );
    return { points: mapTrendPoints(raw), statistics: raw.statistics };
  },

  async getWaterRecord(date) {
    // 复用 /body/today 端点（避免单独的 by-date 查询）
    const today = await this.getTodayRecords(date);
    return today.water;
  },

  async addWaterAmount(date, amount, target) {
    // POST /body/water 语义：amount 为本次"新增"量，同日已有记录时累加
    const payload: Record<string, unknown> = { date, amount };
    if (target !== undefined) payload.target = target;
    const raw = await apiClient.post<BackendWaterRecord>('/body/water', payload);
    return mapWaterRecord(raw);
  },

  async saveBodyData(type, record) {
    const id = (record as { id?: string }).id;
    switch (type) {
      case 'weight': {
        const payload = toWeightPayload(record as Partial<WeightRecord>);
        const raw = id
          ? await apiClient.put<BackendWeightRecord>(`/body/weight/${id}`, payload)
          : await apiClient.post<BackendWeightRecord>('/body/weight', payload);
        return mapWeightRecord(raw);
      }
      case 'measurement': {
        const payload = toMeasurementPayload(record as Partial<MeasurementRecord>);
        const raw = id
          ? await apiClient.put<BackendMeasurementRecord>(
              `/body/measurement/${id}`,
              payload
            )
          : await apiClient.post<BackendMeasurementRecord>(
              '/body/measurement',
              payload
            );
        return mapMeasurementRecord(raw);
      }
      case 'sleep': {
        const payload = toSleepPayload(record as Partial<SleepRecord>);
        const raw = id
          ? await apiClient.put<BackendSleepRecord>(`/body/sleep/${id}`, payload)
          : await apiClient.post<BackendSleepRecord>('/body/sleep', payload);
        return mapSleepRecord(raw);
      }
      case 'exercise': {
        const payload = toExercisePayload(record as Partial<ExerciseRecord>);
        const raw = id
          ? await apiClient.put<BackendExerciseRecord>(`/body/exercise/${id}`, payload)
          : await apiClient.post<BackendExerciseRecord>('/body/exercise', payload);
        return mapExerciseRecord(raw);
      }
      case 'water': {
        // 编辑页直接改"当日累计值"对应 PUT，否则走 POST 累加
        const payload = toWaterPayload(record as Partial<WaterRecord>);
        if (id) {
          const raw = await apiClient.put<BackendWaterRecord>(`/body/water/${id}`, payload);
          return mapWaterRecord(raw);
        }
        // 没有 id → 检查当日是否已有饮水记录
        const date = (record as Partial<WaterRecord>).date ?? todayStr();
        const todayRecords = await this.getTodayRecords(date);
        if (todayRecords.water?.id) {
          // 已有记录 → 用已有记录的 id 做 PUT
          const raw = await apiClient.put<BackendWaterRecord>(`/body/water/${todayRecords.water.id}`, payload);
          return mapWaterRecord(raw);
        }
        // 没有记录 → POST 新增
        const raw = await apiClient.post<BackendWaterRecord>('/body/water', payload);
        return mapWaterRecord(raw);
      }
      case 'bowel': {
        const payload = toBowelPayload(record as Partial<BowelRecord>);
        const raw = id
          ? await apiClient.put<BackendBowelRecord>(`/body/bowel/${id}`, payload)
          : await apiClient.post<BackendBowelRecord>('/body/bowel', payload);
        return mapBowelRecord(raw);
      }
    }
  },

  async getAnalysisData(range) {
    // 根据 range 计算 start_date
    const now = new Date();
    const days = range === '7d' ? 7 : range === '30d' ? 30 : range === '90d' ? 90 : 365;
    const start = new Date(now.getTime() - days * 86400000);
    const startDate = `${start.getFullYear()}-${String(start.getMonth() + 1).padStart(2, '0')}-${String(start.getDate()).padStart(2, '0')}`;

    // 并行拉取 4 个维度，每个独立容错
    const [dietResult, weightResult, plansResult, insightsResult] = await Promise.allSettled([
      apiClient.get<BackendWeeklySummary>(`/diet/weekly-summary?start_date=${startDate}`),
      apiClient.get<BackendTrendResponse>(`/body/trends?type=weight&period=${range}`),
      apiClient.get<BackendPlanListRaw>('/plans?status=active&page_size=1'),
      apiClient.get<BackendInsightsRaw>('/suggestions/insights'),
    ]);

    // 热量趋势
    let caloriesTrend: AnalysisData['caloriesTrend'] = [];
    if (dietResult.status === 'fulfilled') {
      const ds = dietResult.value;
      caloriesTrend = ds.daily_summaries.map((d: any) => ({
        date: d.date,
        intake: Math.round(d.total_nutrition?.total_calories ?? 0),
        target: Math.round(d.target_nutrition?.total_calories ?? 1800),
      }));
    }

    // 营养分布（取最近一天的汇总）
    let nutritionDistribution: AnalysisData['nutritionDistribution'] = {
      carbs: 0, protein: 0, fat: 0,
      carbsPercent: 33, proteinPercent: 33, fatPercent: 34,
    };
    if (dietResult.status === 'fulfilled') {
      const total = dietResult.value.total_nutrition;
      const c = total.total_carbs ?? 0;
      const p = total.total_protein ?? 0;
      const f = total.total_fat ?? 0;
      const sum = c + p + f || 1;
      nutritionDistribution = {
        carbs: Math.round(c), protein: Math.round(p), fat: Math.round(f),
        carbsPercent: Math.round((c / sum) * 100),
        proteinPercent: Math.round((p / sum) * 100),
        fatPercent: Math.round((f / sum) * 100),
      };
    }

    // 体重趋势
    let weightTrend: AnalysisData['weightTrend'] = [];
    let currentWeight = 0;
    let targetWeight = 0;
    if (weightResult.status === 'fulfilled') {
      const wr = weightResult.value;
      weightTrend = wr.data_points.map((p: any) => ({ date: p.date, weight: p.value }));
      currentWeight = wr.statistics?.latest ?? 0;
      targetWeight = wr.target ?? 0;
    }

    // 计划达成
    let planCompletion: AnalysisData['planCompletion'] = {
      totalDays: 0, completedDays: 0, completionRate: 0,
    };
    if (plansResult.status === 'fulfilled') {
      const plans = plansResult.value;
      const activePlan = Array.isArray(plans) ? plans[0] : plans?.data?.[0];
      if (activePlan?.id) {
        try {
          const progress = await apiClient.get<any>(`/plans/${activePlan.id}/progress`);
          planCompletion = {
            totalDays: progress.total_days ?? 0,
            completedDays: progress.elapsed_days ?? 0,
            completionRate: progress.compliance_rate ?? 0,
          };
        } catch { /* 计划进度获取失败不影响其他维度 */ }
      }
    }

    // AI 洞察
    let insights: AnalysisData['insights'] = [];
    if (insightsResult.status === 'fulfilled') {
      const raw = insightsResult.value;
      insights = (raw.insights ?? []).map((item: any) => ({
        type: mapInsightDimension(item.dimension),
        title: item.finding ?? '',
        description: item.suggestion ?? '',
      }));
    }

    return {
      timeRange: range,
      caloriesTrend,
      nutritionDistribution,
      weightTrend,
      currentWeight,
      targetWeight,
      planCompletion,
      insights,
    };
  },
};

// ===== 分页列表查询（历史记录、趋势图同日期段共用）=====

interface PaginatedBodyResponse<T> {
  data: T[];
  pagination: { total: number; page: number; page_size: number; total_pages: number };
}

// apiClient 在 2xx 时会剥壳到 body.data；分页响应 body.data 是数组，pagination 会丢失。
// 这里直接用 fetch 反打或约定：列表接口返回时前端认"data 就是数组"。
// 我们统一用 apiClient.get<T[]>，pagination 若需要可后续扩展 client。
async function getList<T>(path: string): Promise<T[]> {
  const raw = await apiClient.get<T[]>(path);
  return raw;
}

/**
 * 获取最近历史记录（用于数据页"历史记录"列表）
 * @param type  记录类型
 * @param limit 条数
 * @param options 可选日期范围
 */
export async function getRecentRecords(
  type: DataTabType,
  limit: number = 7,
  options: { endDate?: string } = {}
): Promise<BodyRecord[]> {
  const query = buildQuery({
    page: 1,
    page_size: limit,
    end_date: options.endDate,
  });
  switch (type) {
    case 'weight': {
      const raw = await getList<BackendWeightRecord>(`/body/weight${query}`);
      return raw.map(mapWeightRecord);
    }
    case 'measurement': {
      const raw = await getList<BackendMeasurementRecord>(`/body/measurement${query}`);
      return raw.map(mapMeasurementRecord);
    }
    case 'sleep': {
      const raw = await getList<BackendSleepRecord>(`/body/sleep${query}`);
      return raw.map(mapSleepRecord);
    }
    case 'exercise': {
      const raw = await getList<BackendExerciseRecord>(`/body/exercise${query}`);
      return raw.map(mapExerciseRecord);
    }
    case 'water': {
      const raw = await getList<BackendWaterRecord>(`/body/water${query}`);
      return raw.map(mapWaterRecord);
    }
    case 'bowel': {
      const raw = await getList<BackendBowelRecord>(`/body/bowel${query}`);
      return raw.map(mapBowelRecord);
    }
  }
}
