// 数据模块 Mock 数据
// 参考: docs/specs/frontend/modules/13-data-module.md §8

import type {
  AnalysisData,
  BowelRecord,
  ExerciseRecord,
  MeasurementRecord,
  SleepRecord,
  TimeRange,
  TodayRecords,
  WaterRecord,
  WeightRecord,
} from '../types/data.types';

const TODAY = '2026-05-09';
const YESTERDAY = '2026-05-08';

// ===== 体重趋势 mock（30 天，70kg → 66kg 阶梯式下降） =====
function generateWeightTrend(days: number): WeightRecord[] {
  const start = 70;
  const end = 66;
  const list: WeightRecord[] = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(`${TODAY}T00:00:00`);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().slice(0, 10);
    const ratio = (days - 1 - i) / Math.max(1, days - 1);
    const noise = (Math.sin(i * 1.7) * 0.3);
    const weight = Math.round((start - (start - end) * ratio + noise) * 10) / 10;
    const change =
      list.length > 0
        ? Math.round((weight - list[list.length - 1].weight) * 10) / 10
        : 0;
    list.push({
      id: `w-${dateStr}`,
      date: dateStr,
      weight,
      bmi: Math.round((weight / (1.7 * 1.7)) * 10) / 10,
      change,
    });
  }
  return list;
}

export const weightTrend7: WeightRecord[] = generateWeightTrend(7);
export const weightTrend30: WeightRecord[] = generateWeightTrend(30);
export const weightTrend90: WeightRecord[] = generateWeightTrend(90);
export const weightTrend365: WeightRecord[] = generateWeightTrend(90); // 抽样

// ===== 围度趋势 mock =====
export const measurementTrend30: MeasurementRecord[] = Array.from({ length: 10 }).map(
  (_, idx) => {
    const d = new Date(`${TODAY}T00:00:00`);
    d.setDate(d.getDate() - idx * 3);
    const dateStr = d.toISOString().slice(0, 10);
    return {
      id: `m-${dateStr}`,
      date: dateStr,
      waist: Math.round((85 - idx * 0.5) * 10) / 10,
      hip: Math.round((95 - idx * 0.3) * 10) / 10,
      thigh: Math.round((55 - idx * 0.2) * 10) / 10,
      arm: Math.round((30 - idx * 0.1) * 10) / 10,
    };
  }
);

// ===== 睡眠趋势 mock =====
const SLEEP_QUALITIES: SleepRecord['quality'][] = ['good', 'excellent', 'fair', 'good', 'good', 'fair', 'excellent'];
export const sleepTrend7: SleepRecord[] = Array.from({ length: 7 }).map((_, idx) => {
  const d = new Date(`${TODAY}T00:00:00`);
  d.setDate(d.getDate() - (6 - idx));
  const dateStr = d.toISOString().slice(0, 10);
  // 6.5 - 8h
  const minutes = 390 + Math.round(Math.sin(idx) * 60 + 30);
  return {
    id: `s-${dateStr}`,
    date: dateStr,
    bedTime: '23:30',
    wakeTime: '07:00',
    duration: minutes,
    quality: SLEEP_QUALITIES[idx],
  };
});

// ===== 运动趋势 mock（5/7） =====
const EXERCISE_TYPES = ['跑步', '游泳', '瑜伽', '力量训练', '跑步'];
export const exerciseTrend7: ExerciseRecord[] = Array.from({ length: 5 }).map((_, idx) => {
  const d = new Date(`${TODAY}T00:00:00`);
  d.setDate(d.getDate() - (6 - idx));
  const dateStr = d.toISOString().slice(0, 10);
  const duration = 30 + idx * 5;
  return {
    id: `e-${dateStr}`,
    date: dateStr,
    type: EXERCISE_TYPES[idx],
    duration,
    calories: 200 + idx * 50,
  };
});

// ===== 排便趋势 mock =====
const BOWEL_STATUS: BowelRecord['status'][] = ['normal', 'normal', 'normal', 'constipation', 'normal', 'normal', 'diarrhea'];
export const bowelTrend7: BowelRecord[] = Array.from({ length: 7 }).map((_, idx) => {
  const d = new Date(`${TODAY}T00:00:00`);
  d.setDate(d.getDate() - (6 - idx));
  const dateStr = d.toISOString().slice(0, 10);
  return {
    id: `b-${dateStr}`,
    date: dateStr,
    time: '09:30',
    status: BOWEL_STATUS[idx],
  };
});

// ===== 今日饮水 =====
export const todayWater: WaterRecord = {
  id: `wa-${TODAY}`,
  date: TODAY,
  amount: 1500,
  target: 2000,
};

// ===== 今日记录聚合 mock =====
export const todayRecordsMock: TodayRecords = {
  weight: weightTrend30[weightTrend30.length - 1],
  measurement: measurementTrend30[0],
  sleep: sleepTrend7[sleepTrend7.length - 1],
  exercise: exerciseTrend7[exerciseTrend7.length - 1],
  water: todayWater,
  bowel: bowelTrend7[bowelTrend7.length - 1],
};

// ===== 分析数据 mock =====
export const analysisDataMock: AnalysisData = {
  timeRange: '30d',
  caloriesTrend: weightTrend30.map((w, idx) => ({
    date: w.date,
    intake: 1500 + Math.round(Math.sin(idx) * 250 + 250),
    target: 1800,
  })),
  nutritionDistribution: {
    carbs: 180,
    protein: 90,
    fat: 60,
    carbsPercent: 50,
    proteinPercent: 25,
    fatPercent: 25,
  },
  weightTrend: weightTrend30.map((w) => ({ date: w.date, weight: w.weight })),
  currentWeight: 66,
  targetWeight: 60,
  planCompletion: {
    totalDays: 30,
    completedDays: 25,
    completionRate: 83.3,
  },
  insights: [
    {
      type: 'calorie',
      title: '热量控制良好',
      description: '近 30 天平均摄入 1750 kcal，略低于目标，有助于减重。',
    },
    {
      type: 'weight',
      title: '体重稳步下降',
      description: '30 天减重 4kg，平均每周 1kg，速度健康合理。',
    },
    {
      type: 'achievement',
      title: '坚持记录 25 天',
      description: '计划完成度 83.3%，继续保持！',
    },
  ],
};

// 按时间范围获取体重趋势
export function getWeightTrendByRange(range: TimeRange): WeightRecord[] {
  switch (range) {
    case '7d':
      return weightTrend7;
    case '30d':
      return weightTrend30;
    case '90d':
      return weightTrend90;
    case '365d':
      return weightTrend365;
  }
}

export const constants = { TODAY, YESTERDAY };
