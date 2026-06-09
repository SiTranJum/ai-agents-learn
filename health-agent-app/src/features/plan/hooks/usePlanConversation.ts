import { useCallback, useMemo, useRef, useState } from 'react';

import { createSSEStream } from '@features/ai/services/streamingClient';
import type { ChatCard, ChatMessage, ChoicePrompt, MessageSegment, DietParseCard, BodyParseCard } from '@features/ai/types/ai.types';
import { getCardId } from '@features/ai/utils/cardId';
import type { MockStreamHandle } from '@features/ai/demo/types';
import { useDietStore } from '@features/diet/store/dietStore';
import { useBodyPendingStore } from '@features/data/store/bodyPendingStore';
import type { FoodItem, MealType } from '@features/diet/types/diet.types';

type CardStatus = 'pending' | 'submitted' | 'cancelled';

interface BackendTranscriptMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

function localTodayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function inferMealTypeByTime(): MealType {
  const h = new Date().getHours();
  if (h >= 5 && h < 10) return 'breakfast';
  if (h >= 10 && h < 14) return 'lunch';
  if (h >= 17 && h < 21) return 'dinner';
  return 'snack';
}

function parsedFoodsToItems(foods: DietParseCard['payload']['foods']): FoodItem[] {
  return foods.map((food, index) => ({
    id: `pending-${Date.now()}-${index}`,
    name: food.name,
    amount: food.amount,
    unit: food.unit,
    amountGrams: food.amount_grams,
    cookingMethod: food.cooking_method ?? undefined,
    calories: food.calories,
    protein: food.protein,
    fat: food.fat,
    carbs: food.carbs,
    fiber: food.fiber ?? undefined,
    sodium: food.sodium ?? undefined,
    dataSource: food.data_source,
  }));
}

function syncDietParseToPending(card: ChatCard, sessionId: string | null): void {
  if (card.type !== 'diet_parse') return;
  const { foods, meal_type, suggested_date, operation } = (card as DietParseCard).payload;
  if (!foods || foods.length === 0) return;
  useDietStore.getState().setPending({
    date: suggested_date ?? localTodayStr(),
    mealType: meal_type ?? inferMealTypeByTime(),
    foods: parsedFoodsToItems(foods),
    operation: operation ?? 'replace',
    cardId: getCardId(card),
    sessionId: sessionId ?? undefined,
    createdAt: Date.now(),
  });
}

function syncBodyParseToPending(card: ChatCard, sessionId: string | null): void {
  if (card.type !== 'body_parse') return;
  const payload = (card as BodyParseCard).payload;
  if (!payload.record_type) return;
  useBodyPendingStore.getState().setPending({
    date: payload.suggested_date ?? localTodayStr(),
    recordType: payload.record_type,
    operation: payload.operation ?? 'replace',
    cardId: getCardId(card),
    sessionId: sessionId ?? undefined,
    createdAt: Date.now(),
    waterAmount: payload.water_amount ?? undefined,
    sleepBedTime: payload.sleep_bed_time ?? undefined,
    sleepWakeTime: payload.sleep_wake_time ?? undefined,
    sleepQuality: payload.sleep_quality ?? undefined,
    exerciseType: payload.exercise_type ?? undefined,
    exerciseDuration: payload.exercise_duration ?? undefined,
    bowelTime: payload.bowel_time ?? undefined,
    bowelStatus: payload.bowel_status ?? undefined,
  });
}

function messageText(message: ChatMessage): string {
  if (message.content.trim()) {
    return message.content.trim();
  }
  return (message.segments ?? [])
    .filter((segment): segment is Extract<MessageSegment, { kind: 'text' }> => segment.kind === 'text')
    .map((segment) => segment.content)
    .join('')
    .trim();
}

function toTranscript(messages: ChatMessage[]): BackendTranscriptMessage[] {
  return messages.flatMap((message) => {
    const role = (message.role === 'user' ? 'user' : message.role === 'system' ? 'system' : 'assistant') as BackendTranscriptMessage['role'];
    const items: BackendTranscriptMessage[] = [];
    const content = messageText(message);
    if (content.length > 0) {
      items.push({ role, content });
    }
    for (const segment of message.segments ?? []) {
      if (segment.kind === 'card' && segment.card.type === 'plan_draft') {
        items.push({
          role: 'system',
          content: `[plan_draft] ${JSON.stringify(segment.card.payload.draft)}`,
        });
      }
    }
    return items;
  });
}

