// AI Service - Mock 实现
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §8

import type { ChatMessage, NutritionData } from '../types/ai.types';
import { apiClient } from '@core/api/client';
import type { ChatCard, ChatResponseRaw } from '../types/ai.types';
import {
  classifyIntent,
  estimateNutrition,
  NUTRITION_DB,
} from '../mocks/aiMocks';

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

let _id = 0;
const makeId = () => `m-${Date.now()}-${++_id}`;
const now = (): string =>
  new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

function mapCardActions(cards?: ChatCard[]) {
  return cards?.flatMap((card) =>
    card.actions.map((action) => ({
      key: action.kind,
      label:
        action.label ??
        (action.kind === 'confirm_create_diet_record'
          ? '确认保存'
          : action.kind === 'edit_diet_items'
            ? '修改食物'
            : action.kind),
      action: action.kind === 'confirm_create_diet_record' ? 'confirm' as const : 'navigate' as const,
      variant: action.kind === 'confirm_create_diet_record' ? 'primary' as const : 'secondary' as const,
      params: { card },
    }))
  );
}

function mapBackendReply(raw: ChatResponseRaw): ChatMessage {
  const message = raw.messages[0];
  return {
    id: message.id ?? makeId(),
    role: message.role === 'assistant' ? 'ai' : message.role,
    content: message.content,
    timestamp: message.created_at
      ? new Date(message.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      : now(),
    cards: message.cards,
    actions: mapCardActions(message.cards),
  };
}

export interface AIService {
  /**
   * 模拟发送消息给 AI，返回 AI 回复（可能携带 actions / nutritionData）
   */
  sendMessage(
    message: string,
    sessionId?: string | null,
    context?: Record<string, unknown>
  ): Promise<{ reply: ChatMessage; sessionId?: string; nutritionData?: NutritionData }>;

  /**
   * 营养查询
   */
  queryNutrition(foodName: string, amount?: number): Promise<NutritionData>;
}

export const aiService: AIService = {
  async sendMessage(message, sessionId, context) {
    try {
      const raw = await apiClient.post<ChatResponseRaw>('/ai/chat', {
        session_id: sessionId ?? null,
        message,
        context,
      });
      return { reply: mapBackendReply(raw), sessionId: raw.session_id };
    } catch {
      // 开发阶段允许后端未启动/未登录时回退到本地 mock，保证学习 UI 可用。
    }

    await delay(700);

    const { intent, matchedFood } = classifyIntent(message);

    switch (intent) {
      case 'nutrition_query': {
        const food = matchedFood ?? message.trim();
        const data = NUTRITION_DB[food] ?? estimateNutrition(food);
        return {
          reply: {
            id: makeId(),
            role: 'ai',
            timestamp: now(),
            content: `${data.foodName}（${data.amount}${data.unit}）的营养如下：约 ${data.calories} kcal，蛋白质 ${data.protein}g，脂肪 ${data.fat}g，碳水 ${data.carbs}g。`,
            actions: [
              {
                key: 'view_nutrition',
                label: '查看详情',
                action: 'show_nutrition',
                variant: 'primary',
                params: { foodName: data.foodName },
              },
              {
                key: 'add_to_diet',
                label: '记录到饮食',
                action: 'navigate',
                variant: 'secondary',
                params: { screen: 'DietEdit', foodName: data.foodName },
              },
            ],
          },
          nutritionData: data,
        };
      }
      case 'plan_suggestion':
        return {
          reply: {
            id: makeId(),
            role: 'ai',
            timestamp: now(),
            content:
              '我可以帮你制定一份个性化的健康计划，包括目标体重、饮食安排和运动计划。要不要现在创建？',
            actions: [
              {
                key: 'create_plan',
                label: '帮我制定计划',
                action: 'navigate',
                variant: 'primary',
                params: { screen: 'PlanCreate' },
              },
            ],
          },
        };
      case 'health_advice':
        return {
          reply: {
            id: makeId(),
            role: 'ai',
            timestamp: now(),
            content:
              '基于你最近的数据，我建议：\n· 每日热量摄入控制在 1800 kcal 以内\n· 增加蛋白质比例至 25%\n· 保证 7 小时以上睡眠\n· 每周至少 3 次有氧运动',
          },
        };
      case 'greeting':
        return {
          reply: {
            id: makeId(),
            role: 'ai',
            timestamp: now(),
            content: '你好呀～今天感觉怎么样？要不要先看一眼今日数据概况？',
          },
        };
      default:
        return {
          reply: {
            id: makeId(),
            role: 'ai',
            timestamp: now(),
            content:
              '我已经收到你的消息。你可以试试问我"苹果的营养"、"帮我制定减脂计划"，或者让我给点健康建议～',
          },
        };
    }
  },

  async queryNutrition(foodName) {
    await delay(300);
    return NUTRITION_DB[foodName] ?? estimateNutrition(foodName);
  },
};
