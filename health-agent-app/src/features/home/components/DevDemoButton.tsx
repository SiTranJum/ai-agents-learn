// Dev 浮动按钮：仅在 __DEV__ 模式可见
// 跳转到流式 demo 页
// 参考: docs/plans/2026-05-22-streaming-chat-impl-tasks.md §T1

import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { theme } from '@app/styles/theme';
import type { MainStackParamList } from '@app/navigation/types';

type Nav = NativeStackNavigationProp<MainStackParamList>;

export function DevDemoButton() {
  // 正式构建（__DEV__ === false）时不渲染，自动从 bundle 中树摇
  if (!__DEV__) return null;

  const navigation = useNavigation<Nav>();

  return (
    <TouchableOpacity
      style={styles.fab}
      onPress={() => navigation.navigate('StreamingDemo')}
      activeOpacity={0.7}
    >
      <Text style={styles.icon}>🧪</Text>
      <Text style={styles.label}>Demo</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 100, // 避开 AIInputBar(56) + Tab(60)
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1F2937',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.pill,
    gap: theme.spacing.xs,
    ...theme.shadows.brandButton,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    elevation: 8,
  },
  icon: {
    fontSize: 14,
  },
  label: {
    ...theme.typography.caption,
    color: '#FFF',
    fontWeight: '600',
  },
});
