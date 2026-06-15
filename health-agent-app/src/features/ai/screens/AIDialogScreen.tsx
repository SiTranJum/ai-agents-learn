// AIDialogScreen - AI 全屏对话页 (P17)
// T6: 替换 useAIChat 为 useStreamingChat，支持流式渲染
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §P17
// UI 文稿: docs/prd/v1/ui-design/14-ai-dialog-and-overlays.md

import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Platform,
  Keyboard,
} from 'react-native';
import { useNavigation, useRoute, useFocusEffect } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';
import { useQueryClient } from '@tanstack/react-query';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { AIInputBar } from '@shared/ui/AIInputBar';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList } from '@app/navigation/types';

import { ChatMessageList } from '../components/ChatMessageList';
import { NutritionBottomSheet } from '../components/NutritionBottomSheet';
import { useStreamingChat } from '../hooks/useStreamingChat';
import { useAIStore } from '../store/aiStore';
import { useDietStore } from '@features/diet/store/dietStore';
import { useBodyPendingStore } from '@features/data/store/bodyPendingStore';
import type { MealType } from '@features/diet/types/diet.types';
import type { ChatAction, ChatCard, ChatMessage, ChoicePrompt, DietParseCard, BodyParseCard } from '../types/ai.types';
import { getCardId } from '../utils/cardId';

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

type Nav = NativeStackNavigationProp<MainStackParamList, 'AIDialog'>;
type R = RouteProp<MainStackParamList, 'AIDialog'>;

