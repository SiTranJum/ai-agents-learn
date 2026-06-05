// GlobalAIInputBar - 全局 AI 输入栏 + 浮层
// 挂在 TabNavigator 之上、TabBar 之上，4 个主 Tab 页面共享
// T6 后：发消息先展开半屏浮层（流式），浮层内可展开全屏

import React, { useCallback } from 'react';
import { View, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AIInputBar } from '@shared/ui/AIInputBar';
import { theme } from '@app/styles/theme';
import type { MainStackParamList } from '@app/navigation/types';
import { useAIStore } from '../store/aiStore';
import { useStreamingChat } from '../hooks/useStreamingChat';
import { AIChatOverlay } from './AIChatOverlay';

export function GlobalAIInputBar() {
  const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();
  const overlayState = useAIStore((s) => s.overlayState);
  const setOverlayState = useAIStore((s) => s.setOverlayState);
  const hasMessages = useAIStore((s) => s.chatMessages.length > 0);
  const { send } = useStreamingChat();

  const handleSend = useCallback(
    (text: string) => {
      if (overlayState === 'collapsed') {
        setOverlayState('floating');
      }
      send(text);
    },
    [overlayState, setOverlayState, send]
  );

  const handleInputPress = useCallback(() => {
    // 有历史消息时，点击输入框自动展开浮层（如果未展开）
    console.log('[GlobalAIInputBar] onInputPress triggered', { hasMessages, overlayState });
    if (hasMessages && overlayState === 'collapsed') {
      console.log('[GlobalAIInputBar] Opening overlay');
      setOverlayState('floating');
    }
  }, [hasMessages, overlayState, setOverlayState]);

  const handleCamera = useCallback(() => {
    setOverlayState('fullscreen');
    navigation.navigate('AIDialog', {});
  }, [navigation, setOverlayState]);

  const handleVoice = useCallback(() => {
    setOverlayState('fullscreen');
    navigation.navigate('AIDialog', {});
  }, [navigation, setOverlayState]);

  return (
    <View style={styles.wrap}>
      <AIChatOverlay />
      <AIInputBar
        onSend={handleSend}
        onCamera={handleCamera}
        onVoice={handleVoice}
        onInputPress={handleInputPress}
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
