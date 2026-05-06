// AuxiliaryRecordGrid - 辅助记录小卡片区
// 2×2 网格：饮水 / 睡眠 / 运动 / 排便
// 参考: docs/prd/v1/ui-design/03-home-dashboard.md §3.G, §6.5

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { theme } from '@app/styles/theme';
import { Images } from '@constants/assets';
import type { AuxiliaryItemType, HomeAuxiliary } from '../types/home.types';

export interface AuxiliaryRecordGridProps {
  auxiliary: HomeAuxiliary;
  onItemPress: (type: AuxiliaryItemType) => void;
}

interface ItemConfig {
  type: AuxiliaryItemType;
  label: string;
  illustration?: any; // 插画图片
  icon?: keyof typeof Feather.glyphMap; // 备用图标
  color: string;
  primary: string;
  secondary?: string;
}

export function AuxiliaryRecordGrid({ auxiliary, onItemPress }: AuxiliaryRecordGridProps) {
  const items: ItemConfig[] = [
    {
      type: 'water',
      label: '饮水',
      illustration: Images.illustrations.waterCup,
      color: theme.colors.info,
      primary:
        auxiliary.water.current > 0
          ? `${auxiliary.water.current.toLocaleString()} ml`
          : '-- ml',
      secondary: `/ ${auxiliary.water.target.toLocaleString()} ml`,
    },
    {
      type: 'sleep',
      label: '睡眠',
      illustration: Images.illustrations.sleep,
      color: '#A78BFA',
      primary: auxiliary.sleep?.duration ?? '未记录',
    },
    {
      type: 'exercise',
      label: '运动',
      illustration: Images.illustrations.exercise,
      color: theme.colors.success,
      primary: auxiliary.exercise?.duration ?? '未记录',
    },
    {
      type: 'bowel',
      label: '排便',
      icon: 'check-circle',
      color: theme.colors.textSecondary,
      primary: auxiliary.bowel?.status ?? '未记录',
    },
  ];

  return (
    <View style={styles.grid}>
      {items.map((item) => (
        <AuxItem key={item.type} config={item} onPress={() => onItemPress(item.type)} />
      ))}
    </View>
  );
}

function AuxItem({ config, onPress }: { config: ItemConfig; onPress: () => void }) {
  const isEmpty = config.primary === '未记录' || config.primary.startsWith('--');

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.headerRow}>
        {config.illustration ? (
          <Image source={config.illustration} style={styles.illustration} />
        ) : (
          <View style={[styles.iconWrap, { backgroundColor: `${config.color}22` }]}>
            <Feather name={config.icon!} size={16} color={config.color} />
          </View>
        )}
        <Text style={styles.label}>{config.label}</Text>
      </View>
      <Text style={[styles.primary, isEmpty && styles.primaryEmpty]} numberOfLines={1}>
        {config.primary}
      </Text>
      {config.secondary && (
        <Text style={styles.secondary} numberOfLines={1}>
          {config.secondary}
        </Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.md,
  },
  card: {
    width: '47.5%', // 2 列，gap 12
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    ...theme.shadows.card,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.xs,
    gap: theme.spacing.xs,
  },
  iconWrap: {
    width: 24,
    height: 24,
    borderRadius: theme.radius.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
  illustration: {
    width: 24,
    height: 24,
    resizeMode: 'contain',
  },
  label: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  primary: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  primaryEmpty: {
    color: theme.colors.textTertiary,
    fontWeight: '400',
  },
  secondary: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginTop: 2,
  },
});
