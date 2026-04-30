// QuickActionBar - 快捷操作区
// 三个等宽按钮：记录饮食、记录体重、查看计划
// 参考: docs/prd/v1/ui-design/03-home-dashboard.md §3.C, §6.1

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { theme } from '@app/styles/theme';

export interface QuickActionBarProps {
  onRecordDiet: () => void;
  onRecordWeight: () => void;
  onViewPlan: () => void;
}

export function QuickActionBar({
  onRecordDiet,
  onRecordWeight,
  onViewPlan,
}: QuickActionBarProps) {
  return (
    <View style={styles.row}>
      <ActionButton icon="coffee" label="记录饮食" onPress={onRecordDiet} />
      <ActionButton icon="bar-chart-2" label="记录体重" onPress={onRecordWeight} />
      <ActionButton icon="clipboard" label="查看计划" onPress={onViewPlan} />
    </View>
  );
}

interface ActionButtonProps {
  icon: keyof typeof Feather.glyphMap;
  label: string;
  onPress: () => void;
}

function ActionButton({ icon, label, onPress }: ActionButtonProps) {
  return (
    <TouchableOpacity style={styles.btn} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.iconWrap}>
        <Feather name={icon} size={20} color={theme.colors.primary} />
      </View>
      <Text style={styles.label}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  btn: {
    flex: 1,
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    paddingVertical: theme.spacing.md,
    alignItems: 'center',
    ...theme.shadows.card,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: theme.radius.full,
    backgroundColor: theme.colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.xs,
  },
  label: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    fontWeight: '500',
  },
});
