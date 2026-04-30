// NutritionAnalysisCard - 营养分布卡片（饼图 + 数值）
// 参考: docs/specs/frontend/modules/13-data-module.md §P09

import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { PieChart } from '@shared/charts/PieChart';
import { Card } from '@shared/ui/Card';
import { theme } from '@app/styles/theme';
import type { AnalysisData } from '../types/data.types';

export interface NutritionAnalysisCardProps {
  data: AnalysisData['nutritionDistribution'];
}

export function NutritionAnalysisCard({ data }: NutritionAnalysisCardProps) {
  return (
    <Card>
      <Text style={styles.title}>营养分布</Text>
      <PieChart
        size={Dimensions.get('window').width - 64}
        data={[
          { name: '碳水', value: data.carbsPercent, color: theme.colors.success },
          { name: '蛋白质', value: data.proteinPercent, color: theme.colors.info },
          { name: '脂肪', value: data.fatPercent, color: theme.colors.warning },
        ]}
      />
      <View style={styles.kvList}>
        <Row label="碳水" value={`${data.carbs}g (${data.carbsPercent}%)`} />
        <Row label="蛋白质" value={`${data.protein}g (${data.proteinPercent}%)`} />
        <Row label="脂肪" value={`${data.fat}g (${data.fatPercent}%)`} />
      </View>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.kvRow}>
      <Text style={styles.kvLabel}>{label}</Text>
      <Text style={styles.kvValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
  },
  kvList: {
    marginTop: theme.spacing.sm,
  },
  kvRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  kvLabel: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
  kvValue: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
});
