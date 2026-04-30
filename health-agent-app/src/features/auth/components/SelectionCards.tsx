// SelectionCards - 通用单选卡片（性别 / 活动量 / 目标 / 饮食偏好等）
// 参考: docs/specs/frontend/modules/10-auth-module.md §GenderSelector / ActivityLevelSelector

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

export interface SelectionCardOption<T extends string> {
  value: T;
  label: string;
  description?: string;
}

export interface SelectionCardsProps<T extends string> {
  label?: string;
  value: T | null | undefined;
  onChange: (value: T) => void;
  options: SelectionCardOption<T>[];
  columns?: 1 | 2;
  error?: string;
}

export function SelectionCards<T extends string>({
  label,
  value,
  onChange,
  options,
  columns = 2,
  error,
}: SelectionCardsProps<T>) {
  return (
    <View style={styles.container}>
      {label && <Text style={styles.label}>{label}</Text>}
      <View style={[styles.grid, columns === 1 && styles.gridSingle]}>
        {options.map((opt) => {
          const isSelected = value === opt.value;
          return (
            <TouchableOpacity
              key={opt.value}
              style={[
                styles.card,
                columns === 2 ? styles.cardHalf : styles.cardFull,
                isSelected && styles.cardSelected,
              ]}
              onPress={() => onChange(opt.value)}
              activeOpacity={0.8}
            >
              <Text
                style={[styles.cardLabel, isSelected && styles.cardLabelSelected]}
              >
                {opt.label}
              </Text>
              {opt.description && (
                <Text
                  style={[
                    styles.cardDesc,
                    isSelected && styles.cardDescSelected,
                  ]}
                >
                  {opt.description}
                </Text>
              )}
            </TouchableOpacity>
          );
        })}
      </View>
      {error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: theme.spacing.lg,
  },
  label: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.md,
  },
  gridSingle: {
    flexDirection: 'column',
  },
  card: {
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    borderWidth: 1.5,
    borderColor: '#EEEEEE',
    padding: theme.spacing.lg,
    minHeight: 56,
    justifyContent: 'center',
  },
  cardHalf: {
    flexBasis: '47%',
    flexGrow: 1,
  },
  cardFull: {
    width: '100%',
  },
  cardSelected: {
    borderColor: theme.colors.primary,
    backgroundColor: theme.colors.primaryLight,
  },
  cardLabel: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    fontWeight: '500',
  },
  cardLabelSelected: {
    color: theme.colors.primary,
    fontWeight: '600',
  },
  cardDesc: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginTop: theme.spacing.xs,
  },
  cardDescSelected: {
    color: theme.colors.primary,
  },
  errorText: {
    ...theme.typography.caption,
    color: theme.colors.error,
    marginTop: theme.spacing.xs,
  },
});
