// FoodItemRow - 食物编辑行
// 食物名称 + 份量 + 单位 + 热量显示 + 删除按钮
// 食物名称带搜索候选浮层
// 参考: docs/prd/v1/ui-design/05-diet-edit-page.md §3, §4.1

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { TextInput } from '@shared/forms/TextInput';
import { Picker } from '@shared/forms/Picker';
import { theme } from '@app/styles/theme';
import type { FoodCandidate, FoodItem } from '../types/diet.types';
import { FoodSearchModal } from './FoodSearchModal';
import { useFoodSearch } from '../hooks/useFoodSearch';

const UNIT_OPTIONS = [
  { label: '克 (g)', value: 'g' },
  { label: '碗', value: '碗' },
  { label: '个', value: '个' },
  { label: '片', value: '片' },
  { label: '杯', value: '杯' },
  { label: '勺', value: '勺' },
  { label: '份', value: '份' },
];

export interface FoodItemRowProps {
  item: FoodItem;
  /** 字段变更（任意字段变更都会重新计算并回传） */
  onChange: (next: FoodItem) => void;
  /** 删除该条 */
  onDelete: () => void;
  /** 错误信息 */
  errors?: { name?: string; amount?: string };
}

export function FoodItemRow({ item, onChange, onDelete, errors }: FoodItemRowProps) {
  const [searchKeyword, setSearchKeyword] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const { results } = useFoodSearch(searchKeyword);

  const handleNameChange = (text: string) => {
    onChange({ ...item, name: text });
    setSearchKeyword(text);
    setShowSearch(text.trim().length > 0);
  };

  const handleSelectCandidate = (c: FoodCandidate) => {
    setShowSearch(false);
    setSearchKeyword('');
    // 自动填充：名称 + 默认份量/单位 + 默认营养
    onChange({
      ...item,
      name: c.name,
      amount: c.defaultAmount,
      unit: c.defaultUnit,
      calories: c.caloriesPerPortion,
      protein: c.proteinPerPortion,
      fat: c.fatPerPortion,
      carbs: c.carbsPerPortion,
    });
  };

  const handleAmountChange = (text: string) => {
    const num = parseFloat(text);
    const safe = Number.isFinite(num) ? num : 0;
    // 按比例缩放营养（基于当前 amount，避免名称未匹配时丢失数据）
    if (item.amount > 0 && safe > 0) {
      const ratio = safe / item.amount;
      onChange({
        ...item,
        amount: safe,
        calories: Math.round(item.calories * ratio),
        protein: Math.round(item.protein * ratio * 10) / 10,
        fat: Math.round(item.fat * ratio * 10) / 10,
        carbs: Math.round(item.carbs * ratio * 10) / 10,
      });
    } else {
      onChange({ ...item, amount: safe });
    }
  };

  const handleUnitChange = (unit: string) => {
    onChange({ ...item, unit });
  };

  return (
    <View style={styles.card}>
      <View style={styles.nameWrap}>
        <TextInput
          label="食物名称"
          value={item.name}
          onChangeText={handleNameChange}
          placeholder="请输入食物名称"
          error={errors?.name}
        />
        <FoodSearchModal
          keyword={searchKeyword}
          results={results}
          visible={showSearch}
          onSelect={handleSelectCandidate}
        />
      </View>

      <View style={styles.row}>
        <View style={styles.amountCol}>
          <TextInput
            label="份量"
            value={item.amount > 0 ? String(item.amount) : ''}
            onChangeText={handleAmountChange}
            keyboardType="numeric"
            placeholder="0"
            error={errors?.amount}
          />
        </View>
        <View style={styles.unitCol}>
          <Picker
            label="单位"
            value={item.unit}
            onChange={handleUnitChange}
            options={UNIT_OPTIONS}
          />
        </View>
      </View>

      <View style={styles.footer}>
        <Text style={styles.calorieText}>
          热量：
          <Text style={styles.calorieValue}>
            {item.calories > 0 ? `${item.calories} kcal` : '--'}
          </Text>
          <Text style={styles.calorieHint}> （自动计算）</Text>
        </Text>
        <TouchableOpacity onPress={onDelete} style={styles.deleteBtn}>
          <Feather name="trash-2" size={18} color={theme.colors.textTertiary} />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.md,
    ...theme.shadows.card,
  },
  nameWrap: {
    position: 'relative',
    zIndex: 10,
  },
  row: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  amountCol: {
    flex: 1,
  },
  unitCol: {
    flex: 1,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: theme.spacing.sm,
  },
  calorieText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  calorieValue: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  calorieHint: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  deleteBtn: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.full,
  },
});
