// Plan Store - Zustand
// 仅保管对话流状态（消息列表 / AI 思考态 / 当前步骤 / 收集到的字段）
// 参考: docs/specs/frontend/modules/14-plan-module.md §6

import { create } from 'zustand';
import type {
  ChatMessage,
  ChatStep,
  PlanType,
} from '../types/plan.types';

interface ChatDraft {
  type?: PlanType;
  targetWeight?: number;
  duration?: string;
}

interface PlanStore {
  chatMessages: ChatMessage[];
  isAIThinking: boolean;
  step: ChatStep;
  draft: ChatDraft;

  addMessage: (message: ChatMessage) => void;
  setAIThinking: (thinking: boolean) => void;
  setStep: (step: ChatStep) => void;
  patchDraft: (patch: Partial<ChatDraft>) => void;
  clearChat: () => void;
}

export const usePlanStore = create<PlanStore>((set) => ({
  chatMessages: [],
  isAIThinking: false,
  step: 'ask_type',
  draft: {},

  addMessage: (message) =>
    set((s) => ({ chatMessages: [...s.chatMessages, message] })),
  setAIThinking: (thinking) => set({ isAIThinking: thinking }),
  setStep: (step) => set({ step }),
  patchDraft: (patch) => set((s) => ({ draft: { ...s.draft, ...patch } })),
  clearChat: () =>
    set({ chatMessages: [], isAIThinking: false, step: 'ask_type', draft: {} }),
}));
