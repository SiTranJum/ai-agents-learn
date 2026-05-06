// SettingsList - 设置项列表（白底分组卡片 + 分割线）
// 参�? docs/prd/v1/ui-design/12-profile-and-settings.md §C3 (设置�?

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card } from '@shared/ui/Card';
import { Switch } from '@shared/forms/Switch';
import { theme } from '@app/styles/theme';

export type SettingItem =
  | {
      type: 'link';
      key: string;
      label: string;
      icon?: keyof typeof Feather.glyphMap;
      /** 右侧附加值（如版本号 v1.0.0�?*/
      rightText?: string;
      onPress?: () => void;
      /** 标题颜色（如退�?删除使用错误色） */
      danger?: boolean;
    }
  | {
      type: 'switch';
      key: string;
      label: string;
      icon?: keyof typeof Feather.glyphMap;
      value: boolean;
      onChange: (v: boolean) => void;
    }
  | {
      type: 'radio';
      key: string;
      label: string;
      description?: string;
      selected: boolean;
      onPress: () => void;
    };

export interface SettingsListSection {
  title?: string;
  items: SettingItem[];
}

export interface SettingsListProps {
  sections: SettingsListSection[];
}

export function SettingsList({ sections }: SettingsListProps) {
  return (
    <View style={styles.root}>
      {sections.map((sec, sIdx) => (
        <View key={sIdx} style={styles.section}>
          {sec.title && <Text style={styles.sectionTitle}>{sec.title}</Text>}
          <Card style={styles.card}>
            {sec.items.map((item, idx) => (
              <Row
                key={item.key}
                item={item}
                last={idx === sec.items.length - 1}
              />
            ))}
          </Card>
        </View>
      ))}
    </View>
  );
}

function Row({ item, last }: { item: SettingItem; last: boolean }) {
  if (item.type === 'switch') {
    return (
      <View style={[styles.row, !last && styles.rowBorder]}>
        {item.icon && (
          <Feather
            name={item.icon}
            size={18}
            color={theme.colors.textSecondary}
            style={styles.icon}
          />
        )}
        <Text style={styles.label}>{item.label}</Text>
        <Switch value={item.value} onChange={item.onChange} />
      </View>
    );
  }

  if (item.type === 'radio') {
    return (
      <TouchableOpacity
        style={[styles.row, !last && styles.rowBorder]}
        onPress={item.onPress}
        activeOpacity={0.7}
      >
        <View style={styles.radioOuter}>
          {item.selected && <View style={styles.radioInner} />}
        </View>
        <View style={styles.radioBody}>
          <Text style={styles.label}>{item.label}</Text>
          {item.description && (
            <Text style={styles.desc}>{item.description}</Text>
          )}
        </View>
      </TouchableOpacity>
    );
  }

  // link
  return (
    <TouchableOpacity
      style={[styles.row, !last && styles.rowBorder]}
      onPress={item.onPress}
      activeOpacity={item.onPress ? 0.7 : 1}
      disabled={!item.onPress}
    >
      {item.icon && (
        <Feather
          name={item.icon}
          size={18}
          color={
            item.danger ? theme.colors.error : theme.colors.textSecondary
          }
          style={styles.icon}
        />
      )}
      <Text
        style={[
          styles.label,
          item.danger && { color: theme.colors.error, fontWeight: '600' },
        ]}
      >
        {item.label}
      </Text>
      {item.rightText && (
        <Text style={styles.rightText}>{item.rightText}</Text>
      )}
      {item.onPress && !item.danger && (
        <Feather
          name="chevron-right"
          size={18}
          color={theme.colors.textTertiary}
        />
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  root: {
    gap: theme.spacing.md,
  },
  section: {},
  sectionTitle: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
    marginLeft: theme.spacing.xs,
  },
  card: {
    padding: 0,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    gap: theme.spacing.md,
    minHeight: 52,
  },
  rowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
  },
  icon: {
    width: 18,
  },
  label: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    flex: 1,
  },
  rightText: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
  },
  desc: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginTop: 2,
  },
  radioBody: {
    flex: 1,
  },
  radioOuter: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: theme.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: theme.colors.primary,
  },
});
