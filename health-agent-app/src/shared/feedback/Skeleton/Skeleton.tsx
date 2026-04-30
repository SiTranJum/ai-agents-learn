import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { animation } from '@app/styles/tokens';

interface SkeletonProps {
  width: number;
  height: number;
  borderRadius?: number;
}

/**
 * 骨架屏组件
 * 用于内容加载时的占位显示
 * 使用 Animated API 实现 shimmer 脉冲动画
 *
 * Props:
 * - width: 宽度（数字或百分比字符串，如 '100%'）
 * - height: 高度（数字）
 * - borderRadius: 圆角（可选）
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  width,
  height,
  borderRadius = 8,
}) => {
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    // 创建循环动画：opacity 从 0.3 到 1 再回到 0.3
    const pulseAnimation = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: animation.skeletonPulse / 2, // 750ms
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.3,
          duration: animation.skeletonPulse / 2, // 750ms
          useNativeDriver: true,
        }),
      ])
    );

    pulseAnimation.start();

    // 组件卸载时停止动画
    return () => {
      pulseAnimation.stop();
    };
  }, []);

  return (
    <Animated.View
      style={[
        styles.skeleton,
        {
          width,
          height,
          borderRadius,
          opacity,
        },
      ]}
    />
  );
};

const styles = StyleSheet.create({
  skeleton: {
    backgroundColor: '#F0F0F0', // 浅灰背景
  },
});
