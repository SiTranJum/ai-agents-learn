// AIInsightCard - AI 洞察卡片
// T10: 支持 streaming 状态（status chip + 流式文字）+ 错误态（重试按钮）
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
  error?: string | null;
  onPress?: () => void;
  onRetry?: () => void;
}

export function AIInsightCard({
  insight,
  isStreaming,
  status,
  error,
  onPress,
  onRetry,
}: AIInsightCardProps) {
  const hasError = !!error && !insight;

  return (
    <Card>
      <View style={styles.header}>
        <View style={[styles.iconWrap, hasError && styles.iconWrapError]}>
          {isStreaming ? (
            <ActivityIndicator size="small" color={theme.colors.primary} />
          ) : hasError ? (
            <Feather name="alert-circle" size={16} color={theme.colors.error} />
          ) : (
            <Feather name="zap" size={16} color={theme.colors.primary} />
          )}
        </View>
        <Text style={styles.title}>趋势解读</Text>
      </View>

      {status && <Text style={styles.status}>{status}</Text>}

      {hasError ? (
        <View>
          <Text style={styles.errorText}>AI 服务暂时不可用</Text>
          <Text style={styles.errorDetail}>{error}</Text>
          {onRetry && (
            <TouchableOpacity onPress={onRetry} style={styles.retryBtn}>
              <Feather name="refresh-cw" size={14} color={theme.colors.primary} />
              <Text style={styles.retryText}>重试</Text>
            </TouchableOpacity>
          )}
        </View>
      ) : insight ? (
        <Text style={styles.body}>{insight}</Text>
      ) : (
        <Text style={styles.placeholder}>
          {isStreaming ? 'AI 正在为你生成今日建议...' : '记得多喝水、均衡饮食、保持运动。'}
        </Text>
      )}

      {onPress && !isStreaming && !hasError && (
        <TouchableOpacity onPress={onPress} style={styles.linkRow}>
          <Text style={styles.link}>查看报告 →</Text>
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
  iconWrapError: {
    backgroundColor: '#FEE2E2',
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
  errorText: { ...theme.typography.body, color: theme.colors.error, fontWeight: '600' },
  errorDetail: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginTop: 2,
  },
  retryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    marginTop: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.primaryLight,
    gap: theme.spacing.xs,
  },
  retryText: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  linkRow: { alignSelf: 'flex-end', marginTop: theme.spacing.sm },
  link: { ...theme.typography.bodySm, color: theme.colors.primary, fontWeight: '600' },
});

