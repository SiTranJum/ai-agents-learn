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
} from '../types/ai.types';
import { createSSEStream } from '../services/streamingClient';
import type { MockStreamHandle } from '../demo/types';
import { useAIStore } from '../store/aiStore';

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

// 辅助：生成卡片唯一 ID（与 demo 保持一致）
function getCardId(card: ChatCard): string {
  return `card_${card.type}_${JSON.stringify(card.payload).slice(0, 32)}`;
}
