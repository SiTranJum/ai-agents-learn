// Plan Service - Mock 实现
// 参考: docs/specs/frontend/modules/14-plan-module.md §7

import type {
  ChatMessage,
  PlanDetail,
  PlanListItem,
  PlanSummary,
  PlanType,
} from '../types/plan.types';
import {
  buildDefaultSummary,
  DURATION_OPTIONS,
  planDetailsMock,
  planListMock,
  TYPE_OPTIONS,
} from '../mocks/planMocks';

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

const STATUS_ORDER: Record<PlanListItem['status'], number> = {
  active: 0,
  paused: 1,
  completed: 2,
  terminated: 3,
};

let LIST: PlanListItem[] = [...planListMock];
let DETAILS: Record<string, PlanDetail> = { ...planDetailsMock };

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
    await delay(400);
    return [...LIST].sort(
      (a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status]
    );
  },

  async getPlanDetail(planId) {
    await delay(400);
    const detail = DETAILS[planId];
    if (!detail) {
      throw new Error('计划不存在');
    }
    return { ...detail, tasks: [...detail.tasks] };
  },

  async createPlan(summary) {
    await delay(800);
    const id = `plan-${Date.now()}`;
    const start = new Date();
    const end = new Date(start);
    const months = Number(summary.duration.replace(/[^\d]/g, '')) || 3;
    end.setMonth(end.getMonth() + months);

    const startDate = start.toISOString().slice(0, 10);
    const endDate = end.toISOString().slice(0, 10);

    const detail: PlanDetail = {
      id,
      name: summary.name,
      type: summary.type as PlanType,
      status: 'active',
      targetWeight: summary.targetWeight,
      dailyCalorieTarget: summary.dailyCalorieTarget,
      duration: summary.duration,
      currentPhase: '第1阶段',
      startDate,
      endDate,
      progress: 0,
      tasks: summary.keyRules.map((text, idx) => ({
        id: `t-${id}-${idx}`,
        text,
        completed: false,
      })),
      trendData: [],
      aiSuggestion: '计划已创建，开始记录吧～',
    };

    DETAILS = { ...DETAILS, [id]: detail };
    LIST = [
      {
        id,
        name: detail.name,
        type: detail.type,
        status: 'active',
        progress: 0,
        startDate,
        endDate,
      },
      ...LIST,
    ];

    return detail;
  },

  async toggleTask(planId, taskId) {
    await delay(150);
    const detail = DETAILS[planId];
    if (!detail) throw new Error('计划不存在');
    const tasks = detail.tasks.map((t) =>
      t.id === taskId ? { ...t, completed: !t.completed } : t
    );
    const next = { ...detail, tasks };
    DETAILS = { ...DETAILS, [planId]: next };
    return { ...next, tasks: [...tasks] };
  },

  async terminatePlan(planId) {
    await delay(400);
    const detail = DETAILS[planId];
    if (!detail) return;
    DETAILS = {
      ...DETAILS,
      [planId]: { ...detail, status: 'terminated' },
    };
    LIST = LIST.map((p) =>
      p.id === planId ? { ...p, status: 'terminated' } : p
    );
  },

  async resumePlan(planId) {
    await delay(300);
    const detail = DETAILS[planId];
    if (!detail) return;
    DETAILS = { ...DETAILS, [planId]: { ...detail, status: 'active' } };
    LIST = LIST.map((p) => (p.id === planId ? { ...p, status: 'active' } : p));
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
  减重计划: 'lose_weight',
  营养调整: 'nutrition',
  习惯养成: 'habit',
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
      const planType = TYPE_TEXT_TO_KEY[userInput] ?? 'lose_weight';
      // 减重计划：问目标体重；其他：直接问周期
      if (planType === 'lose_weight') {
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
        draft.type ?? 'lose_weight',
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
