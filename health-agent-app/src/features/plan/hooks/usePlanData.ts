import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { planService } from '../services/planService';
import type { PlanDimension } from '../types/plan.types';

export function usePlans() {
  return useQuery({
    queryKey: ['plans'],
    queryFn: () => planService.getPlans(),
  });
}

/**
 * 当前 active 计划在某维度的目标曲线，供数据模块趋势图叠加。
 * 无 active 计划或无曲线时 data 为 null（图表自动不显示目标线）。
 */
export function useActivePlanTargetCurve(dimension: PlanDimension) {
  return useQuery({
    queryKey: ['plan', 'target-curve', dimension],
    queryFn: () => planService.getActivePlanTargetCurve(dimension),
  });
}

export function usePlanDetail(planId: string | undefined) {
  return useQuery({
    queryKey: ['plan', 'detail', planId],
    queryFn: () => planService.getPlanDetail(planId!),
    enabled: !!planId,
  });
}

export function useToggleTask(planId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => planService.toggleTask(planId, taskId),
    onSuccess: (data) => {
      queryClient.setQueryData(['plan', 'detail', planId], data);
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      queryClient.invalidateQueries({ queryKey: ['home'] });
    },
  });
}

export function useTerminatePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (planId: string) => planService.terminatePlan(planId),
    onSuccess: (_, planId) => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      queryClient.invalidateQueries({ queryKey: ['plan', 'detail', planId] });
      queryClient.invalidateQueries({ queryKey: ['home'] });
    },
  });
}

export function useResumePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (planId: string) => planService.resumePlan(planId),
    onSuccess: (_, planId) => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      queryClient.invalidateQueries({ queryKey: ['plan', 'detail', planId] });
    },
  });
}
