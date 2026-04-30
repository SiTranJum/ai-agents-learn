// AnalysisScreen - 数据分析页 (P09)
// 时间范围 + 热量/体重趋势 + 营养分布 + 计划达成 + AI 洞察
// 参考: docs/specs/frontend/modules/13-data-module.md §P09
// UI 文稿: docs/prd/v1/ui-design/11-analysis-page.md

import React, { useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { Card } from '@shared/ui/Card';
import { ProgressBar } from '@shared/ui/ProgressBar';
import { LineChart } from '@shared/charts/LineChart';
import type { MainStackParamList } from '@app/navigation/types';

import { useAnalysisData } from '../hooks/useDataTrend';
import { useDataStore } from '../store/dataStore';
import { TimeRangeSelector } from '../components/TimeRangeSelector';
import { NutritionAnalysisCard } from '../components/NutritionAnalysisCard';
import { AIInsightSummaryCard } from '../components/AIInsightSummaryCard';

type Nav = NativeStackNavigationProp<MainStackParamList, 'Analysis'>;

export function AnalysisScreen() {
  const navigation = useNavigation<Nav>();
  const range = useDataStore((s) => s.selectedTimeRange);
  const setRange = useDataStore((s) => s.setSelectedTimeRange);
  const { data, isLoading } = useAnalysisData();

  const handleBack = useCallback(() => navigation.goBack(), [navigation]);

  const chartWidth = Dimensions.get('window').width - 64;

  return (
    <PageContainer useSafeArea>
      {/* 顶部导航栏 */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
          <Feather name="chevron-left" size={24} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>数据分析</Text>
        <View style={styles.backBtn} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* 时间范围 */}
        <TimeRangeSelector value={range} onChange={setRange} />

        {isLoading || !data ? (
          <View style={styles.center}>
            <ActivityIndicator color={theme.colors.primary} />
          </View>
        ) : (
          <>
            {/* 热量趋势 */}
            <Card>
              <Text style={styles.cardTitle}>热量趋势</Text>
              <LineChart
                data={{
                  labels: sampleLabels(data.caloriesTrend.map((p) => p.date), 6),
                  datasets: [
                    { data: data.caloriesTrend.map((p) => p.intake) },
                  ],
                }}
                width={chartWidth}
                height={180}
              />
              <Text style={styles.subText}>
                平均摄入：
                {Math.round(
                  data.caloriesTrend.reduce((s, p) => s + p.intake, 0) /
                    data.caloriesTrend.length
                )}{' '}
                / {data.caloriesTrend[0]?.target ?? 0} kcal
              </Text>
            </Card>

            {/* 营养分布 */}
            <NutritionAnalysisCard data={data.nutritionDistribution} />

            {/* 体重变化 */}
            <Card>
              <Text style={styles.cardTitle}>体重变化</Text>
              <LineChart
                data={{
                  labels: sampleLabels(data.weightTrend.map((p) => p.date), 6),
                  datasets: [{ data: data.weightTrend.map((p) => p.weight) }],
                }}
                width={chartWidth}
                height={180}
              />
              <View style={styles.weightInfo}>
                <Text style={styles.subText}>
                  当前：
                  <Text style={styles.subValue}>{data.currentWeight} kg</Text>
                </Text>
                <Text style={styles.subText}>
                  目标：
                  <Text style={styles.subValue}>{data.targetWeight} kg</Text>
                </Text>
              </View>
            </Card>

            {/* 计划达成率 */}
            <Card>
              <Text style={styles.cardTitle}>计划达成</Text>
              <Text style={styles.heroValue}>
                {data.planCompletion.completionRate.toFixed(1)}%
              </Text>
              <View style={{ marginVertical: theme.spacing.sm }}>
                <ProgressBar
                  current={data.planCompletion.completedDays}
                  target={data.planCompletion.totalDays}
                  color={theme.colors.primary}
                  height={10}
                />
              </View>
              <Text style={styles.subText}>
                已坚持 {data.planCompletion.completedDays} /{' '}
                {data.planCompletion.totalDays} 天
              </Text>
            </Card>

            {/* AI 洞察 */}
            <AIInsightSummaryCard insights={data.insights} />
          </>
        )}
      </ScrollView>
    </PageContainer>
  );
}

function sampleLabels(arr: string[], n: number): string[] {
  if (arr.length <= n) return arr.map(formatLabel);
  const step = Math.floor(arr.length / n);
  const out: string[] = [];
  for (let i = 0; i < arr.length; i += step) {
    out.push(formatLabel(arr[i]));
    if (out.length >= n) break;
  }
  return out;
}

function formatLabel(d: string): string {
  const parts = d.split('-');
  if (parts.length !== 3) return d;
  return `${Number(parts[1])}/${Number(parts[2])}`;
}

const styles = StyleSheet.create({
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
    paddingBottom: theme.layout.bottomSafeArea,
    gap: theme.spacing.md,
  },
  cardTitle: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
  },
  subText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
  },
  subValue: {
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  weightInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: theme.spacing.sm,
  },
  heroValue: {
    fontSize: 28,
    fontWeight: '700',
    color: theme.colors.primary,
  },
  center: {
    paddingVertical: theme.spacing.xxl,
    alignItems: 'center',
  },
});
