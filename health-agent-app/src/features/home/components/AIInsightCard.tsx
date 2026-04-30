// AIInsightCard - AI 洞察卡片
// 灯泡图标 + 一句话建议 + "查看详情"链接
// 参考: docs/prd/v1/ui-design/03-home-dashboard.md §3.E

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card } from '@shared/ui/Card';
import { theme } from '@app/styles/theme';

export interface AIInsightCardProps {
  insight: string;
  onPress?: () => void;
}

export function AIInsightCard({ insight, onPress }: AIInsightCardProps) {
  return (
    <Card>
      <View style={styles.header}>
        <View style={styles.iconWrap}>
          <Feather name="zap" size={16} color={theme.colors.primary} />
        </View>
        <Text style={styles.title}>AI 洞察</Text>
      </View>
      <Text style={styles.body}>{insight}</Text>
      {onPress && (
        <TouchableOpacity onPress={onPress} style={styles.linkRow}>
          <Text style={styles.link}>查看详情 →</Text>
        </TouchableOpacity>
      )}
    </Card>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  iconWrap: {
    width: 28,
    height: 28,
    borderRadius: theme.radius.full,
    backgroundColor: theme.colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: theme.spacing.sm,
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  body: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    lineHeight: 22,
  },
  linkRow: {
    alignSelf: 'flex-end',
    marginTop: theme.spacing.sm,
  },
  link: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
    fontWeight: '600',
  },
});
