// GlobalAIInputBar - 全局 AI 输入栏
// 挂在 TabNavigator 之上、TabBar 之上，4 个主 Tab 页面共享
// 输入文字 → 跳转 AIDialog 并自动发送
// 这是 Phase 8 的入口

import React, { useCallback } from 'react';
import { View, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AIInputBar } from '@shared/ui/AIInputBar';
import { theme } from '@app/styles/theme';
import type { MainStackParamList } from '@app/navigation/types';

export function GlobalAIInputBar() {
  const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();

  const handleSend = useCallback(
    (text: string) => {
      navigation.navigate('AIDialog', { initialMessage: text });
    },
    [navigation]
  );

  const handleCamera = useCallback(() => {
    navigation.navigate('AIDialog', {});
  }, [navigation]);

  const handleVoice = useCallback(() => {
    navigation.navigate('AIDialog', {});
  }, [navigation]);

  return (
    <View style={styles.wrap}>
      <AIInputBar
        onSend={handleSend}
        onCamera={handleCamera}
        onVoice={handleVoice}
        placeholder="说点什么... (试试'苹果的营养')"
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
