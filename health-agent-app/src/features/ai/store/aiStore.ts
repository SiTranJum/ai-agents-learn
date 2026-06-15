// AI 模块 Store
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §7

import { create } from 'zustand';
import type { ChatMessage, NutritionData } from '../types/ai.types';

export type OverlayState = 'collapsed' | 'floating' | 'fullscreen';
export type CardStatusValue = 'pending' | 'submitted' | 'cancelled';

/**
 * 会话被后端 interrupt 暂停时挂起的 prompt。
 * 收到 `paused` 事件时写入，用户作答（sendChoice/sendCardAction）后清空。
 * 用来标识"等待用户作答"态，并让 resume 请求带上正确的 prompt_id。
 */
export interface PendingPrompt {
  promptId: string;
  kind: 'choice' | 'card';
  domain?: string | null;
}

interface AIStore {
  chatMessages: ChatMessage[];
  isAIThinking: boolean;
  /** 后端 chat session_id；首条消息返回后保存，后续消息复用同一会话 */
  currentSessionId: string | null;
  /** 会话当前被 interrupt 暂停时挂起的 prompt；null 表示空闲 */
  pendingPrompt: PendingPrompt | null;
  /** 当前展示的营养查询结果（用于触发 BottomSheet） */
  nutritionResult: NutritionData | null;
  /** AI 浮层状态：collapsed → floating → fullscreen */
  overlayState: OverlayState;
  /** 卡片状态 map（T6 流式卡片用） */
  cardStatus: Map<string, CardStatusValue>;
  /** 未读 AI 消息数（进入全屏对话后清零） */
  unreadCount: number;
  /** 最后一条已弹幕通知的消息 ID */
  lastToastMessageId: string | null;

  addMessage: (message: ChatMessage) => void;
  /** 流式更新：找最后一条 assistant 消息并用 updater 替换 */
  updateLastAIMessage: (updater: (msg: ChatMessage) => ChatMessage) => void;
  setAIThinking: (thinking: boolean) => void;
  setCurrentSessionId: (sessionId: string | null) => void;
  setPendingPrompt: (prompt: PendingPrompt | null) => void;
  setNutritionResult: (data: NutritionData | null) => void;
  setOverlayState: (state: OverlayState) => void;
  setCardStatus: (cardId: string, status: CardStatusValue) => void;
  setUnreadCount: (count: number) => void;
  incrementUnread: () => void;
  clearUnread: () => void;
  setLastToastMessageId: (id: string | null) => void;
  clearChat: () => void;
}

export const useAIStore = create<AIStore>((set) => ({
  chatMessages: [],
  isAIThinking: false,
  currentSessionId: null,
  pendingPrompt: null,
  nutritionResult: null,
  overlayState: 'collapsed',
  cardStatus: new Map(),
  unreadCount: 0,
  lastToastMessageId: null,

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
  setPendingPrompt: (prompt) => set({ pendingPrompt: prompt }),
  setNutritionResult: (data) => set({ nutritionResult: data }),
  setOverlayState: (overlayState) => set({ overlayState }),

  setCardStatus: (cardId, status) =>
    set((s) => {
      const next = new Map(s.cardStatus);
      next.set(cardId, status);
      return { cardStatus: next };
    }),

  setUnreadCount: (count) => set({ unreadCount: count }),
  incrementUnread: () => set((s) => ({ unreadCount: s.unreadCount + 1 })),
  clearUnread: () => set({ unreadCount: 0 }),
  setLastToastMessageId: (id) => set({ lastToastMessageId: id }),

  clearChat: () =>
    set({
      chatMessages: [],
      isAIThinking: false,
      currentSessionId: null,
      pendingPrompt: null,
      nutritionResult: null,
      overlayState: 'collapsed',
      cardStatus: new Map(),
      unreadCount: 0,
      lastToastMessageId: null,
    }),
}));
