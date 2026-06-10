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

import type { BowelRecord } from '../types/data.types';

interface BowelRecordSheetProps {
  visible: boolean;
  record: BowelRecord | null;
  isSaving?: boolean;
  onClose: () => void;
  onSave: (record: Partial<BowelRecord>) => Promise<void>;
}

const STATUS_OPTIONS = [
  { label: '正常', value: 'normal' },
  { label: '便秘', value: 'constipation' },
  { label: '腹泻', value: 'diarrhea' },
];

export function BowelRecordSheet({
  visible,
  record,
  isSaving,
  onClose,
  onSave,
}: BowelRecordSheetProps) {
  const [date, setDate] = useState(record?.date ?? todayStr());
  const [time, setTime] = useState(record?.time ?? '08:00');
  const [status, setStatus] = useState(record?.status ?? 'normal');
  const [note, setNote] = useState(record?.note ?? '');
  const [showNote, setShowNote] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) return;
    setDate(record?.date ?? todayStr());
    setTime(record?.time ?? '08:00');
    setStatus(record?.status ?? 'normal');
    setNote(record?.note ?? '');
    setShowNote(false);
    setError(null);
  }, [visible, record]);

  const handleSave = async () => {
    if (!time) {
      setError('请填写时间');
      return;
    }

    // 简单验证时间格式 HH:MM
    const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;
    if (!timeRegex.test(time)) {
      setError('时间格式错误，应为 HH:MM');
      return;
    }

    await onSave({
      id: record?.id,
      date,
      time,
      status: status as 'normal' | 'constipation' | 'diarrhea',
      note: note.trim() || undefined,
    });
  };

  return (
    <BottomSheet visible={visible} onClose={onClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <View style={styles.headerRow}>
            <Text style={styles.title}>{record ? '修改排便' : '记录排便'}</Text>
            <DatePicker
              value={parseLocalDate(date)}
              onChange={(next) => setDate(formatDate(next))}
              displayFormatter={formatFriendlyDate}
              minYear={2020}
              maxYear={new Date().getFullYear()}
            />
          </View>

          <TextInput
            label="时间"
            value={time}
            onChangeText={setTime}
            placeholder="08:00"
            error={error ?? undefined}
          />

          <View style={styles.statusSection}>
            <Text style={styles.statusLabel}>状态</Text>
            <View style={styles.statusOptions}>
              {STATUS_OPTIONS.map((opt) => (
                <TouchableOpacity
                  key={opt.value}
                  style={[
                    styles.statusOption,
                    status === opt.value && styles.statusOptionActive,
                  ]}
                  onPress={() => setStatus(opt.value)}
                >
                  <Text
                    style={[
                      styles.statusOptionText,
                      status === opt.value && styles.statusOptionTextActive,
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
    maxHeight: 450,
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
  statusSection: {
    marginBottom: theme.spacing.md,
  },
  statusLabel: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
  },
  statusOptions: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  statusOption: {
    flex: 1,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.xs,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.bgCard,
    alignItems: 'center',
  },
  statusOptionActive: {
    borderColor: theme.colors.primary,
    backgroundColor: theme.colors.primaryLight,
  },
  statusOptionText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  statusOptionTextActive: {
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
