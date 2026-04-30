// DietRecordScreen - 饮食记录页 (P02)
// 参考: docs/specs/frontend/modules/12-diet-module.md §P02
// UI 文稿: docs/prd/v1/ui-design/04-diet-record-page.md

import React, { useCallback, useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Text,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { CompositeNavigationProp } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { ConfirmDialog } from '@shared/feedback/ConfirmDialog';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList, TabParamList } from '@app/navigation/types';

import { useDietData } from '../hooks/useDietData';
import { DateSwitcher } from '../components/DateSwitcher';
import { NutritionSummary } from '../components/NutritionSummary';
import { MealCardList } from '../components/MealCardList';
import type { MealType } from '../types/diet.types';

type Nav = CompositeNavigationProp<
  BottomTabNavigationProp<TabParamList, 'DietTab'>,
  NativeStackNavigationProp<MainStackParamList>
>;

export function DietRecordScreen() {
  const navigation = useNavigation<Nav>();
  const toast = useToast();

  const {
    date,
    setSelectedDate,
    data,
    isLoading,
    isRefetching,
    refetch,
    deleteRecord,
  } = useDietData();

  const [confirmState, setConfirmState] = useState<{
    visible: boolean;
    recordId?: string;
    mealType?: MealType;
  }>({ visible: false });

  const handleMealPress = useCallback(
    (mealType: MealType, recordId?: string) => {
      navigation.navigate('DietEdit', { mealType, date, recordId });
    },
    [navigation, date]
  );

  const handleEditPending = useCallback(
    (mealType: MealType, recordId?: string) => {
      navigation.navigate('DietEdit', { mealType, date, recordId });
    },
    [navigation, date]
  );

  const handleConfirm = useCallback(
    async (_recordId: string) => {
      toast.show({ type: 'success', message: '已保存到记录' });
      await refetch();
    },
    [toast, refetch]
  );

  const handleCancelPending = useCallback((recordId: string) => {
    setConfirmState({
      visible: true,
      recordId,
    });
  }, []);

  const handleConfirmDelete = useCallback(async () => {
    if (!confirmState.recordId) {
      setConfirmState({ visible: false });
      return;
    }
    try {
      await deleteRecord(confirmState.recordId);
      toast.show({ type: 'success', message: '已取消该记录' });
    } catch {
      toast.show({ type: 'error', message: '操作失败，请重试' });
    } finally {
      setConfirmState({ visible: false });
    }
  }, [confirmState.recordId, deleteRecord, toast]);

  // 是否有待确认餐次（用于汇总区提示）
  const pendingMeal = data?.meals.find((m) => m.status === 'pending');
  const hint = pendingMeal
    ? `${getMealLabel(pendingMeal.mealType)}待确认，暂未计入总摄入`
    : undefined;

  return (
    <PageContainer>
      {/* 顶部日期切换栏 */}
      <DateSwitcher date={date} onDateChange={setSelectedDate} />

      {isLoading && !data ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      ) : !data ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>加载失败，请下拉刷新</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor={theme.colors.primary}
            />
          }
        >
          {/* 今日摄入汇总 */}
          <NutritionSummary
            totalCalories={data.totalCalories}
            nutrients={data.nutrients}
            hint={hint}
          />

          {/* 餐次卡片列表 */}
          <View style={styles.mealsWrap}>
            <MealCardList
              meals={data.meals}
              onMealPress={handleMealPress}
              onConfirm={handleConfirm}
              onEdit={handleEditPending}
              onCancel={handleCancelPending}
            />
          </View>
        </ScrollView>
      )}

      <ConfirmDialog
        visible={confirmState.visible}
        title="取消该记录？"
        message="取消后该餐 AI 解析结果将被丢弃，无法恢复。"
        confirmText="确认取消"
        cancelText="继续保留"
        variant="danger"
        onConfirm={handleConfirmDelete}
        onCancel={() => setConfirmState({ visible: false })}
      />
    </PageContainer>
  );
}

function getMealLabel(type: MealType): string {
  return { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '加餐' }[type];
}

const styles = StyleSheet.create({
  scrollContent: {
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingBottom: theme.layout.bottomSafeArea,
    gap: theme.spacing.md,
  },
  mealsWrap: {
    marginTop: theme.spacing.md,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorText: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
});
