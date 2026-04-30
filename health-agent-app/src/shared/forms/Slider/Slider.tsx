import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, radius, spacing, typography } from '@app/styles/tokens';

export interface SliderProps {
  label?: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  unit?: string;
}

export function Slider({
  label,
  value,
  onChange,
  min,
  max,
  step,
  unit = '',
}: SliderProps) {
  const trackRef = React.useRef<View>(null);
  const [trackWidth, setTrackWidth] = React.useState(0);

  const percentage = ((value - min) / (max - min)) * 100;

  const handleTrackPress = (event: any) => {
    const { locationX } = event.nativeEvent;
    if (trackWidth > 0) {
      const ratio = Math.max(0, Math.min(1, locationX / trackWidth));
      const rawValue = min + ratio * (max - min);
      const steppedValue = Math.round(rawValue / step) * step;
      const clampedValue = Math.max(min, Math.min(max, steppedValue));
      onChange(clampedValue);
    }
  };

  return (
    <View style={styles.container}>
      {label && (
        <View style={styles.labelRow}>
          <Text style={styles.label}>{label}</Text>
          <Text style={styles.valueText}>
            {value}
            {unit}
          </Text>
        </View>
      )}
      <View
        ref={trackRef}
        style={styles.track}
        onLayout={(e) => setTrackWidth(e.nativeEvent.layout.width)}
        onStartShouldSetResponder={() => true}
        onResponderRelease={handleTrackPress}
      >
        <View style={[styles.trackFill, { width: `${percentage}%` }]} />
        <View style={[styles.thumb, { left: `${percentage}%` }]} />
      </View>
      <View style={styles.rangeRow}>
        <Text style={styles.rangeText}>
          {min}
          {unit}
        </Text>
        <Text style={styles.rangeText}>
          {max}
          {unit}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.lg,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  label: {
    ...typography.bodySm,
    color: colors.textSecondary,
  },
  valueText: {
    ...typography.body,
    color: colors.primary,
    fontWeight: '600',
  },
  track: {
    height: 6,
    backgroundColor: colors.inputBg,
    borderRadius: 3,
    justifyContent: 'center',
    position: 'relative',
  },
  trackFill: {
    height: 6,
    backgroundColor: colors.primary,
    borderRadius: 3,
    position: 'absolute',
    left: 0,
    top: 0,
  },
  thumb: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.bgCard,
    borderWidth: 3,
    borderColor: colors.primary,
    position: 'absolute',
    top: -8,
    marginLeft: -11,
  },
  rangeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  rangeText: {
    ...typography.caption,
    color: colors.textTertiary,
  },
});
