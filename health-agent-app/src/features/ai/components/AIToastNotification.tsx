// AIToastNotification - 弹幕式 AI 消息通知
// 监听最新的 AI 消息，在首页左下角/右下角以弹幕形式显示
// 显示流式状态（识别意图、分析饮食）+ 文本内容 + 卡片摘要

import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  Easing,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { theme } from '@app/styles/theme';
import type { MainStackParamList } from '@app/navigation/types';
import { useAIStore } from '../store/aiStore';
import type { ChatMessage, ChatCard, MessageSegment } from '../types/ai.types';

type Nav = NativeStackNavigationProp<MainStackParamList>;

interface ToastContent {
  messageId: string;
  lines: string[]; // 多行内容：[status, text, cardSummary]
  hasCard: boolean;
}

/** 从 AI 消息提取弹幕内容 */
function extractToastContent(message: ChatMessage): ToastContent | null {
  if (message.role !== 'assistant' && message.role !== 'ai') return null;

  const lines: string[] = [];

  // 1. 显示 status（识别意图、分析饮食等）
  if (message.status) {
    lines.push(`📝 ${message.status}`);
  }

  // 2. 显示文本内容（text_delta 累积）
  if (message.segments) {
    const textSegments = message.segments.filter((s) => s.kind === 'text');
    if (textSegments.length > 0) {
      const fullText = textSegments.map((s) => s.kind === 'text' ? s.content : '').join('');
      if (fullText.trim()) {
        const truncated = fullText.length > 60 ? `${fullText.slice(0, 60)}...` : fullText;
        lines.push(truncated);
      }
    }

    // 3. 显示卡片摘要
    const cardSegment = message.segments.find((s) => s.kind === 'card');
    if (cardSegment && cardSegment.kind === 'card') {
      const summary = formatCardSummary(cardSegment.card);
      if (summary) {
        lines.push(summary);
      }
    }
  }

  if (lines.length === 0) return null;

  return {
    messageId: message.id,
    lines,
    hasCard: message.segments?.some((s) => s.kind === 'card') ?? false,
  };
}

/** 格式化卡片摘要 */
function formatCardSummary(card: ChatCard): string {
  switch (card.type) {
    case 'diet_parse': {
      const payload = card.payload as any;
      const mealLabel: Record<string, string> = {
        breakfast: '🍳 早餐',
        lunch: '🍱 午餐',
        dinner: '🍲 晚餐',
        snack: '🍎 加餐',
      };
      const meal = mealLabel[payload.meal_type] || '饮食';
      const foods = payload.foods || [];
      const foodNames = foods.slice(0, 2).map((f: any) => f.name).join('、');
      return `${meal}: ${foodNames}${foods.length > 2 ? '...' : ''}`;
    }
    case 'body_parse': {
      const payload = card.payload as any;
      const typeLabel: Record<string, string> = {
        water: '💧 饮水',
        sleep: '😴 睡眠',
        exercise: '🏃 运动',
        bowel: '🚽 排便',
      };
      const label = typeLabel[payload.record_type] || '健康数据';
      if (payload.record_type === 'water') {
        return `${label}: ${payload.water_amount}ml`;
      }
      return `${label}已记录`;
    }
    default:
      return '';
  }
}

export function AIToastNotification() {
  const navigation = useNavigation<Nav>();
  const messages = useAIStore((s) => s.chatMessages);
  const lastToastMessageId = useAIStore((s) => s.lastToastMessageId);
  const setLastToastMessageId = useAIStore((s) => s.setLastToastMessageId);
  const incrementUnread = useAIStore((s) => s.incrementUnread);

  const [currentToast, setCurrentToast] = useState<ToastContent | null>(null);
  const translateY = useRef(new Animated.Value(200)).current; // 从下往上
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];

    // 每次消息更新都检查（包括流式更新）
    const content = extractToastContent(lastMessage);
    if (!content) return;

    // 如果是同一条消息的更新，刷新内容但不重新触发动画
    if (lastMessage.id === currentToast?.messageId) {
      setCurrentToast(content);
      return;
    }

    // 新消息：显示弹幕并记录
    setCurrentToast(content);
    setLastToastMessageId(content.messageId);

    // 只在非流式状态增加未读（流式完成后才算一条完整消息）
    if (!lastMessage.isStreaming) {
      incrementUnread();
    }

    // 动画：从下往上弹出
    translateY.setValue(200);
    opacity.setValue(0);
    Animated.parallel([
      Animated.timing(translateY, {
        toValue: 0,
        duration: 400,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();

    // 如果消息流式完成，5秒后淡出
    if (!lastMessage.isStreaming) {
      const timer = setTimeout(() => {
        Animated.parallel([
          Animated.timing(translateY, {
            toValue: 200,
            duration: 300,
            easing: Easing.in(Easing.cubic),
            useNativeDriver: true,
          }),
          Animated.timing(opacity, {
            toValue: 0,
            duration: 300,
            useNativeDriver: true,
          }),
        ]).start(() => {
          setCurrentToast(null);
        });
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [messages, currentToast, lastToastMessageId, setLastToastMessageId, incrementUnread, translateY, opacity]);

  if (!currentToast) return null;

  const handlePress = () => {
    // 点击弹幕 → 进入全屏对话页
    navigation.navigate('AIDialog', {});
    // 立即隐藏弹幕
    Animated.parallel([
      Animated.timing(translateY, {
        toValue: 200,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      setCurrentToast(null);
    });
  };

  return (
    <Animated.View
      style={[
        styles.container,
        {
          transform: [{ translateY }],
          opacity,
        },
      ]}
    >
      <TouchableOpacity
        style={styles.toast}
        onPress={handlePress}
        activeOpacity={0.8}
      >
        {currentToast.lines.map((line, idx) => (
          <Text key={idx} style={styles.text} numberOfLines={1}>
            {line}
          </Text>
        ))}
        {currentToast.hasCard && (
          <Text style={styles.hint}>轻触展开</Text>
        )}
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 70, // TabBar(60px) + 10px 间距
    left: theme.spacing.md,
    maxWidth: 240, // 只占左下角小块区域
    zIndex: 999,
  },
  toast: {
    // 完全透明，无背景无边框，裸露的文字弹幕
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.sm,
  },
  text: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    lineHeight: 20,
    marginBottom: 4,
    // 文字描边，确保在任何背景上都清晰可见
    textShadowColor: 'rgba(255, 255, 255, 0.9)',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 3,
    fontWeight: '600',
  },
  hint: {
    ...theme.typography.caption,
    color: theme.colors.primary,
    marginTop: theme.spacing.xs,
    fontWeight: '600',
    textShadowColor: 'rgba(255, 255, 255, 0.8)',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 2,
  },
});
