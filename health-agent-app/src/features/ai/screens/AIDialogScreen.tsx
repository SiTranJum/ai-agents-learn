// AIDialogScreen - AI 全屏对话页 (P17)
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
import { useNavigation, useRoute } from '@react-navigation/native';
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
import { useAIChat } from '../hooks/useAIChat';
import { useAIStore } from '../store/aiStore';
import { buildAIWelcomeMessage } from '../mocks/aiMocks';
import type { ChatAction, ChatMessage } from '../types/ai.types';

type Nav = NativeStackNavigationProp<MainStackParamList, 'AIDialog'>;
type R = RouteProp<MainStackParamList, 'AIDialog'>;

export function AIDialogScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<R>();
  const toast = useToast();

  const { chatMessages, isAIThinking, sendMessage, handleAction } = useAIChat();
  const addMessage = useAIStore((s) => s.addMessage);
  const nutritionResult = useAIStore((s) => s.nutritionResult);
  const setNutritionResult = useAIStore((s) => s.setNutritionResult);

  const [sheetVisible, setSheetVisible] = useState(false);

  // 初始化：注入欢迎消息（仅当对话为空）+ 处理 initialMessage
  useEffect(() => {
    if (chatMessages.length === 0) {
      addMessage(buildAIWelcomeMessage());
    }
    const initial = route.params?.initialMessage;
    if (initial) {
      // 用 setTimeout 让欢迎消息先入栈
      setTimeout(() => sendMessage(initial), 100);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 拦截 action：show_nutrition → 打开 BottomSheet
  const handleActionWithSheet = useCallback(
    (action: ChatAction, message: ChatMessage) => {
      if (action.action === 'show_nutrition') {
        if (nutritionResult) {
          setSheetVisible(true);
        } else {
          toast.show({ type: 'info', message: '暂无营养数据' });
        }
        return;
      }
      handleAction(action);
    },
    [handleAction, nutritionResult, toast]
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
        <View style={styles.backBtn} />
      </View>

      <KeyboardAvoidingView
        style={styles.flex1}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ChatMessageList
          messages={chatMessages}
          isAIThinking={isAIThinking}
          onActionPress={handleActionWithSheet}
        />

        {/* 底部输入栏 */}
        <View style={styles.inputBarWrap}>
          <AIInputBar
            onSend={sendMessage}
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
