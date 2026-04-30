// AIInsightSummaryCard - AI 洞察总结卡片
// 渲染 2-3 条洞察
// 参考: docs/specs/frontend/modules/13-data-module.md §P09

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card } from '@shared/ui/Card';
import { theme } from '@app/styles/theme';
import type { AnalysisInsight } from '../types/data.types';

export interface AIInsightSummaryCardProps {
  insights: AnalysisInsight[];
}

const ICONS: Record<AnalysisInsight['type'], keyof typeof Feather.glyphMap> = {
  calorie: 'pie-chart',
  nutrition: 'grid',
  weight: 'trending-down',
  habit: 'clock',
  achievement: 'award',
};

export function AIInsightSummaryCard({ insights }: AIInsightSummaryCardProps) {
  return (
    <Card>
      <View style={styles.header}>
        <View style={styles.iconWrap}>
          <Feather name="zap" size={16} color={theme.colors.primary} />
        </View>
        <Text style={styles.title}>AI 洞察</Text>
      </View>

      {insights.map((it, idx) => (
        <View
          key={idx}
          style={[styles.item, idx === insights.length - 1 && styles.itemLast]}
        >
          <Feather
            name={ICONS[it.type]}
            size={16}
            color={theme.colors.primary}
            style={styles.itemIcon}
          />
          <View style={styles.itemBody}>
            <Text style={styles.itemTitle}>{it.title}</Text>
            <Text style={styles.itemDesc}>{it.description}</Text>
          </View>
        </View>
      ))}
    </Card>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  iconWrap: {
    width: 28,
    height: 28,
    borderRadius: theme.radius.full,
    backgroundColor: theme.colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  item: {
    flexDirection: 'row',
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
    gap: theme.spacing.sm,
  },
  itemLast: {
    borderBottomWidth: 0,
  },
  itemIcon: {
    marginTop: 2,
  },
  itemBody: {
    flex: 1,
  },
  itemTitle: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
    marginBottom: 2,
  },
  itemDesc: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    lineHeight: 20,
  },
});
