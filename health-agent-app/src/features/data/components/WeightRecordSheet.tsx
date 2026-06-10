import React, { useEffect, useMemo, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { theme } from '@app/styles/theme';
import { BottomSheet } from '@shared/feedback/BottomSheet';
import { Button } from '@shared/ui/Button';
import { DatePicker } from '@shared/forms/DatePicker';
import { RulerPicker } from '@shared/forms/RulerPicker';
import { TextInput } from '@shared/forms/TextInput';
import { formatDate, formatFriendlyDate, parseLocalDate, todayStr } from '@shared/utils/date';

import type { WeightRecord } from '../types/data.types';
import { BMI_CATEGORY_LABEL, METRIC_SOURCE_LABEL } from '../utils/weightMetrics';

interface WeightRecordSheetProps {
  visible: boolean;
  record: WeightRecord | null;
  fallbackWeight?: number;
  isSaving?: boolean;
  onClose: () => void;
  onSave: (record: Partial<WeightRecord>) => Promise<void>;
}

const round1 = (value: number) => Math.round(value * 10) / 10;

export function WeightRecordSheet({
  visible,
  record,
  fallbackWeight,
  isSaving,
  onClose,
  onSave,
}: WeightRecordSheetProps) {
  const baseWeight = record?.weight ?? fallbackWeight ?? 65;
  const [date, setDate] = useState(record?.date ?? todayStr());
  const [weight, setWeight] = useState(round1(baseWeight));
  const [manualMode, setManualMode] = useState(false);
  const [weightText, setWeightText] = useState(String(round1(baseWeight)));
  const [bodyFatRate, setBodyFatRate] = useState(record?.bodyFatRate != null ? String(record.bodyFatRate) : '');
  const [muscleRate, setMuscleRate] = useState(record?.muscleRate != null ? String(record.muscleRate) : '');
  const [note, setNote] = useState(record?.note ?? '');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) return;
    const nextWeight = round1(record?.weight ?? fallbackWeight ?? 65);
    setDate(record?.date ?? todayStr());
    setWeight(nextWeight);
    setWeightText(String(nextWeight));
    setBodyFatRate(record?.bodyFatRate != null && record.bodyFatRateSource === 'manual' ? String(record.bodyFatRate) : '');
    setMuscleRate(record?.muscleRate != null && record.muscleRateSource === 'manual' ? String(record.muscleRate) : '');
    setNote(record?.note ?? '');
    setManualMode(false);
    setError(null);
  }, [visible, record, fallbackWeight]);

  const rulerRange = useMemo(() => {
    const center = record?.weight ?? fallbackWeight ?? weight;
    return {
      min: Math.max(30, Math.floor(center - 20)),
      max: Math.min(300, Math.ceil(center + 20)),
    };
  }, [record?.weight, fallbackWeight, weight]);

  const commitManualWeight = () => {
    const parsed = Number(weightText);
    if (!Number.isFinite(parsed) || parsed < 30 || parsed > 300) {
      setError('体重需在 30-300 kg 之间');
      return;
    }
    setWeight(round1(parsed));
    setWeightText(String(round1(parsed)));
    setManualMode(false);
    setError(null);
  };

  const handleSave = async () => {
    const nextWeight = manualMode ? Number(weightText) : weight;
    if (!Number.isFinite(nextWeight) || nextWeight < 30 || nextWeight > 300) {
      setError('体重需在 30-300 kg 之间');
      return;
    }
    const fat = bodyFatRate.trim() ? Number(bodyFatRate) : undefined;
    const muscle = muscleRate.trim() ? Number(muscleRate) : undefined;
    if (fat !== undefined && (!Number.isFinite(fat) || fat < 3 || fat > 70)) {
      setError('体脂率需在 3-70% 之间');
      return;
    }
    if (muscle !== undefined && (!Number.isFinite(muscle) || muscle < 10 || muscle > 80)) {
      setError('肌肉率需在 10-80% 之间');
      return;
    }

    await onSave({
      id: record?.id,
      date,
      weight: round1(nextWeight),
      bodyFatRate: fat,
      muscleRate: muscle,
      note: note.trim() || undefined,
    });
  };

  const bmiLabel =
    record?.bmi != null
      ? `BMI ${record.bmi}${record.bmiCategory ? ` · ${BMI_CATEGORY_LABEL[record.bmiCategory]}` : ''}`
      : '保存后根据健康档案计算 BMI';

  return (
    <BottomSheet visible={visible} onClose={onClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <View style={styles.headerRow}>
            <Text style={styles.title}>{record ? '修改体重' : '记录体重'}</Text>
            <DatePicker
              value={parseLocalDate(date)}
              onChange={(next) => setDate(formatDate(next))}
              displayFormatter={formatFriendlyDate}
              minYear={2020}
              maxYear={new Date().getFullYear()}
            />
          </View>

          {manualMode ? (
            <View style={styles.manualBlock}>
              <TextInput
                label="体重 (kg)"
                value={weightText}
                onChangeText={setWeightText}
                keyboardType="decimal-pad"
                placeholder="请输入体重"
                error={error ?? undefined}
              />
              <Button variant="secondary" size="medium" onPress={commitManualWeight}>
                完成
              </Button>
            </View>
          ) : (
            <>
              <TouchableOpacity style={styles.valueButton} activeOpacity={0.75} onPress={() => setManualMode(true)}>
                <Text style={styles.weightValue}>
                  {weight.toFixed(1)}
                  <Text style={styles.weightUnit}> kg</Text>
                </Text>
              </TouchableOpacity>
              <RulerPicker
                value={weight}
                min={rulerRange.min}
                max={rulerRange.max}
                step={0.1}
                unit="kg"
                showValue={false}
                onChange={(next) => {
                  setWeight(next);
                  setWeightText(String(next));
                  setError(null);
                }}
                error={error ?? undefined}
              />
            </>
          )}

          <View style={styles.metricStrip}>
            <Text style={styles.metricText}>{bmiLabel}</Text>
            {record?.bodyFatRate != null && (
              <Text style={styles.metricText}>
                体脂 {record.bodyFatRate}% {record.bodyFatRateSource ? `(${METRIC_SOURCE_LABEL[record.bodyFatRateSource]})` : ''}
              </Text>
            )}
            {record?.muscleRate != null && (
              <Text style={styles.metricText}>
                肌肉 {record.muscleRate}% {record.muscleRateSource ? `(${METRIC_SOURCE_LABEL[record.muscleRateSource]})` : ''}
              </Text>
            )}
          </View>

          <View style={styles.grid}>
            <View style={styles.gridItem}>
              <TextInput
                label="体脂率 (%)"
                value={bodyFatRate}
                onChangeText={setBodyFatRate}
                keyboardType="decimal-pad"
                placeholder="可选"
              />
            </View>
            <View style={styles.gridItem}>
              <TextInput
                label="肌肉率 (%)"
                value={muscleRate}
                onChangeText={setMuscleRate}
                keyboardType="decimal-pad"
                placeholder="可选"
              />
            </View>
          </View>

          <TextInput
            label="备注（可选）"
            value={note}
            onChangeText={setNote}
            placeholder="补充信息"
            multiline
            maxLength={100}
          />

          <View style={styles.actions}>
            <View style={styles.actionButton}>
              <Button variant="secondary" size="medium" onPress={onClose}>
                取消
              </Button>
            </View>
            <View style={styles.actionButton}>
              <Button variant="primary" size="medium" loading={isSaving} onPress={handleSave}>
                保存
              </Button>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </BottomSheet>
  );
}

const styles = StyleSheet.create({
  content: {
    maxHeight: 620,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: theme.spacing.md,
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginTop: theme.spacing.sm,
  },
  valueButton: {
    alignItems: 'center',
    paddingVertical: theme.spacing.sm,
  },
  weightValue: {
    fontSize: 42,
    fontWeight: '800',
    color: theme.colors.textPrimary,
    letterSpacing: 0,
  },
  weightUnit: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    fontWeight: '500',
  },
  manualBlock: {
    marginTop: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  metricStrip: {
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.bgPage,
    padding: theme.spacing.md,
    gap: theme.spacing.xs,
    marginBottom: theme.spacing.md,
  },
  metricText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  grid: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  gridItem: {
    flex: 1,
  },
  actions: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginTop: theme.spacing.xs,
    marginBottom: theme.spacing.md,
  },
  actionButton: {
    flex: 1,
  },
});
