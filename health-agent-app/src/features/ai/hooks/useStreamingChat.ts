// useStreamingChat: 流式聊天 hook
// T6 从 demo/StreamingDemoScreen 提炼，封装 wireStreamHandlers + 状态管理
// 状态写入 aiStore，半屏浮层和全屏 AIDialogScreen 共享同一份消息列表

import { useRef, useCallback, useEffect } from 'react';
import type {
  ChatMessage,
  ChatCard,
  ChoicePrompt,
  MessageSegment,
  ToolCallState,
  DietParseCard,
  BodyParseCard,
} from '../types/ai.types';
import { createSSEStream } from '../services/streamingClient';
import type { MockStreamHandle } from '../demo/types';
import { useAIStore } from '../store/aiStore';
import { getCardId } from '../utils/cardId';
import { useDietStore } from '@features/diet/store/dietStore';
import { useBodyPendingStore } from '@features/data/store/bodyPendingStore';
import type { FoodItem, MealType } from '@features/diet/types/diet.types';

function localTodayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/** 后端未返回餐次时，按当前时间推断默认餐次 */
function inferMealTypeByTime(): MealType {
  const h = new Date().getHours();
  if (h >= 5 && h < 10) return 'breakfast';
  if (h >= 10 && h < 14) return 'lunch';
  if (h >= 17 && h < 21) return 'dinner';
  return 'snack';
}

/** 把后端 ParsedFood → 前端 FoodItem */
function parsedFoodsToItems(foods: DietParseCard['payload']['foods']): FoodItem[] {
  return foods.map((f, idx) => ({
    id: `pending-${Date.now()}-${idx}`,
    name: f.name,
    amount: f.amount,
    unit: f.unit,
    amountGrams: f.amount_grams,
    cookingMethod: f.cooking_method ?? undefined,
    calories: f.calories,
    protein: f.protein,
    fat: f.fat,
    carbs: f.carbs,
    fiber: f.fiber ?? undefined,
    sodium: f.sodium ?? undefined,
    dataSource: f.data_source,
  }));
}

/** AI 解析饮食卡片 → 写入 dietStore.pendingRecords，首页餐次卡片即可显示待确认态 */
function syncDietParseToPending(card: ChatCard, sessionId: string | null): void {
  if (card.type !== 'diet_parse') return;
  const { foods, meal_type, suggested_date, operation } = (card as DietParseCard).payload;
  if (!foods || foods.length === 0) return;
  const resolvedMealType: MealType = meal_type ?? inferMealTypeByTime();
  useDietStore.getState().setPending({
    date: suggested_date ?? localTodayStr(),
    mealType: resolvedMealType,
    foods: parsedFoodsToItems(foods),
    operation: operation ?? 'replace',
    cardId: getCardId(card),
    sessionId: sessionId ?? undefined,
    createdAt: Date.now(),
  });
}

/** AI 解析身体数据卡片 → 写入 bodyPendingStore，首页辅助卡片显示待确认态 */
function syncBodyParseToPending(card: ChatCard, sessionId: string | null): void {
  if (card.type !== 'body_parse') return;
  const p = (card as BodyParseCard).payload;
  if (!p.record_type) return;
  useBodyPendingStore.getState().setPending({
    date: p.suggested_date ?? localTodayStr(),
    recordType: p.record_type,
    operation: p.operation ?? 'replace',
    cardId: getCardId(card),
    sessionId: sessionId ?? undefined,
    createdAt: Date.now(),
    waterAmount: p.water_amount ?? undefined,
    sleepBedTime: p.sleep_bed_time ?? undefined,
    sleepWakeTime: p.sleep_wake_time ?? undefined,
    sleepQuality: p.sleep_quality ?? undefined,
    exerciseType: p.exercise_type ?? undefined,
    exerciseDuration: p.exercise_duration ?? undefined,
    bowelTime: p.bowel_time ?? undefined,
    bowelStatus: p.bowel_status ?? undefined,
  });
}

interface UseStreamingChatReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  send: (text: string, ctx?: { image_url?: string; referenced_date?: string }) => void;
  sendChoice: (promptId: string, value: string, freeText?: string) => void;
  sendCardAction: (card: ChatCard, actionId: string) => void;
  cancel: () => void;
  cardStatus: Map<string, 'pending' | 'submitted' | 'cancelled'>;
  sessionId: string | null;
}

