import type { WeightRecord } from '../types/data.types';

export const BMI_CATEGORY_LABEL: Record<NonNullable<WeightRecord['bmiCategory']>, string> = {
  underweight: '偏瘦',
  normal: '正常',
  overweight: '超重',
  obese: '肥胖',
};

export const METRIC_SOURCE_LABEL = {
  manual: '手动',
  estimated: '估算',
} as const;
