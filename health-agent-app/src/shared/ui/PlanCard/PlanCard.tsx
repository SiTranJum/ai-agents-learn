import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { theme } from '@app/styles/theme';

export interface PlanCardProps {
  name: string;
  progress: number; // 0-100
  progressText: string; // 如 "第 3 天 / 共 21 天"
  dateRange: string; // 如 "2026.04.10 - 2026.05.01"
  status: 'active' | 'paused' | 'completed';
  onPress: () => void;
}

const statusConfig = {
  active: { label: '进行中', bg: '#E8F9ED', text: '#4CD964' },
  paused: { label: '已暂停', bg: '#FFF5E0', text: '#E6A800' },
  completed: { label: '已完成', bg: '#E8F6FF', text: '#5AC8FA' },
};

export function PlanCard({
  name,
  progress,
  progressText,
  dateRange,
  status,
  onPress,
}: PlanCardProps) {
  const statusStyle = statusConfig[status];
  const clampedProgress = Math.max(0, Math.min(progress, 100));

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.header}>
        <Text style={styles.name} numberOfLines={1}>{name}</Text>
        <View style={[styles.statusTag, { backgroundColor: statusStyle.bg }]}>
          <Text style={[styles.statusText, { color: statusStyle.text }]}>
            {statusStyle.label}
          </Text>
        </View>
      </View>

      <View style={styles.progressSection}>
        <View style={styles.progressTrack}>
          <View
            style={[
              styles.progressFill,
              { width: `${clampedProgress}%` },
            ]}
          />
        </View>
        <Text style={styles.progressText}>{progressText}</Text>
      </View>

      <Text style={styles.dateRange}>{dateRange}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    minHeight: 108,
    borderRadius: theme.radius.md,
    padding: theme.spacing.lg,
    backgroundColor: theme.colors.bgCard,
    ...theme.shadows.card,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  name: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    flex: 1,
    marginRight: theme.spacing.sm,
  },
  statusTag: {
    borderRadius: theme.radius.full,
    paddingHorizontal: 10,
    paddingVertical: 2,
  },
  statusText: {
    ...theme.typography.tag,
  },
  progressSection: {
    marginBottom: theme.spacing.sm,
  },
  progressTrack: {
    height: 8,
    borderRadius: 999,
    backgroundColor: '#F0F0F0',
    overflow: 'hidden',
    marginBottom: theme.spacing.xs,
  },
  progressFill: {
    height: 8,
    borderRadius: 999,
    backgroundColor: theme.colors.primary,
  },
  progressText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  dateRange: {
    ...theme.typography.caption,
    color: '#999999',
  },
});
