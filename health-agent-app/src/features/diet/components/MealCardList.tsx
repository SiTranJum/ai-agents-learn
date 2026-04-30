// MealCardList - 餐次卡片列表
// 4 餐固定顺序：早餐 / 午餐 / 晚餐 / 加餐
// 复用 @shared/ui/MealCard，三种状态：empty / pending / recorded
// 参考: docs/prd/v1/ui-design/04-diet-record-page.md §3, §5

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { MealCard } from '@shared/ui/MealCard';
import { theme } from '@app/styles/theme';
import type { DietRecord, MealType } from '../types/diet.types';

export interface MealCardListProps {
  meals: DietRecord[];
  onMealPress: (mealType: MealType, recordId?: string) => void;
  onConfirm?: (recordId: string) => void;
  onEdit?: (mealType: MealType, recordId?: string) => void;
  onCancel?: (recordId: string) => void;
}

const MEAL_LABELS: Record<MealType, string> = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐',
};

const MEAL_ORDER: MealType[] = ['breakfast', 'lunch', 'dinner', 'snack'];

export function MealCardList({
  meals,
  onMealPress,
  onConfirm,
  onEdit,
  onCancel,
}: MealCardListProps) {
  // 按固定顺序排列
  const sortedMeals = MEAL_ORDER.map(
    (type) =>
      meals.find((m) => m.mealType === type) ?? {
        mealType: type,
        status: 'empty' as const,
        foods: [],
        totalCalories: 0,
        nutrients: { carbs: 0, protein: 0, fat: 0 },
      }
  );

  return (
    <View style={styles.list}>
      {sortedMeals.map((meal) => {
        const foodsForCard = meal.foods.map((f) => ({
          name: f.name,
          amount: `${f.amount}${f.unit}`,
          calories: f.calories,
        }));

        return (
          <View key={meal.mealType} style={styles.section}>
            <Text style={styles.sectionTitle}>
              {MEAL_LABELS[meal.mealType]}
              {meal.status === 'pending' && (
                <Text style={styles.pendingTag}> · 待确认</Text>
              )}
            </Text>
            <MealCard
              mealType={meal.mealType}
              status={meal.status === 'editing' ? 'pending' : meal.status}
              foods={foodsForCard}
              totalCalories={meal.totalCalories}
              onPress={() => onMealPress(meal.mealType, meal.id)}
              onConfirm={
                onConfirm && meal.id ? () => onConfirm(meal.id!) : undefined
              }
              onEdit={
                onEdit
                  ? () => onEdit(meal.mealType, meal.id)
                  : undefined
              }
              onCancel={
                onCancel && meal.id ? () => onCancel(meal.id!) : undefined
              }
            />
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  list: {
    gap: theme.spacing.md,
  },
  section: {
    gap: theme.spacing.sm,
  },
  sectionTitle: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
    paddingHorizontal: theme.spacing.xs,
  },
  pendingTag: {
    ...theme.typography.bodySm,
    color: theme.colors.warning,
    fontWeight: '500',
  },
});