export function AIDialogScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<R>();
  const toast = useToast();
  const queryClient = useQueryClient();

  // T6: 流式 hook 替换老 useAIChat
  const {
    messages, isStreaming, send, sendChoice, sendCardAction, cancel, cardStatus, pendingPrompt,
  } = useStreamingChat();

  const nutritionResult = useAIStore((s) => s.nutritionResult);
  const setNutritionResult = useAIStore((s) => s.setNutritionResult);
  const setOverlayState = useAIStore((s) => s.setOverlayState);
  const setCardStatus = useAIStore((s) => s.setCardStatus);
  const clearUnread = useAIStore((s) => s.clearUnread);

  const [sheetVisible, setSheetVisible] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  // 进入全屏对话页时清零未读
  useEffect(() => {
    clearUnread();
  }, [clearUnread]);

  // 监听键盘事件
  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';

    const showListener = Keyboard.addListener(showEvent, (e) => {
      setKeyboardHeight(e.endCoordinates.height);
    });

    const hideListener = Keyboard.addListener(hideEvent, () => {
      setKeyboardHeight(0);
    });

    return () => {
      showListener.remove();
      hideListener.remove();
    };
  }, []);

  // 离开全屏页面时把 overlay 状态降到 collapsed
  useFocusEffect(
    useCallback(() => {
      return () => {
        setOverlayState('collapsed');
      };
    }, [setOverlayState])
  );

  // 处理 initialMessage（从首页输入栏带过来的文本）
  useEffect(() => {
    const initial = route.params?.initialMessage;
    if (initial) {
      setTimeout(() => send(initial), 100);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 老 action 处理（show_nutrition 等纯前端操作）
  const handleActionPress = useCallback(
    (action: ChatAction, _message: ChatMessage) => {
      if (action.action === 'show_nutrition') {
        if (nutritionResult) {
          setSheetVisible(true);
        } else {
          toast.show({ type: 'info', message: '暂无营养数据' });
        }
        return;
      }
      if (action.action === 'navigate' && action.params?.screen) {
        navigation.navigate(action.params.screen as any, action.params);
      }
    },
    [nutritionResult, toast, navigation]
  );

  // 卡片 action（确认保存 / 编辑 / 取消）。
  //
  // interrupt 模型下：后端 graph 暂停在确认节点，前端点按钮只发"决定"
  // （confirm/edit/cancel），由后端节点落库（checkpoint 是真相源）。
  // 前端不再本地写库，只做乐观 UI：清本地待确认队列 + 失效首页查询。
  const handleCardAction = useCallback(
    async (card: ChatCard, actionId: string, _label: string) => {
      const cardId = getCardId(card);
      const date = todayStr();

      // 编辑：跳转到编辑页（不恢复 graph，用户改完再确认）
      if (actionId === 'edit_diet_items') {
        navigation.navigate('DietEdit', {});
        return;
      }

      if (actionId === 'view_plan_detail' && 'plan_id' in card.payload && typeof card.payload.plan_id === 'string') {
        navigation.navigate('PlanDetail', { planId: card.payload.plan_id });
        return;
      }

      // 饮食确认/取消：清本地待确认队列（乐观），失效首页查询，恢复后端 graph 落库
      if (actionId === 'confirm_create_diet_record' || actionId === 'cancel_diet_record') {
        const dietCard = card as DietParseCard;
        const { meal_type, suggested_date } = dietCard.payload;
        const pending = useDietStore.getState().getPending(
          suggested_date ?? date,
          meal_type ?? ('breakfast' as MealType)
        );
        if (pending) {
          useDietStore.getState().clearPending(pending.date, pending.mealType);
        }
        queryClient.invalidateQueries({ queryKey: ['diet'] });
        queryClient.invalidateQueries({ queryKey: ['home/diet', date] });
        sendCardAction(card, actionId);
        return;
      }

      // 身体数据确认/取消：同上，恢复后端 graph 落库
      if (actionId === 'confirm_create_body_record' || actionId === 'cancel_body_record') {
        const bodyCard = card as BodyParseCard;
        const recordType = bodyCard.payload.record_type;
        const recordDate = bodyCard.payload.suggested_date ?? date;
        useBodyPendingStore.getState().clearPending(recordDate, recordType);
        queryClient.invalidateQueries({ queryKey: ['home/body', date] });
        sendCardAction(card, actionId);
        return;
      }

      // 其他 action：走 SSE 恢复流程
      sendCardAction(card, actionId);
    },
    [navigation, sendCardAction, queryClient]
  );

  // T6: 选项 choice 回调
  const handleChoiceSelect = useCallback(
    (prompt: ChoicePrompt, value: string, freeText?: string) => {
      sendChoice(prompt.prompt_id, value, freeText);
    },
    [sendChoice]
  );

  const handleAddToDiet = useCallback(() => {
    setSheetVisible(false);
    setNutritionResult(null);
    navigation.navigate('DietEdit', {});
  }, [navigation, setNutritionResult]);

  // 边界 UX（§7.4）：会话被 interrupt 暂停时用户直接打字，
  // 提示"还没回答上一个问题"。确认后照常发 text，后端会先 cancel 旧中断再起新一轮。
  const handleSend = useCallback(
    (text: string, ctx?: { image_url?: string; referenced_date?: string }) => {
      if (pendingPrompt) {
        toast.show({ type: 'info', message: '已跳过上一个待确认项' });
      }
      send(text, ctx);
    },
    [pendingPrompt, send, toast]
  );

  const handleBack = useCallback(() => navigation.goBack(), [navigation]);

  return (
    <PageContainer useSafeArea>
      {/* 顶部导航栏 */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
          <Feather name="chevron-left" size={24} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>AI 助手</Text>
        {isStreaming ? (
          <TouchableOpacity onPress={cancel} style={styles.stopBtn}>
            <Feather name="square" size={14} color="#FFF" />
          </TouchableOpacity>
        ) : (
          <View style={styles.backBtn} />
        )}
      </View>

      <View style={styles.flex1}>
        <ChatMessageList
          messages={messages}
          isAIThinking={isStreaming}
          onActionPress={handleActionPress}
          onCardAction={handleCardAction}
          onChoiceSelect={handleChoiceSelect}
          cardStatus={cardStatus}
        />

        {/* 底部输入栏：键盘弹起时通过 marginBottom 上推 */}
        <View style={[styles.inputBarWrap, { marginBottom: keyboardHeight }]}>
          <AIInputBar
            onSend={handleSend}
            placeholder={pendingPrompt ? '请在上方作答，或直接输入新问题...' : '问我任何健康问题...'}
          />
        </View>
      </View>

      <NutritionBottomSheet
        visible={sheetVisible}
        data={nutritionResult}
        onClose={() => setSheetVisible(false)}
        onAddToDiet={handleAddToDiet}
      />
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  flex1: { flex: 1 },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
    backgroundColor: theme.colors.bgPage,
  },
  backBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stopBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#EF5350',
    borderRadius: 20,
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  inputBarWrap: {
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
    backgroundColor: theme.colors.bgPage,
  },
});
