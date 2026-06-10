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

import type { WaterRecord } from '../types/data.types';

interface WaterRecordSheetProps {
  visible: boolean;
  record: WaterRecord | null;
  isSaving?: boolean;
  onClose: () => void;
  onSave: (record: Partial<WaterRecord>) => Promise<void>;
}

export function WaterRecordSheet({
  visible,
  record,
  isSaving,
  onClose,
  onSave,
}: WaterRecordSheetProps) {
  const [date, setDate] = useState(record?.date ?? todayStr());
  const [amount, setAmount] = useState(record?.amount != null ? String(record.amount) : '');
  const [target, setTarget] = useState(record?.target != null ? String(record.target) : '2000');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) return;
    setDate(record?.date ?? todayStr());
    setAmount(record?.amount != null ? String(record.amount) : '');
    setTarget(record?.target != null ? String(record.target) : '2000');
    setError(null);
  }, [visible, record]);

  const handleSave = async () => {
    const amountVal = amount.trim() ? Number(amount) : undefined;
    const targetVal = target.trim() ? Number(target) : 2000;

    if (!amountVal) {
      setError('请填写饮水量');
      return;
    }

    if (!Number.isFinite(amountVal) || amountVal < 0 || amountVal > 10000) {
      setError('饮水量需在 0-10000 ml 之间');
      return;
    }

    if (!Number.isFinite(targetVal) || targetVal < 0 || targetVal > 10000) {
      setError('目标量需在 0-10000 ml 之间');
      return;
    }

    await onSave({
      id: record?.id,
      date,
      amount: amountVal,
      target: targetVal,
    });
  };

  return (
    <BottomSheet visible={visible} onClose={onClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <View style={styles.headerRow}>
            <Text style={styles.title}>{record ? '修改饮水' : '记录饮水'}</Text>
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
                label="饮水量 (ml)"
                value={amount}
                onChangeText={setAmount}
                keyboardType="numeric"
                placeholder="必填"
                error={error ?? undefined}
              />
            </View>
            <View style={styles.gridItem}>
              <TextInput
                label="目标量 (ml)"
                value={target}
                onChangeText={setTarget}
                keyboardType="numeric"
                placeholder="2000"
              />
            </View>
          </View>

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
    maxHeight: 400,
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