export function usePlanConversation() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [cardStatus, setCardStatusMap] = useState<Map<string, CardStatus>>(new Map());
  const streamRef = useRef<MockStreamHandle | null>(null);
  const sessionIdRef = useRef<string | null>(null);

  const setCardStatus = useCallback((cardId: string, status: CardStatus) => {
    setCardStatusMap((prev) => {
      const next = new Map(prev);
      next.set(cardId, status);
      return next;
    });
  }, []);

  const updateLastAssistant = useCallback((updater: (message: ChatMessage) => ChatMessage) => {
    setMessages((prev) => {
      const next = [...prev];
      for (let index = next.length - 1; index >= 0; index -= 1) {
        const item = next[index];
        if (item.role === 'assistant' || item.role === 'ai') {
          next[index] = updater(item);
          break;
        }
      }
      return next;
    });
  }, []);

  const wireStream = useCallback(
    (handle: MockStreamHandle) => {
      handle.on('meta', ({ session_id }) => {
        if (session_id) {
          sessionIdRef.current = session_id;
          setSessionId(session_id);
        }
      });
      handle.on('status', ({ label }) => {
        updateLastAssistant((message) => ({ ...message, status: label }));
      });
      handle.on('text_delta', ({ content }) => {
        updateLastAssistant((message) => {
          const segments = [...(message.segments ?? [])];
          const last = segments[segments.length - 1];
          if (last?.kind === 'text') {
            segments[segments.length - 1] = { kind: 'text', content: last.content + content };
          } else {
            segments.push({ kind: 'text', content });
          }
          return { ...message, status: null, segments };
        });
      });
      handle.on('choice', (prompt: ChoicePrompt) => {
        updateLastAssistant((message) => ({
          ...message,
          status: null,
          segments: [...(message.segments ?? []), { kind: 'choice', prompt }],
        }));
      });
      handle.on('card', ({ card }) => {
        setCardStatus(getCardId(card), 'pending');
        syncDietParseToPending(card, sessionIdRef.current);
        syncBodyParseToPending(card, sessionIdRef.current);
        updateLastAssistant((message) => ({
          ...message,
          status: null,
          segments: [...(message.segments ?? []), { kind: 'card', card: card as ChatCard }],
        }));
      });
      handle.on('done', () => {
        updateLastAssistant((message) => ({ ...message, isStreaming: false, status: null }));
        setIsStreaming(false);
        streamRef.current = null;
      });
      handle.on('error', ({ code, message }) => {
        updateLastAssistant((item) => ({
          ...item,
          isStreaming: false,
          status: null,
          error: { code, message },
        }));
        setIsStreaming(false);
        streamRef.current = null;
      });
    },
    [setCardStatus, updateLastAssistant]
  );

  const dispatch = useCallback(
    (payload: Record<string, unknown>, userDisplayText: string) => {
      const baseMessages = messages;
      const nextUser: ChatMessage = {
        id: `plan-user-${Date.now()}`,
        role: 'user',
        content: userDisplayText,
        timestamp: new Date().toISOString(),
      };
      const nextAssistant: ChatMessage = {
        id: `plan-ai-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        segments: [],
        tools: [],
        isStreaming: true,
        status: null,
      };
      setMessages([...baseMessages, nextUser, nextAssistant]);
      setIsStreaming(true);

      const transcript = toTranscript([...baseMessages, nextUser]);
      const handle = createSSEStream(
        {
          ...payload,
          session_id: sessionId,
          messages: transcript,
        },
        { path: '/plans/stream', method: 'POST', idleTimeoutMs: 120_000 }
      );
      streamRef.current = handle;
      wireStream(handle);
      handle.start();
    },
    [messages, sessionId, wireStream]
  );

  const send = useCallback(
    (text: string) => {
      dispatch({ type: 'text', message: text }, text);
    },
    [dispatch]
  );

  const sendChoice = useCallback(
    (promptId: string, value: string, freeText?: string) => {
      dispatch(
        {
          type: 'choice_response',
          prompt_id: promptId,
          selected_value: value,
          free_text: freeText,
        },
        freeText || value
      );
    },
    [dispatch]
  );

  const sendCardAction = useCallback(
    (card: ChatCard, actionId: string, label: string) => {
      const cardId = getCardId(card);
      setCardStatus(cardId, actionId.startsWith('cancel_') ? 'cancelled' : 'submitted');
      dispatch(
        {
          type: 'card_action',
          card_id: cardId,
          action_id: actionId,
          action_payload: card.payload,
          message: label,
        },
        label
      );
    },
    [dispatch, setCardStatus]
  );

  const reset = useCallback(() => {
    streamRef.current?.cancel();
    streamRef.current = null;
    setMessages([]);
    setIsStreaming(false);
    sessionIdRef.current = null;
    setSessionId(null);
    setCardStatusMap(new Map());
  }, []);

  return useMemo(
    () => ({
      messages,
      isStreaming,
      send,
      sendChoice,
      sendCardAction,
      reset,
      cardStatus,
      sessionId,
    }),
    [cardStatus, isStreaming, messages, reset, send, sendCardAction, sendChoice, sessionId]
  );
}
