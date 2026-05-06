// AI 模块 Store
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §7

import { create } from 'zustand';
import type { ChatMessage, NutritionData } from '../types/ai.types';

interface AIStore {
  chatMessages: ChatMessage[];
  isAIThinking: boolean;
  /** 当前展示的营养查询结果（用于触发 BottomSheet） */
  nutritionResult: NutritionData | null;

  addMessage: (message: ChatMessage) => void;
  setAIThinking: (thinking: boolean) => void;
  setNutritionResult: (data: NutritionData | null) => void;
  clearChat: () => void;
}

export const useAIStore = create<AIStore>((set) => ({
  chatMessages: [],
  isAIThinking: false,
  nutritionResult: null,

  addMessage: (message) =>
    set((s) => ({ chatMessages: [...s.chatMessages, message] })),
  setAIThinking: (thinking) => set({ isAIThinking: thinking }),
  setNutritionResult: (data) => set({ nutritionResult: data }),
  clearChat: () =>
    set({ chatMessages: [], isAIThinking: false, nutritionResult: null }),
}));
