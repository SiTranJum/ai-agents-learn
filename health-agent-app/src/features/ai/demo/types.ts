// AI 流式 demo 类型定义
// 流式核心类型已升级到 ai.types.ts（T6），这里只保留 demo 专用类型。
// 参考: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T1, §T6

import type {
  ChatCard,
  ChoicePrompt,
  MessageSegment,
  ToolCallState,
} from '../types/ai.types';

// Re-export 流式核心类型，保持 demo 旧 import 路径可用
export type {
  ChoiceOption,
  ChoicePrompt,
  MessageSegment,
  ToolCallState,
} from '../types/ai.types';

// ============ SSE 事件定义 ============

export type StreamEvent =
  | { type: 'meta'; data: { message_id: string; session_id: string } }
  | { type: 'status'; data: { label: string } }
  | { type: 'tool_call'; data: { tool: string; label: string } }
  | { type: 'tool_result'; data: { tool: string; summary: string } }
  | { type: 'text_delta'; data: { content: string } }
  | { type: 'choice'; data: ChoicePrompt }
  | { type: 'card'; data: { card: ChatCard } }
  | { type: 'paused'; data: { prompt_id: string; kind: 'choice' | 'card'; domain?: string | null } }
  | { type: 'done'; data: { message_id: string } }
  | { type: 'error'; data: { code: string; message: string } }
  | { type: 'heartbeat'; data: Record<string, never> };

export type StreamEventType = StreamEvent['type'];

/**
 * 类型工具：根据事件名取出 data 类型。
 * 例：StreamEventData<'text_delta'> = { content: string }
 */
export type StreamEventData<T extends StreamEventType> = Extract<
  StreamEvent,
  { type: T }
>['data'];

// ============ 消息分段（demo 专用包装） ============
// AIStreamingMessage 是 demo 页内部的消息状态容器。
// 正式 ChatMessage（types/ai.types.ts）已包含 segments / status / tools / isStreaming
// 等流式字段，AIStreamingMessage 与 ChatMessage 字段一致但 role 限定为 'assistant'。

export interface AIStreamingMessage {
  id: string;
  role: 'assistant';
  status: string | null;
  tools: ToolCallState[];
  segments: MessageSegment[];
  isStreaming: boolean;
  error?: { code: string; message: string };
}

export interface UserMessage {
  id: string;
  role: 'user';
  content: string;
}

export type DemoMessage = AIStreamingMessage | UserMessage;

// ============ Mock 流句柄 ============

export type StreamHandler<T extends StreamEventType> = (
  data: StreamEventData<T>
) => void;

/**
 * 与未来真实 SSE 客户端 API 一致：start / cancel / on / off。
 * T5 阶段会用 react-native-sse 实现一个同名接口的版本，
 * demo 页代码无需任何改动即可切换到真实流。
 */
export interface MockStreamHandle {
  start: () => void;
  cancel: () => void;
  on: <T extends StreamEventType>(type: T, handler: StreamHandler<T>) => void;
  off: <T extends StreamEventType>(type: T, handler: StreamHandler<T>) => void;
}

// ============ 场景定义 ============

export type ScenarioName =
  | 'happy_path' // 基础流程：text → choice → text → card
  | 'failure_retry' // 流中途报错，引导重试
  | 'mid_cancel' // 用户中途点"停止"
  | 'free_text_response' // choice 选了"自己输入"分支
  | 'multi_card_confirm' // 连续多张卡片确认（饮食 → 运动 → 睡眠）
  | 'idle_timeout'; // 30s 静默触发 idle 错误

/** 给场景中预定义事件加相对延迟 */
export interface ScheduledEvent {
  delay_ms: number;
  event: StreamEvent;
}
