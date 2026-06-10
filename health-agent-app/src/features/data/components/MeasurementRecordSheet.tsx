import React, { useEffect, useState } from 'react';
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
import { TextInput } from '@shared/forms/TextInput';
import { formatDate, formatFriendlyDate, parseLocalDate, todayStr } from '@shared/utils/date';

import type { MeasurementRecord } from '../types/data.types';

interface MeasurementRecordSheetProps {
  visible: boolean;
  record: MeasurementRecord | null;
  isSaving?: boolean;
  onClose: () => void;
  onSave: (record: Partial<MeasurementRecord>) => Promise<void>;
}

export function MeasurementRecordSheet({
  visible,
  record,
  isSaving,
  onClose,
  onSave,
}: MeasurementRecordSheetProps) {
  const [date, setDate] = useState(record?.date ?? todayStr());
  const [waist, setWaist] = useState(record?.waist != null ? String(record.waist) : '');
  const [hip, setHip] = useState(record?.hip != null ? String(record.hip) : '');
  const [thigh, setThigh] = useState(record?.thigh != null ? String(record.thigh) : '');
  const [arm, setArm] = useState(record?.arm != null ? String(record.arm) : '');
  const [note, setNote] = useState(record?.note ?? '');
  const [showNote, setShowNote] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) return;
    setDate(record?.date ?? todayStr());
    setWaist(record?.waist != null ? String(record.waist) : '');
    setHip(record?.hip != null ? String(record.hip) : '');
    setThigh(record?.thigh != null ? String(record.thigh) : '');
    setArm(record?.arm != null ? String(record.arm) : '');
    setNote(record?.note ?? '');
    setShowNote(false);
    setError(null);
  }, [visible, record]);

  const handleSave = async () => {
    const waistVal = waist.trim() ? Number(waist) : undefined;
    const hipVal = hip.trim() ? Number(hip) : undefined;
    const thighVal = thigh.trim() ? Number(thigh) : undefined;
    const armVal = arm.trim() ? Number(arm) : undefined;

    if (!waistVal && !hipVal && !thighVal && !armVal) {
      setError('请至少填写一项围度数据');
      return;
    }

    if (waistVal !== undefined && (!Number.isFinite(waistVal) || waistVal < 30 || waistVal > 200)) {
      setError('腰围需在 30-200 cm 之间');
      return;
    }
    if (hipVal !== undefined && (!Number.isFinite(hipVal) || hipVal < 30 || hipVal > 200)) {
      setError('臀围需在 30-200 cm 之间');
      return;
    }
    if (thighVal !== undefined && (!Number.isFinite(thighVal) || thighVal < 20 || thighVal > 150)) {
      setError('大腿围需在 20-150 cm 之间');
      return;
    }
    if (armVal !== undefined && (!Number.isFinite(armVal) || armVal < 10 || armVal > 100)) {
      setError('臂围需在 10-100 cm 之间');
      return;
    }

    await onSave({
      id: record?.id,
      date,
      waist: waistVal,
      hip: hipVal,
      thigh: thighVal,
      arm: armVal,
      note: note.trim() || undefined,
    });
  };

  return (
    <BottomSheet visible={visible} onClose={onClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <View style={styles.headerRow}>
            <Text style={styles.title}>{record ? '修改围度' : '记录围度'}</Text>
            <DatePicker
              value={parseLocalDate(date)}
              onChange={(next) => setDate(formatDate(next))}
              displayFormatter={formatFriendlyDate}
              minYear={2020}
              maxYear={new Date().getFullYear()}
            />
          </View>

          <View style={styles.grid}>
            <View style={styles.gridItem}>
              <TextInput
                label="腰围 (cm)"
                value={waist}
                onChangeText={setWaist}
                keyboardType="decimal-pad"
                placeholder="可选"
                error={error ?? undefined}
              />
            </View>
            <View style={styles.gridItem}>
              <TextInput
                label="臀围 (cm)"
                value={hip}
                onChangeText={setHip}
                keyboardType="decimal-pad"
                placeholder="可选"
              />
            </View>
          </View>

          <View style={styles.grid}>
            <View style={styles.gridItem}>
              <TextInput
                label="大腿围 (cm)"
                value={thigh}
                onChangeText={setThigh}
                keyboardType="decimal-pad"
                placeholder="可选"
              />
            </View>
            <View style={styles.gridItem}>
              <TextInput
                label="臂围 (cm)"
                value={arm}
                onChangeText={setArm}
                keyboardType="decimal-pad"
                placeholder="可选"
              />
            </View>
          </View>

          {!showNote ? (
            <TouchableOpacity style={styles.addNoteButton} onPress={() => setShowNote(true)}>
              <Text style={styles.addNoteText}>+ 添加备注</Text>
            </TouchableOpacity>
          ) : (
            <TextInput
              label="备注（可选）"
              value={note}
              onChangeText={setNote}
              placeholder="补充信息"
              multiline
              maxLength={100}
            />
          )}

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
    maxHeight: 480,
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
  grid: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  gridItem: {
    flex: 1,
  },
  addNoteButton: {
    paddingVertical: theme.spacing.md,
    alignItems: 'center',
  },
  addNoteText: {
    ...theme.typography.body,
    color: theme.colors.primary,
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
