// PlanCreateChatScreen - 计划创建对话页 (P08)
// 多轮对话 → 生成计划摘要 → 确认创建
// 参考: docs/specs/frontend/modules/14-plan-module.md §P08
// UI 文稿: docs/prd/v1/ui-design/10-plan-create-chat-page.md

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { ConfirmDialog } from '@shared/feedback/ConfirmDialog';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList } from '@app/navigation/types';

import { ChatMessageBubble, TypingIndicator } from '../components/ChatMessage';
import { usePlanStore } from '../store/planStore';
import { useCreatePlan } from '../hooks/usePlanData';
import {
  buildCreatedMessage,
  buildWelcomeMessage,
  processChatStep,
} from '../services/planService';
import type {
  ChatActionButton,
  ChatMessage,
  PlanSummary,
} from '../types/plan.types';

type Nav = NativeStackNavigationProp<MainStackParamList, 'PlanCreate'>;

const now = (): string =>
  new Date().toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  });

export function PlanCreateChatScreen() {
  const navigation = useNavigation<Nav>();
  const toast = useToast();

  const {
    chatMessages,
    isAIThinking,
    step,
    draft,
    addMessage,
    setAIThinking,
    setStep,
    patchDraft,
    clearChat,
  } = usePlanStore();

  const createMutation = useCreatePlan();

  const [input, setInput] = useState('');
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);
  /** 已被回应过的 AI 消息 ID 集合 — 这些消息的快捷选项 / 操作按钮置灰 */
  const [respondedIds, setRespondedIds] = useState<Set<string>>(new Set());

  const scrollRef = useRef<ScrollView>(null);

  // 进入页面时若聊天为空 → 推入欢迎消息
  useEffect(() => {
    if (chatMessages.length === 0) {
      addMessage(buildWelcomeMessage());
      setStep('ask_type');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 50);
  }, [chatMessages.length, isAIThinking]);

  // 标记最后一条 AI 消息为"已回应"
  const markLastAIResponded = useCallback(() => {
    const lastAI = [...chatMessages].reverse().find((m) => m.role === 'ai');
    if (lastAI) {
      setRespondedIds((prev) => new Set(prev).add(lastAI.id));
    }
  }, [chatMessages]);

  // 发送用户消息并触发 AI 回复
  const sendUserMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;
      if (step === 'created') return;

      // 1. 推入用户消息
      const userMsg: ChatMessage = {
        id: `u-${Date.now()}`,
        role: 'user',
        content: text.trim(),
        timestamp: now(),
      };
      addMessage(userMsg);
      markLastAIResponded();

      // 2. 触发 AI 思考
      setAIThinking(true);
      try {
        const result = await processChatStep(step, text.trim(), draft);
        if (result.patch) patchDraft(result.patch);
        addMessage(result.message);
        setStep(result.nextStep);
      } finally {
        setAIThinking(false);
      }
    },
    [step, draft, addMessage, markLastAIResponded, setAIThinking, patchDraft, setStep]
  );

  const handleSend = useCallback(() => {
    const text = input.trim();
    if (!text) return;
    setInput('');
    void sendUserMessage(text);
  }, [input, sendUserMessage]);

  const handleQuickOption = useCallback(
    (opt: string) => {
      void sendUserMessage(opt);
    },
    [sendUserMessage]
  );

  // 操作按钮：确认创建 / 修改目标 / 查看计划
  const handleActionPress = useCallback(
    async (btn: ChatActionButton) => {
      if (btn.key === 'confirm') {
        // 找到最近的 planSummary
        const summaryMsg = [...chatMessages]
          .reverse()
          .find((m) => m.planSummary);
        const summary: PlanSummary | undefined = summaryMsg?.planSummary;
        if (!summary) {
          toast.show({ type: 'error', message: '未找到计划摘要' });
          return;
        }
        markLastAIResponded();
        try {
          const created = await createMutation.mutateAsync(summary);
          addMessage(buildCreatedMessage(created.id));
          setStep('created');
          toast.show({ type: 'success', message: '计划已创建' });
        } catch {
          toast.show({ type: 'error', message: '创建失败，请重试' });
        }
        return;
      }

      if (btn.key === 'modify') {
        markLastAIResponded();
        addMessage({
          id: `m-${Date.now()}`,
          role: 'ai',
          timestamp: now(),
          content: '好的，请告诉我你想调整哪部分？目标 / 周期 / 计划类型？',
        });
        return;
      }

      if (btn.key.startsWith('view:')) {
        const planId = btn.key.slice(5);
        clearChat();
        navigation.replace('PlanDetail', { planId });
      }
    },
    [
      chatMessages,
      markLastAIResponded,
      addMessage,
      setStep,
      createMutation,
      toast,
      clearChat,
      navigation,
    ]
  );

  // 返回：若有对话内容则确认
  const handleBack = useCallback(() => {
    if (chatMessages.length > 1 && step !== 'created') {
      setShowLeaveConfirm(true);
    } else {
      clearChat();
      navigation.goBack();
    }
  }, [chatMessages.length, step, clearChat, navigation]);

  const lastAIId = useMemo(() => {
    const lastAI = [...chatMessages].reverse().find((m) => m.role === 'ai');
    return lastAI?.id;
  }, [chatMessages]);

  return (
    <PageContainer useSafeArea>
      {/* 顶部导航栏 */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
          <Feather name="chevron-left" size={24} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>创建计划</Text>
        <View style={styles.backBtn} />
      </View>

      <KeyboardAvoidingView
        style={styles.flex1}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          ref={scrollRef}
          style={styles.flex1}
          contentContainerStyle={styles.chatContent}
          keyboardShouldPersistTaps="handled"
        >
          {chatMessages.map((msg) => {
            // 仅最后一条 AI 消息且未被标记为 responded 时，按钮可用
            const optionsActive =
              msg.id === lastAIId && !respondedIds.has(msg.id);
            return (
              <ChatMessageBubble
                key={msg.id}
                message={msg}
                optionsActive={optionsActive}
                onQuickOptionPress={handleQuickOption}
                onActionPress={handleActionPress}
              />
            );
          })}
          {isAIThinking && <TypingIndicator />}
        </ScrollView>

        {/* 底部输入框 */}
        <View style={styles.inputBar}>
          <View style={styles.inputWrap}>
            <TextInput
              style={styles.input}
              value={input}
              onChangeText={setInput}
              placeholder="输入你的想法..."
              placeholderTextColor={theme.colors.textTertiary}
              editable={step !== 'created' && !isAIThinking}
              onSubmitEditing={handleSend}
              returnKeyType="send"
            />
          </View>
          <TouchableOpacity
            style={[
              styles.sendBtn,
              (!input.trim() || isAIThinking) && styles.sendBtnDisabled,
            ]}
            onPress={handleSend}
            disabled={!input.trim() || isAIThinking}
            activeOpacity={0.8}
          >
            <Feather name="send" size={18} color={theme.colors.bgCard} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>

      <ConfirmDialog
        visible={showLeaveConfirm}
        title="退出创建"
        message="退出将丢失当前对话，确定退出？"
        confirmText="确定退出"
        cancelText="继续创建"
        variant="danger"
        onConfirm={() => {
          setShowLeaveConfirm(false);
          clearChat();
          navigation.goBack();
        }}
        onCancel={() => setShowLeaveConfirm(false)}
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
  chatContent: {
    paddingVertical: theme.spacing.md,
    paddingBottom: theme.spacing.lg,
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    padding: theme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
    backgroundColor: theme.colors.bgPage,
  },
  inputWrap: {
    flex: 1,
    backgroundColor: theme.colors.bgPage,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.colors.divider,
    paddingHorizontal: theme.spacing.md,
    height: 40,
    justifyContent: 'center',
  },
  input: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    padding: 0,
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: theme.radius.full,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnDisabled: {
    opacity: 0.4,
  },
});
