// DataScreen - 数据页 (P04)
// 6 个 Tab + 趋势图 + 时间范围 + 今日卡片 + 历史记录
// 参考: docs/specs/frontend/modules/13-data-module.md §P04
// UI 文稿: docs/prd/v1/ui-design/06-data-page.md

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { CompositeNavigationProp, RouteProp } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList, TabParamList } from '@app/navigation/types';

import { useDataStore } from '../store/dataStore';
import {
  useCalendarRecords,
  useAddWater,
  useRecentRecords,
  useSaveBodyData,
  useTodayRecords,
  useTrendData,
} from '../hooks/useDataTrend';
import { TimeRangeSelector } from '../components/TimeRangeSelector';
import { DataTabBar } from '../components/DataTabBar';
import { TrendChart } from '../components/TrendChart';
import { DataRecordList } from '../components/DataRecordList';
import { DataCalendarView } from '../components/DataCalendarView';
import { WeightRecordSheet } from '../components/WeightRecordSheet';
import {
  BowelCard,
  ExerciseCard,
  MeasurementCard,
  SleepCard,
  WaterCard,
  WeightCard,
} from '../components/TodayCards';
import type { DataTabType } from '../types/data.types';
import type { WeightRecord } from '../types/data.types';
import { todayStr } from '@shared/utils/date';

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
  const route = useRoute<RouteProp<TabParamList, 'DataTab'>>();
  const toast = useToast();

  const selectedTab = useDataStore((s) => s.selectedTab);
  const setSelectedTab = useDataStore((s) => s.setSelectedTab);
  const selectedTimeRange = useDataStore((s) => s.selectedTimeRange);
  const setSelectedTimeRange = useDataStore((s) => s.setSelectedTimeRange);
  const [recordViewMode, setRecordViewMode] = useState<'history' | 'calendar'>('history');
  const [calendarMonth, setCalendarMonth] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const [weightSheetVisible, setWeightSheetVisible] = useState(false);
  const [editingWeightRecord, setEditingWeightRecord] = useState<WeightRecord | null>(null);

  // 处理从首页跳转过来自动打开浮窗的情况
  useEffect(() => {
    const params = route.params as any;
    if (params?.autoOpenSheet && params?.tab === 'weight') {
      setWeightSheetVisible(true);
      // 清除参数避免重复触发
      navigation.setParams({ autoOpenSheet: undefined } as any);
    }
  }, [route.params, navigation]);

  const todayQuery = useTodayRecords();
  const trendQuery = useTrendData(selectedTab, selectedTimeRange);
  const recentQuery = useRecentRecords(selectedTab, 7);
  const calendarQuery = useCalendarRecords(selectedTab, calendarMonth);
  const saveBody = useSaveBodyData();
  const addWater = useAddWater();

  const handleEdit = useCallback(
    (recordType: DataTabType, recordId?: string) => {
      if (recordType === 'weight') {
        setEditingWeightRecord(recordId ? todayQuery.data?.weight ?? null : null);
        setWeightSheetVisible(true);
        return;
      }
      navigation.navigate('BodyEdit', { recordType, recordId });
    },
    [navigation, todayQuery.data?.weight]
  );

  const handleSaveWeight = useCallback(
    async (record: Partial<WeightRecord>) => {
      try {
        await saveBody.mutateAsync({ type: 'weight', record });
        toast.show({ type: 'success', message: '已保存体重记录' });
        setWeightSheetVisible(false);
        setEditingWeightRecord(null);
      } catch {
        toast.show({ type: 'error', message: '保存失败，请稍后重试' });
      }
    },
    [saveBody, toast]
  );

  const handleAddWater = useCallback(
    async (amount: number) => {
      try {
        await addWater.mutateAsync({
          date: todayQuery.data?.water?.date ?? todayStr(),
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
  const latestWeight = useMemo(() => {
    const points = trendQuery.data?.points ?? [];
    const last = points[points.length - 1];
    return selectedTab === 'weight' ? last?.value : today?.weight?.weight;
  }, [selectedTab, today?.weight?.weight, trendQuery.data?.points]);

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
          <Text style={styles.analysisBtnText}>数据报告 →</Text>
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

        {/* 历史记录 / 日历 */}
        <View style={styles.section}>
          <View style={styles.recordModeRow}>
            <TouchableOpacity
              style={[styles.recordModeButton, recordViewMode === 'history' && styles.recordModeButtonActive]}
              onPress={() => setRecordViewMode('history')}
              activeOpacity={0.75}
            >
              <Text style={[styles.recordModeText, recordViewMode === 'history' && styles.recordModeTextActive]}>
                历史记录
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.recordModeButton, recordViewMode === 'calendar' && styles.recordModeButtonActive]}
              onPress={() => setRecordViewMode('calendar')}
              activeOpacity={0.75}
            >
              <Text style={[styles.recordModeText, recordViewMode === 'calendar' && styles.recordModeTextActive]}>
                日历
              </Text>
            </TouchableOpacity>
          </View>
          {recordViewMode === 'history' ? (
            <DataRecordList
              tab={selectedTab}
              records={recentQuery.data ?? []}
              isLoading={recentQuery.isLoading}
            />
          ) : (
            <DataCalendarView
              tab={selectedTab}
              month={calendarMonth}
              records={calendarQuery.data ?? []}
              isLoading={calendarQuery.isLoading}
              onMonthChange={setCalendarMonth}
            />
          )}
        </View>
      </ScrollView>
      <WeightRecordSheet
        visible={weightSheetVisible}
        record={editingWeightRecord}
        fallbackWeight={latestWeight}
        isSaving={saveBody.isPending}
        onClose={() => {
          setWeightSheetVisible(false);
          setEditingWeightRecord(null);
        }}
        onSave={handleSaveWeight}
      />
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
  recordModeRow: {
    flexDirection: 'row',
    alignSelf: 'flex-start',
    padding: 3,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.bgCard,
    borderWidth: 1,
    borderColor: theme.colors.divider,
    marginBottom: theme.spacing.sm,
  },
  recordModeButton: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
  },
  recordModeButtonActive: {
    backgroundColor: theme.colors.primary,
  },
  recordModeText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    fontWeight: '600',
  },
  recordModeTextActive: {
    color: theme.colors.bgCard,
  },
  tabBarWrap: {
    marginHorizontal: -theme.layout.pageHorizontalPadding,
  },
});
