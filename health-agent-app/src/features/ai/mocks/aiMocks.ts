// AI 模块 Mock 数据
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §9

import type { ChatCard, ChatMessage, NutritionData } from '../types/ai.types';

const now = (): string =>
  new Date().toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  });

let _id = 0;
const makeId = () => `m-${Date.now()}-${++_id}`;

// ===== 欢迎消息 =====
export function buildAIWelcomeMessage(): ChatMessage {
  return {
    id: makeId(),
    role: 'ai',
    timestamp: now(),
    content:
      '你好，我是你的健康管家 AI 助手 👋\n你可以问我食物的营养、记录饮食/运动、或者获取健康建议。',
  };
}

// ===== 食物营养库（mock） =====
export const NUTRITION_DB: Record<string, NutritionData> = {
  苹果: {
    foodName: '苹果',
    amount: 100,
    unit: 'g',
    calories: 52,
    protein: 0.3,
    fat: 0.2,
    carbs: 14,
    dataSource: 'local_db',
  },
  鸡蛋: {
    foodName: '鸡蛋',
    amount: 1,
    unit: '个 (约 50g)',
    calories: 78,
    protein: 6.3,
    fat: 5.3,
    carbs: 0.6,
    dataSource: 'local_db',
  },
  米饭: {
    foodName: '米饭',
    amount: 100,
    unit: 'g',
    calories: 116,
    protein: 2.6,
    fat: 0.3,
    carbs: 25.6,
    dataSource: 'local_db',
  },
  鸡胸肉: {
    foodName: '鸡胸肉',
    amount: 100,
    unit: 'g',
    calories: 165,
    protein: 31,
    fat: 3.6,
    carbs: 0,
    dataSource: 'local_db',
  },
  牛奶: {
    foodName: '牛奶',
    amount: 250,
    unit: 'ml',
    calories: 135,
    protein: 8.0,
    fat: 7.5,
    carbs: 12,
    dataSource: 'local_db',
  },
  香蕉: {
    foodName: '香蕉',
    amount: 100,
    unit: 'g',
    calories: 89,
    protein: 1.1,
    fat: 0.3,
    carbs: 23,
    dataSource: 'local_db',
  },
};

export const DIET_PARSE_CARD_MOCK: ChatCard = {
  type: 'diet_parse',
  payload: {
    foods: [
      {
        name: '米饭',
        amount: 1,
        unit: '碗',
        amount_grams: 200,
        calories: 232,
        protein: 5.2,
        fat: 0.6,
        carbs: 51.8,
        fiber: 0.6,
        sodium: 4,
        data_source: 'database',
        food_id: null,
      },
      {
        name: '鸡胸肉',
        amount: 100,
        unit: 'g',
        amount_grams: 100,
        calories: 165,
        protein: 31,
        fat: 3.6,
        carbs: 0,
        data_source: 'database',
        food_id: null,
      },
    ],
    meal_type: 'lunch',
    confidence: 0.9,
    suggested_date: new Date().toISOString().slice(0, 10),
  },
  actions: [
    { kind: 'confirm_create_diet_record', label: '确认保存' },
    { kind: 'edit_diet_items', label: '修改食物' },
  ],
};

/** AI 估算回退值 */
export function estimateNutrition(foodName: string): NutritionData {
  return {
    foodName,
    amount: 100,
    unit: 'g',
    calories: 120,
    protein: 5,
    fat: 3,
    carbs: 18,
    dataSource: 'ai_estimate',
  };
}

// ===== 关键字 → 意图分类 =====
export function classifyIntent(text: string): {
  intent: 'nutrition_query' | 'health_advice' | 'plan_suggestion' | 'greeting' | 'general';
  matchedFood?: string;
} {
  const t = text.trim();
  // 营养查询
  if (/营养|热量|卡路里|多少卡|kcal/i.test(t)) {
    const food = Object.keys(NUTRITION_DB).find((k) => t.includes(k));
    return { intent: 'nutrition_query', matchedFood: food };
  }
  // 命中食物名 → 也视为营养查询
  const food = Object.keys(NUTRITION_DB).find((k) => t.includes(k));
  if (food) return { intent: 'nutrition_query', matchedFood: food };

  if (/计划|目标|减肥|减脂|增肌/.test(t)) return { intent: 'plan_suggestion' };
  if (/建议|怎么|如何|应该|可以吗/.test(t)) return { intent: 'health_advice' };
  if (/^(你好|hi|hello|嗨)/i.test(t)) return { intent: 'greeting' };
  return { intent: 'general' };
}
