// GlobalAIInputBar - 全局 AI 输入栏 + 浮层
// 挂在 TabNavigator 之上、TabBar 之上，4 个主 Tab 页面共享
// T6 后：发送消息直接跳全屏 AIDialogScreen（流式），浮层仅用于展示历史

import React, { useCallback } from 'react';
import { View, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AIInputBar } from '@shared/ui/AIInputBar';
import { theme } from '@app/styles/theme';
import type { MainStackParamList } from '@app/navigation/types';
import { useAIStore } from '../store/aiStore';
import { AIChatOverlay } from './AIChatOverlay';

export function GlobalAIInputBar() {
  const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();
  const overlayState = useAIStore((s) => s.overlayState);
  const setOverlayState = useAIStore((s) => s.setOverlayState);
  const hasMessages = useAIStore((s) => s.chatMessages.length > 0);

  const handleSend = useCallback(
    (text: string) => {
      // T6: 发消息直接进全屏流式对话，不走浮层老路径
      setOverlayState('fullscreen');
      navigation.navigate('AIDialog', { initialMessage: text });
    },
    [navigation, setOverlayState]
  );

  const handleFocus = useCallback(() => {
    if (overlayState === 'collapsed' && hasMessages) {
      setOverlayState('floating');
    }
  }, [overlayState, hasMessages, setOverlayState]);

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
        onFocus={handleFocus}
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
