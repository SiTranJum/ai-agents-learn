// HomeScreen - 首页 Dashboard (P01)
// 参考: docs/specs/frontend/modules/11-home-module.md §P01
// UI 文稿: docs/prd/v1/ui-design/03-home-dashboard.md

import React, { useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { CompositeNavigationProp } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { SectionBlock } from '@shared/layout/SectionBlock/SectionBlock';
import type { MainStackParamList, TabParamList } from '@app/navigation/types';

import { useHomeData } from '../hooks/useHomeData';
import { useDataStore } from '@features/data/store/dataStore';
import { HealthOverviewCard } from '../components/HealthOverviewCard';
import { QuickActionBar } from '../components/QuickActionBar';
import { MealTimelineCard } from '../components/MealTimelineCard';
import { AIInsightCard } from '../components/AIInsightCard';
import { PlanProgressCard } from '../components/PlanProgressCard';
import { AuxiliaryRecordGrid } from '../components/AuxiliaryRecordGrid';
import type { AuxiliaryItemType, MealType } from '../types/home.types';

type Nav = CompositeNavigationProp<
  BottomTabNavigationProp<TabParamList, 'HomeTab'>,
  NativeStackNavigationProp<MainStackParamList>
>;

// 格式化日期为 "今天 · 4月29日 周二"
function formatHomeDate(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00`);
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
  const wd = weekDays[d.getDay()];
  return `今天 · ${month}月${day}日 周${wd}`;
}

export function HomeScreen() {
  const navigation = useNavigation<Nav>();
  const { date, data, isLoading, isRefetching, refetch } = useHomeData();

  const handleRecordDiet = useCallback(() => {
    navigation.navigate('DietTab');
  }, [navigation]);

  const handleRecordWeight = useCallback(() => {
    navigation.navigate('BodyEdit', { recordType: 'weight' });
  }, [navigation]);

  const handleViewPlan = useCallback(() => {
    navigation.navigate('PlanList');
  }, [navigation]);

  const handleMealPress = useCallback(
    (_mealType: MealType) => {
      navigation.navigate('DietTab');
    },
    [navigation]
  );

  const handleAIInsightPress = useCallback(() => {
    navigation.navigate('Analysis');
  }, [navigation]);

  const handlePlanCardPress = useCallback(() => {
    if (data?.plan) {
      navigation.navigate('PlanDetail', { planId: data.plan.id });
    }
  }, [navigation, data?.plan]);

  const handleCreatePlan = useCallback(() => {
    navigation.navigate('PlanCreate');
  }, [navigation]);

  const handleAuxItemPress = useCallback(
    (type: AuxiliaryItemType) => {
      useDataStore.getState().setSelectedTab(type as any);
      navigation.navigate('DataTab');
    },
    [navigation]
  );

  if (isLoading && !data) {
    return (
      <PageContainer>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      </PageContainer>
    );
  }

  if (!data) {
    return (
      <PageContainer>
        <View style={styles.center}>
          <Text style={styles.errorText}>加载失败，请下拉刷新</Text>
        </View>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <View style={styles.topBar}>
        <Text style={styles.greeting}>{formatHomeDate(date)}</Text>
        <TouchableOpacity onPress={() => refetch()} style={styles.refreshBtn}>
          <Feather
            name="refresh-cw"
            size={18}
            color={isRefetching ? theme.colors.primary : theme.colors.textTertiary}
          />
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor={theme.colors.primary}
            colors={[theme.colors.primary]}
          />
        }
      >
        <SectionBlock spacing="md">
          <HealthOverviewCard
            calories={data.calories}
            nutrients={data.nutrients}
          />
          <QuickActionBar
            onRecordDiet={handleRecordDiet}
            onRecordWeight={handleRecordWeight}
            onViewPlan={handleViewPlan}
          />
          <MealTimelineCard
            meals={data.meals}
            onMealPress={handleMealPress}
            onViewAll={handleRecordDiet}
          />
          <AIInsightCard
            insight={data.aiInsight}
            onPress={handleAIInsightPress}
          />
          <PlanProgressCard
            plan={data.plan}
            onPress={handlePlanCardPress}
            onCreatePlan={handleCreatePlan}
          />
          <AuxiliaryRecordGrid
            auxiliary={data.auxiliary}
            onItemPress={handleAuxItemPress}
          />
        </SectionBlock>
      </ScrollView>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingVertical: theme.spacing.md,
  },
  refreshBtn: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  greeting: {
    ...theme.typography.pageTitle,
    color: theme.colors.textPrimary,
  },
  scrollContent: {
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingBottom: theme.layout.bottomSafeArea,
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
