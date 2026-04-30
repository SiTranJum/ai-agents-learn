// 今日记录卡片组合：6 类身体数据
// 三态：empty / pending / recorded
// 参考: docs/prd/v1/ui-design/06-data-page.md §5

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Card } from '@shared/ui/Card';
import { ProgressBar } from '@shared/ui/ProgressBar';
import { theme } from '@app/styles/theme';
import type {
  BowelRecord,
  ExerciseRecord,
  MeasurementRecord,
  SleepQuality,
  SleepRecord,
  WaterRecord,
  WeightRecord,
} from '../types/data.types';

const SLEEP_QUALITY_LABEL: Record<SleepQuality, string> = {
  excellent: '优秀',
  good: '良好',
  fair: '一般',
  poor: '较差',
};

const BOWEL_STATUS_LABEL = {
  normal: '正常',
  constipation: '便秘',
  diarrhea: '腹泻',
} as const;

// ===== 通用空态/操作按钮 =====
function EmptyCard({
  title,
  hint,
  onAdd,
}: {
  title: string;
  hint: string;
  onAdd: () => void;
}) {
  return (
    <Card>
      <Text style={styles.cardTitle}>{title}</Text>
      <Text style={styles.emptyHint}>{hint}</Text>
      <TouchableOpacity style={styles.addBtn} onPress={onAdd} activeOpacity={0.8}>
        <Text style={styles.addBtnText}>+ 手动记录</Text>
      </TouchableOpacity>
    </Card>
  );
}

function EditButton({ onEdit }: { onEdit: () => void }) {
  return (
    <TouchableOpacity onPress={onEdit} style={styles.editBtn} activeOpacity={0.7}>
      <Text style={styles.editBtnText}>修改</Text>
    </TouchableOpacity>
  );
}

// ===== 体重 =====
export function WeightCard({
  record,
  onAdd,
  onEdit,
}: {
  record: WeightRecord | null;
  onAdd: () => void;
  onEdit: () => void;
}) {
  if (!record) {
    return (
      <EmptyCard title="今日体重" hint="还没有记录今天的体重" onAdd={onAdd} />
    );
  }
  const changeText =
    record.change > 0 ? `比昨天 +${record.change}kg` :
    record.change < 0 ? `比昨天 ${record.change}kg` :
    '与昨天持平';
  return (
    <Card>
      <View style={styles.headerRow}>
        <Text style={styles.cardTitle}>今日体重</Text>
        <EditButton onEdit={onEdit} />
      </View>
      <Text style={styles.heroValue}>
        {record.weight}
        <Text style={styles.heroUnit}> kg</Text>
      </Text>
      <Text style={styles.subHint}>{changeText}</Text>
      <Text style={styles.subSuccess}>BMI {record.bmi}（正常）</Text>
    </Card>
  );
}

// ===== 围度 =====
export function MeasurementCard({
  record,
  onAdd,
  onEdit,
}: {
  record: MeasurementRecord | null;
  onAdd: () => void;
  onEdit: () => void;
}) {
  if (!record) {
    return (
      <EmptyCard title="今日围度" hint="记录腰围、臀围等数据" onAdd={onAdd} />
    );
  }
  return (
    <Card>
      <View style={styles.headerRow}>
        <Text style={styles.cardTitle}>今日围度</Text>
        <EditButton onEdit={onEdit} />
      </View>
      {row('腰围', record.waist, 'cm')}
      {row('臀围', record.hip, 'cm')}
      {row('大腿围', record.thigh, 'cm')}
      {row('上臂围', record.arm, 'cm')}
    </Card>
  );
}

// ===== 睡眠 =====
export function SleepCard({
  record,
  onAdd,
  onEdit,
}: {
  record: SleepRecord | null;
  onAdd: () => void;
  onEdit: () => void;
}) {
  if (!record) {
    return (
      <EmptyCard title="昨晚睡眠" hint="还没有记录昨晚的睡眠" onAdd={onAdd} />
    );
  }
  const h = Math.floor(record.duration / 60);
  const m = record.duration % 60;
  return (
    <Card>
      <View style={styles.headerRow}>
        <Text style={styles.cardTitle}>昨晚睡眠</Text>
        <EditButton onEdit={onEdit} />
      </View>
      <Text style={styles.heroValue}>
        {h}
        <Text style={styles.heroUnit}>小时</Text>
        {m}
        <Text style={styles.heroUnit}>分</Text>
      </Text>
      <Text style={styles.subHint}>
        {record.bedTime} 入睡 → {record.wakeTime} 起床
      </Text>
      <Text style={styles.subHint}>
        睡眠质量：{SLEEP_QUALITY_LABEL[record.quality]}
      </Text>
    </Card>
  );
}

