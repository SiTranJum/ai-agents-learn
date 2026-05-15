// GlobalAIInputBar - 全局 AI 输入栏 + 浮层
// 挂在 TabNavigator 之上、TabBar 之上，4 个主 Tab 页面共享
// 优化 #4：发送消息后先展开浮层，不直接跳全屏

import React, { useCallback } from 'react';
import { View, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AIInputBar } from '@shared/ui/AIInputBar';
import { theme } from '@app/styles/theme';
import type { MainStackParamList } from '@app/navigation/types';
import { useAIStore } from '../store/aiStore';
import { useAIChat } from '../hooks/useAIChat';
import { AIChatOverlay } from './AIChatOverlay';

export function GlobalAIInputBar() {
  const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();
  const overlayState = useAIStore((s) => s.overlayState);
  const setOverlayState = useAIStore((s) => s.setOverlayState);
  const { sendMessage } = useAIChat();

  const handleSend = useCallback(
    (text: string) => {
      if (overlayState === 'collapsed') {
        // 首次发送：展开浮层 + 发消息
        setOverlayState('floating');
      }
      // 浮层已展开：直接发消息（浮层内显示）
      sendMessage(text);
    },
    [overlayState, setOverlayState, sendMessage]
  );

  const handleCamera = useCallback(() => {
    // 拍照直接进全屏（需要相机权限等复杂交互）
    setOverlayState('fullscreen');
    navigation.navigate('AIDialog', {});
  }, [navigation, setOverlayState]);

  const handleVoice = useCallback(() => {
    // 语音也进全屏
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
