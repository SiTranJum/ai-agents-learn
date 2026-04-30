import React from 'react';
import { View, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

export interface ProgressBarProps {
  current: number;
  target: number;
  color?: string;
  height?: number;
}

export function ProgressBar({
  current,
  target,
  color = theme.colors.primary,
  height = 10,
}: ProgressBarProps) {
  const progress = target > 0 ? Math.min(current / target, 1) : 0;

  return (
    <View style={[styles.track, { height }]}>
      <View
        style={[
          styles.fill,
          { width: `${progress * 100}%`, backgroundColor: color, height },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    backgroundColor: '#F0F0F0',
    borderRadius: theme.radius.full,
    overflow: 'hidden',
    width: '100%',
  },
  fill: {
    borderRadius: theme.radius.full,
  },
});
