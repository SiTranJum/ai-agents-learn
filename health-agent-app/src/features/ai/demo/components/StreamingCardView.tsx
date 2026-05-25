// 流式卡片视图：渲染 ChatCard
// 已知类型：diet_parse / exercise_suggestion / sleep_reminder
// 其他类型走通用 fallback（显示 type + payload JSON）

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { theme } from '@app/styles/theme';
import type { ChatCard, DietParseCard } from '../../types/ai.types';

interface Props {
  card: ChatCard;
  /** 卡片状态：pending=可操作 / submitted=已确认（变灰）/ cancelled=已取消 */
  status?: 'pending' | 'submitted' | 'cancelled';
  /** 用户点击某个 action */
  onActionPress?: (actionKind: string, label: string) => void;
}

export function StreamingCardView({ card, status = 'pending', onActionPress }: Props) {
  const isInteractive = status === 'pending';

  if (card.type === 'diet_parse') {
    return (
      <DietParseCardView
        card={card as DietParseCard}
        status={status}
        isInteractive={isInteractive}
        onActionPress={onActionPress}
      />
    );
  }

  // 通用 fallback：显示 type + 简单 payload
  return (
    <GenericCardView
      card={card}
      status={status}
      isInteractive={isInteractive}
      onActionPress={onActionPress}
    />
  );
}

// ============ 饮食卡片 ============

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
    breakfast: '🍳 早餐',
    lunch: '🍱 午餐',
    dinner: '🍲 晚餐',
    snack: '🍎 加餐',
  };
  return (
    <View style={[styles.card, !isInteractive && styles.cardDisabled]}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{mealLabel[meal_type ?? 'snack'] ?? '饮食'}</Text>
        {status === 'submitted' && <Text style={styles.statusBadge}>✓ 已保存</Text>}
        {status === 'cancelled' && <Text style={styles.statusBadge}>已取消</Text>}
      </View>
      {foods.map((f, idx) => (
        <View key={idx} style={styles.foodRow}>
          <Text style={styles.foodName}>• {f.name}</Text>
          <Text style={styles.foodAmount}>
            {f.amount}
            {f.unit} · {Math.round(f.calories)} kcal
          </Text>
        </View>
      ))}
      {nutrition_summary && (
        <View style={styles.summaryRow}>
          <Text style={styles.summary}>
            合计 {Math.round(nutrition_summary.total_calories)} kcal · 蛋白{' '}
            {Math.round(nutrition_summary.total_protein)}g
          </Text>
        </View>
      )}
      {isInteractive && card.actions && card.actions.length > 0 && (
        <View style={styles.actionsRow}>
          {card.actions.map((a, idx) => (
            <TouchableOpacity
              key={idx}
              style={[styles.actionBtn, idx === 0 && styles.actionBtnPrimary]}
              onPress={() => onActionPress?.(a.kind, a.label ?? '')}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.actionLabel,
                  idx === 0 && styles.actionLabelPrimary,
                ]}
              >
                {a.label ?? a.kind}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

// ============ 通用 fallback ============

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
        {status === 'submitted' && <Text style={styles.statusBadge}>✓ 已确认</Text>}
        {status === 'cancelled' && <Text style={styles.statusBadge}>已取消</Text>}
      </View>
      {Object.entries(card.payload).map(([k, v]) => (
        <View key={k} style={styles.foodRow}>
          <Text style={styles.foodName}>{k}</Text>
          <Text style={styles.foodAmount}>{String(v)}</Text>
        </View>
      ))}
      {isInteractive && card.actions && card.actions.length > 0 && (
        <View style={styles.actionsRow}>
          {card.actions.map((a, idx) => (
            <TouchableOpacity
              key={idx}
              style={[styles.actionBtn, idx === 0 && styles.actionBtnPrimary]}
              onPress={() => onActionPress?.(a.kind, a.label ?? '')}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.actionLabel,
                  idx === 0 && styles.actionLabelPrimary,
                ]}
              >
                {a.label ?? a.kind}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
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
  },
  statusBadge: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  foodRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.xs,
  },
  foodName: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
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
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
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
});
