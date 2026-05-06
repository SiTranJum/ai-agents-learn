// ProfileInfoCard - 档案信息卡片
// 支持 grid (2x2) 和 list 两种布局
// 参考: docs/prd/v1/ui-design/12-profile-and-settings.md §A4

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card } from '@shared/ui/Card';
import { theme } from '@app/styles/theme';

export interface ProfileInfoItem {
  label: string;
  value: string;
}

export interface ProfileInfoCardProps {
  title: string;
  icon?: keyof typeof Feather.glyphMap;
  layout?: 'grid' | 'list';
  items: ProfileInfoItem[];
  /** 整张卡片可点击 → 跳到编辑 */
  onPress?: () => void;
  /** 空态占位文案 */
  emptyHint?: string;
}

export function ProfileInfoCard({
  title,
  icon,
  layout = 'list',
  items,
  onPress,
  emptyHint,
}: ProfileInfoCardProps) {
  const isEmpty = items.length === 0 || items.every((it) => !it.value);

  const inner = (
    <>
      <View style={styles.header}>
        {icon && (
          <Feather name={icon} size={16} color={theme.colors.primary} />
        )}
        <Text style={styles.title}>{title}</Text>
        {onPress && (
          <Feather
            name="chevron-right"
            size={18}
            color={theme.colors.textTertiary}
            style={styles.chev}
          />
        )}
      </View>

      {isEmpty && emptyHint ? (
        <Text style={styles.emptyHint}>{emptyHint}</Text>
      ) : layout === 'grid' ? (
        <View style={styles.grid}>
          {items.map((it, idx) => (
            <View key={idx} style={styles.gridItem}>
              <Text style={styles.gridLabel}>{it.label}</Text>
              <Text style={styles.gridValue} numberOfLines={1}>
                {it.value || '未设置'}
              </Text>
            </View>
          ))}
        </View>
      ) : (
        <View>
          {items.map((it, idx) => (
            <View key={idx} style={styles.row}>
              <Text style={styles.rowLabel}>{it.label}</Text>
              <Text style={styles.rowValue} numberOfLines={2}>
                {it.value || '未设置'}
              </Text>
            </View>
          ))}
        </View>
      )}
    </>
  );

  if (onPress) {
    return (
      <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
        <Card>{inner}</Card>
      </TouchableOpacity>
    );
  }

  return <Card>{inner}</Card>;
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    marginBottom: theme.spacing.sm,
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    flex: 1,
  },
  chev: {
    marginLeft: 'auto',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -theme.spacing.xs,
  },
  gridItem: {
    width: '50%',
    paddingHorizontal: theme.spacing.xs,
    paddingVertical: theme.spacing.sm,
  },
  gridLabel: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginBottom: 2,
  },
  gridValue: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },
  row: {
    flexDirection: 'row',
    paddingVertical: 6,
    gap: theme.spacing.md,
  },
  rowLabel: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    width: 56,
  },
  rowValue: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
    flex: 1,
    fontWeight: '500',
  },
  emptyHint: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
    textAlign: 'center',
    paddingVertical: theme.spacing.md,
  },
});