export function useStreamingChat(): UseStreamingChatReturn {
  const streamRef = useRef<MockStreamHandle | null>(null);

  const messages = useAIStore((s) => s.chatMessages);
  const sessionId = useAIStore((s) => s.currentSessionId);
  const cardStatus = useAIStore((s) => s.cardStatus);
  const addMessage = useAIStore((s) => s.addMessage);
  const updateLastAIMessage = useAIStore((s) => s.updateLastAIMessage);
  const setCurrentSessionId = useAIStore((s) => s.setCurrentSessionId);
  const setCardStatus = useAIStore((s) => s.setCardStatus);
  const setAIThinking = useAIStore((s) => s.setAIThinking);

  // 卸载时关闭活动流
  useEffect(() => {
    return () => {
      streamRef.current?.cancel();
    };
  }, []);

  // 把所有 SSE 事件 handler 注册到给定 handle 上
  const wireStreamHandlers = useCallback(
    (handle: MockStreamHandle) => {
      handle.on('meta', ({ session_id }) => {
        if (session_id) setCurrentSessionId(session_id);
      });

      handle.on('status', ({ label }) => {
        updateLastAIMessage((msg) => ({ ...msg, status: label }));
      });

      handle.on('tool_call', ({ tool, label }) => {
        updateLastAIMessage((msg) => {
          const without = (msg.tools || []).filter((t) => t.tool !== tool);
          return {
            ...msg,
            tools: [...without, { tool, label, state: 'pending' as const }] as ToolCallState[],
          };
        });
      });

      handle.on('tool_result', ({ tool, summary }) => {
        updateLastAIMessage((msg) => ({
          ...msg,
          tools: (msg.tools || []).map((t) =>
            t.tool === tool ? { ...t, summary, state: 'done' as const } : t
          ) as ToolCallState[],
        }));
      });

      handle.on('text_delta', ({ content }) => {
        updateLastAIMessage((msg) => {
          const segs = [...(msg.segments || [])];
          const last = segs[segs.length - 1];
          if (last && last.kind === 'text') {
            segs[segs.length - 1] = { kind: 'text', content: last.content + content };
          } else {
            segs.push({ kind: 'text', content });
          }
          return { ...msg, segments: segs, status: null };
        });
      });

      handle.on('choice', (prompt: ChoicePrompt) => {
        updateLastAIMessage((msg) => ({
          ...msg,
          status: null,
          segments: [
            ...(msg.segments || []),
            { kind: 'choice', prompt } satisfies MessageSegment,
          ],
        }));
      });

      handle.on('card', ({ card }) => {
        const cardId = getCardId(card);
        setCardStatus(cardId, 'pending');
        // AI 解析饮食卡片 → 同步写入 dietStore.pendingRecords，
        // 让首页对应餐次卡片显示"待确认"态（确认/修改/取消）
        syncDietParseToPending(card, useAIStore.getState().currentSessionId);
        // AI 解析身体数据卡片 → 同步写入 bodyPendingStore，
        // 让首页辅助卡片（饮水/睡眠/运动/排便）显示"待确认"态
        syncBodyParseToPending(card, useAIStore.getState().currentSessionId);
        updateLastAIMessage((msg) => ({
          ...msg,
          status: null,
          segments: [
            ...(msg.segments || []),
            { kind: 'card', card } satisfies MessageSegment,
          ],
        }));
      });

      handle.on('done', () => {
        updateLastAIMessage((msg) => ({ ...msg, isStreaming: false, status: null }));
        setAIThinking(false);
        streamRef.current = null;
      });

      handle.on('error', ({ code, message }) => {
        updateLastAIMessage((msg) => ({
          ...msg,
          isStreaming: false,
          status: null,
          error: { code, message },
        }));
        setAIThinking(false);
        streamRef.current = null;
      });
    },
    [updateLastAIMessage, setCurrentSessionId, setCardStatus, setAIThinking]
  );

  // 通用流式请求分发
  const _dispatch = useCallback(
    (payload: any) => {
      // 用户消息
      const userMsg: ChatMessage = {
        id: `u_${Date.now()}`,
        role: 'user',
        content: payload.message || `[${payload.type}]`,
        timestamp: new Date().toISOString(),
      };
      addMessage(userMsg);

      // 占位 AI 消息（流式中）
      const aiMsg: ChatMessage = {
        id: `ai_${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        segments: [],
        status: null,
        tools: [],
        isStreaming: true,
      };
      addMessage(aiMsg);
      setAIThinking(true);

      const handle = createSSEStream(payload);
      streamRef.current = handle;
      wireStreamHandlers(handle);
      handle.start();
    },
    [addMessage, setAIThinking, wireStreamHandlers]
  );

  const send = useCallback(
    (text: string, ctx?: { image_url?: string; referenced_date?: string }) => {
      _dispatch({
        type: 'text',
        message: text,
        context: ctx,
        session_id: sessionId,
      });
    },
    [_dispatch, sessionId]
  );

  const sendChoice = useCallback(
    (promptId: string, value: string, freeText?: string) => {
      _dispatch({
        type: 'choice_response',
        prompt_id: promptId,
        selected_value: value,
        free_text: freeText,
        session_id: sessionId,
        message: value || freeText || '已选择',
      });
    },
    [_dispatch, sessionId]
  );

  const sendCardAction = useCallback(
    (card: ChatCard, actionId: string) => {
      const cardId = getCardId(card);
      setCardStatus(cardId, 'submitted');
      _dispatch({
        type: 'card_action',
        card_id: cardId,
        action_id: actionId,
        action_payload: card.payload,
        session_id: sessionId,
        message: `[card_action] ${actionId}`,
      });
    },
    [_dispatch, sessionId, setCardStatus]
  );

  const cancel = useCallback(() => {
    streamRef.current?.cancel();
    updateLastAIMessage((msg) => ({ ...msg, isStreaming: false, status: null }));
    setAIThinking(false);
    streamRef.current = null;
  }, [updateLastAIMessage, setAIThinking]);

  const isStreaming = messages.some(
    (m) => (m.role === 'assistant' || m.role === 'ai') && m.isStreaming
  );

  return {
    messages,
    isStreaming,
    send,
    sendChoice,
    sendCardAction,
    cancel,
    cardStatus,
    sessionId,
  };
}
