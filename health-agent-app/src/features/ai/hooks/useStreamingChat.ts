// useStreamingChat: 流式聊天 hook
// T6 从 demo/StreamingDemoScreen 提炼，封装 wireStreamHandlers + 状态管理
// 设计参考: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T6

import { useState, useRef, useCallback, useEffect } from 'react';
import type {
  ChatMessage,
  ChatCard,
  ChoicePrompt,
  MessageSegment,
  ToolCallState,
} from '../types/ai.types';
import { createSSEStream } from '../services/streamingClient';
import type { MockStreamHandle } from '../demo/types';

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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const streamRef = useRef<MockStreamHandle | null>(null);
  const cardStatusRef = useRef<Map<string, 'pending' | 'submitted' | 'cancelled'>>(
    new Map()
  );

  // 卸载时关闭活动流
  useEffect(() => {
    return () => {
      streamRef.current?.cancel();
    };
  }, []);

  // 取最后一条 AI 消息（流式中的）
  const updateLastAI = useCallback((updater: (msg: ChatMessage) => ChatMessage) => {
    setMessages((prev) => {
      const arr = [...prev];
      for (let i = arr.length - 1; i >= 0; i--) {
        const m = arr[i];
        if (m.role === 'assistant' || m.role === 'ai') {
          arr[i] = updater(m);
          return arr;
        }
      }
      return prev;
    });
  }, []);

  // 把所有 SSE 事件 handler 注册到给定 handle 上
  // 复制自 demo/StreamingDemoScreen 的 wireStreamHandlers
  const wireStreamHandlers = useCallback(
    (handle: MockStreamHandle) => {
      handle.on('meta', ({ session_id }) => {
        if (session_id) {
          setSessionId(session_id);
        }
      });

      handle.on('status', ({ label }) => {
        updateLastAI((msg) => ({ ...msg, status: label }));
      });

      handle.on('tool_call', ({ tool, label }) => {
        updateLastAI((msg) => {
          const without = (msg.tools || []).filter((t) => t.tool !== tool);
          return {
            ...msg,
            tools: [...without, { tool, label, state: 'pending' as const }],
          };
        });
      });

      handle.on('tool_result', ({ tool, summary }) => {
        updateLastAI((msg) => ({
          ...msg,
          tools: (msg.tools || []).map((t) =>
            t.tool === tool ? { ...t, summary, state: 'done' as const } : t
          ),
        }));
      });

      handle.on('text_delta', ({ content }) => {
        updateLastAI((msg) => {
          const segs = [...(msg.segments || [])];
          const last = segs[segs.length - 1];
          if (last && last.kind === 'text') {
            segs[segs.length - 1] = {
              kind: 'text',
              content: last.content + content,
            };
          } else {
            segs.push({ kind: 'text', content });
          }
          return { ...msg, segments: segs, status: null };
        });
      });

      handle.on('choice', (prompt: ChoicePrompt) => {
        updateLastAI((msg) => ({
          ...msg,
          status: null,
          segments: [
            ...(msg.segments || []),
            { kind: 'choice', prompt } satisfies MessageSegment,
          ],
        }));
      });

      handle.on('card', ({ card }) => {
        cardStatusRef.current.set(getCardId(card), 'pending');
        updateLastAI((msg) => ({
          ...msg,
          status: null,
          segments: [
            ...(msg.segments || []),
            { kind: 'card', card } satisfies MessageSegment,
          ],
        }));
      });

      handle.on('done', () => {
        updateLastAI((msg) => ({ ...msg, isStreaming: false, status: null }));
        streamRef.current = null;
      });

      handle.on('error', ({ code, message }) => {
        updateLastAI((msg) => ({
          ...msg,
          isStreaming: false,
          status: null,
          error: { code, message },
        }));
        streamRef.current = null;
      });
    },
    [updateLastAI]
  );

  // 通用流式请求分发：创建占位 AI 消息 → 启动 SSE 流 → 注册事件处理器
  const _dispatch = useCallback(
    (payload: any) => {
      // 添加用户消息
      const userMsg: ChatMessage = {
        id: `u_${Date.now()}`,
        role: 'user',
        content: payload.message || `[${payload.type}]`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      // 创建占位 AI 消息
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
      setMessages((prev) => [...prev, aiMsg]);

      // 启动 SSE 流
      const handle = createSSEStream(payload);
      streamRef.current = handle;
      wireStreamHandlers(handle);
      handle.start();
    },
    [wireStreamHandlers]
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
      });
    },
    [_dispatch, sessionId]
  );

  const sendCardAction = useCallback(
    (card: ChatCard, actionId: string) => {
      _dispatch({
        type: 'card_action',
        card_id: getCardId(card),
        action_id: actionId,
        action_payload: card.payload,
        session_id: sessionId,
      });
    },
    [_dispatch, sessionId]
  );

  const cancel = useCallback(() => {
    streamRef.current?.cancel();
  }, []);

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
    cardStatus: cardStatusRef.current,
    sessionId,
  };
}

// 辅助：生成卡片唯一 ID
function getCardId(card: ChatCard): string {
  return `card_${card.type}_${Date.now()}`;
}
