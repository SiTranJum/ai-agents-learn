// PlanProgressCard - 计划进度卡片
// 有计划：名称 + 状态标签 + 进度条 + 任务完成数
// 无计划：显示"创建计划"引导
// 参考: docs/prd/v1/ui-design/03-home-dashboard.md §3.F, §5.1

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card } from '@shared/ui/Card';
import { ProgressBar } from '@shared/ui/ProgressBar';
import { Tag } from '@shared/ui/Tag';
import { theme } from '@app/styles/theme';
import type { HomePlan } from '../types/home.types';

export interface PlanProgressCardProps {
  plan: HomePlan | null;
  onPress?: () => void;
  onCreatePlan?: () => void;
}

export function PlanProgressCard({ plan, onPress, onCreatePlan }: PlanProgressCardProps) {
  if (!plan) {
    return (
      <Card>
        <View style={styles.header}>
          <View style={styles.iconWrap}>
            <Feather name="clipboard" size={16} color={theme.colors.primary} />
          </View>
          <Text style={styles.title}>计划</Text>
        </View>
        <Text style={styles.emptyText}>还没有计划，和 AI 聊聊你的健康目标吧</Text>
        {onCreatePlan && (
          <TouchableOpacity onPress={onCreatePlan} style={styles.createBtn} activeOpacity={0.8}>
            <Text style={styles.createBtnText}>创建计划</Text>
          </TouchableOpacity>
        )}
      </Card>
    );
  }

  return (
    <Card onPress={onPress}>
      <View style={styles.header}>
        <View style={styles.iconWrap}>
          <Feather name="clipboard" size={16} color={theme.colors.primary} />
        </View>
        <Text style={styles.title} numberOfLines={1}>
          {plan.name}
        </Text>
        <Tag label="进行中" variant="default" size="small" />
      </View>

      <View style={styles.progressRow}>
        <ProgressBar current={plan.progress} target={100} color={theme.colors.primary} height={8} />
        <Text style={styles.progressText}>{plan.progress}%</Text>
      </View>

      <View style={styles.footer}>
        <Text style={styles.taskText}>
          今日任务 {plan.completedTasks}/{plan.totalTasks} 已完成
        </Text>
        {onPress && <Text style={styles.link}>查看计划 →</Text>}
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
    gap: theme.spacing.sm,
  },
  iconWrap: {
    width: 28,
    height: 28,
    borderRadius: theme.radius.full,
    backgroundColor: theme.colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    flex: 1,
  },
  progressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginVertical: theme.spacing.sm,
  },
  progressText: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    fontWeight: '600',
    minWidth: 40,
    textAlign: 'right',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: theme.spacing.xs,
  },
  taskText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  link: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  emptyText: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    marginVertical: theme.spacing.sm,
  },
  createBtn: {
    backgroundColor: theme.colors.primary,
    borderRadius: theme.radius.pill,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
    alignSelf: 'flex-start',
    marginTop: theme.spacing.xs,
  },
  createBtnText: {
    ...theme.typography.bodySm,
    color: theme.colors.bgCard,
    fontWeight: '600',
  },
});
