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
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation, useRoute, useFocusEffect } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { AIInputBar } from '@shared/ui/AIInputBar';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList } from '@app/navigation/types';

import { ChatMessageList } from '../components/ChatMessageList';
import { NutritionBottomSheet } from '../components/NutritionBottomSheet';
import { useStreamingChat } from '../hooks/useStreamingChat';
import { useAIStore } from '../store/aiStore';
import type { ChatAction, ChatCard, ChatMessage, ChoicePrompt } from '../types/ai.types';

type Nav = NativeStackNavigationProp<MainStackParamList, 'AIDialog'>;
type R = RouteProp<MainStackParamList, 'AIDialog'>;

export function AIDialogScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<R>();
  const toast = useToast();

  // T6: 流式 hook 替换老 useAIChat
  const {
    messages, isStreaming, send, sendChoice, sendCardAction, cancel, cardStatus,
  } = useStreamingChat();

  const nutritionResult = useAIStore((s) => s.nutritionResult);
  const setNutritionResult = useAIStore((s) => s.setNutritionResult);
  const setOverlayState = useAIStore((s) => s.setOverlayState);

  const [sheetVisible, setSheetVisible] = useState(false);

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

  // T6: 卡片 action（确认保存 / 编辑 / 跳过）
  const handleCardAction = useCallback(
    (card: ChatCard, actionId: string, _label: string) => {
      if (actionId === 'edit_diet_items') {
        navigation.navigate('DietEdit', {});
        return;
      }
      sendCardAction(card, actionId);
    },
    [sendCardAction, navigation]
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

      <KeyboardAvoidingView
        style={styles.flex1}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ChatMessageList
          messages={messages}
          isAIThinking={isStreaming}
          onActionPress={handleActionPress}
          onCardAction={handleCardAction}
          onChoiceSelect={handleChoiceSelect}
          cardStatus={cardStatus}
        />

        {/* 底部输入栏 */}
        <View style={styles.inputBarWrap}>
          <AIInputBar
            onSend={send}
            placeholder="问我任何健康问题..."
          />
        </View>
      </KeyboardAvoidingView>

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
