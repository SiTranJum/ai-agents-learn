// 前端 SSE 流监控埋点（T15）
//
// 与后端 app/streaming/metrics.py 对齐。当前用 console.info 输出结构化日志
// 前缀 `[METRIC]`，方便开发期排查。生产环境可改为对接 Sentry / Datadog /
// 自建 analytics service，只需替换 _emit 函数。
//
// 指标列表（与后端 endpoint 标签共用）：
// - chat_stream_started        流发起
// - chat_stream_first_event_ms 首个业务事件延迟（不计 meta/heartbeat）
// - chat_stream_total_ms       流总时长
// - chat_stream_done           正常完成
// - chat_stream_error          异常终止
// - chat_stream_cancelled      用户/客户端主动取消

interface MetricFields {
  endpoint: string;
  elapsed_ms?: number;
  event_count?: number;
  code?: string;
}

function _emit(metric: string, fields: MetricFields): void {
  // 用 console.info（不是 warn），避免 dev 环境刷红
  // eslint-disable-next-line no-console
  console.info(
    '[METRIC]',
    metric,
    Object.entries(fields)
      .map(([k, v]) => `${k}=${v}`)
      .join(' ')
  );
}

export function recordStarted(endpoint: string): void {
  _emit('chat_stream_started', { endpoint });
}

export function recordFirstEvent(endpoint: string, elapsedMs: number): void {
  _emit('chat_stream_first_event_ms', { endpoint, elapsed_ms: Math.round(elapsedMs) });
}

export function recordDone(endpoint: string, elapsedMs: number, eventCount: number): void {
  _emit('chat_stream_done', {
    endpoint,
    elapsed_ms: Math.round(elapsedMs),
    event_count: eventCount,
  });
}

export function recordError(endpoint: string, elapsedMs: number, code: string): void {
  _emit('chat_stream_error', {
    endpoint,
    elapsed_ms: Math.round(elapsedMs),
    code,
  });
}

export function recordCancelled(endpoint: string, elapsedMs: number): void {
  _emit('chat_stream_cancelled', { endpoint, elapsed_ms: Math.round(elapsedMs) });
}

// ============ Tracking 上下文 ============

/**
 * 单次流的累积指标。由 createSSEStream 持有，事件到达时调 mark*，
 * 流结束时调 finalize 自动 emit done/error/cancelled。
 */
export class StreamMetrics {
  readonly endpoint: string;
  private readonly startedAt: number;
  private firstEventAt: number | null = null;
  private eventCount = 0;
  private finalized = false;

  constructor(endpoint: string) {
    this.endpoint = endpoint;
    this.startedAt = performance.now();
    recordStarted(endpoint);
  }

  markEvent(eventType: string): void {
    this.eventCount += 1;
    if (this.firstEventAt === null && eventType !== 'meta' && eventType !== 'heartbeat') {
      this.firstEventAt = performance.now();
      recordFirstEvent(this.endpoint, this.firstEventAt - this.startedAt);
    }
  }

  finalizeDone(): void {
    if (this.finalized) return;
    this.finalized = true;
    recordDone(this.endpoint, performance.now() - this.startedAt, this.eventCount);
  }

  finalizeError(code: string): void {
    if (this.finalized) return;
    this.finalized = true;
    recordError(this.endpoint, performance.now() - this.startedAt, code);
  }

  finalizeCancelled(): void {
    if (this.finalized) return;
    this.finalized = true;
    recordCancelled(this.endpoint, performance.now() - this.startedAt);
  }
}
