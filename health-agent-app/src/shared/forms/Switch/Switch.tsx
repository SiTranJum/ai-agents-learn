import React from 'react';
import { View, Text, Switch as RNSwitch, StyleSheet } from 'react-native';
import { colors, spacing, typography } from '@app/styles/tokens';

export interface SwitchProps {
  label?: string;
  value: boolean;
  onChange: (value: boolean) => void;
  description?: string;
}

export function Switch({ label, value, onChange, description }: SwitchProps) {
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.textContainer}>
          {label && <Text style={styles.label}>{label}</Text>}
          {description && <Text style={styles.description}>{description}</Text>}
        </View>
        <RNSwitch
          value={value}
          onValueChange={onChange}
          trackColor={{ false: colors.divider, true: colors.primary }}
          thumbColor={colors.bgCard}
          ios_backgroundColor={colors.divider}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.lg,
  },
  content: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  textContainer: {
    flex: 1,
    marginRight: spacing.md,
  },
  label: {
    ...typography.body,
    color: colors.textPrimary,
  },
  description: {
    ...typography.caption,
    color: colors.textSecondary,
  },
});
