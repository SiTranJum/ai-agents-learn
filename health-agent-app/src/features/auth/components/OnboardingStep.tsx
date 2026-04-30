// OnboardingStep - 单步表单容器
// 参考: docs/specs/frontend/modules/10-auth-module.md §OnboardingStep

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

export interface OnboardingStepProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}

export function OnboardingStep({ title, subtitle, children }: OnboardingStepProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
      <View style={styles.content}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  title: {
    ...theme.typography.pageTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.xs,
  },
  subtitle: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xl,
  },
  content: {
    flex: 1,
  },
});
