// 真实 SSE 客户端：与 streamingMock 同一接口，前端组件零改动切换。
// 任务规格: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T5
// 设计参考: docs/plans/2026-05-21-streaming-chat-design.md §15.2

import EventSource from 'react-native-sse';
import { supabase } from '@core/supabase/client';
import { getApiBaseUrl } from '@core/api/apiBaseUrl';

import type {
  MockStreamHandle,
  StreamEvent,
  StreamEventData,
  StreamEventType,
  StreamHandler,
} from '../demo/types';

/**
 * 流式 chat 端点的请求体。
 *
 * 与后端 ``app.schemas.chat.ChatStreamRequest`` 字段对齐。
 */
export interface ChatStreamRequest {
  session_id?: string | null;
  type?: 'text' | 'card_action' | 'choice_response';

  // type=text
  message?: string;
  context?: { image_url?: string | null; referenced_date?: string | null };

  // type=card_action
  card_id?: string;
  action_id?: string;
  action_payload?: Record<string, unknown>;

  // type=choice_response
  prompt_id?: string;
  selected_value?: string;
  free_text?: string;
}

/**
 * 自定义事件名集合（必须与后端 :class:`StreamEventType` 对齐）。
 */
const CUSTOM_EVENT_TYPES = [
  'meta',
  'status',
  'tool_call',
  'tool_result',
  'text_delta',
  'choice',
  'card',
  'done',
  'error',
  'heartbeat',
] as const;

type RNSEventType = (typeof CUSTOM_EVENT_TYPES)[number];

/**
 * 创建一个真实 SSE 流，与 ``createMockStream`` 一致的 handle 接口。
 *
 * 实现要点：
 * - POST 起 SSE，body 为 ``ChatStreamRequest``
 * - 自动从 supabase 取 access_token 注入 Bearer
 * - 内部维护 30s idle timer，任何事件到达都 reset
 * - cancel() 立即关闭底层 EventSource，listeners 不再触发
 * - 复用与 mock 同一份 listener API（``on(type, handler)``）
 *
 * 注意：``react-native-sse`` 的 ``addEventListener`` 给出的 ``data`` 是 string，
 * 我们需要 JSON.parse 后再分发。
 */
export function createSSEStream(
  payload: ChatStreamRequest,
  options?: { idleTimeoutMs?: number; path?: string }
): MockStreamHandle {
  const idleTimeoutMs = options?.idleTimeoutMs ?? 30_000;
  const path = options?.path ?? '/ai/chat';
  const listeners = new Map<StreamEventType, Set<StreamHandler<StreamEventType>>>();

  let source: EventSource<RNSEventType> | null = null;
  let started = false;
  let cancelled = false;
  let idleTimer: ReturnType<typeof setTimeout> | null = null;

  function emit<T extends StreamEventType>(type: T, data: StreamEventData<T>): void {
    if (cancelled) return;
    const set = listeners.get(type);
    if (!set) return;
    set.forEach((handler) => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (handler as any)(data);
      } catch (err) {
        // 单个 handler 出错不应阻断其他 handler
        // eslint-disable-next-line no-console
        console.warn('[sse-stream] handler error', err);
      }
    });
    resetIdleTimer();
  }

  function resetIdleTimer(): void {
    if (idleTimer) clearTimeout(idleTimer);
    if (cancelled) return;
    idleTimer = setTimeout(() => {
      if (cancelled) return;
      emit('error', {
        code: 'IDLE_TIMEOUT',
        message: '后端无响应，请重试',
      });
      cleanup();
    }, idleTimeoutMs);
  }

  function cleanup(): void {
    if (idleTimer) {
      clearTimeout(idleTimer);
      idleTimer = null;
    }
    if (source) {
      source.removeAllEventListeners();
      source.close();
      source = null;
    }
  }

  async function connect(): Promise<void> {
    // 1. 取 token
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (!token) {
      emit('error', {
        code: 'AUTH_TOKEN_MISSING',
        message: '未登录或会话已过期',
      });
      return;
    }

    // 2. 建 EventSource（POST + body）
    const url = `${getApiBaseUrl()}${path}`;
    source = new EventSource<RNSEventType>(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(payload),
      // 不要内置轮询；后端流式
      pollingInterval: 0,
    });

    // 3. 注册 native 错误事件
    source.addEventListener('open', () => {
      resetIdleTimer();
    });

    source.addEventListener('error', (ev) => {
      if (cancelled) return;
      const message =
        ev.type === 'error' && 'message' in ev
          ? String((ev as { message?: string }).message ?? 'SSE 连接出错')
          : '连接异常';
      emit('error', { code: 'SSE_CONNECTION_ERROR', message });
      cleanup();
    });

    source.addEventListener('close', () => {
      // EventSource 主动关闭（done 事件后调用 close 也会触发）
      cleanup();
    });

    // 4. 注册业务事件
    CUSTOM_EVENT_TYPES.forEach((evtName) => {
      source!.addEventListener(evtName, (ev) => {
        if (cancelled) return;
        const raw = (ev as { data?: string | null }).data;
        if (!raw) {
          emit(evtName as StreamEventType, {} as StreamEventData<StreamEventType>);
          return;
        }
        try {
          const parsed = JSON.parse(raw);
          emit(evtName as StreamEventType, parsed);
          // done 事件后主动关闭
          if (evtName === 'done') {
            cleanup();
          }
        } catch (err) {
          // eslint-disable-next-line no-console
          console.warn('[sse-stream] failed to parse event data', evtName, raw);
        }
      });
    });
  }

  return {
    start() {
      if (started || cancelled) return;
      started = true;
      // 异步启动：取 token + 建连
      void connect().catch((err) => {
        // eslint-disable-next-line no-console
        console.error('[sse-stream] connect failed', err);
        emit('error', {
          code: 'SSE_CONNECT_FAILED',
          message: err?.message ?? '连接失败',
        });
        cleanup();
      });
    },
    cancel() {
      cancelled = true;
      cleanup();
    },
    on(type, handler) {
      if (!listeners.has(type)) {
        listeners.set(type, new Set());
      }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      listeners.get(type)!.add(handler as any);
    },
    off(type, handler) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      listeners.get(type)?.delete(handler as any);
    },
  };
}

// 重新导出类型供调用方共用
export type { MockStreamHandle, StreamEvent, StreamEventType };
