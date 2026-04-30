import React from 'react';
import { View, StyleSheet } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { colors } from '@app/styles/tokens';

export interface CircularProgressProps {
  current: number;
  target: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
}

export function CircularProgress({
  current,
  target,
  size = 120,
  strokeWidth = 12,
  color = colors.primary,
}: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(current / target, 1);
  const strokeDashoffset = circumference * (1 - progress);

  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Svg width={size} height={size}>
        {/* 背景圆环 */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={colors.divider}
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* 进度圆环 */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
