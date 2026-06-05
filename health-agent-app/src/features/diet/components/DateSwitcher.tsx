// DateSwitcher - 日期切换栏
// 仅负责外层 UI（日期文字 + 日历图标）；日期选择器逻辑委托给平台专属的 DatePicker：
//   - Web   → DatePicker.web.tsx（浏览器原生 <input type="date">）
//   - 原生  → DatePicker.tsx（@react-native-community/datetimepicker）
// 参考: docs/prd/v1/ui-design/04-diet-record-page.md §3.1, §6.5

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { theme } from '@app/styles/theme';
import { DatePicker } from './DatePicker';

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

export function DateSwitcher({
  date,
  onDateChange,
  disableFuture = true,
}: DateSwitcherProps) {
  return (
    <View style={styles.container}>
      <DatePicker date={date} onDateChange={onDateChange} disableFuture={disableFuture}>
        <View style={styles.dateButton}>
          <Text style={styles.label}>{formatDate(date)}</Text>
          <Feather
            name="calendar"
            size={16}
            color={theme.colors.textSecondary}
            style={styles.calendarIcon}
          />
        </View>
      </DatePicker>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.bgPage,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.md,
    gap: theme.spacing.xs,
  },
  label: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  calendarIcon: {
    marginLeft: 4,
  },
});
