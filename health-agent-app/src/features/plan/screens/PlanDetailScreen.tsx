import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { Card } from '@shared/ui/Card';
import { Button } from '@shared/ui/Button';
import { LineChart } from '@shared/charts/LineChart';
import { ConfirmDialog } from '@shared/feedback/ConfirmDialog';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList } from '@app/navigation/types';

import { TaskList } from '../components/TaskList';
import { usePlanDetail, useTerminatePlan, useToggleTask } from '../hooks/usePlanData';
import type { PlanStatus } from '../types/plan.types';

type Nav = NativeStackNavigationProp<MainStackParamList, 'PlanDetail'>;
type R = RouteProp<MainStackParamList, 'PlanDetail'>;

const STATUS_CONFIG: Record<PlanStatus, { label: string; bg: string; text: string }> = {
  active: { label: '进行中', bg: '#E8F9ED', text: '#4CD964' },
  completed: { label: '已完成', bg: '#E8F6FF', text: '#5AC8FA' },
  terminated: { label: '已终止', bg: '#F0F0F0', text: '#999999' },
};

export function PlanDetailScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<R>();
  const toast = useToast();

  const planId = route.params?.planId;
  const { data: plan, isLoading } = usePlanDetail(planId);
  const toggleMutation = useToggleTask(planId ?? '');
  const terminateMutation = useTerminatePlan();

  const [showTerminateConfirm, setShowTerminateConfirm] = useState(false);

  const handleBack = useCallback(() => navigation.goBack(), [navigation]);

  const handleToggleTask = useCallback(
    (taskId: string) => {
      toggleMutation.mutate(taskId);
    },
    [toggleMutation]
  );

  const handleTerminate = useCallback(async () => {
    if (!planId) return;
    try {
      await terminateMutation.mutateAsync(planId);
      toast.show({ type: 'success', message: '计划已终止' });
      navigation.goBack();
    } catch {
      toast.show({ type: 'error', message: '终止计划失败，请重试' });
    } finally {
      setShowTerminateConfirm(false);
    }
  }, [navigation, planId, terminateMutation, toast]);

  if (isLoading || !plan) {
    return (
      <PageContainer useSafeArea>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      </PageContainer>
    );
  }

  const statusStyle = STATUS_CONFIG[plan.status];
  const isActive = plan.status === 'active';
  const isCompleted = plan.status === 'completed';
  const chartWidth = Dimensions.get('window').width - 64;

  return (
    <PageContainer useSafeArea>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
          <Feather name="chevron-left" size={24} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>{plan.name}</Text>
        <View style={[styles.statusTag, { backgroundColor: statusStyle.bg }]}>
          <Text style={[styles.statusText, { color: statusStyle.text }]}>{statusStyle.label}</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {plan.warning ? (
          <Card style={styles.warningCard}>
            <Text style={styles.warningTitle}>连续 {plan.warning.daysMissed} 天未达标</Text>
            <Text style={styles.warningDesc}>{plan.warning.description}</Text>
          </Card>
        ) : null}

        <Card>
          {plan.targetWeight != null ? <Row label="目标体重" value={`${plan.targetWeight} kg`} /> : null}
          {plan.duration ? <Row label="计划周期" value={plan.duration} /> : null}
          {plan.currentPhase ? <Row label="当前阶段" value={plan.currentPhase} /> : null}
          <Row label="今日任务" value={`${plan.completedTasks}/${plan.totalTasks}`} />
          <Row label="连续达标" value={`${plan.streakDays} 天`} last={plan.dailyCalorieTarget == null} />
          {plan.dailyCalorieTarget != null ? <Row label="每日热量" value={`${plan.dailyCalorieTarget} kcal`} last /> : null}
        </Card>

        {plan.phases.length > 0 ? (
          <>
            <Text style={styles.sectionTitle}>阶段时间线</Text>
            <Card>
              {plan.phases.map((phase, index) => (
                <View key={phase.id} style={[styles.phaseBlock, index !== plan.phases.length - 1 && styles.phaseBorder]}>
                  <Text style={styles.phaseTitle}>{phase.title}</Text>
                  <Text style={styles.phaseMeta}>
                    {phase.startDate} 至 {phase.endDate}
                  </Text>
                  <Text style={styles.phaseGoal}>{phase.goal}</Text>
                  {phase.tasks.map((task) => (
                    <Text key={task.id} style={styles.phaseTask}>
                      • {task.text}
                    </Text>
                  ))}
                </View>
              ))}
            </Card>
          </>
        ) : null}

        <Text style={styles.sectionTitle}>{isCompleted ? '计划总结' : '今日任务'}</Text>
        {isCompleted ? (
          <Card>
            <Text style={styles.summaryText}>{plan.aiSuggestion}</Text>
          </Card>
        ) : (
          <TaskList tasks={plan.tasks} readonly={!isActive} onToggle={handleToggleTask} />
        )}

        {plan.trendData.length > 0 ? (
          <>
            <Text style={styles.sectionTitle}>执行趋势</Text>
            <Card>
              <LineChart
                data={{
                  labels: sampleLabels(plan.trendData.map((point) => point.date), 5),
                  datasets: [{ data: plan.trendData.map((point) => point.value) }],
                }}
                width={chartWidth}
                height={180}
              />
            </Card>
          </>
        ) : null}

        {!isCompleted ? (
          <>
            <Text style={styles.sectionTitle}>AI 调整建议</Text>
            <Card>
              <Text style={styles.adviceText}>{plan.aiSuggestion}</Text>
            </Card>
          </>
        ) : null}

        <View style={styles.actions}>
          {isCompleted ? (
            <View style={styles.actionBtn}>
              <Button variant="primary" onPress={() => navigation.navigate('PlanCreate')}>
                创建新计划
              </Button>
            </View>
          ) : (
            <>
              <View style={styles.actionBtn}>
                <Button
                  variant="primary"
                  onPress={() => toast.show({ type: 'info', message: '可以在 AI 对话里直接提出计划调整需求' })}
                >
                  修改计划
                </Button>
              </View>
              <View style={styles.actionBtn}>
                <Button variant="secondary" onPress={() => setShowTerminateConfirm(true)}>
                  终止计划
                </Button>
              </View>
            </>
          )}
        </View>
      </ScrollView>

      <ConfirmDialog
        visible={showTerminateConfirm}
        title="终止计划？"
        message="终止后将不再追踪当前计划进度。"
        confirmText="终止"
        cancelText="取消"
        variant="danger"
        onConfirm={handleTerminate}
        onCancel={() => setShowTerminateConfirm(false)}
      />
    </PageContainer>
  );
}

