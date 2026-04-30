// HealthOverviewCard - 今日概览大卡片
// 左侧热量环形图 + 三大营养素进度条
// 参考: docs/prd/v1/ui-design/03-home-dashboard.md §3.B

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Card } from '@shared/ui/Card';
import { CircularProgress } from '@shared/ui/CircularProgress';
import { ProgressBar } from '@shared/ui/ProgressBar';
import { theme } from '@app/styles/theme';
import type { HomeData } from '../types/home.types';

export interface HealthOverviewCardProps {
  calories: HomeData['calories'];
  nutrients: HomeData['nutrients'];
}

// 根据达标率切换环形图颜色：正常/接近/超标
function getCalorieColor(current: number, target: number): string {
  if (target <= 0) return theme.colors.primary;
  const ratio = current / target;
  if (ratio > 1) return theme.colors.error;
  if (ratio >= 0.9) return theme.colors.warning;
  return theme.colors.primary;
}

export function HealthOverviewCard({ calories, nutrients }: HealthOverviewCardProps) {
  const calorieColor = getCalorieColor(calories.current, calories.target);

  return (
    <Card>
      <Text style={styles.title}>今日概览</Text>
      <View style={styles.row}>
        {/* 左侧：热量环形图 */}
        <View style={styles.ringWrap}>
          <CircularProgress
            current={calories.current}
            target={calories.target}
            size={120}
            strokeWidth={12}
            color={calorieColor}
          />
          <View style={styles.ringCenter} pointerEvents="none">
            <Text style={styles.calorieValue}>
              {calories.current.toLocaleString()}
            </Text>
            <Text style={styles.calorieTarget}>
              / {calories.target.toLocaleString()}
            </Text>
            <Text style={styles.calorieUnit}>kcal</Text>
          </View>
        </View>

        {/* 右侧：三大营养素 */}
        <View style={styles.nutrientList}>
          <NutrientRow
            label="蛋白质"
            value={nutrients.protein.current}
            target={nutrients.protein.target}
            color={theme.colors.info}
          />
          <NutrientRow
            label="脂肪"
            value={nutrients.fat.current}
            target={nutrients.fat.target}
            color={theme.colors.warning}
          />
          <NutrientRow
            label="碳水"
            value={nutrients.carbs.current}
            target={nutrients.carbs.target}
            color={theme.colors.success}
          />
        </View>
      </View>
    </Card>
  );
}

interface NutrientRowProps {
  label: string;
  value: number;
  target: number;
  color: string;
}

function NutrientRow({ label, value, target, color }: NutrientRowProps) {
  return (
    <View style={styles.nutrientRow}>
      <View style={styles.nutrientHeader}>
        <Text style={styles.nutrientLabel}>{label}</Text>
        <Text style={styles.nutrientValue}>
          {value}
          <Text style={styles.nutrientUnit}>g</Text>
        </Text>
      </View>
      <ProgressBar current={value} target={target} color={color} height={6} />
    </View>
  );
}

const styles = StyleSheet.create({
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.lg,
  },
  ringWrap: {
    width: 120,
    height: 120,
    position: 'relative',
  },
  ringCenter: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },
  calorieValue: {
    fontSize: 22,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  calorieTarget: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginTop: 2,
  },
  calorieUnit: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  nutrientList: {
    flex: 1,
    gap: theme.spacing.md,
  },
  nutrientRow: {
    width: '100%',
  },
  nutrientHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: theme.spacing.xs,
  },
  nutrientLabel: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  nutrientValue: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  nutrientUnit: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    fontWeight: '400',
  },
});
