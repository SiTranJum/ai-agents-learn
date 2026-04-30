// MealTimelineCard - 今日饮食时间轴卡片
// 4 餐时间轴，支持 empty / pending / recorded 三态
// 参考: docs/prd/v1/ui-design/03-home-dashboard.md §3.D, §5

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card } from '@shared/ui/Card';
import { theme } from '@app/styles/theme';
import type { HomeMeal, MealType } from '../types/home.types';

export interface MealTimelineCardProps {
  meals: HomeMeal[];
  onMealPress: (mealType: MealType) => void;
  onConfirmMeal?: (mealType: MealType) => void;
  onEditMeal?: (mealType: MealType) => void;
  onCancelMeal?: (mealType: MealType) => void;
  onViewAll?: () => void;
}

const MEAL_LABELS: Record<MealType, string> = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐',
};

const MEAL_ICONS: Record<MealType, keyof typeof Feather.glyphMap> = {
  breakfast: 'sunrise',
  lunch: 'sun',
  dinner: 'moon',
  snack: 'coffee',
};

export function MealTimelineCard({
  meals,
  onMealPress,
  onConfirmMeal,
  onEditMeal,
  onCancelMeal,
  onViewAll,
}: MealTimelineCardProps) {
  return (
    <Card>
      <View style={styles.header}>
        <Text style={styles.title}>今日饮食</Text>
        {onViewAll && (
          <TouchableOpacity onPress={onViewAll}>
            <Text style={styles.viewAll}>查看全部 →</Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.list}>
        {meals.map((meal, idx) => (
          <MealRow
            key={meal.type}
            meal={meal}
            isLast={idx === meals.length - 1}
            onPress={() => onMealPress(meal.type)}
            onConfirm={onConfirmMeal ? () => onConfirmMeal(meal.type) : undefined}
            onEdit={onEditMeal ? () => onEditMeal(meal.type) : undefined}
            onCancel={onCancelMeal ? () => onCancelMeal(meal.type) : undefined}
          />
        ))}
      </View>
    </Card>
  );
}

interface MealRowProps {
  meal: HomeMeal;
  isLast: boolean;
  onPress: () => void;
  onConfirm?: () => void;
  onEdit?: () => void;
  onCancel?: () => void;
}

function MealRow({ meal, isLast, onPress, onConfirm, onEdit, onCancel }: MealRowProps) {
  const label = MEAL_LABELS[meal.type];
  const iconName = MEAL_ICONS[meal.type];
  const isPending = meal.status === 'pending';
  const isRecorded = meal.status === 'recorded';

  return (
    <View style={[styles.row, isPending && styles.rowPending]}>
      {/* 左侧时间轴节点 */}
      <View style={styles.timelineCol}>
        <View
          style={[
            styles.dot,
            isRecorded && styles.dotRecorded,
            isPending && styles.dotPending,
          ]}
        >
          <Feather
            name={iconName}
            size={14}
            color={
              isRecorded || isPending
                ? theme.colors.bgCard
                : theme.colors.textTertiary
            }
          />
        </View>
        {!isLast && <View style={styles.line} />}
      </View>

      {/* 右侧内容 */}
      <TouchableOpacity
        style={styles.content}
        onPress={onPress}
        activeOpacity={0.7}
        disabled={isPending}
      >
        <View style={styles.contentHeader}>
          <Text style={styles.mealLabel}>{label}</Text>
          {isRecorded && (
            <Text style={styles.mealCalories}>{meal.calories} kcal</Text>
          )}
          {meal.status === 'empty' && (
            <Text style={styles.mealEmpty}>未记录</Text>
          )}
          {isPending && <Text style={styles.mealPendingTag}>AI 已识别</Text>}
        </View>

        {isRecorded && !!meal.foods && (
          <Text style={styles.foodsText} numberOfLines={2}>
            {meal.foods}
          </Text>
        )}
        {meal.status === 'empty' && (
          <Text style={styles.emptyHint}>点击记录或告诉 AI</Text>
        )}
        {isPending && (
          <>
            <Text style={styles.foodsText} numberOfLines={2}>
              {meal.foods}
            </Text>
            <View style={styles.actionRow}>
              {onConfirm && (
                <TouchableOpacity
                  style={[styles.actionBtn, styles.confirmBtn]}
                  onPress={onConfirm}
                >
                  <Text style={styles.confirmBtnText}>确认</Text>
                </TouchableOpacity>
              )}
              {onEdit && (
                <TouchableOpacity style={styles.actionBtn} onPress={onEdit}>
                  <Text style={styles.actionBtnText}>修改</Text>
                </TouchableOpacity>
              )}
              {onCancel && (
                <TouchableOpacity style={styles.actionBtn} onPress={onCancel}>
                  <Text style={styles.cancelBtnText}>取消</Text>
                </TouchableOpacity>
              )}
            </View>
          </>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  viewAll: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
  },
  list: {
    gap: 0,
  },
  row: {
    flexDirection: 'row',
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.sm,
    paddingHorizontal: theme.spacing.xs,
  },
  rowPending: {
    backgroundColor: theme.colors.primaryLight,
  },
  timelineCol: {
    width: 32,
    alignItems: 'center',
  },
  dot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: theme.colors.divider,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
  },
  dotRecorded: {
    backgroundColor: theme.colors.primary,
  },
  dotPending: {
    backgroundColor: theme.colors.warning,
  },
  line: {
    position: 'absolute',
    top: 28,
    bottom: -theme.spacing.sm,
    left: 15,
    width: 2,
    backgroundColor: theme.colors.divider,
  },
  content: {
    flex: 1,
    marginLeft: theme.spacing.sm,
    paddingBottom: theme.spacing.xs,
  },
  contentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 2,
  },
  mealLabel: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  mealCalories: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  mealEmpty: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  mealPendingTag: {
    ...theme.typography.tag,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  foodsText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  emptyHint: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginTop: 2,
  },
  actionRow: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.sm,
  },
  actionBtn: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.bgCard,
    borderWidth: 1,
    borderColor: theme.colors.divider,
  },
  confirmBtn: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  confirmBtnText: {
    ...theme.typography.bodySm,
    color: theme.colors.bgCard,
    fontWeight: '600',
  },
  actionBtnText: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
  },
  cancelBtnText: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
  },
});
