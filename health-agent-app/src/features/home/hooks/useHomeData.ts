// useHomeData - 封装 TanStack Query 获取首页聚合数据
// 参考: docs/specs/frontend/modules/11-home-module.md §6

import { useQuery } from '@tanstack/react-query';
import { homeService } from '../services/homeService';
import { useHomeStore } from '../store/homeStore';

export function useHomeData(dateOverride?: string) {
  const selectedDate = useHomeStore((s) => s.selectedDate);
  const date = dateOverride ?? selectedDate;

  const query = useQuery({
    queryKey: ['home', date],
    queryFn: () => homeService.getHomeData(date),
  });

  return {
    date,
    data: query.data,
    isLoading: query.isLoading,
    isRefetching: query.isRefetching,
    error: query.error,
    refetch: query.refetch,
  };
}
