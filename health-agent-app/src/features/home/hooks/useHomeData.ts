// useHomeData - 拆分为独立查询，每个卡片独立 loading
// T2: 首页多接口并行加载
// 参考: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T2

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import {
  fetchDietSummary,
  fetchBodyToday,
  fetchAIInsight,
  fetchActivePlan,
} from '../services/homeService';
import { useHomeStore } from '../store/homeStore';
import type { HomeAuxiliary, HomeMeal, HomePlan, NutrientValue } from '../types/home.types';

// ============ 独立查询 hooks ============

export interface DietSummaryData {
  calories: { current: number; target: number };
  nutrients: { carbs: NutrientValue; protein: NutrientValue; fat: NutrientValue };
  meals: HomeMeal[];
}

export function useDietSummary(date: string) {
  return useQuery<DietSummaryData>({
    queryKey: ['home/diet', date],
    queryFn: () => fetchDietSummary(date),
  });
}

export function useBodyToday(date: string) {
  return useQuery<HomeAuxiliary>({
    queryKey: ['home/body', date],
    queryFn: () => fetchBodyToday(date),
  });
}

export function useAIInsight(date: string) {
  return useQuery<string>({
    queryKey: ['home/insight', date],
    queryFn: () => fetchAIInsight(),
    // AI 洞察可以稍微 stale 一些，减少不必要的重新请求
    staleTime: 60_000,
  });
}

export function usePlanProgress() {
  return useQuery<HomePlan | null>({
    queryKey: ['home/plan'],
    queryFn: () => fetchActivePlan(),
    staleTime: 30_000,
  });
}

// ============ 聚合 hook（保持向后兼容） ============

/**
 * useHomeData 保留原有接口，内部改为 4 个独立查询。
 * HomeScreen 可以选择用这个聚合 hook（旧行为），
 * 也可以直接用上面 4 个独立 hook（新行为，独立 loading）。
 */
export function useHomeData(dateOverride?: string) {
  const selectedDate = useHomeStore((s) => s.selectedDate);
  const date = dateOverride ?? selectedDate;
  const queryClient = useQueryClient();

  const dietQuery = useDietSummary(date);
  const bodyQuery = useBodyToday(date);
  const insightQuery = useAIInsight(date);
  const planQuery = usePlanProgress();

  const isLoading =
    dietQuery.isLoading || bodyQuery.isLoading || insightQuery.isLoading || planQuery.isLoading;
  const isRefetching =
    dietQuery.isRefetching || bodyQuery.isRefetching || insightQuery.isRefetching || planQuery.isRefetching;

  // 只有全部就绪才组装 data（保持旧行为兼容）
  const data =
    dietQuery.data && bodyQuery.data
      ? {
          date,
          calories: dietQuery.data.calories,
          nutrients: dietQuery.data.nutrients,
          meals: dietQuery.data.meals,
          aiInsight: insightQuery.data ?? '记得多喝水、均衡饮食、保持运动。',
          plan: planQuery.data ?? null,
          auxiliary: bodyQuery.data,
        }
      : undefined;

  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['home/diet', date] });
    queryClient.invalidateQueries({ queryKey: ['home/body', date] });
    queryClient.invalidateQueries({ queryKey: ['home/insight', date] });
    queryClient.invalidateQueries({ queryKey: ['home/plan'] });
  }, [queryClient, date]);

  return {
    date,
    data,
    isLoading,
    isRefetching,
    error: dietQuery.error || bodyQuery.error,
    refetch,
    // 暴露独立查询，供 HomeScreen 渐进渲染使用
    dietQuery,
    bodyQuery,
    insightQuery,
    planQuery,
  };
}
