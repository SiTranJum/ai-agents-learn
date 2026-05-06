// NutritionBottomSheet - 营养查询结果浮层
// 参考: docs/specs/frontend/modules/16-ai-dialog-module.md §O01
// UI 文稿: docs/prd/v1/ui-design/14-ai-dialog-and-overlays.md

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { BottomSheet } from '@shared/feedback/BottomSheet';
import { Button } from '@shared/ui/Button';
import { Tag } from '@shared/ui/Tag';
import { theme } from '@app/styles/theme';
import type { DataSource, NutritionData } from '../types/ai.types';

export interface NutritionBottomSheetProps {
  visible: boolean;
  data: NutritionData | null;
  onClose: () => void;
  onAddToDiet?: (data: NutritionData) => void;
}

const SOURCE_LABEL: Record<DataSource, string> = {
  local_db: '本地数据库',
  api: '在线 API',
  ai_estimate: 'AI 估算',
};

const SOURCE_VARIANT: Record<DataSource, 'success' | 'info' | 'warning'> = {
  local_db: 'success',
  api: 'info',
  ai_estimate: 'warning',
};

export function NutritionBottomSheet({
  visible,
  data,
  onClose,
  onAddToDiet,
}: NutritionBottomSheetProps) {
  return (
    <BottomSheet visible={visible} onClose={onClose}>
      <View style={styles.container}>
        {data ? (
          <>
            <Text style={styles.foodName}>{data.foodName}</Text>
            <Text style={styles.amount}>
              {data.amount} {data.unit}
            </Text>

            <View style={styles.calorieRow}>
              <Text style={styles.calorieValue}>{data.calories}</Text>
              <Text style={styles.calorieUnit}>kcal</Text>
            </View>

            <View style={styles.nutrientGrid}>
              <Nutrient label="碳水" value={`${data.carbs}g`} color={theme.colors.success} />
              <Nutrient label="蛋白质" value={`${data.protein}g`} color={theme.colors.info} />
              <Nutrient label="脂肪" value={`${data.fat}g`} color={theme.colors.warning} />
            </View>

            <View style={styles.sourceRow}>
              <Text style={styles.sourceLabel}>数据来源</Text>
              <Tag
                variant={SOURCE_VARIANT[data.dataSource]}
                size="small"
                label={SOURCE_LABEL[data.dataSource]}
              />
            </View>

            <View style={styles.actions}>
              <View style={styles.actionFlex}>
                <Button variant="secondary" onPress={onClose}>
                  关闭
                </Button>
              </View>
              <View style={styles.actionFlex}>
                <Button
                  variant="primary"
                  onPress={() => onAddToDiet?.(data)}
                  disabled={!onAddToDiet}
                >
                  记录到饮食
                </Button>
              </View>
            </View>
          </>
        ) : (
          <Text style={styles.empty}>暂无营养数据</Text>
        )}
      </View>
    </BottomSheet>
  );
}

function Nutrient({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <View style={styles.nutrientItem}>
      <View style={[styles.nutrientDot, { backgroundColor: color }]} />
      <Text style={styles.nutrientLabel}>{label}</Text>
      <Text style={styles.nutrientValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: theme.spacing.lg,
    paddingBottom: theme.spacing.xl,
  },
  foodName: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  amount: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  calorieRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginTop: theme.spacing.md,
  },
  calorieValue: {
    fontSize: 36,
    fontWeight: '700',
    color: theme.colors.primary,
  },
  calorieUnit: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    marginLeft: theme.spacing.xs,
  },
  nutrientGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: theme.spacing.md,
    paddingVertical: theme.spacing.md,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: theme.colors.divider,
  },
  nutrientItem: {
    flex: 1,
    alignItems: 'center',
  },
  nutrientDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginBottom: 6,
  },
  nutrientLabel: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginBottom: 2,
  },
  nutrientValue: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  sourceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: theme.spacing.md,
  },
  sourceLabel: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  actions: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginTop: theme.spacing.lg,
  },
  actionFlex: { flex: 1 },
  empty: {
    ...theme.typography.body,
    color: theme.colors.textTertiary,
    textAlign: 'center',
    padding: theme.spacing.xl,
  },
});
