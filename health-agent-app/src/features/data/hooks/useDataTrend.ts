// useDataTrend - TanStack Query 封装：今日记录、趋势、历史、分析
// 参考: docs/specs/frontend/modules/13-data-module.md §6

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dataService, getRecentRecords } from '../services/dataService';
import { useDataStore } from '../store/dataStore';
import type {
  BodyRecord,
  DataTabType,
  TimeRange,
  TrendPoint,
} from '../types/data.types';

export function useTodayRecords() {
  return useQuery({
    queryKey: ['data', 'today'],
    queryFn: () => dataService.getTodayRecords(),
  });
}

export function useTrendData(tab: DataTabType, range: TimeRange) {
  return useQuery({
    queryKey: ['data', 'trend', tab, range],
    queryFn: async (): Promise<{ points: TrendPoint[]; unit: string; label: string }> => {
      switch (tab) {
        case 'weight': {
          const r = await dataService.getWeightTrend(range);
          return { points: r.points, unit: 'kg', label: '体重' };
        }
        case 'measurement': {
          const r = await dataService.getMeasurementTrend(range, 'waist');
          return { points: r.points, unit: 'cm', label: '腰围' };
        }
        case 'sleep': {
          const r = await dataService.getSleepTrend(range);
          return { points: r.points, unit: 'h', label: '睡眠时长' };
        }
        case 'exercise': {
          const r = await dataService.getExerciseTrend(range);
          return { points: r.points, unit: 'min', label: '运动时长' };
        }
        case 'water': {
          // 饮水使用最近 7 天
          const records = (await getRecentRecords('water', 7)) as Array<{
            date: string;
            amount: number;
          }>;
          return {
            points: records.reverse().map((r) => ({ date: r.date, value: r.amount })),
            unit: 'ml',
            label: '饮水',
          };
        }
        case 'bowel': {
          const records = (await getRecentRecords('bowel', 7)) as Array<{ date: string }>;
          return {
            points: records.reverse().map((r) => ({ date: r.date, value: 1 })),
            unit: '次',
            label: '排便次数',
          };
        }
      }
    },
  });
}

export function useRecentRecords(tab: DataTabType, limit: number = 7) {
  return useQuery({
    queryKey: ['data', 'recent', tab, limit],
    queryFn: () => getRecentRecords(tab, limit),
  });
}

export function useAnalysisData() {
  const range = useDataStore((s) => s.selectedTimeRange);
  return useQuery({
    queryKey: ['data', 'analysis', range],
    queryFn: () => dataService.getAnalysisData(range),
  });
}

// ===== Mutations =====
export function useSaveBodyData() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: { type: DataTabType; record: Partial<BodyRecord> }) =>
      dataService.saveBodyData(params.type, params.record),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['data'] });
      qc.invalidateQueries({ queryKey: ['home'] });
    },
  });
}

export function useAddWater() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: { date: string; amount: number }) =>
      dataService.addWaterAmount(params.date, params.amount),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['data', 'today'] });
      qc.invalidateQueries({ queryKey: ['home'] });
    },
  });
}
