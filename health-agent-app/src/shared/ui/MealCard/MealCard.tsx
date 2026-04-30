import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, radius, spacing, shadows, typography } from '@app/styles/tokens';

// MealCard 组件的 Props 接口
// 用于定义餐次卡片的所有可配置属性
export interface MealCardProps {
  // 餐次类型：早餐、午餐、晚餐、加餐
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  // 卡片状态：空白、待确认、已记录
  status: 'empty' | 'pending' | 'recorded';
  // 食物列表（pending 和 recorded 状态使用）
  foods?: Array<{ name: string; amount: string; calories: number }>;
  // 总热量（recorded 状态显示）
  totalCalories?: number;
  // 点击卡片的回调（empty 状态使用）
  onPress?: () => void;
  // 确认按钮回调（pending 状态使用）
  onConfirm?: () => void;
  // 修改按钮回调（pending 状态使用）
  onEdit?: () => void;
  // 取消按钮回调（pending 状态使用）
  onCancel?: () => void;
}

// 餐次类型到中文名称的映射
const MEAL_TYPE_LABELS: Record<MealCardProps['mealType'], string> = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐',
};

/**
 * MealCard 餐次卡片组件
 *
 * 三种状态：
 * 1. empty: 空白状态，显示"+ 点击记录"提示
 * 2. pending: 待确认状态，显示 AI 解析的食物列表和操作按钮
 * 3. recorded: 已记录状态，显示食物列表和总热量
 */
export function MealCard({
  mealType,
  status,
  foods = [],
  totalCalories = 0,
  onPress,
  onConfirm,
  onEdit,
  onCancel,
}: MealCardProps) {
  const label = MEAL_TYPE_LABELS[mealType];

  // ===== empty 状态：浅灰背景 + 点击记录提示 =====
  if (status === 'empty') {
    return (
      <TouchableOpacity
        style={[styles.card, styles.emptyCard]}
        onPress={onPress}
        activeOpacity={0.7}
      >
        <Text style={styles.mealTitle}>{label}</Text>
        <Text style={styles.emptyHint}>+ 点击记录</Text>
      </TouchableOpacity>
    );
  }

  // ===== pending 状态：白底 + 品牌色边框 + 操作按钮 =====
  if (status === 'pending') {
    return (
      <View style={[styles.card, styles.pendingCard]}>
        <Text style={styles.mealTitle}>{label}</Text>
        <FoodList foods={foods} />
        <View style={styles.actionRow}>
          <TouchableOpacity style={styles.actionBtn} onPress={onConfirm}>
            <Text style={styles.actionBtnText}>✓ 确认</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionBtn} onPress={onEdit}>
            <Text style={styles.actionBtnText}>✏️ 修改</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionBtn} onPress={onCancel}>
            <Text style={[styles.actionBtnText, styles.cancelText]}>✗ 取消</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // ===== recorded 状态：正常白底卡片 + 食物列表 + 总热量 =====
  return (
    <TouchableOpacity
      style={[styles.card, styles.recordedCard]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.recordedHeader}>
        <Text style={styles.mealTitle}>{label}</Text>
        <Text style={styles.totalCalories}>{totalCalories} kcal</Text>
      </View>
      <FoodList foods={foods} />
    </TouchableOpacity>
  );
}

// ===== 食物列表子组件 =====
function FoodList({ foods }: { foods: Array<{ name: string; amount: string; calories: number }> }) {
  if (foods.length === 0) return null;

  return (
    <View style={styles.foodList}>
      {foods.map((food, index) => (
        <View key={index} style={styles.foodItem}>
          <Text style={styles.foodName} numberOfLines={1}>
            {food.name}
          </Text>
          <Text style={styles.foodAmount}>{food.amount}</Text>
          <Text style={styles.foodCalories}>{food.calories} kcal</Text>
        </View>
      ))}
    </View>
  );
}

// ===== 样式定义 =====
const styles = StyleSheet.create({
  // 基础卡片样式
  card: {
    minHeight: 104,
    backgroundColor: colors.bgCard,
    borderRadius: radius.md,
    padding: spacing.lg,
    ...shadows.card,
  },

  // empty 状态：浅灰背景，居中布局
  emptyCard: {
    backgroundColor: colors.bgPage,
    alignItems: 'center',
    justifyContent: 'center',
  },

  // pending 状态：白底 + 品牌浅色边框
  pendingCard: {
    borderWidth: 1,
    borderColor: colors.primaryLight,
  },

  // recorded 状态：正常白底
  recordedCard: {
    backgroundColor: colors.bgCard,
  },

  // 餐次标题
  mealTitle: {
    ...typography.cardTitle,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },

  // empty 状态的提示文案
  emptyHint: {
    ...typography.body,
    color: colors.textTertiary,
    marginTop: spacing.xs,
  },

  // recorded 状态的头部（标题 + 总热量）
  recordedHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },

  // 总热量文字
  totalCalories: {
    ...typography.bodySm,
    color: colors.primary,
    fontWeight: '600',
  },

  // 食物列表容器
  foodList: {
    marginTop: spacing.xs,
  },

  // 单个食物项
  foodItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.xs,
  },

  // 食物名称
  foodName: {
    ...typography.body,
    color: colors.textPrimary,
    flex: 1,
  },

  // 食物份量
  foodAmount: {
    ...typography.bodySm,
    color: colors.textSecondary,
    marginHorizontal: spacing.sm,
  },

  // 食物热量
  foodCalories: {
    ...typography.bodySm,
    color: colors.primary,
    minWidth: 60,
    textAlign: 'right',
  },

  // pending 状态的操作按钮行
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: spacing.md,
    gap: spacing.md,
  },

  // 操作按钮
  actionBtn: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
  },

  // 操作按钮文字
  actionBtnText: {
    ...typography.bodySm,
    color: colors.primary,
    fontWeight: '500',
  },

  // 取消按钮文字颜色
  cancelText: {
    color: colors.textTertiary,
  },
});
