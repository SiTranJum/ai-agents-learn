// DietEditScreen - 饮食编辑页 (P03)
// 参考: docs/specs/frontend/modules/12-diet-module.md §P03
// UI 文稿: docs/prd/v1/ui-design/05-diet-edit-page.md

import React, { useCallback, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { Button } from '@shared/ui/Button';
import { ConfirmDialog } from '@shared/feedback/ConfirmDialog';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList } from '@app/navigation/types';

import { FoodItemRow } from '../components/FoodItemRow';
import { useDietData } from '../hooks/useDietData';
import { recalcMeal } from '../services/dietService';
import { nextFoodItemId } from '../mocks/dietMocks';
import type { DietRecord, FoodItem, MealType } from '../types/diet.types';

type Nav = NativeStackNavigationProp<MainStackParamList, 'DietEdit'>;
type EditRoute = RouteProp<MainStackParamList, 'DietEdit'>;

const MEAL_TYPES: { value: MealType; label: string }[] = [
  { value: 'breakfast', label: '早餐' },
  { value: 'lunch', label: '午餐' },
  { value: 'dinner', label: '晚餐' },
  { value: 'snack', label: '加餐' },
];

const MEAL_LABELS: Record<MealType, string> = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐',
};

function makeEmptyFood(): FoodItem {
  return {
    id: nextFoodItemId(),
    name: '',
    amount: 0,
    unit: 'g',
    calories: 0,
    protein: 0,
    fat: 0,
    carbs: 0,
  };
}

interface FoodErrors {
  name?: string;
  amount?: string;
}

