import React from 'react';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import { colors } from '@app/styles/tokens';

interface LoadingSpinnerProps {
  size?: 'small' | 'large';
  color?: string;
}

/**
 * 加载指示器组件
 * 封装 React Native 内置 ActivityIndicator
 * 默认使用品牌色
 *
 * Props:
 * - size: 尺寸，'small' 或 'large'
 * - color: 自定义颜色（默认品牌色）
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'small',
  color = colors.primary,
}) => {
  return (
    <View style={styles.container}>
      <ActivityIndicator size={size} color={color} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
  },
});
