// AI 模块 Store
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §7

import { create } from 'zustand';
import type { ChatMessage, NutritionData } from '../types/ai.types';

export type OverlayState = 'collapsed' | 'floating' | 'fullscreen';
export type CardStatusValue = 'pending' | 'submitted' | 'cancelled';

interface AIStore {
  chatMessages: ChatMessage[];
  isAIThinking: boolean;
  /** 后端 chat session_id；首条消息返回后保存，后续消息复用同一会话 */
  currentSessionId: string | null;
  /** 当前展示的营养查询结果（用于触发 BottomSheet） */
  nutritionResult: NutritionData | null;
  /** AI 浮层状态：collapsed → floating → fullscreen */
  overlayState: OverlayState;
  /** 卡片状态 map（T6 流式卡片用） */
  cardStatus: Map<string, CardStatusValue>;

  addMessage: (message: ChatMessage) => void;
  /** 流式更新：找最后一条 assistant 消息并用 updater 替换 */
  updateLastAIMessage: (updater: (msg: ChatMessage) => ChatMessage) => void;
  setAIThinking: (thinking: boolean) => void;
  setCurrentSessionId: (sessionId: string | null) => void;
  setNutritionResult: (data: NutritionData | null) => void;
  setOverlayState: (state: OverlayState) => void;
  setCardStatus: (cardId: string, status: CardStatusValue) => void;
  clearChat: () => void;
}

export const useAIStore = create<AIStore>((set) => ({
  chatMessages: [],
  isAIThinking: false,
  currentSessionId: null,
  nutritionResult: null,
  overlayState: 'collapsed',
  cardStatus: new Map(),

  addMessage: (message) =>
    set((s) => ({ chatMessages: [...s.chatMessages, message] })),

  updateLastAIMessage: (updater) =>
    set((s) => {
      const arr = [...s.chatMessages];
      for (let i = arr.length - 1; i >= 0; i--) {
        if (arr[i].role === 'assistant' || arr[i].role === 'ai') {
          arr[i] = updater(arr[i]);
          return { chatMessages: arr };
        }
      }
      return {};
    }),

  setAIThinking: (thinking) => set({ isAIThinking: thinking }),
  setCurrentSessionId: (sessionId) => set({ currentSessionId: sessionId }),
  setNutritionResult: (data) => set({ nutritionResult: data }),
  setOverlayState: (overlayState) => set({ overlayState }),

  setCardStatus: (cardId, status) =>
    set((s) => {
      const next = new Map(s.cardStatus);
      next.set(cardId, status);
      return { cardStatus: next };
    }),

  clearChat: () =>
    set({
      chatMessages: [],
      isAIThinking: false,
      currentSessionId: null,
      nutritionResult: null,
      overlayState: 'collapsed',
      cardStatus: new Map(),
    }),
}));
