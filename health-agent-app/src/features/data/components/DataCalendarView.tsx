import React, { useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { Card } from '@shared/ui/Card';
import { formatDate, formatFriendlyDate, todayStr } from '@shared/utils/date';

import type { BodyRecord, DataTabType } from '../types/data.types';

interface DataCalendarViewProps {
  tab: DataTabType;
  month: Date;
  records: BodyRecord[];
  isLoading?: boolean;
  onMonthChange: (month: Date) => void;
}

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日'];

const TAB_LABEL: Record<DataTabType, string> = {
  weight: '体重',
  measurement: '围度',
  sleep: '睡眠',
  exercise: '运动',
  water: '饮水',
  bowel: '排便',
};

export function DataCalendarView({ tab, month, records, isLoading, onMonthChange }: DataCalendarViewProps) {
  const [selectedDate, setSelectedDate] = useState(todayStr());

  const recordsByDate = useMemo(() => {
    const map = new Map<string, BodyRecord[]>();
    records.forEach((record) => {
      const date = (record as { date: string }).date;
      map.set(date, [...(map.get(date) ?? []), record]);
    });
    return map;
  }, [records]);

  const days = useMemo(() => {
    const firstDay = new Date(month.getFullYear(), month.getMonth(), 1);
    const daysInMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
    const leading = (firstDay.getDay() + 6) % 7;
    const cells: Array<{ date: string; day: number } | null> = Array.from({ length: leading }, () => null);
    for (let day = 1; day <= daysInMonth; day += 1) {
      cells.push({
        day,
        date: formatDate(new Date(month.getFullYear(), month.getMonth(), day)),
      });
    }
    while (cells.length % 7 !== 0) cells.push(null);
    return cells;
  }, [month]);

  const selectedRecords = recordsByDate.get(selectedDate) ?? [];

  const shiftMonth = (delta: number) => {
    const next = new Date(month.getFullYear(), month.getMonth() + delta, 1);
    onMonthChange(next);
    setSelectedDate(formatDate(next));
  };

  return (
    <View>
      <View style={styles.header}>
        <Text style={styles.title}>{TAB_LABEL[tab]}日历</Text>
        <View style={styles.monthControls}>
          <TouchableOpacity style={styles.iconButton} onPress={() => shiftMonth(-1)}>
            <Feather name="chevron-left" size={18} color={theme.colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.monthText}>{month.getFullYear()}年{month.getMonth() + 1}月</Text>
          <TouchableOpacity style={styles.iconButton} onPress={() => shiftMonth(1)}>
            <Feather name="chevron-right" size={18} color={theme.colors.textPrimary} />
          </TouchableOpacity>
        </View>
      </View>

      <Card style={styles.card}>
        {isLoading ? (
          <View style={styles.loading}>
            <ActivityIndicator color={theme.colors.primary} />
          </View>
        ) : (
          <>
            <View style={styles.weekRow}>
              {WEEKDAYS.map((day) => (
                <Text key={day} style={styles.weekday}>{day}</Text>
              ))}
            </View>
            <View style={styles.grid}>
              {days.map((cell, index) => {
                if (cell === null) {
                  return <View key={`empty-${index}`} style={styles.dayCell} />;
                }
                const hasRecord = recordsByDate.has(cell.date);
                const selected = selectedDate === cell.date;
                return (
                  <TouchableOpacity
                    key={cell.date}
                    style={[styles.dayCell, selected && styles.daySelected]}
                    onPress={() => setSelectedDate(cell.date)}
                    activeOpacity={0.75}
                  >
                    <Text style={[styles.dayText, selected && styles.dayTextSelected]}>
                      {cell.day}
                    </Text>
                    {hasRecord && <View style={[styles.dot, selected && styles.dotSelected]} />}
                  </TouchableOpacity>
                );
              })}
            </View>
            <View style={styles.detail}>
              <Text style={styles.detailTitle}>{formatFriendlyDate(selectedDate)}</Text>
              {selectedRecords.length === 0 ? (
                <Text style={styles.empty}>当天暂无记录</Text>
              ) : (
                selectedRecords.map((record, index) => (
                  <Text key={(record as { id?: string }).id ?? index} style={styles.recordText}>
                    {renderRecord(tab, record)}
                  </Text>
                ))
              )}
            </View>
          </>
        )}
      </Card>
    </View>
  );
}

function renderRecord(tab: DataTabType, record: BodyRecord): string {
  switch (tab) {
    case 'weight':
      return `${(record as { weight: number }).weight} kg`;
    case 'measurement': {
      const item = record as { waist?: number; hip?: number; thigh?: number; arm?: number };
      return `腰 ${item.waist ?? '--'} / 臀 ${item.hip ?? '--'} / 腿 ${item.thigh ?? '--'} / 臂 ${item.arm ?? '--'} cm`;
    }
    case 'sleep': {
      const item = record as { duration: number; bedTime: string; wakeTime: string };
      return `${Math.floor(item.duration / 60)}小时${item.duration % 60}分 · ${item.bedTime}-${item.wakeTime}`;
    }
    case 'exercise': {
      const item = record as { type: string; duration: number; calories: number };
      return `${item.type} · ${item.duration}分钟 · ${item.calories}kcal`;
    }
    case 'water': {
      const item = record as { amount: number; target: number };
      return `${item.amount} / ${item.target} ml`;
    }
    case 'bowel': {
      const item = record as { time: string; status: string };
      return `${item.time} · ${item.status}`;
    }
  }
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.sm,
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  monthControls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
  },
  iconButton: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.sm,
    borderWidth: 1,
    borderColor: theme.colors.divider,
  },
  monthText: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    minWidth: 86,
    textAlign: 'center',
  },
  card: {
    padding: theme.spacing.md,
  },
  loading: {
    paddingVertical: theme.spacing.xl,
  },
  weekRow: {
    flexDirection: 'row',
    marginBottom: theme.spacing.xs,
  },
  weekday: {
    flex: 1,
    textAlign: 'center',
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  dayCell: {
    width: `${100 / 7}%`,
    aspectRatio: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.sm,
  },
  daySelected: {
    backgroundColor: theme.colors.primaryLight,
  },
  dayText: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  dayTextSelected: {
    color: theme.colors.primary,
  },
  dot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: theme.colors.primary,
    marginTop: 3,
  },
  dotSelected: {
    backgroundColor: theme.colors.success,
  },
  detail: {
    marginTop: theme.spacing.md,
    paddingTop: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
    gap: theme.spacing.xs,
  },
  detailTitle: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    fontWeight: '600',
  },
  empty: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
  },
  recordText: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
});
