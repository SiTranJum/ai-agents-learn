// ChatMessage - 对话消息气泡
// AI 左对齐灰底 / 用户右对齐浅橙底
// 参考: docs/prd/v1/ui-design/10-plan-create-chat-page.md §3

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Animated } from 'react-native';
import { theme } from '@app/styles/theme';
import type { ChatActionButton, ChatMessage as ChatMsg } from '../types/plan.types';
import { PlanSummaryCard } from './PlanSummaryCard';

export interface ChatMessageBubbleProps {
  message: ChatMsg;
  /** 快捷选项点击 */
  onQuickOptionPress?: (option: string) => void;
  /** 操作按钮点击 */
  onActionPress?: (button: ChatActionButton) => void;
  /** 选项 / 按钮是否可用（消息已被回应后置为 false） */
  optionsActive?: boolean;
}

export function ChatMessageBubble({
  message,
  onQuickOptionPress,
  onActionPress,
  optionsActive = true,
}: ChatMessageBubbleProps) {
  const isAI = message.role === 'ai';

  return (
    <View style={[styles.row, isAI ? styles.rowLeft : styles.rowRight]}>
      <View
        style={[
          styles.bubble,
          isAI ? styles.bubbleAI : styles.bubbleUser,
        ]}
      >
        <Text style={styles.text}>{message.content}</Text>
        {message.planSummary && (
          <PlanSummaryCard summary={message.planSummary} />
        )}
      </View>

      {/* 快捷选项 */}
      {isAI && message.quickOptions && optionsActive && (
        <View style={styles.optionsRow}>
          {message.quickOptions.map((opt) => (
            <TouchableOpacity
              key={opt}
              style={styles.optionBtn}
              onPress={() => onQuickOptionPress?.(opt)}
              activeOpacity={0.7}
            >
              <Text style={styles.optionText}>{opt}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* 操作按钮 */}
      {isAI && message.actionButtons && optionsActive && (
        <View style={styles.actionsRow}>
          {message.actionButtons.map((btn) => (
            <TouchableOpacity
              key={btn.key}
              style={[
                styles.actionBtn,
                btn.variant === 'primary'
                  ? styles.actionPrimary
                  : styles.actionSecondary,
              ]}
              onPress={() => onActionPress?.(btn)}
              activeOpacity={0.8}
            >
              <Text
                style={[
                  styles.actionText,
                  btn.variant === 'primary'
                    ? styles.actionTextPrimary
                    : styles.actionTextSecondary,
                ]}
              >
                {btn.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

// AI 思考中动画（三个点跳动）
export function TypingIndicator() {
  const dot1 = React.useRef(new Animated.Value(0)).current;
  const dot2 = React.useRef(new Animated.Value(0)).current;
  const dot3 = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    const animate = (val: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(val, { toValue: 1, duration: 300, useNativeDriver: true }),
          Animated.timing(val, { toValue: 0, duration: 300, useNativeDriver: true }),
        ])
      );

    const a1 = animate(dot1, 0);
    const a2 = animate(dot2, 200);
    const a3 = animate(dot3, 400);
    a1.start();
    a2.start();
    a3.start();
    return () => {
      a1.stop();
      a2.stop();
      a3.stop();
    };
  }, [dot1, dot2, dot3]);

  const translateOf = (v: Animated.Value) =>
    v.interpolate({ inputRange: [0, 1], outputRange: [0, -5] });

  return (
    <View style={[styles.row, styles.rowLeft]}>
      <View style={[styles.bubble, styles.bubbleAI, styles.typingBubble]}>
        <Animated.View
          style={[styles.dot, { transform: [{ translateY: translateOf(dot1) }] }]}
        />
        <Animated.View
          style={[styles.dot, { transform: [{ translateY: translateOf(dot2) }] }]}
        />
        <Animated.View
          style={[styles.dot, { transform: [{ translateY: translateOf(dot3) }] }]}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    marginVertical: theme.spacing.xs,
    paddingHorizontal: theme.layout.pageHorizontalPadding,
  },
  rowLeft: {
    alignItems: 'flex-start',
  },
  rowRight: {
    alignItems: 'flex-end',
  },
  bubble: {
    maxWidth: '78%',
    padding: theme.spacing.md,
    borderRadius: theme.radius.md,
  },
  bubbleAI: {
    backgroundColor: '#F2F3F5',
  },
  bubbleUser: {
    backgroundColor: theme.colors.primaryLight,
  },
  text: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    lineHeight: 22,
  },
  optionsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.sm,
  },
  optionBtn: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.bgCard,
    borderWidth: 1,
    borderColor: theme.colors.divider,
  },
  optionText: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.sm,
  },
  actionBtn: {
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.pill,
  },
  actionPrimary: {
    backgroundColor: theme.colors.primary,
  },
  actionSecondary: {
    backgroundColor: theme.colors.bgCard,
    borderWidth: 1,
    borderColor: theme.colors.primary,
  },
  actionText: {
    ...theme.typography.bodySm,
    fontWeight: '600',
  },
  actionTextPrimary: {
    color: theme.colors.bgCard,
  },
  actionTextSecondary: {
    color: theme.colors.primary,
  },
  typingBubble: {
    flexDirection: 'row',
    gap: 6,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    alignItems: 'center',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: theme.colors.textTertiary,
  },
});
