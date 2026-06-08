// AIToastNotification - 弹幕式 AI 消息通知
// 监听最新的 AI 消息，在首页左下角/右下角以弹幕形式显示
// 显示流式状态（识别意图、分析饮食）+ 文本内容 + 卡片摘要

import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Easing,
  ScrollView,
  Pressable,
} from 'react-native';
import { BlurView } from 'expo-blur';
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
  const setLastToastMessageId = useAIStore((s) => s.setLastToastMessageId);
  const incrementUnread = useAIStore((s) => s.incrementUnread);

  const [currentToast, setCurrentToast] = useState<ToastContent | null>(null);
  const currentMessageIdRef = useRef<string | null>(null); // 追踪当前弹幕对应的消息 ID
  const translateY = useRef(new Animated.Value(200)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const fadeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];

    // 只处理 AI 消息
    const content = extractToastContent(lastMessage);
    if (!content) return;

    // 同一条消息的流式更新：只刷新内容，不重新触发动画
    if (lastMessage.id === currentMessageIdRef.current) {
      setCurrentToast(content);

      // 流式完成时设置淡出定时器
      if (!lastMessage.isStreaming) {
        if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);
        fadeTimerRef.current = setTimeout(() => {
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
            currentMessageIdRef.current = null;
          });
        }, 5000);
      }
      return;
    }

    // 新消息：更新 ref、显示弹幕、触发动画
    currentMessageIdRef.current = lastMessage.id;
    setCurrentToast(content);
    setLastToastMessageId(content.messageId);

    if (!lastMessage.isStreaming) {
      incrementUnread();
    }

    // 清除旧定时器
    if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);

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

    // 非流式消息：5秒后淡出
    if (!lastMessage.isStreaming) {
      fadeTimerRef.current = setTimeout(() => {
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
          currentMessageIdRef.current = null;
        });
      }, 5000);
    }
  }, [messages]); // eslint-disable-line react-hooks/exhaustive-deps

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
      <BlurView intensity={40} tint="light" style={styles.blur}>
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          nestedScrollEnabled
          scrollEnabled
          bounces={false}
          overScrollMode="never"
        >
          {currentToast.lines.map((line, idx) => (
            <Text key={idx} style={styles.text}>
              {line}
            </Text>
          ))}
        </ScrollView>
        {currentToast.hasCard && (
          <Pressable onPress={handlePress} style={styles.expandBtn}>
            <Text style={styles.hint}>轻触展开</Text>
          </Pressable>
        )}
      </BlurView>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 70, // TabBar(60px) + 10px 间距
    left: theme.spacing.md,
    maxWidth: 260, // 只占左下角小块区域
    maxHeight: 160, // 最大高度，超出可滚动
    zIndex: 999,
    // 轻微投影，让毛玻璃块从背景中浮起来
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 4,
  },
  blur: {
    borderRadius: theme.radius.lg,
    overflow: 'hidden', // 关键：裁剪模糊到圆角内
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    // 加厚白底，彻底遮住背景文字
    backgroundColor: 'rgba(255, 255, 255, 0.75)',
  },
  scrollView: {
    maxHeight: 120, // 固定最大高度，超出部分可滚动
  },
  scrollContent: {
    paddingBottom: theme.spacing.xs,
  },
  text: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    lineHeight: 20,
    marginBottom: 4,
  },
  expandBtn: {
    alignSelf: 'flex-start',
    marginTop: theme.spacing.xs,
    paddingTop: theme.spacing.xs,
  },
  hint: {
    ...theme.typography.caption,
    color: theme.colors.primary,
    fontWeight: '600',
  },
});
