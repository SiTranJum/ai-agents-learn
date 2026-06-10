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

import type { SleepRecord } from '../types/data.types';

interface SleepRecordSheetProps {
  visible: boolean;
  record: SleepRecord | null;
  isSaving?: boolean;
  onClose: () => void;
  onSave: (record: Partial<SleepRecord>) => Promise<void>;
}

const QUALITY_OPTIONS = [
  { label: '很好', value: 'excellent' },
  { label: '良好', value: 'good' },
  { label: '一般', value: 'fair' },
  { label: '较差', value: 'poor' },
];

export function SleepRecordSheet({
  visible,
  record,
  isSaving,
  onClose,
  onSave,
}: SleepRecordSheetProps) {
  const [date, setDate] = useState(record?.date ?? todayStr());
  const [bedTime, setBedTime] = useState(record?.bedTime ?? '23:00');
  const [wakeTime, setWakeTime] = useState(record?.wakeTime ?? '07:00');
  const [quality, setQuality] = useState(record?.quality ?? 'good');
  const [note, setNote] = useState(record?.note ?? '');
  const [showNote, setShowNote] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) return;
    setDate(record?.date ?? todayStr());
    setBedTime(record?.bedTime ?? '23:00');
    setWakeTime(record?.wakeTime ?? '07:00');
    setQuality(record?.quality ?? 'good');
    setNote(record?.note ?? '');
    setShowNote(false);
    setError(null);
  }, [visible, record]);

  const handleSave = async () => {
    if (!bedTime || !wakeTime) {
      setError('请填写入睡和起床时间');
      return;
    }

    // 简单验证时间格式 HH:MM
    const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;
    if (!timeRegex.test(bedTime)) {
      setError('入睡时间格式错误，应为 HH:MM');
      return;
    }
    if (!timeRegex.test(wakeTime)) {
      setError('起床时间格式错误，应为 HH:MM');
      return;
    }

    await onSave({
      id: record?.id,
      date,
      bedTime,
      wakeTime,
      quality: quality as 'excellent' | 'good' | 'fair' | 'poor',
      note: note.trim() || undefined,
    });
  };

  return (
    <BottomSheet visible={visible} onClose={onClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <View style={styles.headerRow}>
            <Text style={styles.title}>{record ? '修改睡眠' : '记录睡眠'}</Text>
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
                label="入睡时间"
                value={bedTime}
                onChangeText={setBedTime}
                placeholder="23:00"
                error={error ?? undefined}
              />
            </View>
            <View style={styles.gridItem}>
              <TextInput
                label="起床时间"
                value={wakeTime}
                onChangeText={setWakeTime}
                placeholder="07:00"
              />
            </View>
          </View>

          <View style={styles.qualitySection}>
            <Text style={styles.qualityLabel}>睡眠质量</Text>
            <View style={styles.qualityOptions}>
              {QUALITY_OPTIONS.map((opt) => (
                <TouchableOpacity
                  key={opt.value}
                  style={[
                    styles.qualityOption,
                    quality === opt.value && styles.qualityOptionActive,
                  ]}
                  onPress={() => setQuality(opt.value)}
                >
                  <Text
                    style={[
                      styles.qualityOptionText,
                      quality === opt.value && styles.qualityOptionTextActive,
                    ]}
                  >
                    {opt.label}
                  </Text>
                </TouchableOpacity>
              ))}
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
  qualitySection: {
    marginBottom: theme.spacing.md,
  },
  qualityLabel: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
  },
  qualityOptions: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  qualityOption: {
    flex: 1,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.xs,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.bgCard,
    alignItems: 'center',
  },
  qualityOptionActive: {
    borderColor: theme.colors.primary,
    backgroundColor: theme.colors.primaryLight,
  },
  qualityOptionText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  qualityOptionTextActive: {
    color: theme.colors.primary,
    fontWeight: '600',
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
