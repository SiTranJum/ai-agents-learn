// DataTabBar - 6 个 Tab 切换栏（横向滚动）
// 体重 / 围度 / 睡眠 / 运动 / 饮水 / 排便
// 参考: docs/prd/v1/ui-design/06-data-page.md §3

import React from 'react';
import { ScrollView, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { theme } from '@app/styles/theme';
import type { DataTabType } from '../types/data.types';

export interface DataTabBarProps {
  value: DataTabType;
  onChange: (tab: DataTabType) => void;
}

const TABS: { value: DataTabType; label: string; icon: keyof typeof Feather.glyphMap }[] = [
  { value: 'weight', label: '体重', icon: 'bar-chart-2' },
  { value: 'measurement', label: '围度', icon: 'maximize' },
  { value: 'sleep', label: '睡眠', icon: 'moon' },
  { value: 'exercise', label: '运动', icon: 'activity' },
  { value: 'water', label: '饮水', icon: 'droplet' },
  { value: 'bowel', label: '排便', icon: 'check-circle' },
];

export function DataTabBar({ value, onChange }: DataTabBarProps) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.row}
    >
      {TABS.map((tab) => {
        const active = tab.value === value;
        return (
          <TouchableOpacity
            key={tab.value}
            style={[styles.tab, active && styles.tabActive]}
            onPress={() => onChange(tab.value)}
            activeOpacity={0.8}
          >
            <Feather
              name={tab.icon}
              size={14}
              color={active ? theme.colors.bgCard : theme.colors.textSecondary}
            />
            <Text style={[styles.label, active && styles.labelActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: {
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingVertical: theme.spacing.sm,
    gap: theme.spacing.sm,
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.md,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.bgCard,
    borderWidth: 1,
    borderColor: theme.colors.divider,
  },
  tabActive: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  label: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  labelActive: {
    color: theme.colors.bgCard,
    fontWeight: '600',
  },
});
