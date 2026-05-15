// AI 模块 Store
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §7

import { create } from 'zustand';
import type { ChatMessage, NutritionData } from '../types/ai.types';

export type OverlayState = 'collapsed' | 'floating' | 'fullscreen';

interface AIStore {
  chatMessages: ChatMessage[];
  isAIThinking: boolean;
  /** 后端 chat session_id；首条消息返回后保存，后续消息复用同一会话 */
  currentSessionId: string | null;
  /** 当前展示的营养查询结果（用于触发 BottomSheet） */
  nutritionResult: NutritionData | null;
  /** AI 浮层状态：collapsed → floating → fullscreen */
  overlayState: OverlayState;

  addMessage: (message: ChatMessage) => void;
  setAIThinking: (thinking: boolean) => void;
  setCurrentSessionId: (sessionId: string | null) => void;
  setNutritionResult: (data: NutritionData | null) => void;
  setOverlayState: (state: OverlayState) => void;
  clearChat: () => void;
}

export const useAIStore = create<AIStore>((set) => ({
  chatMessages: [],
  isAIThinking: false,
  currentSessionId: null,
  nutritionResult: null,
  overlayState: 'collapsed',

  addMessage: (message) =>
    set((s) => ({ chatMessages: [...s.chatMessages, message] })),
  setAIThinking: (thinking) => set({ isAIThinking: thinking }),
  setCurrentSessionId: (sessionId) => set({ currentSessionId: sessionId }),
  setNutritionResult: (data) => set({ nutritionResult: data }),
  setOverlayState: (overlayState) => set({ overlayState }),
  clearChat: () =>
    set({
      chatMessages: [],
      isAIThinking: false,
      currentSessionId: null,
      nutritionResult: null,
      overlayState: 'collapsed',
    }),
}));
