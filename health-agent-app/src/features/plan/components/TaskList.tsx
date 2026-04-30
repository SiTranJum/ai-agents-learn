// TaskList - 计划任务列表（可勾选）
// 参考: docs/prd/v1/ui-design/09-plan-detail-page.md §3, §6

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card } from '@shared/ui/Card';
import { theme } from '@app/styles/theme';
import type { PlanTask } from '../types/plan.types';

export interface TaskListProps {
  tasks: PlanTask[];
  /** 只读模式（已暂停 / 已完成 时） */
  readonly?: boolean;
  onToggle?: (taskId: string) => void;
}

export function TaskList({ tasks, readonly = false, onToggle }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <Card>
        <Text style={styles.empty}>暂无任务</Text>
      </Card>
    );
  }

  return (
    <Card style={styles.card}>
      {tasks.map((t, idx) => (
        <TouchableOpacity
          key={t.id}
          style={[styles.row, idx === tasks.length - 1 && styles.rowLast]}
          onPress={() => !readonly && onToggle?.(t.id)}
          activeOpacity={readonly ? 1 : 0.6}
          disabled={readonly}
        >
          <View
            style={[
              styles.checkbox,
              t.completed && styles.checkboxChecked,
            ]}
          >
            {t.completed && (
              <Feather name="check" size={14} color={theme.colors.bgCard} />
            )}
          </View>
          <Text
            style={[
              styles.text,
              t.completed && styles.textChecked,
              readonly && styles.textReadonly,
            ]}
          >
            {t.text}
          </Text>
        </TouchableOpacity>
      ))}
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 0,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
    gap: theme.spacing.md,
  },
  rowLast: {
    borderBottomWidth: 0,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: theme.colors.divider,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxChecked: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
  text: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    flex: 1,
  },
  textChecked: {
    color: theme.colors.textTertiary,
    textDecorationLine: 'line-through',
  },
  textReadonly: {
    color: theme.colors.textSecondary,
  },
  empty: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
    textAlign: 'center',
    paddingVertical: theme.spacing.lg,
  },
});
