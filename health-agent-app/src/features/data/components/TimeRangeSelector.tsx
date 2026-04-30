// TimeRangeSelector - 时间范围切换按钮组
// 7天 / 30天 / 90天 / 365天
// 参考: docs/prd/v1/ui-design/06-data-page.md §3

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';
import type { TimeRange } from '../types/data.types';

export interface TimeRangeSelectorProps {
  value: TimeRange;
  onChange: (range: TimeRange) => void;
}

const OPTIONS: { value: TimeRange; label: string }[] = [
  { value: '7d', label: '7天' },
  { value: '30d', label: '30天' },
  { value: '90d', label: '90天' },
  { value: '365d', label: '365天' },
];

export function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps) {
  return (
    <View style={styles.row}>
      {OPTIONS.map((opt) => {
        const active = opt.value === value;
        return (
          <TouchableOpacity
            key={opt.value}
            style={[styles.btn, active && styles.btnActive]}
            onPress={() => onChange(opt.value)}
            activeOpacity={0.8}
          >
            <Text style={[styles.label, active && styles.labelActive]}>
              {opt.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  btn: {
    flex: 1,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.bgCard,
    borderWidth: 1,
    borderColor: theme.colors.divider,
    alignItems: 'center',
  },
  btnActive: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  label: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
  },
  labelActive: {
    color: theme.colors.bgCard,
    fontWeight: '600',
  },
});
