import React, { useCallback, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { ConfirmDialog } from '@shared/feedback/ConfirmDialog';
import { AIInputBar } from '@shared/ui/AIInputBar';
import type { MainStackParamList } from '@app/navigation/types';
import { ChatMessageList } from '@features/ai/components/ChatMessageList';
import type { ChatCard, ChoicePrompt } from '@features/ai/types/ai.types';

import { usePlanConversation } from '../hooks/usePlanConversation';

type Nav = NativeStackNavigationProp<MainStackParamList, 'PlanCreate'>;

export function PlanCreateChatScreen() {
  const navigation = useNavigation<Nav>();
  const { messages, isStreaming, send, sendChoice, sendCardAction, reset, cardStatus } = usePlanConversation();
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);

  const handleBack = useCallback(() => {
    if (messages.length > 0) {
      setShowLeaveConfirm(true);
      return;
    }
    navigation.goBack();
  }, [messages.length, navigation]);

  const handleCardAction = useCallback(
    (card: ChatCard, actionId: string, label: string) => {
      if (actionId === 'view_plan_detail' && 'plan_id' in card.payload && typeof card.payload.plan_id === 'string') {
        const planId = card.payload.plan_id;
        reset();
        navigation.replace('PlanDetail', { planId });
        return;
      }
      sendCardAction(card, actionId, label);
    },
    [navigation, reset, sendCardAction]
  );

  const handleChoice = useCallback(
    (prompt: ChoicePrompt, value: string, freeText?: string) => {
      sendChoice(prompt.prompt_id, value, freeText);
    },
    [sendChoice]
  );

  return (
    <PageContainer useSafeArea>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
          <Feather name="chevron-left" size={24} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>创建计划</Text>
        <View style={styles.backBtn} />
      </View>

      <View style={styles.hero}>
        <Text style={styles.heroTitle}>AI 会结合你的档案和记忆生成计划</Text>
        <Text style={styles.heroText}>
          直接描述你的目标、周期、限制和偏好；从第一轮开始就是真实 AI 对话。
        </Text>
      </View>

      <View style={styles.content}>
        <ChatMessageList
          messages={messages}
          isAIThinking={isStreaming}
          onCardAction={handleCardAction}
          onChoiceSelect={handleChoice}
          cardStatus={cardStatus}
        />
        <View style={styles.inputBarWrap}>
          <AIInputBar onSend={send} placeholder="例如：帮我 12 周减 4kg" />
        </View>
      </View>

      <ConfirmDialog
        visible={showLeaveConfirm}
        title="退出计划对话？"
        message="退出后将清空当前计划创建对话。"
        confirmText="退出"
        cancelText="继续创建"
        variant="danger"
        onConfirm={() => {
          setShowLeaveConfirm(false);
          reset();
          navigation.goBack();
        }}
        onCancel={() => setShowLeaveConfirm(false)}
      />
    </PageContainer>
  );
}

const styles = StyleSheet.create({
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
  hero: {
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingTop: theme.spacing.lg,
    paddingBottom: theme.spacing.md,
    gap: theme.spacing.xs,
  },
  heroTitle: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  heroText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    lineHeight: 20,
  },
  content: {
    flex: 1,
  },
  inputBarWrap: {
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
    backgroundColor: theme.colors.bgPage,
  },
});
