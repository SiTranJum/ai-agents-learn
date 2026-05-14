// AI Service - 对接后端 API
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §8

import type { ChatMessage, NutritionData } from '../types/ai.types';
import { apiClient } from '@core/api/client';
import type { ChatCard, ChatResponseRaw } from '../types/ai.types';

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
   * 发送消息给 AI，返回 AI 回复（可能携带 actions / nutritionData）
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
    const raw = await apiClient.post<ChatResponseRaw>('/ai/chat', {
      session_id: sessionId ?? null,
      message,
      context,
    });
    return { reply: mapBackendReply(raw), sessionId: raw.session_id };
  },

  async queryNutrition(foodName) {
    const results = await apiClient.get<Array<{ name: string; calories: number; protein: number; fat: number; carbs: number; unit?: string; amount?: number }>>(`/knowledge/foods/search?q=${encodeURIComponent(foodName)}&limit=1`);
    const item = results[0];
    if (!item) {
      throw new Error(`未找到食物: ${foodName}`);
    }
    return {
      foodName: item.name,
      calories: item.calories,
      protein: item.protein,
      fat: item.fat,
      carbs: item.carbs,
      unit: item.unit ?? 'g',
      amount: item.amount ?? 100,
      dataSource: 'database' as const,
    };
  },
};
