// TrendChart - 趋势折线图卡片（含空态/加载态）
// 复用 @shared/charts/LineChart
// 参考: docs/prd/v1/ui-design/06-data-page.md §3

import React from 'react';
import { View, Text, ActivityIndicator, StyleSheet, Dimensions } from 'react-native';
import { LineChart } from '@shared/charts/LineChart';
import { Card } from '@shared/ui/Card';
import { theme } from '@app/styles/theme';
import type { TrendPoint } from '../types/data.types';

export interface TrendChartProps {
  title: string;
  unit: string;
  points: TrendPoint[];
  isLoading?: boolean;
  /** 最多展示标签数（避免横轴拥挤） */
  maxLabels?: number;
}

export function TrendChart({
  title,
  unit,
  points,
  isLoading = false,
  maxLabels = 6,
}: TrendChartProps) {
  // 数据抽样以保证图表横轴标签数量适中
  const sampled = sample(points, maxLabels * 2);
  const labels = sample(
    sampled.map((p) => formatLabel(p.date)),
    maxLabels
  );

  return (
    <Card>
      <View style={styles.header}>
        <Text style={styles.title}>{title}趋势</Text>
        <Text style={styles.unit}>单位: {unit}</Text>
      </View>

      {isLoading ? (
        <View style={styles.loading}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      ) : sampled.length < 2 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>暂无足够数据生成趋势图</Text>
        </View>
      ) : (
        <LineChart
          data={{
            labels,
            datasets: [{ data: sampled.map((p) => p.value) }],
          }}
          width={Dimensions.get('window').width - 32 - 32}
          height={200}
        />
      )}
    </Card>
  );
}

function sample<T>(arr: T[], n: number): T[] {
  if (arr.length <= n) return arr;
  const step = Math.floor(arr.length / n);
  const out: T[] = [];
  for (let i = 0; i < arr.length; i += step) {
    out.push(arr[i]);
    if (out.length >= n) break;
  }
  if (out[out.length - 1] !== arr[arr.length - 1]) {
    out[out.length - 1] = arr[arr.length - 1];
  }
  return out;
}

function formatLabel(dateStr: string): string {
  // YYYY-MM-DD → M/D
  const parts = dateStr.split('-');
  if (parts.length !== 3) return dateStr;
  return `${Number(parts[1])}/${Number(parts[2])}`;
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: theme.spacing.sm,
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  unit: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  loading: {
    height: 200,
    alignItems: 'center',
    justifyContent: 'center',
  },
  empty: {
    height: 200,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyText: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
  },
});
