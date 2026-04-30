// PlanListScreen - 计划列表页 (P06)
// 参考: docs/specs/frontend/modules/14-plan-module.md §P06
// UI 文稿: docs/prd/v1/ui-design/08-plan-list-page.md

import React, { useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { PlanCard } from '@shared/ui/PlanCard';
import { EmptyState } from '@shared/feedback/EmptyState';
import type { MainStackParamList } from '@app/navigation/types';

import { usePlans } from '../hooks/usePlanData';
import type { PlanListItem } from '../types/plan.types';

type Nav = NativeStackNavigationProp<MainStackParamList, 'PlanList'>;

export function PlanListScreen() {
  const navigation = useNavigation<Nav>();
  const { data, isLoading, isRefetching, refetch } = usePlans();

  const handleCreate = useCallback(() => {
    navigation.navigate('PlanCreate');
  }, [navigation]);

  const handleOpen = useCallback(
    (planId: string) => {
      navigation.navigate('PlanDetail', { planId });
    },
    [navigation]
  );

  const handleBack = useCallback(() => navigation.goBack(), [navigation]);

  const isEmpty = !isLoading && (data?.length ?? 0) === 0;

  return (
    <PageContainer useSafeArea>
      {/* 顶部导航栏 */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
          <Feather name="chevron-left" size={24} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>我的计划</Text>
        <TouchableOpacity
          onPress={handleCreate}
          style={styles.createBtn}
          activeOpacity={0.8}
        >
          <Feather name="plus" size={14} color={theme.colors.bgCard} />
          <Text style={styles.createBtnText}>新建</Text>
        </TouchableOpacity>
      </View>

      {isLoading && !data ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      ) : isEmpty ? (
        <EmptyState
          title="还没有健康计划哦"
          description="让 AI 帮你制定一个吧"
          actionText="创建我的第一个计划"
          onAction={handleCreate}
        />
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
          {data!.map((plan) => (
            <View key={plan.id} style={styles.cardWrap}>
              <PlanCard
                name={`${getTypeIcon(plan.type)} ${plan.name}`}
                progress={plan.progress}
                progressText={`${plan.progress}%`}
                dateRange={`${formatDate(plan.startDate)} → ${formatDate(plan.endDate)}`}
                status={mapStatus(plan.status)}
                onPress={() => handleOpen(plan.id)}
              />
            </View>
          ))}
        </ScrollView>
      )}
    </PageContainer>
  );
}

function getTypeIcon(type: PlanListItem['type']): string {
  return { lose_weight: '🏃', nutrition: '🥗', habit: '💪' }[type];
}

function formatDate(d: string): string {
  const parts = d.split('-');
  if (parts.length !== 3) return d;
  return `${Number(parts[1]).toString().padStart(2, '0')}/${Number(parts[2])
    .toString()
    .padStart(2, '0')}`;
}

function mapStatus(s: PlanListItem['status']): 'active' | 'paused' | 'completed' {
  if (s === 'terminated') return 'completed';
  return s;
}

const styles = StyleSheet.create({
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.sm,
    backgroundColor: theme.colors.bgPage,
  },
  backBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    ...theme.typography.pageTitle,
    color: theme.colors.textPrimary,
  },
  createBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.primary,
  },
  createBtnText: {
    ...theme.typography.bodySm,
    color: theme.colors.bgCard,
    fontWeight: '600',
  },
  scrollContent: {
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingBottom: theme.layout.bottomSafeArea,
  },
  cardWrap: {
    marginTop: theme.spacing.md,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
