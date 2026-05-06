// ChatMessageList - AI 对话消息列表
// AI 左对齐灰底 / 用户右对齐浅橙底 / 系统居中灰字
// 参考: docs/prd/v1/ui-design/14-ai-dialog-and-overlays.md

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';
import { theme } from '@app/styles/theme';
import type { ChatAction, ChatMessage } from '../types/ai.types';

export interface ChatMessageListProps {
  messages: ChatMessage[];
  isAIThinking?: boolean;
  onActionPress?: (action: ChatAction, message: ChatMessage) => void;
}

export function ChatMessageList({
  messages,
  isAIThinking = false,
  onActionPress,
}: ChatMessageListProps) {
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 50);
  }, [messages.length, isAIThinking]);

  return (
    <ScrollView
      ref={scrollRef}
      style={styles.flex1}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      {messages.map((msg) => (
        <Bubble key={msg.id} message={msg} onActionPress={onActionPress} />
      ))}
      {isAIThinking && <TypingIndicator />}
    </ScrollView>
  );
}

function Bubble({
  message,
  onActionPress,
}: {
  message: ChatMessage;
  onActionPress?: (action: ChatAction, message: ChatMessage) => void;
}) {
  if (message.role === 'system') {
    return (
      <View style={styles.systemRow}>
        <Text style={styles.systemText}>{message.content}</Text>
      </View>
    );
  }

  const isAI = message.role === 'ai';

  return (
    <View style={[styles.row, isAI ? styles.rowLeft : styles.rowRight]}>
      <View style={[styles.bubble, isAI ? styles.bubbleAI : styles.bubbleUser]}>
        <Text style={styles.text}>{message.content}</Text>
      </View>

      {isAI && message.actions && message.actions.length > 0 && (
        <View style={styles.actionsRow}>
          {message.actions.map((act) => (
            <TouchableOpacity
              key={act.key}
              style={[
                styles.actionBtn,
                act.variant === 'primary'
                  ? styles.actionPrimary
                  : styles.actionSecondary,
              ]}
              onPress={() => onActionPress?.(act, message)}
              activeOpacity={0.8}
            >
              <Text
                style={[
                  styles.actionText,
                  act.variant === 'primary'
                    ? styles.actionTextPrimary
                    : styles.actionTextSecondary,
                ]}
              >
                {act.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

export function TypingIndicator() {
  const d1 = useRef(new Animated.Value(0)).current;
  const d2 = useRef(new Animated.Value(0)).current;
  const d3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animate = (val: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(val, { toValue: 1, duration: 300, useNativeDriver: true }),
          Animated.timing(val, { toValue: 0, duration: 300, useNativeDriver: true }),
        ])
      );
    const a1 = animate(d1, 0);
    const a2 = animate(d2, 200);
    const a3 = animate(d3, 400);
    a1.start();
    a2.start();
    a3.start();
    return () => {
      a1.stop();
      a2.stop();
      a3.stop();
    };
  }, [d1, d2, d3]);

  const tr = (v: Animated.Value) =>
    v.interpolate({ inputRange: [0, 1], outputRange: [0, -5] });

  return (
    <View style={[styles.row, styles.rowLeft]}>
      <View style={[styles.bubble, styles.bubbleAI, styles.typingBubble]}>
        <Animated.View style={[styles.dot, { transform: [{ translateY: tr(d1) }] }]} />
        <Animated.View style={[styles.dot, { transform: [{ translateY: tr(d2) }] }]} />
        <Animated.View style={[styles.dot, { transform: [{ translateY: tr(d3) }] }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  flex1: { flex: 1 },
  content: {
    paddingVertical: theme.spacing.md,
  },
  row: {
    marginVertical: theme.spacing.xs,
    paddingHorizontal: theme.layout.pageHorizontalPadding,
  },
  rowLeft: { alignItems: 'flex-start' },
  rowRight: { alignItems: 'flex-end' },
  bubble: {
    maxWidth: '78%',
    padding: theme.spacing.md,
    borderRadius: theme.radius.md,
  },
  bubbleAI: { backgroundColor: '#F2F3F5' },
  bubbleUser: { backgroundColor: theme.colors.primaryLight },
  text: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    lineHeight: 22,
  },
  systemRow: {
    alignItems: 'center',
    marginVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
  },
  systemText: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  actionsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.sm,
  },
  actionBtn: {
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
  },
  actionPrimary: { backgroundColor: theme.colors.primary },
  actionSecondary: {
    backgroundColor: theme.colors.bgCard,
    borderWidth: 1,
    borderColor: theme.colors.primary,
  },
  actionText: {
    ...theme.typography.bodySm,
    fontWeight: '600',
  },
  actionTextPrimary: { color: theme.colors.bgCard },
  actionTextSecondary: { color: theme.colors.primary },
  typingBubble: {
    flexDirection: 'row',
    gap: 6,
    paddingVertical: theme.spacing.sm,
    alignItems: 'center',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: theme.colors.textTertiary,
  },
});
