// AIChatOverlay - AI 聊天浮层
// 挂在 GlobalAIInputBar 上方，collapsed → floating → fullscreen 状态机
// 优化 #4：发送消息后先浮层展开，不直接跳全屏

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  Dimensions,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import type { MainStackParamList } from '@app/navigation/types';
import { useAIStore } from '../store/aiStore';
import { useAIChat } from '../hooks/useAIChat';
import type { ChatMessage } from '../types/ai.types';

type Nav = NativeStackNavigationProp<MainStackParamList>;

const SCREEN_HEIGHT = Dimensions.get('window').height;
const MAX_OVERLAY_HEIGHT = SCREEN_HEIGHT * 0.45;
const EXPAND_THRESHOLD = 6; // 消息数超过此值自动提示展开

export function AIChatOverlay() {
  const navigation = useNavigation<Nav>();
  const overlayState = useAIStore((s) => s.overlayState);
  const setOverlayState = useAIStore((s) => s.setOverlayState);
  const chatMessages = useAIStore((s) => s.chatMessages);
  const isAIThinking = useAIStore((s) => s.isAIThinking);
  const { handleAction } = useAIChat();

  const heightAnim = useRef(new Animated.Value(0)).current;
  const scrollRef = useRef<ScrollView>(null);

  // 动画：collapsed=0, floating=MAX_OVERLAY_HEIGHT
  useEffect(() => {
    const toValue = overlayState === 'floating' ? MAX_OVERLAY_HEIGHT : 0;
    Animated.timing(heightAnim, {
      toValue,
      duration: 250,
      useNativeDriver: false,
    }).start();
  }, [overlayState, heightAnim]);

  // 新消息时自动滚到底部
  useEffect(() => {
    if (overlayState === 'floating') {
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }, [chatMessages.length, overlayState]);

  // 消息数超过阈值时提示展开
  const showExpandHint = chatMessages.length >= EXPAND_THRESHOLD && overlayState === 'floating';

  const handleExpand = () => {
    setOverlayState('fullscreen');
    navigation.navigate('AIDialog', {});
  };

  const handleCollapse = () => {
    setOverlayState('collapsed');
  };

  if (overlayState !== 'floating') return null;

  return (
    <Animated.View style={[styles.container, { height: heightAnim }]}>
      {/* 顶部操作栏 */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AI 助手</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={handleExpand} style={styles.headerBtn}>
            <Feather name="maximize-2" size={16} color={theme.colors.textSecondary} />
          </TouchableOpacity>
          <TouchableOpacity onPress={handleCollapse} style={styles.headerBtn}>
            <Feather name="x" size={16} color={theme.colors.textSecondary} />
          </TouchableOpacity>
        </View>
      </View>

      {/* 消息列表 */}
      <ScrollView
        ref={scrollRef}
        style={styles.messageList}
        contentContainerStyle={styles.messageContent}
        showsVerticalScrollIndicator={false}
      >
        {chatMessages.map((msg) => (
          <OverlayMessage key={msg.id} message={msg} onAction={handleAction} />
        ))}
        {isAIThinking && (
          <View style={styles.thinkingRow}>
            <ActivityIndicator size="small" color={theme.colors.primary} />
            <Text style={styles.thinkingText}>思考中...</Text>
          </View>
        )}
      </ScrollView>

      {/* 展开提示 */}
      {showExpandHint && (
        <TouchableOpacity style={styles.expandHint} onPress={handleExpand}>
          <Text style={styles.expandHintText}>对话较长，点击展开全屏</Text>
          <Feather name="chevron-up" size={14} color={theme.colors.primary} />
        </TouchableOpacity>
      )}
    </Animated.View>
  );
}

function OverlayMessage({
  message,
  onAction,
}: {
  message: ChatMessage;
  onAction: (action: any) => void;
}) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <View style={[styles.msgRow, isUser && styles.msgRowUser]}>
      <View
        style={[
          styles.msgBubble,
          isUser && styles.msgBubbleUser,
          isSystem && styles.msgBubbleSystem,
        ]}
      >
        <Text
          style={[
            styles.msgText,
            isUser && styles.msgTextUser,
            isSystem && styles.msgTextSystem,
          ]}
          numberOfLines={4}
        >
          {message.content}
        </Text>
      </View>
      {message.actions && message.actions.length > 0 && (
        <View style={styles.actionsRow}>
          {message.actions.map((action) => (
            <TouchableOpacity
              key={action.key}
              style={[
                styles.actionBtn,
                action.variant === 'primary' && styles.actionBtnPrimary,
              ]}
              onPress={() => onAction(action)}
            >
              <Text
                style={[
                  styles.actionBtnText,
                  action.variant === 'primary' && styles.actionBtnTextPrimary,
                ]}
              >
                {action.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.bgCard,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
  },
  headerTitle: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    fontWeight: '600',
  },
  headerActions: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  headerBtn: {
    width: 28,
    height: 28,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.sm,
  },
  messageList: {
    flex: 1,
  },
  messageContent: {
    padding: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  msgRow: {
    alignItems: 'flex-start',
  },
  msgRowUser: {
    alignItems: 'flex-end',
  },
  msgBubble: {
    maxWidth: '85%',
    backgroundColor: theme.colors.bgPage,
    borderRadius: theme.radius.md,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
  },
  msgBubbleUser: {
    backgroundColor: theme.colors.primaryLight,
  },
  msgBubbleSystem: {
    backgroundColor: '#FFF3CD',
  },
  msgText: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
  },
  msgTextUser: {
    color: theme.colors.textPrimary,
  },
  msgTextSystem: {
    color: '#856404',
  },
  actionsRow: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.xs,
  },
  actionBtn: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.colors.divider,
    backgroundColor: theme.colors.bgCard,
  },
  actionBtnPrimary: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  actionBtnText: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
  },
  actionBtnTextPrimary: {
    color: '#FFFFFF',
  },
  thinkingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    paddingVertical: theme.spacing.xs,
  },
  thinkingText: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  expandHint: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.xs,
    paddingVertical: theme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
  },
  expandHintText: {
    ...theme.typography.caption,
    color: theme.colors.primary,
  },
});
