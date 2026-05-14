// Plan Service - 对接后端 API
// 参考: docs/specs/frontend/modules/14-plan-module.md §7

import type {
  ChatMessage,
  PlanDetail,
  PlanListItem,
  PlanResponseRaw,
  PlanSummary,
  PlanType,
} from '../types/plan.types';
import { apiClient } from '@core/api/client';
import {
  buildDefaultSummary,
  DURATION_OPTIONS,
  TYPE_OPTIONS,
} from '../mocks/planMocks';

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

const STATUS_ORDER: Record<PlanListItem['status'], number> = {
  active: 0,
  completed: 1,
  terminated: 2,
};

interface PaginatedRaw<T> {
  data: T[];
  pagination?: { total: number; page: number; page_size: number; total_pages: number };
}

function durationText(startDate: string, endDate: string): string {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const days = Math.max(1, Math.round((end.getTime() - start.getTime()) / 86400000) + 1);
  const months = Math.max(1, Math.round(days / 30));
  return `${months}个月`;
}

function progressFromDates(startDate: string, endDate: string): number {
  const start = new Date(startDate).getTime();
  const end = new Date(endDate).getTime();
  const nowTime = Date.now();
  if (end <= start) return 100;
  return Math.max(0, Math.min(100, Math.round(((nowTime - start) / (end - start)) * 100)));
}

function mapPlan(raw: PlanResponseRaw): PlanDetail {
  const type = raw.plan_type;
  const progress = raw.status === 'completed' ? 100 : progressFromDates(raw.start_date, raw.target_date);
  return {
    id: raw.id,
    name: raw.name,
    type,
    status: raw.status,
    targetWeight: raw.targets.weight_target ?? undefined,
    dailyCalorieTarget: raw.targets.daily_calories ?? undefined,
    duration: durationText(raw.start_date, raw.target_date),
    currentPhase: '第1阶段',
    startDate: raw.start_date,
    endDate: raw.target_date,
    progress,
    tasks: raw.tasks.map((task) => ({ id: task.id, text: task.description, completed: false })),
    trendData: [],
    aiSuggestion: '计划已同步，继续按任务执行并记录数据吧～',
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
  };
}

export interface PlanService {
  getPlans(): Promise<PlanListItem[]>;
  getPlanDetail(planId: string): Promise<PlanDetail>;
  createPlan(summary: PlanSummary): Promise<PlanDetail>;
  toggleTask(planId: string, taskId: string): Promise<PlanDetail>;
  terminatePlan(planId: string): Promise<void>;
  resumePlan(planId: string): Promise<void>;
}

export const planService: PlanService = {
  async getPlans() {
    const raw = await apiClient.get<PaginatedRaw<PlanResponseRaw> | PlanResponseRaw[]>('/plans');
    const items = Array.isArray(raw) ? raw : raw.data;
    return items.map(mapPlan).map(toListItem).sort(
      (a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status]
    );
  },

  async getPlanDetail(planId) {
    const raw = await apiClient.get<PlanResponseRaw>(`/plans/${planId}`);
    return mapPlan(raw);
  },

  async createPlan(summary) {
    const raw = await apiClient.post<PlanResponseRaw>('/plans', {
      goal_description: [
        summary.name,
        summary.targetWeight ? `目标体重 ${summary.targetWeight}kg` : undefined,
        summary.dailyCalorieTarget ? `每日热量 ${summary.dailyCalorieTarget}kcal` : undefined,
        `周期 ${summary.duration}`,
        ...summary.keyRules,
      ].filter(Boolean).join('；'),
      plan_type: summary.type,
    });
    return mapPlan(raw);
  },

  async toggleTask(planId, taskId) {
    await apiClient.post(`/plans/${planId}/check-ins`, {
      task_id: taskId,
      completed: true,
    });
    return await this.getPlanDetail(planId);
  },

  async terminatePlan(planId) {
    await apiClient.delete(`/plans/${planId}`);
  },

  async resumePlan(_planId) {
    throw new Error('暂不支持恢复计划');
  },
};

