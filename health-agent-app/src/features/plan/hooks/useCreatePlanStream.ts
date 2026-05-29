// useCreatePlanStream - 流式创建计划 hook（T11）
// 替换 useCreatePlan（同步 mutation），改用 SSE 流式获取创建进度
// 事件序列：meta → status(×N) → card(plan) + done | error

import { useState, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { createSSEStream } from '@features/ai/services/streamingClient';
import type { MockStreamHandle } from '@features/ai/demo/types';
import type { PlanSummary } from '../types/plan.types';

interface UseCreatePlanStreamReturn {
  isCreating: boolean;
  status: string | null;
  error: string | null;
  createdPlanId: string | null;
  create: (summary: PlanSummary) => void;
  reset: () => void;
}

export function useCreatePlanStream(): UseCreatePlanStreamReturn {
  const [isCreating, setIsCreating] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [createdPlanId, setCreatedPlanId] = useState<string | null>(null);
  const handleRef = useRef<MockStreamHandle | null>(null);
  const qc = useQueryClient();

  const create = useCallback((summary: PlanSummary) => {
    handleRef.current?.cancel();
    setIsCreating(true);
    setStatus(null);
    setError(null);
    setCreatedPlanId(null);

    const goalDescription = [
      summary.name,
      summary.targetWeight ? `目标体重 ${summary.targetWeight}kg` : undefined,
      summary.dailyCalorieTarget ? `每日热量 ${summary.dailyCalorieTarget}kcal` : undefined,
      `周期 ${summary.duration}`,
      ...summary.keyRules,
    ].filter(Boolean).join('；');

    const handle = createSSEStream(
      // 后端 PlanCreate schema: { goal_description, plan_type }
      // createSSEStream 会 JSON.stringify 整个 payload 作为 body
      { goal_description: goalDescription, plan_type: summary.type } as any,
      { path: '/plans/stream', method: 'POST', idleTimeoutMs: 120_000 }
    );
    handleRef.current = handle;

    handle.on('status', ({ label }) => setStatus(label));

    handle.on('card', ({ card }) => {
      const planCard = card as Record<string, unknown>;
      if (planCard.id) {
        setCreatedPlanId(String(planCard.id));
      }
    });

    handle.on('done', () => {
      setIsCreating(false);
      setStatus(null);
      handleRef.current = null;
      qc.invalidateQueries({ queryKey: ['plans'] });
      qc.invalidateQueries({ queryKey: ['home'] });
    });

    handle.on('error', ({ message, code }) => {
      setIsCreating(false);
      setStatus(null);
      setError(message || '创建失败');
      handleRef.current = null;
    });

    handle.start();
  }, [qc]);

  const reset = useCallback(() => {
    handleRef.current?.cancel();
    setIsCreating(false);
    setStatus(null);
    setError(null);
    setCreatedPlanId(null);
  }, []);

  return { isCreating, status, error, createdPlanId, create, reset };
}
