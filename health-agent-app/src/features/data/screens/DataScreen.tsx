// DataScreen - 数据页 (P04)
// 6 个 Tab + 趋势图 + 时间范围 + 今日卡片 + 历史记录
// 参考: docs/specs/frontend/modules/13-data-module.md §P04
// UI 文稿: docs/prd/v1/ui-design/06-data-page.md

import React, { useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { CompositeNavigationProp } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList, TabParamList } from '@app/navigation/types';

import { useDataStore } from '../store/dataStore';
import {
  useAddWater,
  useRecentRecords,
  useTodayRecords,
  useTrendData,
} from '../hooks/useDataTrend';
import { TimeRangeSelector } from '../components/TimeRangeSelector';
import { DataTabBar } from '../components/DataTabBar';
import { TrendChart } from '../components/TrendChart';
import { DataRecordList } from '../components/DataRecordList';
import {
  BowelCard,
  ExerciseCard,
  MeasurementCard,
  SleepCard,
  WaterCard,
  WeightCard,
} from '../components/TodayCards';
import type { DataTabType } from '../types/data.types';

type Nav = CompositeNavigationProp<
  BottomTabNavigationProp<TabParamList, 'DataTab'>,
  NativeStackNavigationProp<MainStackParamList>
>;

const TAB_TITLES: Record<DataTabType, string> = {
  weight: '体重',
  measurement: '腰围',
  sleep: '睡眠时长',
  exercise: '运动时长',
  water: '饮水',
  bowel: '排便',
};

export function DataScreen() {
  const navigation = useNavigation<Nav>();
  const toast = useToast();

  const selectedTab = useDataStore((s) => s.selectedTab);
  const setSelectedTab = useDataStore((s) => s.setSelectedTab);
  const selectedTimeRange = useDataStore((s) => s.selectedTimeRange);
  const setSelectedTimeRange = useDataStore((s) => s.setSelectedTimeRange);

  const todayQuery = useTodayRecords();
  const trendQuery = useTrendData(selectedTab, selectedTimeRange);
  const recentQuery = useRecentRecords(selectedTab, 7);
  const addWater = useAddWater();

  const handleEdit = useCallback(
    (recordType: DataTabType, recordId?: string) => {
      navigation.navigate('BodyEdit', { recordType, recordId });
    },
    [navigation]
  );

  const handleAddWater = useCallback(
    async (amount: number) => {
      try {
        await addWater.mutateAsync({
          date: todayQuery.data?.water?.date ?? new Date().toISOString().slice(0, 10),
          amount,
        });
        toast.show({ type: 'success', message: `已添加 ${amount}ml` });
      } catch {
        toast.show({ type: 'error', message: '操作失败，请重试' });
      }
    },
    [addWater, todayQuery.data?.water?.date, toast]
  );

  const handleAnalysis = useCallback(() => {
    navigation.navigate('Analysis');
  }, [navigation]);

  const refreshAll = useCallback(() => {
    todayQuery.refetch();
    trendQuery.refetch();
    recentQuery.refetch();
  }, [todayQuery, trendQuery, recentQuery]);

  const today = todayQuery.data;
  const isRefreshing =
    todayQuery.isRefetching || trendQuery.isRefetching || recentQuery.isRefetching;

  return (
    <PageContainer>
      {/* 顶部标题 */}
      <View style={styles.topBar}>
        <Text style={styles.title}>数据</Text>
        <TouchableOpacity
          onPress={handleAnalysis}
          style={styles.analysisBtn}
          activeOpacity={0.7}
        >
          <Text style={styles.analysisBtnText}>数据分析 →</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={refreshAll}
            tintColor={theme.colors.primary}
          />
        }
      >
        {/* 趋势图 */}
        <TrendChart
          title={TAB_TITLES[selectedTab]}
          unit={trendQuery.data?.unit ?? ''}
          points={trendQuery.data?.points ?? []}
          isLoading={trendQuery.isLoading}
        />

        {/* 时间范围切换 */}
        <View style={styles.section}>
          <TimeRangeSelector
            value={selectedTimeRange}
            onChange={setSelectedTimeRange}
          />
        </View>

        {/* Tab 切换栏（自带横向滚动） */}
        <View style={styles.tabBarWrap}>
          <DataTabBar value={selectedTab} onChange={setSelectedTab} />
        </View>

        {/* 今日记录卡片（根据 Tab 切换） */}
        <View style={styles.section}>
          {selectedTab === 'weight' && (
            <WeightCard
              record={today?.weight ?? null}
              onAdd={() => handleEdit('weight')}
              onEdit={() => handleEdit('weight', today?.weight?.id)}
            />
          )}
          {selectedTab === 'measurement' && (
            <MeasurementCard
              record={today?.measurement ?? null}
              onAdd={() => handleEdit('measurement')}
              onEdit={() => handleEdit('measurement', today?.measurement?.id)}
            />
          )}
          {selectedTab === 'sleep' && (
            <SleepCard
              record={today?.sleep ?? null}
              onAdd={() => handleEdit('sleep')}
              onEdit={() => handleEdit('sleep', today?.sleep?.id)}
            />
          )}
          {selectedTab === 'exercise' && (
            <ExerciseCard
              record={today?.exercise ?? null}
              onAdd={() => handleEdit('exercise')}
              onEdit={() => handleEdit('exercise', today?.exercise?.id)}
            />
          )}
          {selectedTab === 'water' && (
            <WaterCard
              record={today?.water ?? null}
              onAddAmount={handleAddWater}
            />
          )}
          {selectedTab === 'bowel' && (
            <BowelCard
              record={today?.bowel ?? null}
              onAdd={() => handleEdit('bowel')}
              onEdit={() => handleEdit('bowel', today?.bowel?.id)}
            />
          )}
        </View>

        {/* 历史记录 */}
        <View style={styles.section}>
          <DataRecordList
            tab={selectedTab}
            records={recentQuery.data ?? []}
            isLoading={recentQuery.isLoading}
          />
        </View>
      </ScrollView>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingVertical: theme.spacing.md,
  },
  title: {
    ...theme.typography.pageTitle,
    color: theme.colors.textPrimary,
  },
  analysisBtn: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
  },
  analysisBtnText: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  scrollContent: {
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingBottom: theme.layout.bottomSafeArea,
    gap: theme.spacing.md,
  },
  section: {
    marginTop: theme.spacing.xs,
  },
  tabBarWrap: {
    marginHorizontal: -theme.layout.pageHorizontalPadding,
  },
});
