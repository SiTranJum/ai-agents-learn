import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { spacing } from '@app/styles/tokens';

export interface SectionBlockProps {
  children: React.ReactNode;
  style?: ViewStyle;
  spacing?: 'none' | 'sm' | 'md' | 'lg';
}

export function SectionBlock({ children, style, spacing: gap = 'md' }: SectionBlockProps) {
  const gapValue = gap === 'none' ? 0 : gap === 'sm' ? spacing.sm : gap === 'md' ? spacing.md : spacing.lg;

  return <View style={[styles.container, { gap: gapValue }, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
});