// ===== 对话流程 Mock：根据当前 step + 用户输入生成 AI 回复 =====
export interface ChatStepResult {
  message: ChatMessage;
  /** 推进到下一步 */
  nextStep:
    | 'ask_type'
    | 'ask_target_weight'
    | 'ask_duration'
    | 'show_summary'
    | 'created';
  /** 用户答复中提取的字段（合并到 store.draft） */
  patch?: { type?: PlanType; targetWeight?: number; duration?: string };
}

const TYPE_TEXT_TO_KEY: Record<string, PlanType> = {
  '\u51cf\u91cd\u8ba1\u5212': 'weight_loss',
  '\u8425\u517b\u8c03\u6574': 'nutrition_adjustment',
  '\u4e60\u60ef\u517b\u6210': 'habit_formation',
};

function makeId(): string {
  return `m-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}

const now = (): string =>
  new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

/**
 * 处理对话流程：根据当前 step 和用户输入，模拟 AI 回复
 */
export async function processChatStep(
  step: 'ask_type' | 'ask_target_weight' | 'ask_duration' | 'show_summary',
  userInput: string,
  draft: { type?: PlanType; targetWeight?: number; duration?: string }
): Promise<ChatStepResult> {
  await delay(700); // 模拟 AI 思考

  switch (step) {
    case 'ask_type': {
      const planType = TYPE_TEXT_TO_KEY[userInput] ?? 'weight_loss';
      // 减重计划：问目标体重；其他：直接问周期
      if (planType === 'weight_loss') {
        return {
          patch: { type: planType },
          nextStep: 'ask_target_weight',
          message: {
            id: makeId(),
            role: 'ai',
            timestamp: now(),
            content: '好的！你的目标体重是多少？（例如 70）',
          },
        };
      }
      return {
        patch: { type: planType },
        nextStep: 'ask_duration',
        message: {
          id: makeId(),
          role: 'ai',
          timestamp: now(),
          content: '好的！你希望多久达成这个目标？',
          quickOptions: DURATION_OPTIONS,
        },
      };
    }

    case 'ask_target_weight': {
      const num = parseFloat(userInput.replace(/[^\d.]/g, ''));
      const safe = Number.isFinite(num) && num > 0 ? num : 70;
      return {
        patch: { targetWeight: safe },
        nextStep: 'ask_duration',
        message: {
          id: makeId(),
          role: 'ai',
          timestamp: now(),
          content: '好的，你希望多久达成这个目标？',
          quickOptions: DURATION_OPTIONS,
        },
      };
    }

    case 'ask_duration': {
      const duration = userInput || '3个月';
      const summary = buildDefaultSummary(
        draft.type ?? 'weight_loss',
        draft.targetWeight ?? 70,
        duration
      );
      return {
        patch: { duration },
        nextStep: 'show_summary',
        message: {
          id: makeId(),
          role: 'ai',
          timestamp: now(),
          content: '明白了，我为你制定了以下计划：',
          planSummary: summary,
          actionButtons: [
            { key: 'confirm', label: '确认创建', variant: 'primary' },
            { key: 'modify', label: '修改目标', variant: 'secondary' },
          ],
        },
      };
    }

    case 'show_summary': {
      // 用户在 summary 阶段输入文字 → 视为修改请求
      return {
        nextStep: 'show_summary',
        message: {
          id: makeId(),
          role: 'ai',
          timestamp: now(),
          content: '好的，请告诉我你想调整哪部分？目标 / 周期 / 计划类型？',
        },
      };
    }
  }
}

/** 第一条欢迎消息 */
export function buildWelcomeMessage(): ChatMessage {
  return {
    id: makeId(),
    role: 'ai',
    timestamp: now(),
    content: '你好！我来帮你制定健康计划。你想制定什么类型的计划？',
    quickOptions: TYPE_OPTIONS,
  };
}

/** "确认创建"成功后的提示消息 */
export function buildCreatedMessage(planId: string): ChatMessage {
  return {
    id: makeId(),
    role: 'ai',
    timestamp: now(),
    content: '计划已创建！你可以在计划详情页查看每日任务和进度。',
    actionButtons: [
      { key: `view:${planId}`, label: '查看计划', variant: 'primary' },
    ],
  };
}
