// 流式 demo 页面
// 6 种场景一键切换，模拟完整流式 + 富交互流程
// 参考: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T1
// 参考: docs/plans/2026-05-21-streaming-chat-design.md §16

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';

import { createMockStream } from './streamingMock';
import type {
  AIStreamingMessage,
  ChoicePrompt,
  DemoMessage,
  MessageSegment,
  MockStreamHandle,
  ScenarioName,
  ToolCallState,
  UserMessage,
} from './types';
import type { ChatCard } from '../types/ai.types';

import { StatusChip } from './components/StatusChip';
import { ToolCallChip } from './components/ToolCallChip';
import { StreamingText } from './components/StreamingText';
import { ChoicePromptView } from './components/ChoicePromptView';
import { StreamingCardView } from './components/StreamingCardView';

// ============ 场景元信息 ============

const SCENARIOS: { name: ScenarioName; label: string; description: string }[] = [
  { name: 'happy_path', label: '基础流程', description: 'text → 选项 → text → 卡片' },
  { name: 'failure_retry', label: '失败重试', description: '流中途报错引导重试' },
  { name: 'mid_cancel', label: '中途取消', description: '慢速流中点停止' },
  { name: 'free_text_response', label: '自由输入', description: '选项之外用文本' },
  { name: 'multi_card_confirm', label: '多卡片', description: '连续多张卡片确认' },
  { name: 'idle_timeout', label: '超时检测', description: '30s 无事件触发超时' },
];

// 触发用户消息文本（每个场景对应固定的"用户发问"）
const SCENARIO_INITIAL_USER_MSG: Record<ScenarioName, string> = {
  happy_path: '今天中午吃了鸡胸肉 200g',
  failure_retry: '今天中午吃了鸡胸肉 200g',
  mid_cancel: '给我详细讲讲健康饮食原则',
  free_text_response: '今天中午吃了鸡胸肉 200g',
  multi_card_confirm: '今天中午吃了鸡胸肉，再帮我安排下午的运动和睡眠',
  idle_timeout: '一个会卡住的请求',
};

// ============ 主组件 ============