export function DietEditScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<EditRoute>();
  const toast = useToast();

  const { mealType: routeMealType, recordId } = route.params ?? {};
  const { data, saveRecord, isSaving } = useDietData();

  // 是否为编辑已有记录
  const existingRecord: DietRecord | undefined = useMemo(() => {
    if (!recordId || !data) return undefined;
    return data.meals.find((m) => m.id === recordId);
  }, [recordId, data]);

  const isEditMode = !!existingRecord;

  // 初始 mealType
  const initialMealType: MealType =
    existingRecord?.mealType ?? (routeMealType as MealType) ?? 'breakfast';

  const [mealType, setMealType] = useState<MealType>(initialMealType);
  const [foods, setFoods] = useState<FoodItem[]>(() =>
    existingRecord?.foods.length ? [...existingRecord.foods] : [makeEmptyFood()]
  );
  const [errors, setErrors] = useState<FoodErrors[]>([]);
  const [dirty, setDirty] = useState(false);
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);

  const markDirty = () => {
    if (!dirty) setDirty(true);
  };

  // 实时汇总
  const summary = useMemo(() => {
    const merged = recalcMeal({
      mealType,
      status: 'editing',
      foods,
      totalCalories: 0,
      nutrients: { carbs: 0, protein: 0, fat: 0 },
    });
    return {
      totalCalories: merged.totalCalories,
      nutrients: merged.nutrients,
    };
  }, [foods, mealType]);

  // ===== 操作 =====
  const handleFoodChange = useCallback((idx: number, next: FoodItem) => {
    setFoods((prev) => prev.map((f, i) => (i === idx ? next : f)));
    markDirty();
    // 清除该行的错误
    setErrors((prev) => {
      const copy = [...prev];
      copy[idx] = {};
      return copy;
    });
  }, [dirty]);

  const handleDeleteFood = useCallback((idx: number) => {
    setFoods((prev) => {
      const next = prev.filter((_, i) => i !== idx);
      return next.length === 0 ? [makeEmptyFood()] : next;
    });
    markDirty();
  }, [dirty]);

  const handleAddFood = useCallback(() => {
    setFoods((prev) => [...prev, makeEmptyFood()]);
    markDirty();
  }, [dirty]);

  const handleSelectMealType = useCallback(
    (next: MealType) => {
      if (isEditMode) return; // 编辑模式不可切换餐次
      setMealType(next);
      markDirty();
    },
    [isEditMode, dirty]
  );

  // ===== 校验 =====
  const validate = (): boolean => {
    const next: FoodErrors[] = foods.map((f) => {
      const e: FoodErrors = {};
      if (!f.name.trim()) e.name = '请填写食物名称';
      if (!(f.amount > 0)) e.amount = '份量必须大于 0';
      return e;
    });
    setErrors(next);
    return next.every((e) => !e.name && !e.amount);
  };

  // ===== 保存 =====
  const handleSave = useCallback(async () => {
    if (!validate()) {
      toast.show({ type: 'error', message: '请检查表单中的错误' });
      return;
    }
    try {
      await saveRecord({
        id: existingRecord?.id,
        mealType,
        status: 'recorded',
        foods,
        totalCalories: summary.totalCalories,
        nutrients: summary.nutrients,
      });
      toast.show({
        type: 'success',
        message: `已保存${MEAL_LABELS[mealType]}记录`,
      });
      navigation.goBack();
    } catch {
      toast.show({ type: 'error', message: '保存失败，请稍后重试' });
    }
  }, [foods, mealType, summary, existingRecord, saveRecord, navigation, toast]);

  // ===== 取消 =====
  const handleCancel = useCallback(() => {
    if (dirty) {
      setShowLeaveConfirm(true);
    } else {
      navigation.goBack();
    }
  }, [dirty, navigation]);

  return (
    <PageContainer useSafeArea>
      {/* 顶部导航栏 */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={handleCancel} style={styles.backBtn}>
          <Feather name="chevron-left" size={24} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>
          {isEditMode ? `编辑${MEAL_LABELS[mealType]}记录` : '新增饮食记录'}
        </Text>
        <View style={styles.backBtn} />
      </View>

      <KeyboardAvoidingView
        style={styles.flex1}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          style={styles.flex1}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* 餐次选择器 */}
          <View style={styles.mealTabs}>
            {MEAL_TYPES.map((m) => {
              const active = m.value === mealType;
              return (
                <TouchableOpacity
                  key={m.value}
                  style={[
                    styles.mealTab,
                    active && styles.mealTabActive,
                    isEditMode && !active && styles.mealTabDisabled,
                  ]}
                  onPress={() => handleSelectMealType(m.value)}
                  disabled={isEditMode && !active}
                  activeOpacity={0.8}
                >
                  <Text
                    style={[
                      styles.mealTabText,
                      active && styles.mealTabTextActive,
                    ]}
                  >
                    {m.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
          {isEditMode && (
            <Text style={styles.mealHint}>编辑模式下餐次不可切换</Text>
          )}

          {/* 食物列表 */}
          <Text style={styles.sectionTitle}>食物列表</Text>
          {foods.map((food, idx) => (
            <FoodItemRow
              key={food.id}
              item={food}
              onChange={(next) => handleFoodChange(idx, next)}
              onDelete={() => handleDeleteFood(idx)}
              errors={errors[idx]}
            />
          ))}

          {/* 添加食物按钮 */}
          <TouchableOpacity
            style={styles.addBtn}
            onPress={handleAddFood}
            activeOpacity={0.7}
          >
            <Feather name="plus" size={18} color={theme.colors.primary} />
            <Text style={styles.addBtnText}>添加食物</Text>
          </TouchableOpacity>

          {/* 营养汇总 */}
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>营养汇总</Text>
            <Text style={styles.summaryCalorie}>
              总热量：
              <Text style={styles.summaryCalorieValue}>
                {summary.totalCalories} kcal
              </Text>
            </Text>
            <Text style={styles.summaryNutrients}>
              碳水：{summary.nutrients.carbs}g 蛋白质：{summary.nutrients.protein}g
              脂肪：{summary.nutrients.fat}g
            </Text>
          </View>
        </ScrollView>

        {/* 底部操作栏 */}
        <View style={styles.actionBar}>
          <View style={styles.actionBtnWrap}>
            <Button variant="secondary" onPress={handleCancel} size="medium">
              取消
            </Button>
          </View>
          <View style={styles.actionBtnWrap}>
            <Button
              variant="primary"
              onPress={handleSave}
              loading={isSaving}
              size="medium"
            >
              保存
            </Button>
          </View>
        </View>
      </KeyboardAvoidingView>

      <ConfirmDialog
        visible={showLeaveConfirm}
        title="放弃修改？"
        message="当前修改尚未保存，确认离开吗？"
        confirmText="放弃修改"
        cancelText="继续编辑"
        variant="danger"
        onConfirm={() => {
          setShowLeaveConfirm(false);
          navigation.goBack();
        }}
        onCancel={() => setShowLeaveConfirm(false)}
      />
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  flex1: { flex: 1 },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
    backgroundColor: theme.colors.bgPage,
  },
  backBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  scrollContent: {
    padding: theme.layout.pageHorizontalPadding,
    paddingBottom: theme.spacing.xxl,
  },
  mealTabs: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.sm,
  },
  mealTab: {
    flex: 1,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.bgCard,
    borderWidth: 1,
    borderColor: theme.colors.divider,
    alignItems: 'center',
  },
  mealTabActive: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  mealTabDisabled: {
    opacity: 0.5,
  },
  mealTabText: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
  },
  mealTabTextActive: {
    color: theme.colors.bgCard,
    fontWeight: '600',
  },
  mealHint: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginBottom: theme.spacing.md,
  },
  sectionTitle: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.lg,
    marginBottom: theme.spacing.sm,
  },
  addBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.md,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.primaryLight,
    borderStyle: 'dashed',
    backgroundColor: theme.colors.bgCard,
    gap: theme.spacing.xs,
    marginBottom: theme.spacing.lg,
  },
  addBtnText: {
    ...theme.typography.body,
    color: theme.colors.primary,
    fontWeight: '500',
  },
  summaryCard: {
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    ...theme.shadows.card,
  },
  summaryTitle: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
  },
  summaryCalorie: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.xs,
  },
  summaryCalorieValue: {
    color: theme.colors.primary,
    fontWeight: '700',
  },
  summaryNutrients: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  actionBar: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    padding: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
    backgroundColor: theme.colors.bgPage,
  },
  actionBtnWrap: {
    flex: 1,
  },
});
