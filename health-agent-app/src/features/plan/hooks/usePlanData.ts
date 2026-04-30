// usePlanData - TanStack Query 封装
// 参考: docs/specs/frontend/modules/14-plan-module.md §6

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { planService } from '../services/planService';
import type { PlanSummary } from '../types/plan.types';

export function usePlans() {
  return useQuery({
    queryKey: ['plans'],
    queryFn: () => planService.getPlans(),
  });
}

export function usePlanDetail(planId: string | undefined) {
  return useQuery({
    queryKey: ['plan', 'detail', planId],
    queryFn: () => planService.getPlanDetail(planId!),
    enabled: !!planId,
  });
}

export function useCreatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (summary: PlanSummary) => planService.createPlan(summary),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['plans'] });
      qc.invalidateQueries({ queryKey: ['home'] });
    },
  });
}

export function useToggleTask(planId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => planService.toggleTask(planId, taskId),
    onSuccess: (data) => {
      qc.setQueryData(['plan', 'detail', planId], data);
    },
  });
}

export function useTerminatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (planId: string) => planService.terminatePlan(planId),
    onSuccess: (_, planId) => {
      qc.invalidateQueries({ queryKey: ['plans'] });
      qc.invalidateQueries({ queryKey: ['plan', 'detail', planId] });
      qc.invalidateQueries({ queryKey: ['home'] });
    },
  });
}

export function useResumePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (planId: string) => planService.resumePlan(planId),
    onSuccess: (_, planId) => {
      qc.invalidateQueries({ queryKey: ['plans'] });
      qc.invalidateQueries({ queryKey: ['plan', 'detail', planId] });
    },
  });
}
