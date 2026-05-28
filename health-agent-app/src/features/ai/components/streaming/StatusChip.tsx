// 状态条：节点切换时显示"正在分析饮食..."等
// 圆角胶囊，浅蓝底 + 旋转 spinner
// T6 从 demo/components/StatusChip.tsx 提升到正式组件目录

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { theme } from '@app/styles/theme';

interface Props {
  label: string;
}

export function StatusChip({ label }: Props) {
  return (
    <View style={styles.chip}>
      <ActivityIndicator size="small" color="#1E88E5" style={styles.spinner} />
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#E3F2FD',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
    marginVertical: theme.spacing.xs,
  },
  spinner: {
    marginRight: theme.spacing.sm,
  },
  label: {
    ...theme.typography.caption,
    color: '#1565C0',
  },
});
