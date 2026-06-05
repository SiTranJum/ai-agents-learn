// AIToastNotification - 弹幕式 AI 消息通知
// 监听最新的 AI 消息，在首页输入框上方以弹幕形式滑动显示
// 参考抖音直播弹幕效果

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
import type { ChatMessage, ChatCard } from '../types/ai.types';

type Nav = NativeStackNavigationProp<MainStackParamList>;

interface ToastContent {
  messageId: string;
  text: string;
  hasCard: boolean;
  cardType?: string;
  duration: number; // 停留时长（毫秒）
}

/** 从 AI 消息提取弹幕内容 */
function extractToastContent(message: ChatMessage): ToastContent | null {
  if (message.role !== 'assistant' && message.role !== 'ai') return null;
  if (message.isStreaming) return null; // 流式中不显示

  // 优先显示卡片摘要
  if (message.segments) {
    const cardSegment = message.segments.find((s) => s.kind === 'card');
    if (cardSegment && cardSegment.kind === 'card') {
      const card = cardSegment.card;
      return {
        messageId: message.id,
        text: formatCardSummary(card),
        hasCard: true,
        cardType: card.type,
        duration: 5000, // 卡片停留 5 秒
      };
    }
  }

  // 纯文本消息
  const text = message.content || '';
  if (!text.trim()) return null;

  return {
    messageId: message.id,
    text: text.length > 50 ? `${text.slice(0, 50)}...` : text,
    hasCard: false,
    duration: 3000, // 文字停留 3 秒
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
      return '🤖 AI 回复';
  }
}

export function AIToastNotification() {
  const navigation = useNavigation<Nav>();
  const messages = useAIStore((s) => s.chatMessages);
  const lastToastMessageId = useAIStore((s) => s.lastToastMessageId);
  const setLastToastMessageId = useAIStore((s) => s.setLastToastMessageId);
  const incrementUnread = useAIStore((s) => s.incrementUnread);

  const [currentToast, setCurrentToast] = useState<ToastContent | null>(null);
  const translateX = useRef(new Animated.Value(400)).current; // 从右侧滑入
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];

    // 已经弹过幕的消息不再重复
    if (lastMessage.id === lastToastMessageId) return;

    const content = extractToastContent(lastMessage);
    if (!content) return;

    // 显示弹幕
    setCurrentToast(content);
    setLastToastMessageId(content.messageId);
    incrementUnread();

    // 动画：从右向左滑入
    translateX.setValue(400);
    opacity.setValue(0);
    Animated.parallel([
      Animated.timing(translateX, {
        toValue: 0,
        duration: 500,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();

    // 停留后淡出
    const timer = setTimeout(() => {
      Animated.parallel([
        Animated.timing(translateX, {
          toValue: -400,
          duration: 400,
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
    }, content.duration);

    return () => clearTimeout(timer);
  }, [messages, lastToastMessageId, setLastToastMessageId, incrementUnread, translateX, opacity]);

  if (!currentToast) return null;

  const handlePress = () => {
    // 点击弹幕 → 进入全屏对话页
    navigation.navigate('AIDialog', {});
    // 立即隐藏弹幕
    Animated.parallel([
      Animated.timing(translateX, {
        toValue: -400,
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
          transform: [{ translateX }],
          opacity,
        },
      ]}
    >
      <TouchableOpacity
        style={styles.toast}
        onPress={handlePress}
        activeOpacity={0.8}
      >
        <Text style={styles.text} numberOfLines={2}>
          🤖 {currentToast.text}
        </Text>
        {currentToast.hasCard && (
          <Text style={styles.hint}>点击查看详情</Text>
        )}
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 120, // 在输入框上方 60px（输入框56px + TabBar60px + 间隙）
    left: theme.spacing.md,
    right: theme.spacing.md,
    zIndex: 999,
  },
  toast: {
    backgroundColor: 'rgba(50, 50, 50, 0.95)',
    borderRadius: theme.radius.lg,
    padding: theme.spacing.md,
    ...theme.shadows.card,
  },
  text: {
    ...theme.typography.body,
    color: '#FFFFFF',
    lineHeight: 20,
  },
  hint: {
    ...theme.typography.caption,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: theme.spacing.xs,
  },
});
