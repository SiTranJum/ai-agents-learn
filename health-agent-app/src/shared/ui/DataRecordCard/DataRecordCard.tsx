import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

export interface DataRecordCardProps {
  recordType: 'weight' | 'measurement' | 'sleep' | 'exercise' | 'water' | 'bowel';
  status: 'empty' | 'pending' | 'recorded';
  data?: {
    label: string;
    value: string;
    unit: string;
    subItems?: Array<{ label: string; value: string; unit: string }>;
  };
  onPress?: () => void;
  onConfirm?: () => void;
  onEdit?: () => void;
  onCancel?: () => void;
}

const recordTypeLabels: Record<DataRecordCardProps['recordType'], string> = {
  weight: '体重',
  measurement: '围度',
  sleep: '睡眠',
  exercise: '运动',
  water: '饮水',
  bowel: '排便',
};

export function DataRecordCard({
  recordType,
  status,
  data,
  onPress,
  onConfirm,
  onEdit,
  onCancel,
}: DataRecordCardProps) {
  const typeLabel = recordTypeLabels[recordType];

  // Empty 状态：浅灰背景，点击记录
  if (status === 'empty') {
    return (
      <TouchableOpacity
        style={[styles.card, styles.emptyCard]}
        onPress={onPress}
        activeOpacity={0.7}
      >
        <Text style={styles.emptyTitle}>{typeLabel}</Text>
        <Text style={styles.emptyHint}>点击记录</Text>
      </TouchableOpacity>
    );
  }

  // Pending 状态：白底 + primaryLight 边框，显示 AI 解析结果 + 操作按钮
  if (status === 'pending') {
    return (
      <View style={[styles.card, styles.pendingCard]}>
        <Text style={styles.pendingLabel}>{typeLabel}</Text>
        {data && (
          <View style={styles.dataRow}>
            <Text style={styles.dataLabel}>{data.label}</Text>
            <Text style={styles.dataValue}>
              {data.value}
              <Text style={styles.dataUnit}> {data.unit}</Text>
            </Text>
          </View>
        )}
        {data?.subItems?.map((item, index) => (
          <View key={index} style={styles.subItemRow}>
            <Text style={styles.subItemLabel}>{item.label}</Text>
            <Text style={styles.subItemValue}>
              {item.value}
              <Text style={styles.dataUnit}> {item.unit}</Text>
            </Text>
          </View>
        ))}
        <View style={styles.actionRow}>
          <TouchableOpacity style={styles.confirmBtn} onPress={onConfirm}>
            <Text style={styles.confirmBtnText}>确认</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.editBtn} onPress={onEdit}>
            <Text style={styles.editBtnText}>修改</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.cancelBtn} onPress={onCancel}>
            <Text style={styles.cancelBtnText}>取消</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Recorded 状态：白底卡片，显示数据值
  return (
    <TouchableOpacity
      style={[styles.card, styles.recordedCard]}
      onPress={onPress}
      activeOpacity={0.7}
      disabled={!onPress}
    >
      <Text style={styles.recordedLabel}>{typeLabel}</Text>
      {data && (
        <View style={styles.dataRow}>
          <Text style={styles.dataLabel}>{data.label}</Text>
          <Text style={styles.dataValue}>
            {data.value}
            <Text style={styles.dataUnit}> {data.unit}</Text>
          </Text>
        </View>
      )}
      {data?.subItems?.map((item, index) => (
        <View key={index} style={styles.subItemRow}>
          <Text style={styles.subItemLabel}>{item.label}</Text>
          <Text style={styles.subItemValue}>
            {item.value}
            <Text style={styles.dataUnit}> {item.unit}</Text>
          </Text>
        </View>
      ))}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    minHeight: 116,
    borderRadius: theme.radius.md,
    padding: theme.spacing.lg,
    ...theme.shadows.card,
  },
  emptyCard: {
    backgroundColor: theme.colors.bgPage,
    justifyContent: 'center',
    alignItems: 'center',
  },
  pendingCard: {
    backgroundColor: theme.colors.bgCard,
    borderWidth: 1,
    borderColor: theme.colors.primaryLight,
  },
  recordedCard: {
    backgroundColor: theme.colors.bgCard,
  },
  emptyTitle: {
    ...theme.typography.cardTitle,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
  },
  emptyHint: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
  },
  pendingLabel: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
  },
  recordedLabel: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
  },
  dataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.xs,
  },
  dataLabel: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
  dataValue: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  dataUnit: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
  },
  subItemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.xs,
  },
  subItemLabel: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
  },
  subItemValue: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
    marginTop: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  confirmBtn: {
    backgroundColor: theme.colors.primary,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
  },
  confirmBtnText: {
    ...theme.typography.bodySm,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  editBtn: {
    backgroundColor: theme.colors.bgPage,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
  },
  editBtnText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  cancelBtn: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
  },
  cancelBtnText: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
  },
});
