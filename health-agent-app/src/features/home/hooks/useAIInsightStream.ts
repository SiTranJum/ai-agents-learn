// useAIInsightStream - 首页 AI 洞察流式 hook（T10）
// 替换 useAIInsight（React Query），改用 SSE 流式获取每日建议
// 缓存命中时后端直接 emit card，无 status；未命中时先 status 再 card

import { useState, useEffect, useRef, useCallback } from 'react';
import { createSSEStream } from '@features/ai/services/streamingClient';
import type { MockStreamHandle } from '@features/ai/demo/types';

interface UseAIInsightStreamReturn {
  insight: string | null;
  isStreaming: boolean;
  status: string | null;
  error: string | null;
  refetch: () => void;
}

export function useAIInsightStream(): UseAIInsightStreamReturn {
  const [insight, setInsight] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const handleRef = useRef<MockStreamHandle | null>(null);
  const [tick, setTick] = useState(0);

  // 组件挂载 / refetch 时启动 SSE 流。
  // 注意 deps 不包含 insight：避免 insight 变化时重建 callback 引发不必要的影响。
  const start = useCallback(() => {
    handleRef.current?.cancel();
    setIsStreaming(true);
    setStatus(null);
    setError(null);
    setInsight(null);

    const handle = createSSEStream(
      {},
      {
        path: '/suggestions/daily',
        method: 'GET',
        idleTimeoutMs: 120_000,
        endpoint: 'suggestions/daily',
      }
    );
    handleRef.current = handle;

    handle.on('status', ({ label }) => setStatus(label));

    handle.on('card', ({ card }) => {
      // card 是 SuggestionItem，取 content 字段作为洞察文本
      const content = (card as Record<string, unknown>).content;
      if (typeof content === 'string' && content) {
        setInsight(content);
      }
    });

    handle.on('done', () => {
      setIsStreaming(false);
      setStatus(null);
      handleRef.current = null;
    });

    handle.on('error', ({ message }) => {
      setIsStreaming(false);
      setStatus(null);
      // 不再静默回落到默认文案，把错误暴露给 UI 让用户清楚知道是失败了
      setError(message || 'AI 服务暂时不可用');
      handleRef.current = null;
    });

    handle.start();
  }, []);

  // 组件挂载时自动开始
  useEffect(() => {
    start();
    return () => {
      handleRef.current?.cancel();
    };
  }, [tick, start]);

  const refetch = useCallback(() => {
    setTick((n) => n + 1);
  }, []);

  return { insight, isStreaming, status, error, refetch };
}

