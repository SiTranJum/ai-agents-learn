import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

export function LoginScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>健康管家</Text>
      <Text style={styles.subtitle}>登录页面 - Phase 2 实现</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.bgPage,
  },
  title: {
    ...theme.typography.pageTitle,
    color: theme.colors.primary,
    marginBottom: theme.spacing.md,
  },
  subtitle: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
});
