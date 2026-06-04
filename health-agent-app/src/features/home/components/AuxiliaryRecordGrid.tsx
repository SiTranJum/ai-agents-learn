// AuxiliaryRecordGrid - 辅助记录小卡片区
// 2×2 网格：饮水 / 睡眠 / 运动 / 排便
// 参考: docs/prd/v1/ui-design/03-home-dashboard.md §3.G, §6.5

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { theme } from '@app/styles/theme';
import { Images } from '@constants/assets';
import type { AuxiliaryItemType, AuxiliaryPending, HomeAuxiliary } from '../types/home.types';

export interface AuxiliaryRecordGridProps {
  auxiliary: HomeAuxiliary;
  onItemPress: (type: AuxiliaryItemType) => void;
  /** 确认某类型的 pending 记录 */
  onConfirm?: (type: AuxiliaryItemType) => void;
  /** 取消某类型的 pending 记录 */
  onCancel?: (type: AuxiliaryItemType) => void;
}

interface ItemConfig {
  type: AuxiliaryItemType;
  label: string;
  illustration?: any; // 插画图片
  icon?: keyof typeof Feather.glyphMap; // 备用图标
  color: string;
  primary: string;
  secondary?: string;
  pending?: AuxiliaryPending;
}

export function AuxiliaryRecordGrid({
  auxiliary,
  onItemPress,
  onConfirm,
  onCancel,
}: AuxiliaryRecordGridProps) {
  const pend = auxiliary.pending;
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
      pending: pend?.water,
    },
    {
      type: 'sleep',
      label: '睡眠',
      illustration: Images.illustrations.sleep,
      color: '#A78BFA',
      primary: auxiliary.sleep?.duration ?? '未记录',
      pending: pend?.sleep,
    },
    {
      type: 'exercise',
      label: '运动',
      illustration: Images.illustrations.exercise,
      color: theme.colors.success,
      primary: auxiliary.exercise?.duration ?? '未记录',
      pending: pend?.exercise,
    },
    {
      type: 'bowel',
      label: '排便',
      icon: 'check-circle',
      color: theme.colors.textSecondary,
      primary: auxiliary.bowel?.status ?? '未记录',
      pending: pend?.bowel,
    },
  ];

  return (
    <View style={styles.grid}>
      {items.map((item) => (
        <AuxItem
          key={item.type}
          config={item}
          onPress={() => onItemPress(item.type)}
          onConfirm={onConfirm ? () => onConfirm(item.type) : undefined}
          onCancel={onCancel ? () => onCancel(item.type) : undefined}
        />
      ))}
    </View>
  );
}

function AuxItem({
  config,
  onPress,
  onConfirm,
  onCancel,
}: {
  config: ItemConfig;
  onPress: () => void;
  onConfirm?: () => void;
  onCancel?: () => void;
}) {
  const isEmpty = config.primary === '未记录' || config.primary.startsWith('--');
  const pending = config.pending;

  // pending 态：高亮卡片 + 预览 + 确认/取消按钮（点卡片本身不跳转）
  if (pending) {
    return (
      <View style={[styles.card, styles.pendingCard]}>
        <View style={styles.headerRow}>
          {config.illustration ? (
            <Image source={config.illustration} style={styles.illustration} />
          ) : (
            <View style={[styles.iconWrap, { backgroundColor: `${config.color}22` }]}>
              <Feather name={config.icon!} size={16} color={config.color} />
            </View>
          )}
          <Text style={styles.label}>{config.label}</Text>
          <Text style={styles.pendingTag}>
            {pending.operation === 'append' ? '追加' : 'AI 待确认'}
          </Text>
        </View>
        <Text style={styles.pendingSummary} numberOfLines={1}>
          {pending.summary}
        </Text>
        <View style={styles.pendingActions}>
          <TouchableOpacity
            style={[styles.pendingBtn, styles.confirmBtn]}
            onPress={onConfirm}
            activeOpacity={0.7}
          >
            <Text style={styles.confirmBtnText}>确认</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.pendingBtn, styles.cancelBtn]}
            onPress={onCancel}
            activeOpacity={0.7}
          >
            <Text style={styles.cancelBtnText}>取消</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

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
  pendingCard: {
    backgroundColor: '#FFF7ED',
    borderWidth: 1,
    borderColor: theme.colors.primary,
  },
  pendingTag: {
    ...theme.typography.caption,
    color: theme.colors.primary,
    fontWeight: '600',
    marginLeft: 'auto',
  },
  pendingSummary: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    fontWeight: '600',
    marginTop: 2,
    marginBottom: theme.spacing.xs,
  },
  pendingActions: {
    flexDirection: 'row',
    gap: theme.spacing.xs,
  },
  pendingBtn: {
    flex: 1,
    paddingVertical: 4,
    borderRadius: theme.radius.sm,
    alignItems: 'center',
  },
  confirmBtn: {
    backgroundColor: theme.colors.primary,
  },
  confirmBtnText: {
    ...theme.typography.caption,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  cancelBtn: {
    backgroundColor: theme.colors.primaryLight,
  },
  cancelBtnText: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
  },
});
