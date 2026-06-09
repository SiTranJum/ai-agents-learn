import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

import { theme } from '@app/styles/theme';

import type {
  BodyParseCard,
  ChatCard,
  DietParseCard,
  PlanDraftCard,
  PlanProgressCard,
  PlanSavedCard,
} from '../../types/ai.types';

interface Props {
  card: ChatCard;
  status?: 'pending' | 'submitted' | 'cancelled';
  onActionPress?: (actionKind: string, label: string) => void;
}

export function StreamingCardView({ card, status = 'pending', onActionPress }: Props) {
  const isInteractive = status === 'pending';

  if (card.type === 'diet_parse') {
    return <DietParseCardView card={card as DietParseCard} status={status} isInteractive={isInteractive} onActionPress={onActionPress} />;
  }
  if (card.type === 'body_parse') {
    return <BodyParseCardView card={card as BodyParseCard} status={status} isInteractive={isInteractive} onActionPress={onActionPress} />;
  }
  if (card.type === 'plan_draft') {
    return <PlanDraftCardView card={card as PlanDraftCard} status={status} isInteractive={isInteractive} onActionPress={onActionPress} />;
  }
  if (card.type === 'plan_saved') {
    return <PlanSavedCardView card={card as PlanSavedCard} status={status} isInteractive={isInteractive} onActionPress={onActionPress} />;
  }
  if (card.type === 'plan_progress') {
    return <PlanProgressCardView card={card as PlanProgressCard} status={status} isInteractive={isInteractive} onActionPress={onActionPress} />;
  }

  return <GenericCardView card={card} status={status} isInteractive={isInteractive} onActionPress={onActionPress} />;
}

