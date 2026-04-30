import React from 'react';
import { Dimensions } from 'react-native';
import { PieChart as RNPieChart } from 'react-native-chart-kit';
import { colors } from '@app/styles/tokens';

interface PieChartProps {
  data: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  size?: number;
}

/**
 * 饼图组件
 * 封装 react-native-chart-kit 的 PieChart
 * 用于营养素分布展示（如蛋白质/碳水/脂肪占比）
 */
export const PieChart: React.FC<PieChartProps> = ({
  data,
  size = Dimensions.get('window').width - 32,
}) => {
  // 将 props 数据格式转换为 react-native-chart-kit 需要的格式
  const chartData = data.map((item) => ({
    name: item.name,
    population: item.value, // react-native-chart-kit 使用 population 字段
    color: item.color,
    legendFontColor: colors.textSecondary,
    legendFontSize: 13,
  }));

  return (
    <RNPieChart
      data={chartData}
      width={size}
      height={size * 0.6} // 高度为宽度的 60%，留出图例空间
      chartConfig={{
        color: (opacity = 1) => colors.textPrimary,
      }}
      accessor="population"
      backgroundColor="transparent"
      paddingLeft="15"
      absolute // 显示绝对值而非百分比
    />
  );
};