// ===== 运动 =====
export function ExerciseCard({
  record,
  onAdd,
  onEdit,
}: {
  record: ExerciseRecord | null;
  onAdd: () => void;
  onEdit: () => void;
}) {
  if (!record) {
    return (
      <EmptyCard title="今日运动" hint="记录今天的运动情况" onAdd={onAdd} />
    );
  }
  return (
    <Card>
      <View style={styles.headerRow}>
        <Text style={styles.cardTitle}>今日运动</Text>
        <EditButton onEdit={onEdit} />
      </View>
      <Text style={styles.heroValue}>
        {record.type} · {record.duration}
        <Text style={styles.heroUnit}> 分钟</Text>
      </Text>
      <Text style={styles.subHint}>预估消耗 ~{record.calories} kcal</Text>
    </Card>
  );
}

// ===== 饮水（特殊：无 pending，含快捷按钮） =====
export function WaterCard({
  record,
  onAddAmount,
}: {
  record: WaterRecord | null;
  onAddAmount: (amount: number) => void;
}) {
  const r =
    record ?? { amount: 0, target: 2000, id: '', date: '' } as WaterRecord;
  const ratio = r.target > 0 ? r.amount / r.target : 0;
  const reached = ratio >= 1;
  return (
    <Card>
      <View style={styles.headerRow}>
        <Text style={styles.cardTitle}>
          今日饮水{reached ? ' ✓' : ''}
        </Text>
      </View>
      <Text style={styles.heroValue}>
        {r.amount.toLocaleString()}
        <Text style={styles.heroUnit}>
          {' '}
          / {r.target.toLocaleString()} ml
        </Text>
      </Text>
      <View style={{ marginVertical: theme.spacing.sm }}>
        <ProgressBar
          current={r.amount}
          target={r.target}
          color={reached ? theme.colors.success : theme.colors.primary}
          height={10}
        />
      </View>
      {reached && <Text style={styles.subSuccess}>已达标！继续保持 💧</Text>}
      <View style={styles.quickRow}>
        <TouchableOpacity
          style={styles.quickBtn}
          onPress={() => onAddAmount(250)}
          activeOpacity={0.8}
        >
          <Text style={styles.quickBtnText}>+250ml</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.quickBtn}
          onPress={() => onAddAmount(500)}
          activeOpacity={0.8}
        >
          <Text style={styles.quickBtnText}>+500ml</Text>
        </TouchableOpacity>
      </View>
    </Card>
  );
}

// ===== 排便 =====
export function BowelCard({
  record,
  onAdd,
  onEdit,
}: {
  record: BowelRecord | null;
  onAdd: () => void;
  onEdit: () => void;
}) {
  if (!record) {
    return (
      <EmptyCard title="今日排便" hint="记录今天的排便情况" onAdd={onAdd} />
    );
  }
  return (
    <Card>
      <View style={styles.headerRow}>
        <Text style={styles.cardTitle}>今日排便</Text>
        <EditButton onEdit={onEdit} />
      </View>
      <Text style={styles.heroValue}>
        {record.time} · {BOWEL_STATUS_LABEL[record.status]}
      </Text>
    </Card>
  );
}

function row(label: string, value: number | undefined, unit: string) {
  return (
    <View style={styles.kvRow}>
      <Text style={styles.kvLabel}>{label}</Text>
      <Text style={styles.kvValue}>
        {value != null ? value : '--'}
        <Text style={styles.kvUnit}> {unit}</Text>
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  cardTitle: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  heroValue: {
    fontSize: 32,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.xs,
  },
  heroUnit: {
    ...theme.typography.bodySm,
    fontWeight: '400',
    color: theme.colors.textSecondary,
  },
  subHint: {
    ...theme.typography.bodySm,
    color: theme.colors.warning,
    marginTop: 2,
  },
  subSuccess: {
    ...theme.typography.caption,
    color: theme.colors.success,
    marginTop: 2,
  },
  emptyHint: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
    marginTop: theme.spacing.xs,
    marginBottom: theme.spacing.md,
  },
  addBtn: {
    alignSelf: 'flex-start',
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.primary,
  },
  addBtnText: {
    ...theme.typography.bodySm,
    color: theme.colors.bgCard,
    fontWeight: '600',
  },
  editBtn: {
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.md,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.colors.divider,
  },
  editBtnText: {
    ...theme.typography.caption,
    color: theme.colors.textPrimary,
  },
  kvRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
  },
  kvLabel: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
  kvValue: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  kvUnit: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    fontWeight: '400',
  },
  quickRow: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.sm,
  },
  quickBtn: {
    flex: 1,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.colors.primary,
    alignItems: 'center',
    backgroundColor: theme.colors.primaryLight,
  },
  quickBtnText: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
    fontWeight: '600',
  },
});
