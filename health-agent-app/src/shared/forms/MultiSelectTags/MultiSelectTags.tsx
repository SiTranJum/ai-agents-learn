import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, radius, spacing, typography } from '@app/styles/tokens';

export interface MultiSelectTagsOption {
  label: string;
  value: string;
}

export interface MultiSelectTagsProps {
  label?: string;
  value: string[];
  onChange: (values: string[]) => void;
  options: MultiSelectTagsOption[];
  error?: string;
}

export function MultiSelectTags({
  label,
  value,
  onChange,
  options,
  error,
}: MultiSelectTagsProps) {
  const handleToggle = (optionValue: string) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  return (
    <View style={styles.container}>
      {label && <Text style={styles.label}>{label}</Text>}
      <View style={styles.tagsWrapper}>
        {options.map((option) => {
          const isSelected = value.includes(option.value);
          return (
            <TouchableOpacity
              key={option.value}
              style={[styles.tag, isSelected && styles.tagSelected]}
              onPress={() => handleToggle(option.value)}
              activeOpacity={0.7}
            >
              <Text style={[styles.tagText, isSelected && styles.tagTextSelected]}>
                {option.label}
              </Text>
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
    marginBottom: spacing.lg,
  },
  label: {
    ...typography.bodySm,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  tagsWrapper: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  tag: {
    height: 34,
    paddingHorizontal: spacing.lg,
    borderRadius: 999,
    backgroundColor: colors.bgCard,
    borderWidth: 1,
    borderColor: colors.divider,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tagSelected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  tagText: {
    ...typography.bodySm,
    color: colors.textPrimary,
  },
  tagTextSelected: {
    color: '#FFFFFF',
    fontWeight: '500',
  },
  errorText: {
    ...typography.caption,
    color: colors.error,
    marginTop: spacing.xs,
  },
});
