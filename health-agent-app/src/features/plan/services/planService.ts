import { apiClient } from '@core/api/client';

import type {
  DailyExecutionRaw,
  PlanDetail,
  PlanListItem,
  PlanPhase,
  PlanProgressRaw,
  PlanResponseRaw,
  PlanTask,
} from '../types/plan.types';

const STATUS_ORDER: Record<PlanListItem['status'], number> = {
  active: 0,
  completed: 1,
  terminated: 2,
};

function durationText(startDate: string, endDate: string): string {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const days = Math.max(1, Math.round((end.getTime() - start.getTime()) / 86400000) + 1);
  if (days % 7 === 0) {
    return `${days / 7} 周`;
  }
  return `${days} 天`;
}

function trendValue(record: DailyExecutionRaw): number {
  if (record.status === 'on_track') return 100;
  if (record.status === 'deviation') return 65;
  return 25;
}

function currentPhaseLabel(phases: PlanPhase[]): string | undefined {
  const today = new Date().toISOString().slice(0, 10);
  return phases.find((phase) => phase.startDate <= today && phase.endDate >= today)?.title ?? phases[0]?.title;
}

function mapTasks(raw: PlanResponseRaw, progress: PlanProgressRaw): PlanTask[] {
  const completed = new Set(progress.completed_task_ids);
  return raw.tasks.map((task) => ({
    id: task.id,
    text: task.description,
    completed: completed.has(task.id),
    frequency: task.frequency,
    timePeriod: task.time_period,
  }));
}

function mapPhases(raw: PlanResponseRaw, progress: PlanProgressRaw): PlanPhase[] {
  const completed = new Set(progress.completed_task_ids);
  return raw.phases.map((phase) => ({
    id: phase.id,
    title: phase.title,
    goal: phase.goal,
    startDate: phase.start_date,
    endDate: phase.end_date,
    tasks: phase.tasks.map((task) => ({
      id: task.id,
      text: task.description,
      completed: completed.has(task.id),
      frequency: task.frequency,
      timePeriod: task.time_period,
    })),
  }));
}

function aiSuggestion(progress: PlanProgressRaw): string {
  if (progress.completed_tasks < progress.total_tasks && progress.total_tasks > 0) {
    return '今日任务还未完成。建议先完成剩余任务，再复盘热量执行情况。';
  }
  if (progress.compliance_rate < 0.6) {
    return '执行出现明显偏离。建议降低任务强度，或适当拉长计划周期。';
  }
  return '执行整体稳定。建议保持当前节奏，并继续记录饮食和身体数据。';
}

async function fetchPlanBundle(planId: string) {
  const [plan, progress, execution] = await Promise.all([
    apiClient.get<PlanResponseRaw>(`/plans/${planId}`),
    apiClient.get<PlanProgressRaw>(`/plans/${planId}/progress`),
    apiClient.getPaginated<DailyExecutionRaw>(`/plans/${planId}/execution?page=1&page_size=30`),
  ]);
  return { plan, progress, execution: execution.data };
}

function mapPlanDetail(raw: PlanResponseRaw, progress: PlanProgressRaw, execution: DailyExecutionRaw[]): PlanDetail {
  const phases = mapPhases(raw, progress);
  const tasks = mapTasks(raw, progress);
  const currentPhase = currentPhaseLabel(phases);
  const streakWarning = execution
    .slice()
    .reverse()
    .findIndex((record) => record.status !== 'missed');
  return {
    id: raw.id,
    name: raw.name,
    type: raw.plan_type,
    status: raw.status,
    targetWeight: raw.targets.weight_target ?? undefined,
    dailyCalorieTarget: raw.targets.daily_calories ?? undefined,
    duration: durationText(raw.start_date, raw.target_date),
    currentPhase,
    startDate: raw.start_date,
    endDate: raw.target_date,
    progress: Math.round(progress.compliance_rate * 100),
    completedTasks: progress.completed_tasks,
    totalTasks: progress.total_tasks,
    streakDays: progress.streak_days,
    tasks,
    phases,
    trendData: execution.map((record) => ({ date: record.date, value: trendValue(record) })),
    aiSuggestion: aiSuggestion(progress),
    warning:
      streakWarning >= 5
        ? { daysMissed: streakWarning, description: '已连续多天未达成计划目标。' }
        : undefined,
  };
}

function toListItem(detail: PlanDetail): PlanListItem {
  return {
    id: detail.id,
    name: detail.name,
    type: detail.type,
    status: detail.status,
    progress: detail.progress,
    startDate: detail.startDate,
    endDate: detail.endDate,
    currentPhase: detail.currentPhase,
  };
}

export interface PlanService {
  getPlans(): Promise<PlanListItem[]>;
  getPlanDetail(planId: string): Promise<PlanDetail>;
  toggleTask(planId: string, taskId: string): Promise<PlanDetail>;
  terminatePlan(planId: string): Promise<void>;
  resumePlan(planId: string): Promise<void>;
}

export const planService: PlanService = {
  async getPlans() {
    const listed = await apiClient.getPaginated<PlanResponseRaw>('/plans?page=1&page_size=20');
    const details = await Promise.all(
      listed.data.map(async (plan) => {
        const progress = await apiClient.get<PlanProgressRaw>(`/plans/${plan.id}/progress`);
        return mapPlanDetail(plan, progress, progress.daily_records);
      })
    );
    return details.map(toListItem).sort((left, right) => STATUS_ORDER[left.status] - STATUS_ORDER[right.status]);
  },

  async getPlanDetail(planId) {
    const { plan, progress, execution } = await fetchPlanBundle(planId);
    return mapPlanDetail(plan, progress, execution);
  },

  async toggleTask(planId, taskId) {
    await apiClient.post(`/plans/${planId}/check-ins`, {
      task_id: taskId,
      completed: true,
    });
    return this.getPlanDetail(planId);
  },

  async terminatePlan(planId) {
    await apiClient.delete(`/plans/${planId}`);
  },

  async resumePlan() {
    throw new Error('暂不支持恢复计划。');
  },
};
