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

import type { ExerciseRecord } from '../types/data.types';

interface ExerciseRecordSheetProps {
  visible: boolean;
  record: ExerciseRecord | null;
  isSaving?: boolean;
  onClose: () => void;
  onSave: (record: Partial<ExerciseRecord>) => Promise<void>;
}

export function ExerciseRecordSheet({
  visible,
  record,
  isSaving,
  onClose,
  onSave,
}: ExerciseRecordSheetProps) {
  const [date, setDate] = useState(record?.date ?? todayStr());
  const [exerciseType, setExerciseType] = useState(record?.type ?? '');
  const [duration, setDuration] = useState(record?.duration != null ? String(record.duration) : '');
  const [calories, setCalories] = useState(record?.calories != null ? String(record.calories) : '');
  const [note, setNote] = useState(record?.note ?? '');
  const [showNote, setShowNote] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) return;
    setDate(record?.date ?? todayStr());
    setExerciseType(record?.type ?? '');
    setDuration(record?.duration != null ? String(record.duration) : '');
    setCalories(record?.calories != null ? String(record.calories) : '');
    setNote(record?.note ?? '');
    setShowNote(false);
    setError(null);
  }, [visible, record]);

  const handleSave = async () => {
    if (!exerciseType.trim()) {
      setError('请填写运动类型');
      return;
    }

    const durationVal = duration.trim() ? Number(duration) : undefined;
    const caloriesVal = calories.trim() ? Number(calories) : undefined;

    if (!durationVal) {
      setError('请填写运动时长');
      return;
    }

    if (!Number.isFinite(durationVal) || durationVal < 1 || durationVal > 1440) {
      setError('运动时长需在 1-1440 分钟之间');
      return;
    }

    if (caloriesVal !== undefined && (!Number.isFinite(caloriesVal) || caloriesVal < 0 || caloriesVal > 5000)) {
      setError('消耗卡路里需在 0-5000 之间');
      return;
    }

    await onSave({
      id: record?.id,
      date,
      type: exerciseType.trim(),
      duration: durationVal,
      calories: caloriesVal ?? 0,
      note: note.trim() || undefined,
    });
  };

  return (
    <BottomSheet visible={visible} onClose={onClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <View style={styles.headerRow}>
            <Text style={styles.title}>{record ? '修改运动' : '记录运动'}</Text>
            <DatePicker
              value={parseLocalDate(date)}
              onChange={(next) => setDate(formatDate(next))}
              displayFormatter={formatFriendlyDate}
              minYear={2020}
              maxYear={new Date().getFullYear()}
            />
          </View>

          <TextInput
            label="运动类型"
            value={exerciseType}
            onChangeText={setExerciseType}
            placeholder="如：跑步、游泳、力量训练"
            error={error ?? undefined}
          />

          <View style={styles.grid}>
            <View style={styles.gridItem}>
              <TextInput
                label="时长 (分钟)"
                value={duration}
                onChangeText={setDuration}
                keyboardType="numeric"
                placeholder="必填"
              />
            </View>
            <View style={styles.gridItem}>
              <TextInput
                label="消耗卡路里"
                value={calories}
                onChangeText={setCalories}
                keyboardType="numeric"
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
