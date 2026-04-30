// PlanSummaryCard - 计划摘要卡片
// 嵌套在 AI 消息气泡中（对话流第 4 步）
// 参考: docs/prd/v1/ui-design/10-plan-create-chat-page.md §3

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { theme } from '@app/styles/theme';
import type { PlanSummary } from '../types/plan.types';

export interface PlanSummaryCardProps {
  summary: PlanSummary;
}

export function PlanSummaryCard({ summary }: PlanSummaryCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Feather name="clipboard" size={18} color={theme.colors.primary} />
        <Text style={styles.name}>{summary.name}</Text>
      </View>
      {summary.targetWeight != null && (
        <Row label="目标" value={`${summary.targetWeight}kg`} />
      )}
      <Row label="周期" value={summary.duration} />
      {summary.phases != null && (
        <Row label="阶段" value={`${summary.phases}个阶段`} />
      )}
      {summary.dailyCalorieTarget != null && (
        <Row label="每日热量" value={`${summary.dailyCalorieTarget} kcal`} />
      )}
      {summary.keyRules.length > 0 && (
        <View style={styles.rules}>
          <Text style={styles.rulesTitle}>关键规则</Text>
          {summary.keyRules.map((r, idx) => (
            <Text key={idx} style={styles.ruleItem}>
              · {r}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.primary,
    padding: theme.spacing.md,
    marginTop: theme.spacing.sm,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    marginBottom: theme.spacing.sm,
  },
  name: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  rowLabel: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  rowValue: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  rules: {
    marginTop: theme.spacing.xs,
    paddingTop: theme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
  },
  rulesTitle: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginBottom: 4,
  },
  ruleItem: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    lineHeight: 22,
  },
});
