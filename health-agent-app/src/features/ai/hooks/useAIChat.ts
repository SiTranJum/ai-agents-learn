// useAIChat - 封装"用户输入 → AI 回复 → store 更新"流程
// 同时处理 actions：navigate / show_nutrition

import { useCallback } from 'react';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList } from '@app/navigation/types';
import { aiService } from '../services/aiService';
import { useAIStore } from '../store/aiStore';
import type { ChatAction, ChatMessage } from '../types/ai.types';

type Nav = NativeStackNavigationProp<MainStackParamList>;

const now = (): string =>
  new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

export function useAIChat() {
  const navigation = useNavigation<Nav>();
  const toast = useToast();
  const {
    addMessage,
    setAIThinking,
    setNutritionResult,
    isAIThinking,
    chatMessages,
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
        const { reply, nutritionData } = await aiService.sendMessage(t);
        addMessage(reply);
        if (nutritionData) {
          // 营养数据存入 store，等用户点击 actions 时再展示
          setNutritionResult(nutritionData);
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
    [addMessage, setAIThinking, setNutritionResult, isAIThinking]
  );

  const handleAction = useCallback(
    (action: ChatAction) => {
      switch (action.action) {
        case 'navigate': {
          const screen = action.params?.screen as keyof MainStackParamList;
          if (screen === 'DietEdit') {
            navigation.navigate('DietEdit', {});
          } else if (screen === 'PlanCreate') {
            navigation.navigate('PlanCreate');
          } else if (screen) {
            // 兜底
            toast.show({ type: 'info', message: `准备跳转到 ${screen}` });
          }
          break;
        }
        case 'show_nutrition': {
          // BottomSheet 由 AIDialogScreen 监听 nutritionResult 自动展示
          // 这里只需要确保最近一次 nutritionData 已被设置
          toast.show({ type: 'info', message: '查看营养详情' });
          break;
        }
        case 'cancel':
          toast.show({ type: 'info', message: '已取消' });
          break;
        case 'confirm':
          toast.show({ type: 'success', message: '已确认' });
          break;
      }
    },
    [navigation, toast]
  );

  return {
    chatMessages,
    isAIThinking,
    sendMessage,
    handleAction,
    clearChat,
  };
}
