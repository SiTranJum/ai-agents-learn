// AIInsightCard - AI 洞察卡片
// T10: 支持 streaming 状态（status chip + 流式文字）
// 参考: docs/prd/v1/ui-design/03-home-dashboard.md §3.E

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card } from '@shared/ui/Card';
import { theme } from '@app/styles/theme';

export interface AIInsightCardProps {
  insight: string | null;
  isStreaming?: boolean;
  status?: string | null;
  onPress?: () => void;
}

export function AIInsightCard({ insight, isStreaming, status, onPress }: AIInsightCardProps) {
  return (
    <Card>
      <View style={styles.header}>
        <View style={styles.iconWrap}>
          {isStreaming
            ? <ActivityIndicator size="small" color={theme.colors.primary} />
            : <Feather name="zap" size={16} color={theme.colors.primary} />
          }
        </View>
        <Text style={styles.title}>AI 洞察</Text>
      </View>

      {status && <Text style={styles.status}>{status}</Text>}

      {insight ? (
        <Text style={styles.body}>{insight}</Text>
      ) : (
        <Text style={styles.placeholder}>
          {isStreaming ? 'AI 正在为你生成今日建议...' : '记得多喝水、均衡饮食、保持运动。'}
        </Text>
      )}

      {onPress && !isStreaming && (
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
  title: { ...theme.typography.cardTitle, color: theme.colors.textPrimary },
  status: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    fontStyle: 'italic',
    marginBottom: theme.spacing.xs,
  },
  body: { ...theme.typography.body, color: theme.colors.textSecondary, lineHeight: 22 },
  placeholder: { ...theme.typography.body, color: theme.colors.textTertiary, lineHeight: 22 },
  linkRow: { alignSelf: 'flex-end', marginTop: theme.spacing.sm },
  link: { ...theme.typography.bodySm, color: theme.colors.primary, fontWeight: '600' },
});
