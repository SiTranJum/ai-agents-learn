import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Dimensions,
  NativeScrollEvent,
  NativeSyntheticEvent,
} from 'react-native';
import { colors, radius, spacing, typography } from '@app/styles/tokens';

const SCREEN_WIDTH = Dimensions.get('window').width;
const ITEM_WIDTH = 4; // 每个刻度的宽度（紧凑间距）
const SIDE_PADDING = (SCREEN_WIDTH - ITEM_WIDTH) / 2; // 两侧留白，让中心指示器对齐

export interface RulerPickerProps {
  label?: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  error?: string;
}

export function RulerPicker({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  unit = '',
  error,
}: RulerPickerProps) {
  const scrollViewRef = useRef<ScrollView>(null);
  const [currentValue, setCurrentValue] = useState(value);

  // 生成刻度数组（修复浮点数精度问题）
  const values: number[] = [];
  const steps = Math.round((max - min) / step);
  for (let i = 0; i <= steps; i++) {
    const value = min + i * step;
    // 根据 step 决定保留几位小数
    const decimals = step < 1 ? 1 : 0;
    values.push(parseFloat(value.toFixed(decimals)));
  }

  // 滚动到指定值
  const scrollToValue = (val: number) => {
    const index = values.findIndex((v) => v === val);
    if (index !== -1 && scrollViewRef.current) {
      scrollViewRef.current.scrollTo({
        x: index * ITEM_WIDTH,
        animated: true,
      });
    }
  };

  // 初始化时滚动到当前值
  React.useEffect(() => {
    if (value) {
      setTimeout(() => scrollToValue(value), 100);
    }
  }, []);

  // 处理滚动事件
  const handleScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const offsetX = event.nativeEvent.contentOffset.x;
    const index = Math.round(offsetX / ITEM_WIDTH);
    const newValue = values[index];

    if (newValue !== undefined && newValue !== currentValue) {
      setCurrentValue(newValue);
    }
  };

  // 滚动结束时更新值
  const handleScrollEnd = () => {
    if (currentValue !== value) {
      onChange(currentValue);
    }
  };

  return (
    <View style={styles.container}>
      {label && <Text style={styles.label}>{label}</Text>}

      <View style={[styles.rulerContainer, error ? styles.errorBorder : null]}>
        {/* 当前值显示 */}
        <View style={styles.valueDisplay}>
          <Text style={styles.valueText}>
            {currentValue} {unit}
          </Text>
        </View>

        {/* 中心指示器 */}
        <View style={styles.centerIndicator} />

        {/* 滚动刻度尺 */}
        <ScrollView
          ref={scrollViewRef}
          horizontal
          showsHorizontalScrollIndicator={false}
          onScroll={handleScroll}
          onMomentumScrollEnd={handleScrollEnd}
          scrollEventThrottle={16}
          snapToInterval={ITEM_WIDTH}
          decelerationRate="fast"
          contentContainerStyle={{
            paddingHorizontal: SIDE_PADDING,
          }}
        >
          {values.map((val, index) => {
            // 对于小数步长，每 5 个刻度显示一次标签
            // 对于整数步长，每 10 个刻度显示一次标签
            const labelInterval = step < 1 ? 5 : 10;
            const isLabelTick = index % labelInterval === 0;
            const isMediumTick = index % 5 === 0 && !isLabelTick;

            return (
              <View key={index} style={styles.rulerItem}>
                <View
                  style={[
                    styles.tick,
                    isLabelTick && styles.tickLarge,
                    isMediumTick && styles.tickMedium,
                  ]}
                />
                {isLabelTick && (
                  <Text style={styles.tickLabel}>
                    {step < 1 ? val.toFixed(1) : val}
                  </Text>
                )}
              </View>
            );
          })}
        </ScrollView>
      </View>

      {error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.lg,
  },
  label: {
    ...typography.bodySm,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    fontWeight: '600',
  },
  rulerContainer: {
    height: 140,
    backgroundColor: '#FFFFFF',
    borderRadius: radius.lg,
    borderWidth: 2,
    borderColor: colors.divider,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  errorBorder: {
    borderColor: colors.error,
  },
  errorText: {
    ...typography.caption,
    color: colors.error,
    marginTop: spacing.xs,
  },
  valueDisplay: {
    position: 'absolute',
    top: spacing.lg,
    left: 0,
    right: 0,
    alignItems: 'center',
    zIndex: 10,
  },
  valueText: {
    fontSize: 36,
    color: colors.primary,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  centerIndicator: {
    position: 'absolute',
    top: 70,
    left: SCREEN_WIDTH / 2 - 2,
    width: 4,
    height: 50,
    backgroundColor: colors.primary,
    borderRadius: 2,
    zIndex: 5,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  rulerItem: {
    width: ITEM_WIDTH,
    height: 90,
    justifyContent: 'flex-end',
    alignItems: 'center',
    marginTop: 70,
  },
  tick: {
    width: 1.5,
    height: 30,
    backgroundColor: colors.divider,
    borderRadius: 1,
  },
  tickMedium: {
    height: 31,
    backgroundColor: colors.textTertiary,
    width: 2,
  },
  tickLarge: {
    height: 32,
    backgroundColor: colors.textSecondary,
    width: 2.5,
  },
  tickLabel: {
    ...typography.caption,
    color: colors.textPrimary,
    marginTop: spacing.xs,
    fontWeight: '600',
    fontSize: 13,
  },
});

