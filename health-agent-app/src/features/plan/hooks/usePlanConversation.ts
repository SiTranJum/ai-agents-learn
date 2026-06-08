import { useCallback, useMemo, useRef, useState } from 'react';

import { createSSEStream } from '@features/ai/services/streamingClient';
import type { ChatCard, ChatMessage, ChoicePrompt, MessageSegment } from '@features/ai/types/ai.types';
import { getCardId } from '@features/ai/utils/cardId';
import type { MockStreamHandle } from '@features/ai/demo/types';

type CardStatus = 'pending' | 'submitted' | 'cancelled';

interface BackendTranscriptMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
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
  return messages
    .map((message) => ({
      role: (message.role === 'user' ? 'user' : message.role === 'system' ? 'system' : 'assistant') as BackendTranscriptMessage['role'],
      content: messageText(message),
    }))
    .filter((message) => message.content.length > 0);
}

export function usePlanConversation() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [cardStatus, setCardStatusMap] = useState<Map<string, CardStatus>>(new Map());
  const streamRef = useRef<MockStreamHandle | null>(null);

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