function CardActions({
  card,
  isInteractive,
  onActionPress,
}: {
  card: ChatCard;
  isInteractive: boolean;
  onActionPress?: (actionKind: string, label: string) => void;
}) {
  if (!isInteractive || !card.actions?.length) {
    return null;
  }
  return (
    <View style={styles.actionsRow}>
      {card.actions.map((action, index) => (
        <TouchableOpacity
          key={`${action.kind}-${index}`}
          style={[styles.actionBtn, index === 0 && styles.actionBtnPrimary]}
          onPress={() => onActionPress?.(action.kind, action.label ?? action.kind)}
          activeOpacity={0.7}
        >
          <Text style={[styles.actionLabel, index === 0 && styles.actionLabelPrimary]}>
            {action.label ?? action.kind}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

function StatusBadge({ status }: { status: 'pending' | 'submitted' | 'cancelled' }) {
  if (status === 'submitted') {
    return <Text style={styles.statusBadge}>已确认</Text>;
  }
  if (status === 'cancelled') {
    return <Text style={styles.statusBadge}>已取消</Text>;
  }
  return null;
}

function DietParseCardView({
  card,
  status,
  isInteractive,
  onActionPress,
}: {
  card: DietParseCard;
  status: 'pending' | 'submitted' | 'cancelled';
  isInteractive: boolean;
  onActionPress?: (actionKind: string, label: string) => void;
}) {
  const { foods, meal_type, nutrition_summary } = card.payload;
  const mealLabel: Record<string, string> = {
    breakfast: '早餐',
    lunch: '午餐',
    dinner: '晚餐',
    snack: '加餐',
  };
  return (
    <View style={[styles.card, !isInteractive && styles.cardDisabled]}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{mealLabel[meal_type ?? 'snack'] ?? '饮食'}</Text>
        <StatusBadge status={status} />
      </View>
      {foods.map((food, index) => (
        <View key={`${food.name}-${index}`} style={styles.foodRow}>
          <Text style={styles.foodName}>{food.name}</Text>
          <Text style={styles.foodAmount}>
            {food.amount}
            {food.unit} · {Math.round(food.calories)} kcal
          </Text>
        </View>
      ))}
      {nutrition_summary ? (
        <View style={styles.summaryRow}>
          <Text style={styles.summary}>
            合计 {Math.round(nutrition_summary.total_calories)} kcal · 蛋白质 {Math.round(nutrition_summary.total_protein)} g
          </Text>
        </View>
      ) : null}
      <CardActions card={card} isInteractive={isInteractive} onActionPress={onActionPress} />
    </View>
  );
}

function BodyParseCardView({
  card,
  status,
  isInteractive,
  onActionPress,
}: {
  card: BodyParseCard;
  status: 'pending' | 'submitted' | 'cancelled';
  isInteractive: boolean;
  onActionPress?: (actionKind: string, label: string) => void;
}) {
  const rows = bodyRows(card);
  return (
    <View style={[styles.card, !isInteractive && styles.cardDisabled]}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{bodyTitle(card.payload.record_type)}</Text>
        <StatusBadge status={status} />
      </View>
      {rows.map(([label, value]) => (
        <View key={label} style={styles.foodRow}>
          <Text style={styles.foodName}>{label}</Text>
          <Text style={styles.foodAmount}>{value}</Text>
        </View>
      ))}
      <CardActions card={card} isInteractive={isInteractive} onActionPress={onActionPress} />
    </View>
  );
}

function bodyTitle(type: BodyParseCard['payload']['record_type']): string {
  const labels: Record<BodyParseCard['payload']['record_type'], string> = {
    water: '饮水',
    sleep: '睡眠',
    exercise: '运动',
    bowel: '排便',
  };
  return labels[type] ?? '身体数据';
}

function bodyRows(card: BodyParseCard): Array<[string, string]> {
  const payload = card.payload;
  if (payload.record_type === 'water') {
    return [['饮水量', `${payload.water_amount ?? 0} ml`]];
  }
  if (payload.record_type === 'sleep') {
    return [
      ['时间', `${payload.sleep_bed_time ?? '--'} - ${payload.sleep_wake_time ?? '--'}`],
      ['质量', payload.sleep_quality ?? '--'],
    ];
  }
  if (payload.record_type === 'exercise') {
    return [
      ['类型', payload.exercise_type ?? '--'],
      ['时长', payload.exercise_duration ? `${payload.exercise_duration} 分钟` : '--'],
    ];
  }
  return [
    ['时间', payload.bowel_time ?? '--'],
    ['状态', payload.bowel_status ?? '--'],
  ];
}

function PlanDraftCardView({
  card,
  status,
  isInteractive,
  onActionPress,
}: {
  card: PlanDraftCard;
  status: 'pending' | 'submitted' | 'cancelled';
  isInteractive: boolean;
  onActionPress?: (actionKind: string, label: string) => void;
}) {
  const { draft, violations = [] } = card.payload;
  const [expanded, setExpanded] = useState(false);
  const phases = draft.phases ?? [];
  const firstPhase = phases[0];
  const taskCount = phases.reduce((total, phase) => total + phase.tasks.length, 0) || draft.tasks.length;
  const targetBits = [
    draft.targets.weight_target != null ? `目标体重 ${draft.targets.weight_target} kg` : null,
    draft.targets.daily_calories != null ? `${draft.targets.daily_calories} kcal/天` : null,
  ].filter(Boolean);
  return (
    <View style={[styles.card, !isInteractive && styles.cardDisabled]}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{draft.name}</Text>
        <StatusBadge status={status} />
      </View>
      <Text style={styles.summary}>{draft.goal_description}</Text>
      <View style={styles.metricGrid}>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>周期</Text>
          <Text style={styles.metricValue}>{draft.start_date} 至 {draft.target_date}</Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>结构</Text>
          <Text style={styles.metricValue}>{phases.length || 1} 个阶段 · {taskCount} 个任务</Text>
        </View>
        {targetBits.length > 0 ? (
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>目标</Text>
            <Text style={styles.metricValue}>{targetBits.join(' · ')}</Text>
          </View>
        ) : null}
      </View>
      {violations.length > 0 ? (
        <View style={styles.warningBox}>
          <Text style={styles.warningTitle}>安全调整</Text>
          <Text style={styles.warningText}>{violations.join('，')}</Text>
        </View>
      ) : null}
      {firstPhase ? (
        <View style={styles.previewBlock}>
          <Text style={styles.previewLabel}>先执行</Text>
          <Text style={styles.phaseTitle}>{firstPhase.title}</Text>
          <Text style={styles.phaseGoal}>{firstPhase.goal}</Text>
          {firstPhase.tasks.slice(0, 3).map((task) => (
            <View key={task.id} style={styles.taskRow}>
              <View style={styles.taskDot} />
              <Text style={styles.phaseTask}>{task.description}</Text>
            </View>
          ))}
        </View>
      ) : null}
      {phases.length > 0 ? (
        <TouchableOpacity style={styles.detailsToggle} onPress={() => setExpanded((value) => !value)} activeOpacity={0.75}>
          <Text style={styles.detailsToggleText}>{expanded ? '收起阶段详情' : `展开 ${phases.length} 个阶段和全部任务`}</Text>
        </TouchableOpacity>
      ) : null}
      {expanded
        ? phases.map((phase) => (
            <View key={phase.id} style={styles.phaseBlock}>
              <Text style={styles.phaseTitle}>{phase.title}</Text>
              <Text style={styles.phaseMeta}>
                {phase.start_date} 至 {phase.end_date}
              </Text>
              <Text style={styles.phaseGoal}>{phase.goal}</Text>
              {phase.tasks.map((task) => (
                <View key={task.id} style={styles.taskRow}>
                  <View style={styles.taskDot} />
                  <Text style={styles.phaseTask}>{task.description}</Text>
                </View>
              ))}
            </View>
          ))
        : null}
      <CardActions card={card} isInteractive={isInteractive} onActionPress={onActionPress} />
    </View>
  );
}

function PlanSavedCardView({
  card,
  status,
  isInteractive,
  onActionPress,
}: {
  card: PlanSavedCard;
  status: 'pending' | 'submitted' | 'cancelled';
  isInteractive: boolean;
  onActionPress?: (actionKind: string, label: string) => void;
}) {
  return (
    <View style={[styles.card, !isInteractive && styles.cardDisabled]}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>计划已保存</Text>
        <StatusBadge status={status} />
      </View>
      <Text style={styles.summary}>计划 ID：{card.payload.plan_id}</Text>
      <CardActions card={card} isInteractive={isInteractive} onActionPress={onActionPress} />
    </View>
  );
}

function PlanProgressCardView({
  card,
  status,
  isInteractive,
  onActionPress,
}: {
  card: PlanProgressCard;
  status: 'pending' | 'submitted' | 'cancelled';
  isInteractive: boolean;
  onActionPress?: (actionKind: string, label: string) => void;
}) {
  const payload = card.payload;
  return (
    <View style={[styles.card, !isInteractive && styles.cardDisabled]}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{payload.plan_name}</Text>
        <StatusBadge status={status} />
      </View>
      <Text style={styles.summary}>当前阶段：{payload.current_phase ?? '--'}</Text>
      <Text style={styles.phaseMeta}>
        今日任务：{payload.completed_tasks}/{payload.total_tasks}
      </Text>
      <Text style={styles.phaseMeta}>
        达标率：{Math.round((payload.compliance_rate ?? 0) * 100)}% · 连续达标：{payload.streak_days} 天
      </Text>
      <CardActions card={card} isInteractive={isInteractive} onActionPress={onActionPress} />
    </View>
  );
}

function GenericCardView({
  card,
  status,
  isInteractive,
  onActionPress,
}: {
  card: ChatCard;
  status: 'pending' | 'submitted' | 'cancelled';
  isInteractive: boolean;
  onActionPress?: (actionKind: string, label: string) => void;
}) {
  return (
    <View style={[styles.card, !isInteractive && styles.cardDisabled]}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{card.type}</Text>
        <StatusBadge status={status} />
      </View>
      {Object.entries(card.payload).map(([key, value]) => (
        <View key={key} style={styles.foodRow}>
          <Text style={styles.foodName}>{key}</Text>
          <Text style={styles.foodAmount}>{String(value)}</Text>
        </View>
      ))}
      <CardActions card={card} isInteractive={isInteractive} onActionPress={onActionPress} />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    padding: theme.spacing.lg,
    marginVertical: theme.spacing.sm,
    ...theme.shadows.card,
  },
  cardDisabled: {
    opacity: 0.6,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.sm,
  },
  cardTitle: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    flex: 1,
  },
  statusBadge: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  foodRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.xs,
    gap: theme.spacing.md,
  },
  foodName: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    flex: 1,
  },
  foodAmount: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
  },
  summaryRow: {
    paddingTop: theme.spacing.sm,
    marginTop: theme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
  },
  summary: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    lineHeight: 20,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.md,
  },
  actionBtn: {
    flex: 1,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.divider,
    backgroundColor: theme.colors.bgCard,
    alignItems: 'center',
  },
  actionBtnPrimary: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  actionLabel: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
  },
  actionLabelPrimary: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  warningBox: {
    marginTop: theme.spacing.sm,
    padding: theme.spacing.sm,
    borderRadius: theme.radius.md,
    backgroundColor: '#FFF5E8',
  },
  warningTitle: {
    ...theme.typography.bodySm,
    color: '#8A5200',
    fontWeight: '600',
    marginBottom: theme.spacing.xs,
  },
  warningText: {
    ...theme.typography.caption,
    color: '#8A5200',
  },
  metricGrid: {
    marginTop: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  metricItem: {
    padding: theme.spacing.sm,
    borderRadius: theme.radius.md,
    backgroundColor: '#F6F8F4',
  },
  metricLabel: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginBottom: 2,
  },
  metricValue: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  previewBlock: {
    marginTop: theme.spacing.md,
    padding: theme.spacing.md,
    borderRadius: theme.radius.md,
    backgroundColor: '#F8F3EA',
  },
  previewLabel: {
    ...theme.typography.caption,
    color: '#8A5A16',
    fontWeight: '600',
    marginBottom: theme.spacing.xs,
  },
  detailsToggle: {
    marginTop: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    alignItems: 'center',
    borderRadius: theme.radius.md,
    backgroundColor: '#F2F3F5',
  },
  detailsToggleText: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  phaseBlock: {
    marginTop: theme.spacing.md,
    paddingTop: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
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
    flex: 1,
    lineHeight: 20,
  },
  taskRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.xs,
  },
  taskDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 7,
    backgroundColor: theme.colors.primary,
  },
});
