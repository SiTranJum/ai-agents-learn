// DataRecordList - 历史记录列表
// 根据 Tab 类型渲染对应字段
// 参考: docs/prd/v1/ui-design/06-data-page.md §3

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Card } from '@shared/ui/Card';
import { theme } from '@app/styles/theme';
import type {
  BodyRecord,
  BowelRecord,
  DataTabType,
  ExerciseRecord,
  MeasurementRecord,
  SleepRecord,
  WaterRecord,
  WeightRecord,
} from '../types/data.types';

export interface DataRecordListProps {
  tab: DataTabType;
  records: BodyRecord[];
  isLoading?: boolean;
}

const BOWEL_STATUS_LABEL = {
  normal: '正常',
  constipation: '便秘',
  diarrhea: '腹泻',
} as const;

const SLEEP_QUALITY_LABEL = {
  excellent: '优秀',
  good: '良好',
  fair: '一般',
  poor: '较差',
} as const;

export function DataRecordList({ tab, records, isLoading }: DataRecordListProps) {
  return (
    <View>
      <Text style={styles.title}>历史记录</Text>
      <Card style={styles.list}>
        {isLoading ? (
          <View style={styles.center}>
            <ActivityIndicator color={theme.colors.primary} />
          </View>
        ) : records.length === 0 ? (
          <Text style={styles.empty}>暂无历史记录</Text>
        ) : (
          records.map((r, idx) => (
            <View
              key={(r as { id?: string }).id ?? idx}
              style={[styles.row, idx === records.length - 1 && styles.rowLast]}
            >
              <Text style={styles.date}>{formatDate((r as { date: string }).date)}</Text>
              <Text style={styles.value}>{renderValue(tab, r)}</Text>
            </View>
          ))
        )}
      </Card>
    </View>
  );
}

function formatDate(d: string): string {
  const parts = d.split('-');
  if (parts.length !== 3) return d;
  return `${Number(parts[1])}月${Number(parts[2])}日`;
}

function renderValue(tab: DataTabType, r: BodyRecord): string {
  switch (tab) {
    case 'weight':
      return `${(r as WeightRecord).weight} kg`;
    case 'measurement': {
      const m = r as MeasurementRecord;
      return `腰 ${m.waist ?? '--'} / 臀 ${m.hip ?? '--'} cm`;
    }
    case 'sleep': {
      const s = r as SleepRecord;
      const h = Math.floor(s.duration / 60);
      const min = s.duration % 60;
      return `${h}h${min}min · ${SLEEP_QUALITY_LABEL[s.quality]}`;
    }
    case 'exercise': {
      const e = r as ExerciseRecord;
      return `${e.type} · ${e.duration}min · ${e.calories}kcal`;
    }
    case 'water': {
      const w = r as WaterRecord;
      return `${w.amount} / ${w.target} ml`;
    }
    case 'bowel': {
      const b = r as BowelRecord;
      return `${b.time} · ${BOWEL_STATUS_LABEL[b.status]}`;
    }
  }
}

const styles = StyleSheet.create({
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
  },
  list: {
    padding: 0,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
  },
  rowLast: {
    borderBottomWidth: 0,
  },
  date: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
  value: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  center: {
    paddingVertical: theme.spacing.xl,
    alignItems: 'center',
  },
  empty: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
    textAlign: 'center',
    paddingVertical: theme.spacing.xl,
  },
});
