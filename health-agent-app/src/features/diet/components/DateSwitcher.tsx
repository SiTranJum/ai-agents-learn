// DateSwitcher - 日期切换栏
// 左右箭头切换日期 + 中央日期显示
// 参考: docs/prd/v1/ui-design/04-diet-record-page.md §3.1, §6.5

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { theme } from '@app/styles/theme';
import { todayStr } from '@shared/utils/date';

export interface DateSwitcherProps {
  /** 当前选中的日期 YYYY-MM-DD */
  date: string;
  onDateChange: (date: string) => void;
  /** 是否禁止切到未来日期，默认 true */
  disableFuture?: boolean;
}

const WEEK_DAYS = ['日', '一', '二', '三', '四', '五', '六'];

function formatDate(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00`);
  const y = d.getFullYear();
  const m = d.getMonth() + 1;
  const day = d.getDate();
  const wd = WEEK_DAYS[d.getDay()];
  return `${y}年${m}月${day}日 周${wd}`;
}

function shiftDate(dateStr: string, days: number): string {
  const d = new Date(`${dateStr}T00:00:00`);
  d.setDate(d.getDate() + days);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

export function DateSwitcher({
  date,
  onDateChange,
  disableFuture = true,
}: DateSwitcherProps) {
  const isToday = date === todayStr();
  const canGoNext = !disableFuture || !isToday;

  return (
    <View style={styles.container}>
      <TouchableOpacity
        onPress={() => onDateChange(shiftDate(date, -1))}
        style={styles.btn}
        activeOpacity={0.7}
      >
        <Feather name="chevron-left" size={22} color={theme.colors.textPrimary} />
      </TouchableOpacity>

      <Text style={styles.label}>{formatDate(date)}</Text>

      <TouchableOpacity
        onPress={() => canGoNext && onDateChange(shiftDate(date, 1))}
        style={styles.btn}
        activeOpacity={canGoNext ? 0.7 : 1}
        disabled={!canGoNext}
      >
        <Feather
          name="chevron-right"
          size={22}
          color={canGoNext ? theme.colors.textPrimary : theme.colors.divider}
        />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.bgPage,
  },
  btn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.full,
  },
  label: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
});