export function StreamingDemoScreen() {
  const navigation = useNavigation();
  const [messages, setMessages] = useState<DemoMessage[]>([]);
  const [activeScenario, setActiveScenario] = useState<ScenarioName | null>(null);
  const [round, setRound] = useState(1);
  const streamRef = useRef<MockStreamHandle | null>(null);
  const cardStatusRef = useRef<Map<string, 'pending' | 'submitted' | 'cancelled'>>(
    new Map()
  );
  const [, forceUpdate] = useState(0);

  // 卸载时关闭活动流，避免内存泄漏
  useEffect(() => {
    return () => {
      streamRef.current?.cancel();
    };
  }, []);

  // 取最后一条 AI 消息（流式中的）
  const updateLastAI = useCallback((updater: (msg: AIStreamingMessage) => AIStreamingMessage) => {
    setMessages((prev) => {
      const arr = [...prev];
      for (let i = arr.length - 1; i >= 0; i--) {
        const m = arr[i];
        if (m.role === 'assistant') {
          arr[i] = updater(m);
          return arr;
        }
      }
      return prev;
    });
  }, []);

  // 启动一个场景或一段对话
  const startStream = useCallback(
    (scenario: ScenarioName, currentRound: number) => {
      // 创建流式占位消息
      const placeholder: AIStreamingMessage = {
        id: `ai_${Date.now()}_${currentRound}`,
        role: 'assistant',
        status: null,
        tools: [],
        segments: [],
        isStreaming: true,
      };
      setMessages((prev) => [...prev, placeholder]);

      const handle = createMockStream(scenario, currentRound);
      streamRef.current = handle;

      handle.on('meta', () => {
        // meta 不需要 UI 改动，仅记录
      });

      handle.on('status', ({ label }) => {
        updateLastAI((msg) => ({ ...msg, status: label }));
      });

      handle.on('tool_call', ({ tool, label }) => {
        updateLastAI((msg) => {
          const without = msg.tools.filter((t) => t.tool !== tool);
          return {
            ...msg,
            tools: [...without, { tool, label, state: 'pending' as const }],
          };
        });
      });

      handle.on('tool_result', ({ tool, summary }) => {
        updateLastAI((msg) => ({
          ...msg,
          tools: msg.tools.map((t) =>
            t.tool === tool ? { ...t, summary, state: 'done' as const } : t
          ),
        }));
      });

      handle.on('text_delta', ({ content }) => {
        updateLastAI((msg) => {
          const segs = [...msg.segments];
          const last = segs[segs.length - 1];
          if (last && last.kind === 'text') {
            segs[segs.length - 1] = {
              kind: 'text',
              content: last.content + content,
            };
          } else {
            segs.push({ kind: 'text', content });
          }
          return { ...msg, segments: segs, status: null };
        });
      });

      handle.on('choice', (prompt: ChoicePrompt) => {
        updateLastAI((msg) => ({
          ...msg,
          status: null,
          segments: [
            ...msg.segments,
            { kind: 'choice', prompt } satisfies MessageSegment,
          ],
        }));
      });

      handle.on('card', ({ card }) => {
        cardStatusRef.current.set(getCardId(card), 'pending');
        updateLastAI((msg) => ({
          ...msg,
          status: null,
          segments: [...msg.segments, { kind: 'card', card } satisfies MessageSegment],
        }));
      });

      handle.on('done', () => {
        updateLastAI((msg) => ({ ...msg, isStreaming: false, status: null }));
        streamRef.current = null;
      });

      handle.on('error', ({ code, message }) => {
        updateLastAI((msg) => ({
          ...msg,
          isStreaming: false,
          status: null,
          error: { code, message },
        }));
        streamRef.current = null;
      });

      handle.start();
    },
    [updateLastAI]
  );

  // 用户点击"运行场景"
  const handleRunScenario = useCallback(
    (scenario: ScenarioName) => {
      // 清空旧状态
      streamRef.current?.cancel();
      streamRef.current = null;
      cardStatusRef.current.clear();
      setMessages([]);
      setActiveScenario(scenario);
      setRound(1);

      // 加用户消息
      const userMsg: UserMessage = {
        id: `u_${Date.now()}`,
        role: 'user',
        content: SCENARIO_INITIAL_USER_MSG[scenario],
      };
      setMessages([userMsg]);

      // 启动流（短延迟让 user msg 先渲染）
      setTimeout(() => startStream(scenario, 1), 100);
    },
    [startStream]
  );

  // 用户点选项 chip → 渲染为用户消息 → 启动 round 2
  const handleChoiceSelect = useCallback(
    (promptId: string, value: string, label: string) => {
      // 1. 更新已选状态
      updateLastAI((msg) => ({
        ...msg,
        segments: msg.segments.map((seg) =>
          seg.kind === 'choice' && seg.prompt.prompt_id === promptId
            ? { ...seg, selectedValue: value }
            : seg
        ),
      }));

      // 2. 加用户消息（"午餐"）
      const userMsg: UserMessage = {
        id: `u_${Date.now()}`,
        role: 'user',
        content: label,
      };
      setMessages((prev) => [...prev, userMsg]);

      // 3. 启动 round 2
      if (!activeScenario) return;
      const nextRound = round + 1;
      setRound(nextRound);
      setTimeout(() => startStream(activeScenario, nextRound), 200);
    },
    [activeScenario, round, startStream, updateLastAI]
  );

  // 用户用自由文本回应 choice → 启动 round 2
  const handleChoiceFreeText = useCallback(
    (promptId: string, text: string) => {
      updateLastAI((msg) => ({
        ...msg,
        segments: msg.segments.map((seg) =>
          seg.kind === 'choice' && seg.prompt.prompt_id === promptId
            ? { ...seg, freeText: text }
            : seg
        ),
      }));

      const userMsg: UserMessage = {
        id: `u_${Date.now()}`,
        role: 'user',
        content: text,
      };
      setMessages((prev) => [...prev, userMsg]);

      if (!activeScenario) return;
      const nextRound = round + 1;
      setRound(nextRound);
      setTimeout(() => startStream(activeScenario, nextRound), 200);
    },
    [activeScenario, round, startStream, updateLastAI]
  );

  // 卡片 action 点击：确认 / 修改 / 跳过
  const handleCardAction = useCallback(
    (card: ChatCard, actionKind: string, _label: string) => {
      const cardId = getCardId(card);

      if (actionKind === 'edit_diet_items') {
        Alert.alert('演示提示', '真实场景下这里跳转到饮食编辑页');
        return;
      }
      if (actionKind === 'skip') {
        cardStatusRef.current.set(cardId, 'cancelled');
        forceUpdate((n) => n + 1);
        return;
      }
      // 默认视为"确认"操作
      cardStatusRef.current.set(cardId, 'submitted');
      forceUpdate((n) => n + 1);

      // multi_card_confirm 场景：确认后继续下一张卡片
      if (activeScenario === 'multi_card_confirm' && round < 3) {
        const userMsg: UserMessage = {
          id: `u_${Date.now()}`,
          role: 'user',
          content: '确认',
        };
        setMessages((prev) => [...prev, userMsg]);
        const nextRound = round + 1;
        setRound(nextRound);
        setTimeout(() => startStream(activeScenario, nextRound), 200);
      }
    },
    [activeScenario, round, startStream]
  );

  // 用户点"停止"
  const handleCancel = useCallback(() => {
    streamRef.current?.cancel();
    streamRef.current = null;
    updateLastAI((msg) => ({
      ...msg,
      isStreaming: false,
      status: null,
      error: { code: 'CANCELLED', message: '已取消' },
    }));
  }, [updateLastAI]);

  // failure_retry 场景的重试按钮
  const handleRetry = useCallback(() => {
    if (!activeScenario) return;
    // 移除最后一条 AI 错误消息
    setMessages((prev) => {
      const arr = [...prev];
      for (let i = arr.length - 1; i >= 0; i--) {
        if (arr[i].role === 'assistant') {
          arr.splice(i, 1);
          break;
        }
      }
      return arr;
    });
    // 重新走一次（这次走成功流：复用 happy_path round 2 作为成功响应）
    setTimeout(() => startStream(activeScenario, 2), 200);
  }, [activeScenario, startStream]);

  const isStreaming = streamRef.current !== null;

  return (
    <PageContainer>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Feather name="arrow-left" size={20} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>🧪 流式交互 Demo</Text>
        {isStreaming && (
          <TouchableOpacity onPress={handleCancel} style={styles.cancelBtn}>
            <Feather name="square" size={14} color="#FFF" />
            <Text style={styles.cancelText}>停止</Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.scenarioBar}
        contentContainerStyle={styles.scenarioBarContent}
      >
        {SCENARIOS.map((s) => (
          <TouchableOpacity
            key={s.name}
            style={[
              styles.scenarioChip,
              activeScenario === s.name && styles.scenarioChipActive,
            ]}
            onPress={() => handleRunScenario(s.name)}
            disabled={isStreaming}
          >
            <Text
              style={[
                styles.scenarioChipLabel,
                activeScenario === s.name && styles.scenarioChipLabelActive,
              ]}
            >
              {s.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {activeScenario && (
        <View style={styles.scenarioInfo}>
          <Text style={styles.scenarioDesc}>
            💡 {SCENARIOS.find((s) => s.name === activeScenario)?.description}
          </Text>
        </View>
      )}

      <ScrollView
        style={styles.messages}
        contentContainerStyle={styles.messagesContent}
        showsVerticalScrollIndicator={false}
      >
        {messages.length === 0 && (
          <View style={styles.empty}>
            <Text style={styles.emptyTitle}>选一个场景开始演示</Text>
            <Text style={styles.emptyDesc}>
              点击上方任意场景 chip，模拟完整流式交互。
            </Text>
          </View>
        )}
        {messages.map((msg) => (
          <MessageRow
            key={msg.id}
            msg={msg}
            onChoiceSelect={handleChoiceSelect}
            onChoiceFreeText={handleChoiceFreeText}
            onCardAction={handleCardAction}
            cardStatus={cardStatusRef.current}
            onRetry={handleRetry}
          />
        ))}
      </ScrollView>
    </PageContainer>
  );
}

// ============ 单条消息渲染 ============

interface MessageRowProps {
  msg: DemoMessage;
  onChoiceSelect: (promptId: string, value: string, label: string) => void;
  onChoiceFreeText: (promptId: string, text: string) => void;
  onCardAction: (card: ChatCard, actionKind: string, label: string) => void;
  cardStatus: Map<string, 'pending' | 'submitted' | 'cancelled'>;
  onRetry: () => void;
}

function MessageRow({
  msg,
  onChoiceSelect,
  onChoiceFreeText,
  onCardAction,
  cardStatus,
  onRetry,
}: MessageRowProps) {
  if (msg.role === 'user') {
    return (
      <View style={styles.userRow}>
        <View style={styles.userBubble}>
          <Text style={styles.userText}>{msg.content}</Text>
        </View>
      </View>
    );
  }

  const ai = msg;
  return (
    <View style={styles.aiRow}>
      <Text style={styles.aiTag}>AI</Text>
      <View style={styles.aiContent}>
        {/* 状态 chip */}
        {ai.status && <StatusChip label={ai.status} />}

        {/* 工具调用 */}
        {ai.tools.map((t) => (
          <ToolCallChip key={t.tool} tool={t} />
        ))}

        {/* segment 时间线 */}
        {ai.segments.map((seg, idx) => {
          if (seg.kind === 'text') {
            const isLastTextStreaming =
              ai.isStreaming &&
              !ai.segments.slice(idx + 1).some((s) => s.kind === 'text');
            return (
              <StreamingText
                key={`text-${idx}`}
                content={seg.content}
                streaming={isLastTextStreaming}
              />
            );
          }
          if (seg.kind === 'choice') {
            return (
              <ChoicePromptView
                key={`choice-${idx}`}
                prompt={seg.prompt}
                selectedValue={seg.selectedValue}
                freeText={seg.freeText}
                onSelect={(value, label) =>
                  onChoiceSelect(seg.prompt.prompt_id, value, label)
                }
                onFreeText={(text) => onChoiceFreeText(seg.prompt.prompt_id, text)}
              />
            );
          }
          if (seg.kind === 'card') {
            const cardId = getCardId(seg.card);
            const status = cardStatus.get(cardId) ?? 'pending';
            return (
              <StreamingCardView
                key={`card-${idx}`}
                card={seg.card}
                status={status}
                onActionPress={(actionKind, label) =>
                  onCardAction(seg.card, actionKind, label)
                }
              />
            );
          }
          return null;
        })}

        {/* 错误态 */}
        {ai.error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorIcon}>⚠️</Text>
            <View style={styles.errorContent}>
              <Text style={styles.errorTitle}>{ai.error.message}</Text>
              <Text style={styles.errorCode}>{ai.error.code}</Text>
            </View>
            {ai.error.code !== 'CANCELLED' && (
              <TouchableOpacity onPress={onRetry} style={styles.retryBtn}>
                <Text style={styles.retryText}>重试</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </View>
    </View>
  );
}

// ============ helper ============

function getCardId(card: ChatCard): string {
  // 用 type + 内容 hash 兜底（payload 没有强制 id 字段）
  return `${card.type}:${JSON.stringify(card.payload).slice(0, 32)}`;
}

// ============ 样式 ============

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingVertical: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
  },
  backBtn: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    flex: 1,
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginLeft: theme.spacing.sm,
  },
  cancelBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.error,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
    gap: theme.spacing.xs,
  },
  cancelText: {
    ...theme.typography.caption,
    color: '#FFF',
    fontWeight: '600',
  },
  scenarioBar: {
    flexGrow: 0,
    paddingVertical: theme.spacing.sm,
    backgroundColor: theme.colors.bgCard,
  },
  scenarioBarContent: {
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    gap: theme.spacing.sm,
  },
  scenarioChip: {
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.colors.divider,
    backgroundColor: theme.colors.bgCard,
  },
  scenarioChipActive: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  scenarioChipLabel: {
    ...theme.typography.caption,
    color: theme.colors.textPrimary,
  },
  scenarioChipLabelActive: {
    color: '#FFF',
    fontWeight: '600',
  },
  scenarioInfo: {
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingVertical: theme.spacing.sm,
    backgroundColor: '#FFFBEB',
  },
  scenarioDesc: {
    ...theme.typography.caption,
    color: '#92400E',
  },
  messages: {
    flex: 1,
  },
  messagesContent: {
    padding: theme.layout.pageHorizontalPadding,
    paddingBottom: 60,
  },
  empty: {
    alignItems: 'center',
    paddingTop: 80,
    paddingHorizontal: theme.spacing.xl,
  },
  emptyTitle: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
  },
  emptyDesc: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  userRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginVertical: theme.spacing.sm,
  },
  userBubble: {
    maxWidth: '80%',
    backgroundColor: theme.colors.primary,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    borderRadius: theme.radius.lg,
    borderBottomRightRadius: theme.radius.sm,
  },
  userText: {
    ...theme.typography.body,
    color: '#FFF',
  },
  aiRow: {
    flexDirection: 'row',
    marginVertical: theme.spacing.sm,
  },
  aiTag: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: theme.colors.primaryLight,
    color: theme.colors.primary,
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
    lineHeight: 32,
    marginRight: theme.spacing.sm,
  },
  aiContent: {
    flex: 1,
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    marginVertical: theme.spacing.sm,
    gap: theme.spacing.sm,
  },
  errorIcon: {
    fontSize: 20,
  },
  errorContent: {
    flex: 1,
  },
  errorTitle: {
    ...theme.typography.bodySm,
    color: '#991B1B',
    fontWeight: '600',
  },
  errorCode: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginTop: 2,
  },
  retryBtn: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    backgroundColor: theme.colors.error,
    borderRadius: theme.radius.sm,
  },
  retryText: {
    ...theme.typography.caption,
    color: '#FFF',
    fontWeight: '600',
  },
});
