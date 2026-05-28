// 工具调用条：显示"🔍 查找鸡胸肉营养中..."，完成后变绿色 ✓
// 圆角胶囊，浅紫底（pending）/ 浅绿底（done）
// T6 从 demo/components/ToolCallChip.tsx 提升

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { theme } from '@app/styles/theme';
import type { ToolCallState } from '../../types/ai.types';

interface Props {
  tool: ToolCallState;
}

export function ToolCallChip({ tool }: Props) {
  const isDone = tool.state === 'done';
  return (
    <View style={[styles.chip, isDone && styles.chipDone]}>
      {isDone ? (
        <Text style={styles.icon}>✓</Text>
      ) : (
        <ActivityIndicator size="small" color="#7B1FA2" style={styles.spinner} />
      )}
      <Text style={[styles.label, isDone && styles.labelDone]}>
        {isDone && tool.summary ? tool.summary : tool.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#F3E5F5',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
    marginVertical: theme.spacing.xs,
  },
  chipDone: {
    backgroundColor: '#E8F5E9',
  },
  spinner: {
    marginRight: theme.spacing.sm,
  },
  icon: {
    ...theme.typography.caption,
    color: '#2E7D32',
    marginRight: theme.spacing.sm,
    fontWeight: '700',
  },
  label: {
    ...theme.typography.caption,
    color: '#6A1B9A',
  },
  labelDone: {
    color: '#2E7D32',
  },
});
