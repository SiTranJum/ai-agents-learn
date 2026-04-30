import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

interface PlaceholderScreenProps {
  route?: {
    name?: string;
  };
}

export function PlaceholderScreen({ route }: PlaceholderScreenProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{route?.name ?? '页面'}</Text>
      <Text style={styles.subtitle}>占位页面，后续在对应 Phase 中实现</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.bgPage,
    padding: theme.spacing.lg,
  },
  title: {
    ...theme.typography.pageTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
  },
  subtitle: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
});
