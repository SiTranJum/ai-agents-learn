import React from 'react';
import { Dimensions } from 'react-native';
import { LineChart as RNLineChart } from 'react-native-chart-kit';
import { colors } from '@app/styles/tokens';

interface LineChartProps {
  data: {
    labels: string[];
    datasets: Array<{
      data: number[];
      color?: (opacity: number) => string;
    }>;
  };
  width?: number;
  height?: number;
}

/**
 * 折线图组件
 * 封装 react-native-chart-kit 的 LineChart
 * 用于展示趋势数据（如体重变化、热量摄入趋势等）
 */
export const LineChart: React.FC<LineChartProps> = ({
  data,
  width = Dimensions.get('window').width - 32, // 默认屏宽减去左右边距
  height = 220,
}) => {
  return (
    <RNLineChart
      data={data}
      width={width}
      height={height}
      chartConfig={{
        backgroundColor: 'transparent',
        backgroundGradientFrom: '#FFFFFF',
        backgroundGradientTo: '#FFFFFF',
        decimalPlaces: 1, // 小数点位数
        color: (opacity = 1) => colors.primary, // 数据线颜色（品牌色）
        labelColor: (opacity = 1) => colors.textSecondary, // 标签颜色
        style: {
          borderRadius: 16,
        },
        propsForDots: {
          r: '4', // 数据点半径 4px
          strokeWidth: '2',
          stroke: colors.primary,
        },
        propsForBackgroundLines: {
          stroke: '#EEEEEE', // 网格线颜色
        },
      }}
      bezier // 使用贝塞尔曲线平滑折线
      style={{
        borderRadius: 16,
      }}
    />
  );
};
