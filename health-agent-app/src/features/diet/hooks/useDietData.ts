// useDietData - TanStack Query 封装
// 参考: docs/specs/frontend/modules/12-diet-module.md §6

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dietService } from '../services/dietService';
import { useDietStore } from '../store/dietStore';
import type { DietRecord } from '../types/diet.types';

export function useDietData(dateOverride?: string) {
  const selectedDate = useDietStore((s) => s.selectedDate);
  const setSelectedDate = useDietStore((s) => s.setSelectedDate);
  const date = dateOverride ?? selectedDate;
  const qc = useQueryClient();

  const query = useQuery({
    queryKey: ['diet', date],
    queryFn: () => dietService.getDietByDate(date),
  });

  const saveMutation = useMutation({
    mutationFn: (record: DietRecord) => dietService.saveDietRecord(record),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['diet', date] });
      qc.invalidateQueries({ queryKey: ['home'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (recordId: string) => dietService.deleteDietRecord(recordId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['diet', date] });
      qc.invalidateQueries({ queryKey: ['home'] });
    },
  });

  return {
    date,
    setSelectedDate,
    data: query.data,
    isLoading: query.isLoading,
    isRefetching: query.isRefetching,
    error: query.error,
    refetch: query.refetch,
    saveRecord: saveMutation.mutateAsync,
    isSaving: saveMutation.isPending,
    deleteRecord: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
  };
}
