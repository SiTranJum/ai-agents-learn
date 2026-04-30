// NutritionSummary - 今日摄入汇总卡片
// 热量进度条 + 三大营养素环形图
// 参考: docs/prd/v1/ui-design/04-diet-record-page.md §3, §5

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Card } from '@shared/ui/Card';
import { ProgressBar } from '@shared/ui/ProgressBar';
import { CircularProgress } from '@shared/ui/CircularProgress';
import { theme } from '@app/styles/theme';
import type { DietPageData } from '../types/diet.types';

export interface NutritionSummaryProps {
  totalCalories: DietPageData['totalCalories'];
  nutrients: DietPageData['nutrients'];
  /** 顶部提示文案（如"午餐待确认，暂未计入总摄入"） */
  hint?: string;
}

export function NutritionSummary({
  totalCalories,
  nutrients,
  hint,
}: NutritionSummaryProps) {
  const ratio =
    totalCalories.target > 0
      ? Math.round((totalCalories.current / totalCalories.target) * 100)
      : 0;

  return (
    <Card>
      <Text style={styles.title}>今日摄入</Text>

      <View style={styles.calorieRow}>
        <Text style={styles.calorieValue}>
          {totalCalories.current.toLocaleString()}
          <Text style={styles.calorieTarget}>
            {' '}
            / {totalCalories.target.toLocaleString()} kcal
          </Text>
        </Text>
        <Text style={styles.percentText}>{ratio}%</Text>
      </View>

      <ProgressBar
        current={totalCalories.current}
        target={totalCalories.target}
        color={theme.colors.primary}
        height={10}
      />

      {hint && <Text style={styles.hint}>{hint}</Text>}

      <Text style={styles.subTitle}>营养素占比</Text>
      <View style={styles.ringRow}>
        <NutrientRing
          label="碳水"
          current={nutrients.carbs.current}
          target={nutrients.carbs.target}
          color={theme.colors.success}
        />
        <NutrientRing
          label="蛋白质"
          current={nutrients.protein.current}
          target={nutrients.protein.target}
          color={theme.colors.info}
        />
        <NutrientRing
          label="脂肪"
          current={nutrients.fat.current}
          target={nutrients.fat.target}
          color={theme.colors.warning}
        />
      </View>
    </Card>
  );
}

interface NutrientRingProps {
  label: string;
  current: number;
  target: number;
  color: string;
}

function NutrientRing({ label, current, target, color }: NutrientRingProps) {
  return (
    <View style={styles.ringWrap}>
      <View style={styles.ringCircle}>
        <CircularProgress
          current={current}
          target={target}
          size={68}
          strokeWidth={8}
          color={color}
        />
        <View style={styles.ringInner} pointerEvents="none">
          <Text style={styles.ringValue}>{Math.round(current)}</Text>
          <Text style={styles.ringUnit}>g</Text>
        </View>
      </View>
      <Text style={styles.ringLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
  },
  calorieRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: theme.spacing.xs,
  },
  calorieValue: {
    fontSize: 22,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  calorieTarget: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
    fontWeight: '400',
  },
  percentText: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  hint: {
    ...theme.typography.caption,
    color: theme.colors.warning,
    marginTop: theme.spacing.sm,
  },
  subTitle: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.lg,
    marginBottom: theme.spacing.sm,
  },
  ringRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  ringWrap: {
    alignItems: 'center',
  },
  ringCircle: {
    width: 68,
    height: 68,
    position: 'relative',
  },
  ringInner: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ringValue: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    fontWeight: '700',
  },
  ringUnit: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  ringLabel: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
  },
});
