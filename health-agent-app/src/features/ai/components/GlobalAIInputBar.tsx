// GlobalAIInputBar - 全局 AI 输入栏 + 弹幕通知
// 挂在 TabNavigator 之上、TabBar 之上，4 个主 Tab 页面共享
// 废除半屏浮层，改为弹幕通知 + 常驻展开按钮

import React, { useCallback } from 'react';
import { View, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AIInputBar } from '@shared/ui/AIInputBar';
import { theme } from '@app/styles/theme';
import type { MainStackParamList } from '@app/navigation/types';
import { useAIStore } from '../store/aiStore';
import { useStreamingChat } from '../hooks/useStreamingChat';
import { AIToastNotification } from './AIToastNotification';

export function GlobalAIInputBar() {
  const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();
  const unreadCount = useAIStore((s) => s.unreadCount);
  const { send } = useStreamingChat();

  const handleSend = useCallback(
    (text: string) => {
      send(text);
    },
    [send]
  );

  const handleExpandPress = useCallback(() => {
    // 点击展开按钮 → 进入全屏对话页
    navigation.navigate('AIDialog', {});
  }, [navigation]);

  const handleCamera = useCallback(() => {
    navigation.navigate('AIDialog', {});
  }, [navigation]);

  const handleVoice = useCallback(() => {
    navigation.navigate('AIDialog', {});
  }, [navigation]);

  return (
    <View style={styles.wrap}>
      {/* 弹幕通知 */}
      <AIToastNotification />

      {/* 输入栏 */}
      <AIInputBar
        onSend={handleSend}
        onCamera={handleCamera}
        onVoice={handleVoice}
        onExpandPress={handleExpandPress}
        unreadCount={unreadCount}
        placeholder="说点什么..."
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
    backgroundColor: theme.colors.bgPage,
  },
});
