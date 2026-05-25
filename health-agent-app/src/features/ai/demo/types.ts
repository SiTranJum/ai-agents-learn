// AI 流式 demo 类型定义
// 与未来真实 SSE 客户端类型同构，方便 T5 阶段无缝替换。
// 参考: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T1

import type { ChatCard } from '../types/ai.types';

// ============ 选项澄清协议 ============

export interface ChoiceOption {
  value: string;
  label: string;
  description?: string;
}

export interface ChoicePrompt {
  prompt_id: string;
  question?: string;
  options: ChoiceOption[];
  /** 是否允许"自己输入"作为兜底 */
  allow_free_text?: boolean;
}

// ============ SSE 事件定义 ============

export type StreamEvent =
  | { type: 'meta'; data: { message_id: string; session_id: string } }
  | { type: 'status'; data: { label: string } }
  | { type: 'tool_call'; data: { tool: string; label: string } }
  | { type: 'tool_result'; data: { tool: string; summary: string } }
  | { type: 'text_delta'; data: { content: string } }
  | { type: 'choice'; data: ChoicePrompt }
  | { type: 'card'; data: { card: ChatCard } }
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

// ============ 消息分段 ============
// 一条 AI 消息由若干 segment 组成（可跨多次 SSE 连接累积）

export interface ToolCallState {
  tool: string;
  label: string;
  /** 完成时填充 */
  summary?: string;
  /** pending 状态显示旋转图标，done 显示 ✓ */
  state: 'pending' | 'done';
}

export type MessageSegment =
  | { kind: 'text'; content: string }
  | { kind: 'card'; card: ChatCard }
  | { kind: 'choice'; prompt: ChoicePrompt; selectedValue?: string; freeText?: string };

export interface AIStreamingMessage {
  id: string;
  role: 'assistant';
  /** 当前正在流出的状态文案；null 表示无 */
  status: string | null;
  /** 工具调用状态（按 tool 名去重） */
  tools: ToolCallState[];
  /** 组成消息的所有 segment */
  segments: MessageSegment[];
  /** true=流式中，false=已 done 或被 cancel/error */
  isStreaming: boolean;
  /** 错误信息（流被错误终止时） */
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
