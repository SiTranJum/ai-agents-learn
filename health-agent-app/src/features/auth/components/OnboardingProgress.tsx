// OnboardingProgress - 引导页进度条
// 参考: docs/specs/frontend/modules/10-auth-module.md §OnboardingProgress

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

export interface OnboardingProgressProps {
  totalSteps: number;
  currentStep: number; // 1-based
  skippedSteps: number[];
}

export function OnboardingProgress({
  totalSteps,
  currentStep,
  skippedSteps,
}: OnboardingProgressProps) {
  return (
    <View style={styles.container}>
      <View style={styles.barRow}>
        {Array.from({ length: totalSteps }).map((_, idx) => {
          const stepNum = idx + 1;
          const isSkipped = skippedSteps.includes(stepNum);
          const isFilled = stepNum <= currentStep && !isSkipped;
          return (
            <View
              key={stepNum}
              style={[
                styles.segment,
                isFilled && styles.segmentFilled,
                isSkipped && styles.segmentSkipped,
              ]}
            />
          );
        })}
      </View>
      <Text style={styles.caption}>
        第 {currentStep} 步，共 {totalSteps} 步
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: theme.spacing.xl,
  },
  barRow: {
    flexDirection: 'row',
    gap: theme.spacing.xs,
    marginBottom: theme.spacing.sm,
  },
  segment: {
    flex: 1,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#F0F0F0',
  },
  segmentFilled: {
    backgroundColor: theme.colors.primary,
  },
  segmentSkipped: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: '#CCCCCC',
  },
  caption: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
});
