// FoodSearchModal - 食物搜索候选列表
// 显示在食物名输入框下方的浮层候选
// 参考: docs/prd/v1/ui-design/05-diet-edit-page.md §5.3, §6.6

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { theme } from '@app/styles/theme';
import type { FoodCandidate } from '../types/diet.types';

export interface FoodSearchModalProps {
  /** 搜索关键字（外部受控） */
  keyword: string;
  /** 搜索结果 */
  results: FoodCandidate[];
  /** 是否显示 */
  visible: boolean;
  /** 选中候选项 */
  onSelect: (candidate: FoodCandidate) => void;
}

export function FoodSearchModal({
  keyword,
  results,
  visible,
  onSelect,
}: FoodSearchModalProps) {
  if (!visible || keyword.trim().length === 0) return null;

  return (
    <View style={styles.container}>
      {results.length === 0 ? (
        <Text style={styles.empty}>未找到该食物，可手动输入热量</Text>
      ) : (
        <ScrollView keyboardShouldPersistTaps="handled" style={styles.list}>
          {results.map((c) => (
            <TouchableOpacity
              key={c.id}
              style={styles.item}
              onPress={() => onSelect(c)}
              activeOpacity={0.7}
            >
              <Text style={styles.itemName}>{c.name}</Text>
              <Text style={styles.itemHint}>
                常见：{c.defaultAmount}
                {c.defaultUnit} · {c.caloriesPerPortion} kcal
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
    borderColor: theme.colors.divider,
    marginTop: theme.spacing.xs,
    maxHeight: 220,
    ...theme.shadows.card,
  },
  list: {
    flexGrow: 0,
  },
  item: {
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
  },
  itemName: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '500',
  },
  itemHint: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginTop: 2,
  },
  empty: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.md,
    textAlign: 'center',
  },
});
