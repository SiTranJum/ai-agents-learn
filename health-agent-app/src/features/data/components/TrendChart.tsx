// TrendChart - 趋势折线图卡片（含空态/加载态）
// 复用 @shared/charts/LineChart
// 支持叠加"计划目标曲线"（实际值 vs 目标值），体现计划模块服务于数据模块
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
  /** 可选：计划目标曲线（来自计划模块），按日期叠加为第二条线 */
  targetPoints?: TrendPoint[];
}

export function TrendChart({
  title,
  unit,
  points,
  isLoading = false,
  maxLabels = 6,
  targetPoints,
}: TrendChartProps) {
  // 数据抽样以保证图表横轴标签数量适中
  const sampled = sample(points, maxLabels * 2);
  const labels = sample(
    sampled.map((p) => formatLabel(p.date)),
    maxLabels
  );

  // 目标曲线：按实际曲线抽样后的日期对齐取值（缺失则取最近一个目标值）
  const hasTarget = !!targetPoints && targetPoints.length > 0;
  const targetValues = hasTarget
    ? sampled.map((p) => nearestTargetValue(targetPoints!, p.date))
    : [];
  // 仅当对齐后存在有效目标值时才叠加
  const showTarget = hasTarget && targetValues.some((v) => v !== null);

  const datasets: Array<{ data: number[]; color?: (o: number) => string }> = [
    { data: sampled.map((p) => p.value), color: () => theme.colors.primary },
  ];
  if (showTarget) {
    // chart-kit 不接受 null，缺口用前一个有效值填充以保证连线
    datasets.push({
      data: fillForward(targetValues, sampled.map((p) => p.value)),
      color: () => theme.colors.textTertiary,
    });
  }

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
        <>
          <LineChart
            data={{ labels, datasets }}
            width={Dimensions.get('window').width - 32 - 32}
            height={200}
          />
          {showTarget && (
            <View style={styles.legend}>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: theme.colors.primary }]} />
                <Text style={styles.legendText}>实际</Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: theme.colors.textTertiary }]} />
                <Text style={styles.legendText}>计划目标</Text>
              </View>
            </View>
          )}
        </>
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

/** 在目标曲线中找指定日期的目标值；精确命中优先，否则取日期不晚于它的最近一个。 */
function nearestTargetValue(targets: TrendPoint[], date: string): number | null {
  let candidate: number | null = null;
  for (const t of targets) {
    if (t.date === date) return t.value;
    if (t.date <= date) {
      candidate = t.value;
    } else {
      break;
    }
  }
  return candidate;
}

/** 把目标值数组中的 null 用前一个有效值填充；开头为 null 时用实际值兜底，避免曲线断裂。 */
function fillForward(values: Array<number | null>, fallback: number[]): number[] {
  const out: number[] = [];
  let last: number | null = null;
  for (let i = 0; i < values.length; i += 1) {
    const v = values[i];
    if (v !== null) {
      last = v;
      out.push(v);
    } else {
      out.push(last ?? fallback[i] ?? 0);
    }
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
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: theme.spacing.lg,
    marginTop: theme.spacing.sm,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  legendText: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
  },
});
