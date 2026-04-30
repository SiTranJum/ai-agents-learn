import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

export interface TagProps {
  label: string;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'small' | 'medium';
}

const variantColors = {
  default: { bg: theme.colors.primaryLight, text: theme.colors.primary },
  success: { bg: '#E8F9ED', text: theme.colors.success },
  warning: { bg: '#FFF5E0', text: '#E6A800' },
  error: { bg: '#FFE8E8', text: theme.colors.error },
  info: { bg: '#E8F6FF', text: theme.colors.info },
};

export function Tag({ label, variant = 'default', size = 'small' }: TagProps) {
  const colors = variantColors[variant];
  return (
    <View style={[styles.tag, { backgroundColor: colors.bg }, size === 'medium' && styles.medium]}>
      <Text style={[styles.text, { color: colors.text }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  tag: {
    height: 24,
    borderRadius: theme.radius.full,
    paddingHorizontal: 10,
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'flex-start',
  },
  medium: { height: 32, paddingHorizontal: 14 },
  text: { ...theme.typography.tag },
});
