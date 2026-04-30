import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

export function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>首页</Text>
      <Text style={styles.subtitle}>Phase 3 实现</Text>
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
    color: theme.colors.textPrimary,
  },
  subtitle: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.sm,
  },
});