function Row({ label, value, last }: { label: string; value: string; last?: boolean }) {
  return (
    <View style={[styles.kvRow, !last && styles.kvRowBorder]}>
      <Text style={styles.kvLabel}>{label}</Text>
      <Text style={styles.kvValue}>{value}</Text>
    </View>
  );
}

function sampleLabels(labels: string[], count: number): string[] {
  if (labels.length <= count) {
    return labels.map(formatLabel);
  }
  const step = Math.max(1, Math.floor(labels.length / count));
  return labels.filter((_, index) => index % step === 0).slice(0, count).map(formatLabel);
}

function formatLabel(value: string): string {
  const parts = value.split('-');
  if (parts.length !== 3) return value;
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
    flex: 1,
    textAlign: 'center',
  },
  statusTag: {
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 4,
    marginRight: theme.spacing.sm,
  },
  statusText: {
    ...theme.typography.tag,
    fontWeight: '600',
  },
  scrollContent: {
    padding: theme.layout.pageHorizontalPadding,
    paddingBottom: theme.layout.bottomSafeArea,
    gap: theme.spacing.md,
  },
  sectionTitle: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginTop: theme.spacing.sm,
  },
  kvRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.sm,
  },
  kvRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
  },
  kvLabel: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  kvValue: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  warningCard: {
    backgroundColor: '#FFF7E0',
  },
  warningTitle: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
    marginBottom: theme.spacing.xs,
  },
  warningDesc: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  phaseBlock: {
    paddingVertical: theme.spacing.sm,
  },
  phaseBorder: {
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
  },
  phaseTitle: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  phaseMeta: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
  },
  phaseGoal: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
    lineHeight: 20,
  },
  phaseTask: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    marginTop: theme.spacing.xs,
    lineHeight: 20,
  },
  adviceText: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    lineHeight: 22,
  },
  summaryText: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    lineHeight: 22,
  },
  actions: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginTop: theme.spacing.md,
  },
  actionBtn: {
    flex: 1,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
