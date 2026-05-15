// useAIChat - 封装"用户输入 → AI 回复 → store 更新"流程
// 同时处理 actions：navigate / show_nutrition / confirm / cancel
// #5 优化：AI 解析饮食后写入 dietStore.pendingRecords，双向同步

import { useCallback } from 'react';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useQueryClient } from '@tanstack/react-query';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList } from '@app/navigation/types';
import { aiService } from '../services/aiService';
import { useAIStore } from '../store/aiStore';
import { useDietStore } from '@features/diet/store/dietStore';
import { dietService } from '@features/diet/services/dietService';
import type { ChatAction, ChatMessage, DietParseCard } from '../types/ai.types';
import type { FoodItem } from '@features/diet/types/diet.types';

type Nav = NativeStackNavigationProp<MainStackParamList>;

const now = (): string =>
  new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

function localTodayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/** 把后端 ParsedFood → 前端 FoodItem */
function parsedFoodsToItems(foods: DietParseCard['payload']['foods']): FoodItem[] {
  return foods.map((f, idx) => ({
    id: `pending-${Date.now()}-${idx}`,
    name: f.name,
    amount: f.amount,
    unit: f.unit,
    amountGrams: f.amount_grams,
    cookingMethod: f.cooking_method ?? undefined,
    calories: f.calories,
    protein: f.protein,
    fat: f.fat,
    carbs: f.carbs,
    fiber: f.fiber ?? undefined,
    sodium: f.sodium ?? undefined,
    dataSource: f.data_source,
    foodId: f.food_id ?? undefined,
  }));
}

export function useAIChat() {
  const navigation = useNavigation<Nav>();
  const toast = useToast();
  const qc = useQueryClient();
  const {
    addMessage,
    setAIThinking,
    setNutritionResult,
    setCurrentSessionId,
    isAIThinking,
    chatMessages,
    currentSessionId,
    clearChat,
  } = useAIStore();

  const sendMessage = useCallback(
    async (text: string) => {
      const t = text.trim();
      if (!t || isAIThinking) return;

      // 1. 用户消息入栈
      const userMsg: ChatMessage = {
        id: `u-${Date.now()}`,
        role: 'user',
        content: t,
        timestamp: now(),
      };
      addMessage(userMsg);

      // 2. 触发 AI 思考
      setAIThinking(true);
      try {
        const { reply, sessionId, nutritionData } = await aiService.sendMessage(
          t,
          currentSessionId
        );
        if (sessionId) {
          setCurrentSessionId(sessionId);
        }
        addMessage(reply);
        if (nutritionData) {
          setNutritionResult(nutritionData);
        }

        // 3. 检测 diet_parse 卡片 → 写入 pending
        const dietCard = reply.cards?.find((c) => c.type === 'diet_parse') as DietParseCard | undefined;
        if (dietCard) {
          const { foods, meal_type, suggested_date } = dietCard.payload;
          if (meal_type && foods.length > 0) {
            useDietStore.getState().setPending({
              date: suggested_date ?? localTodayStr(),
              mealType: meal_type,
              foods: parsedFoodsToItems(foods),
              sessionId: sessionId ?? undefined,
              createdAt: Date.now(),
            });
          }
        }
      } catch {
        addMessage({
          id: `s-${Date.now()}`,
          role: 'system',
          timestamp: now(),
          content: 'AI 服务暂时不可用，请稍后再试。',
        });
      } finally {
        setAIThinking(false);
      }
    },
    [
      addMessage,
      currentSessionId,
      setAIThinking,
      setCurrentSessionId,
      setNutritionResult,
      isAIThinking,
    ]
  );

  const handleAction = useCallback(
    async (action: ChatAction) => {
      switch (action.action) {
        case 'navigate': {
          const screen = action.params?.screen as keyof MainStackParamList;
          if (screen === 'DietEdit') {
            // 如果有 pending 数据，带 prefillFoods 跳转
            const card = action.params?.card as DietParseCard | undefined;
            if (card?.payload?.foods) {
              const mealType = card.payload.meal_type ?? 'lunch';
              const date = card.payload.suggested_date ?? localTodayStr();
              navigation.navigate('DietEdit', {
                mealType,
                date,
                prefillFoods: parsedFoodsToItems(card.payload.foods),
              });
            } else {
              navigation.navigate('DietEdit', {});
            }
          } else if (screen === 'PlanCreate') {
            navigation.navigate('PlanCreate');
          } else if (screen) {
            toast.show({ type: 'info', message: `准备跳转到 ${screen}` });
          }
          break;
        }
        case 'show_nutrition': {
          toast.show({ type: 'info', message: '查看营养详情' });
          break;
        }
        case 'cancel': {
          // 取消 pending
          const card = action.params?.card as DietParseCard | undefined;
          if (card?.payload?.meal_type) {
            const date = card.payload.suggested_date ?? localTodayStr();
            useDietStore.getState().clearPending(date, card.payload.meal_type);
          }
          toast.show({ type: 'info', message: '已取消' });
          break;
        }
        case 'confirm': {
          // 确认保存：调 upsert + 清 pending
          const card = action.params?.card as DietParseCard | undefined;
          if (card?.payload?.foods && card.payload.meal_type) {
            const mealType = card.payload.meal_type;
            const date = card.payload.suggested_date ?? localTodayStr();
            const foods = parsedFoodsToItems(card.payload.foods);
            try {
              await dietService.saveDietRecord(
                { mealType, status: 'recorded', foods, totalCalories: 0, nutrients: { carbs: 0, protein: 0, fat: 0 } },
                date
              );
              useDietStore.getState().clearPending(date, mealType);
              qc.invalidateQueries({ queryKey: ['diet'] });
              qc.invalidateQueries({ queryKey: ['home'] });
              toast.show({ type: 'success', message: '饮食记录已保存' });
            } catch {
              toast.show({ type: 'error', message: '保存失败，请重试' });
            }
          } else {
            toast.show({ type: 'success', message: '已确认' });
          }
          break;
        }
      }
    },
    [navigation, toast, qc]
  );

  return {
    chatMessages,
    isAIThinking,
    sendMessage,
    handleAction,
    clearChat,
  };
}
