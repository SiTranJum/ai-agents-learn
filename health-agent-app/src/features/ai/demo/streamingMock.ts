// SSE 流 Mock 调度器 + 6 个场景脚本
// 参考: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T1
// 参考: docs/plans/2026-05-21-streaming-chat-design.md §16.4

import type {
  MockStreamHandle,
  ScenarioName,
  ScheduledEvent,
  StreamEvent,
  StreamEventType,
  StreamHandler,
} from './types';

const IDLE_TIMEOUT_MS = 30_000;

/**
 * 创建一个 Mock 流。返回的 handle 与未来真实 SSE 客户端接口一致。
 *
 * 实现要点：
 * - 用累积绝对时间防止 setTimeout 漂移误差
 * - cancel() 立即清空所有 pending timer
 * - 每个事件触发后 reset idle timer
 * - idle 超过 30s 自动 emit error
 *
 * @param scenario 场景名
 * @param round 第几段对话（multi-turn 时，第 1 段 = 1，用户应答后第 2 段 = 2）
 */
export function createMockStream(
  scenario: ScenarioName,
  round: number = 1
): MockStreamHandle {
  const events = buildScenario(scenario, round);
  const listeners = new Map<StreamEventType, Set<StreamHandler<StreamEventType>>>();
  const timers = new Set<ReturnType<typeof setTimeout>>();

  let cancelled = false;
  let started = false;
  let idleTimer: ReturnType<typeof setTimeout> | null = null;

  function emit<T extends StreamEventType>(
    type: T,
    data: Extract<StreamEvent, { type: T }>['data']
  ): void {
    if (cancelled) return;
    const set = listeners.get(type);
    if (!set) return;
    set.forEach((handler) => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (handler as any)(data);
      } catch (err) {
        // 静默吃掉单个 handler 的异常，避免影响其他事件
        // eslint-disable-next-line no-console
        console.warn('[mock-stream] handler error', err);
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
    }, IDLE_TIMEOUT_MS);
  }

  function clearAllTimers(): void {
    timers.forEach((t) => clearTimeout(t));
    timers.clear();
    if (idleTimer) {
      clearTimeout(idleTimer);
      idleTimer = null;
    }
  }

  return {
    start() {
      if (started || cancelled) return;
      started = true;
      resetIdleTimer();
      events.forEach((scheduled) => {
        const t = setTimeout(() => {
          timers.delete(t);
          if (cancelled) return;
          emit(scheduled.event.type, scheduled.event.data as never);
        }, scheduled.delay_ms);
        timers.add(t);
      });
    },
    cancel() {
      cancelled = true;
      clearAllTimers();
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

// ============ 场景脚本生成 ============

function buildScenario(scenario: ScenarioName, round: number): ScheduledEvent[] {
  switch (scenario) {
    case 'happy_path':
      return round === 1 ? happyPathRound1() : happyPathRound2();
    case 'failure_retry':
      return round === 1 ? failureRetryRound1() : happyPathRound2();
    case 'mid_cancel':
      return midCancel();
    case 'free_text_response':
      return round === 1 ? happyPathRound1() : freeTextRound2();
    case 'multi_card_confirm':
      return multiCardConfirm(round);
    case 'idle_timeout':
      return idleTimeoutScript();
    default:
      return [];
  }
}

// 把整段中文文本切成"流式 token"（按字符切，每 50ms 一个 chunk，每 chunk 1-3 字符）
function tokenize(text: string, baseDelay: number, perTokenMs = 50): ScheduledEvent[] {
  const chunks: string[] = [];
  let i = 0;
  while (i < text.length) {
    // 简单按字符分组，标点单独成块
    const ch = text[i];
    const isPunct = /[，。！？、,.!?:：；;]/.test(ch);
    const len = isPunct ? 1 : 2;
    chunks.push(text.slice(i, i + len));
    i += len;
  }
  return chunks.map((content, idx) => ({
    delay_ms: baseDelay + idx * perTokenMs,
    event: { type: 'text_delta', data: { content } } as StreamEvent,
  }));
}

// ============ 场景 1: happy_path ============

function happyPathRound1(): ScheduledEvent[] {
  const events: ScheduledEvent[] = [
    {
      delay_ms: 0,
      event: { type: 'meta', data: { message_id: 'm_demo_1', session_id: 's_demo' } },
    },
    {
      delay_ms: 200,
      event: { type: 'status', data: { label: '正在识别意图...' } },
    },
    {
      delay_ms: 600,
      event: { type: 'status', data: { label: '正在分析饮食...' } },
    },
    {
      delay_ms: 900,
      event: {
        type: 'tool_call',
        data: { tool: 'search_food', label: '查找鸡胸肉营养...' },
      },
    },
    {
      delay_ms: 1700,
      event: {
        type: 'tool_result',
        data: { tool: 'search_food', summary: '✓ 已找到 (330kcal/100g)' },
      },
    },
  ];
  // text 流式：从 1900ms 开始
  const tokens1 = tokenize('我识别到了鸡胸肉 200g。', 1900);
  events.push(...tokens1);
  const last1 = tokens1[tokens1.length - 1].delay_ms + 200;
  const tokens2 = tokenize('请问是哪一餐？', last1);
  events.push(...tokens2);
  const last2 = tokens2[tokens2.length - 1].delay_ms + 200;
  events.push({
    delay_ms: last2,
    event: {
      type: 'choice',
      data: {
        prompt_id: 'p_meal_1',
        question: '请选择餐次',
        options: [
          { value: 'breakfast', label: '早餐' },
          { value: 'lunch', label: '午餐' },
          { value: 'dinner', label: '晚餐' },
          { value: 'snack', label: '加餐' },
        ],
        allow_free_text: true,
      },
    },
  });
  events.push({
    delay_ms: last2 + 100,
    event: { type: 'done', data: { message_id: 'm_demo_1' } },
  });
  return events;
}

function happyPathRound2(): ScheduledEvent[] {
  const events: ScheduledEvent[] = [
    {
      delay_ms: 0,
      event: { type: 'meta', data: { message_id: 'm_demo_2', session_id: 's_demo' } },
    },
    {
      delay_ms: 300,
      event: { type: 'status', data: { label: '正在生成饮食卡片...' } },
    },
  ];
  const tokens = tokenize('好的，已为你准备好午餐卡片：', 900);
  events.push(...tokens);
  const last = tokens[tokens.length - 1].delay_ms + 200;
  events.push({
    delay_ms: last,
    event: {
      type: 'card',
      data: {
        card: {
          type: 'diet_parse',
          payload: {
            foods: [
              {
                name: '鸡胸肉',
                amount: 200,
                unit: 'g',
                amount_grams: 200,
                calories: 330,
                protein: 62,
                fat: 7.2,
                carbs: 0,
                data_source: 'database',
              },
            ],
            meal_type: 'lunch',
            confidence: 0.92,
            nutrition_summary: {
              total_calories: 330,
              total_protein: 62,
              total_fat: 7.2,
              total_carbs: 0,
            },
          },
          actions: [
            { kind: 'confirm_create_diet_record', label: '确认保存' },
            { kind: 'edit_diet_items', label: '修改食物' },
          ],
        },
      },
    },
  });
  events.push({
    delay_ms: last + 100,
    event: { type: 'done', data: { message_id: 'm_demo_2' } },
  });
  return events;
}

// ============ 场景 2: failure_retry ============

function failureRetryRound1(): ScheduledEvent[] {
  const events: ScheduledEvent[] = [
    {
      delay_ms: 0,
      event: { type: 'meta', data: { message_id: 'm_fail_1', session_id: 's_demo' } },
    },
    {
      delay_ms: 200,
      event: { type: 'status', data: { label: '正在识别意图...' } },
    },
  ];
  const tokens = tokenize('我正在为你', 800);
  events.push(...tokens);
  const last = tokens[tokens.length - 1].delay_ms + 300;
  events.push({
    delay_ms: last,
    event: {
      type: 'error',
      data: { code: 'LLM_PROVIDER_ERROR', message: 'AI 服务暂时不可用' },
    },
  });
  return events;
}

// ============ 场景 3: mid_cancel ============
// 故意拉长，给用户足够时间点取消按钮

function midCancel(): ScheduledEvent[] {
  const events: ScheduledEvent[] = [
    {
      delay_ms: 0,
      event: { type: 'meta', data: { message_id: 'm_cancel', session_id: 's_demo' } },
    },
    {
      delay_ms: 200,
      event: { type: 'status', data: { label: '正在思考一个很长的回答...' } },
    },
  ];
  // 慢速吐 token：每 200ms 一个，给用户时间按取消
  const tokens = tokenize(
    '让我给你详细介绍一下健康饮食的原则：第一，膳食要均衡；第二，要控制总热量；第三，注意食物多样性；第四，多吃蔬菜水果；第五，规律饮食；第六，少吃油腻食物。',
    700,
    200
  );
  events.push(...tokens);
  const last = tokens[tokens.length - 1].delay_ms + 200;
  events.push({
    delay_ms: last,
    event: { type: 'done', data: { message_id: 'm_cancel' } },
  });
  return events;
}

// ============ 场景 4: free_text_response ============
// 第 1 段同 happy_path round1（让用户看到"自己输入"选项）
// 第 2 段：用户输入了自定义文本（如"宵夜"），AI 用相同卡片但 meal_type='snack'

function freeTextRound2(): ScheduledEvent[] {
  const events: ScheduledEvent[] = [
    {
      delay_ms: 0,
      event: { type: 'meta', data: { message_id: 'm_free_2', session_id: 's_demo' } },
    },
    {
      delay_ms: 200,
      event: { type: 'status', data: { label: '理解你的输入中...' } },
    },
  ];
  const tokens = tokenize('好的，已记为"宵夜"，归类到加餐：', 700);
  events.push(...tokens);
  const last = tokens[tokens.length - 1].delay_ms + 200;
  events.push({
    delay_ms: last,
    event: {
      type: 'card',
      data: {
        card: {
          type: 'diet_parse',
          payload: {
            foods: [
              {
                name: '鸡胸肉',
                amount: 200,
                unit: 'g',
                amount_grams: 200,
                calories: 330,
                protein: 62,
                fat: 7.2,
                carbs: 0,
                data_source: 'database',
              },
            ],
            meal_type: 'snack',
            confidence: 0.85,
            nutrition_summary: {
              total_calories: 330,
              total_protein: 62,
              total_fat: 7.2,
              total_carbs: 0,
            },
          },
          actions: [
            { kind: 'confirm_create_diet_record', label: '确认保存' },
            { kind: 'edit_diet_items', label: '修改食物' },
          ],
        },
      },
    },
  });
  events.push({
    delay_ms: last + 100,
    event: { type: 'done', data: { message_id: 'm_free_2' } },
  });
  return events;
}

// ============ 场景 5: multi_card_confirm ============
// 三段连续卡片确认：饮食 → 运动建议 → 睡眠建议

function multiCardConfirm(round: number): ScheduledEvent[] {
  if (round === 1) return happyPathRound2();

  if (round === 2) {
    const events: ScheduledEvent[] = [
      {
        delay_ms: 0,
        event: { type: 'meta', data: { message_id: 'm_multi_2', session_id: 's_demo' } },
      },
      { delay_ms: 200, event: { type: 'status', data: { label: '生成运动建议...' } } },
    ];
    const tokens = tokenize('看了你的午餐摄入，建议下午做一次运动：', 700);
    events.push(...tokens);
    const last = tokens[tokens.length - 1].delay_ms + 200;
    events.push({
      delay_ms: last,
      event: {
        type: 'card',
        data: {
          card: {
            type: 'exercise_suggestion',
            payload: {
              activity: '快走 30 分钟',
              estimated_calories: 180,
              best_time: '15:00-16:00',
            },
            actions: [
              { kind: 'confirm_create_exercise', label: '采纳' },
              { kind: 'skip', label: '不要' },
            ],
          },
        },
      },
    });
    events.push({ delay_ms: last + 100, event: { type: 'done', data: { message_id: 'm_multi_2' } } });
    return events;
  }

  // round === 3
  const events: ScheduledEvent[] = [
    {
      delay_ms: 0,
      event: { type: 'meta', data: { message_id: 'm_multi_3', session_id: 's_demo' } },
    },
    { delay_ms: 200, event: { type: 'status', data: { label: '生成睡眠建议...' } } },
  ];
  const tokens = tokenize('记得今晚 11 点前入睡，提示已为你设置：', 700);
  events.push(...tokens);
  const last = tokens[tokens.length - 1].delay_ms + 200;
  events.push({
    delay_ms: last,
    event: {
      type: 'card',
      data: {
        card: {
          type: 'sleep_reminder',
          payload: {
            bedtime: '23:00',
            target_hours: 8,
          },
          actions: [
            { kind: 'confirm_set_reminder', label: '好的' },
            { kind: 'skip', label: '不需要' },
          ],
        },
      },
    },
  });
  events.push({ delay_ms: last + 100, event: { type: 'done', data: { message_id: 'm_multi_3' } } });
  return events;
}

// ============ 场景 6: idle_timeout ============
// 流开始后什么都不发，30s 后 idle 计时器触发

function idleTimeoutScript(): ScheduledEvent[] {
  return [
    {
      delay_ms: 0,
      event: { type: 'meta', data: { message_id: 'm_idle', session_id: 's_demo' } },
    },
    {
      delay_ms: 300,
      event: { type: 'status', data: { label: '后端正在处理（请等待 30s 看超时）...' } },
    },
    // 然后无事件，等待 30s idle timer 触发 error
  ];
}
