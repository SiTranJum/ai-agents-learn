import React from 'react';
import { Dimensions } from 'react-native';
import { BarChart as RNBarChart } from 'react-native-chart-kit';
import { colors } from '@app/styles/tokens';

interface BarChartProps {
  data: {
    labels: string[];
    datasets: Array<{
      data: number[];
    }>;
  };
  width?: number;
  height?: number;
}

/**
 * 柱状图组件
 * 封装 react-native-chart-kit 的 BarChart
 * 用于展示对比数据（如每日热量对比、营养素摄入对比等）
 */
export const BarChart: React.FC<BarChartProps> = ({
  data,
  width = Dimensions.get('window').width - 32,
  height = 220,
}) => {
  return (
    <RNBarChart
      data={data}
      width={width}
      height={height}
      yAxisLabel=""
      yAxisSuffix=""
      chartConfig={{
        backgroundColor: 'transparent',
        backgroundGradientFrom: '#FFFFFF',
        backgroundGradientTo: '#FFFFFF',
        decimalPlaces: 0,
        color: (opacity = 1) => colors.primary,
        labelColor: (opacity = 1) => colors.textSecondary,
        style: {
          borderRadius: 16,
        },
        barPercentage: 0.6, // 柱子宽度占比
        propsForBackgroundLines: {
          stroke: '#EEEEEE',
        },
      }}
      style={{
        borderRadius: 16,
      }}
    />
  );
};
