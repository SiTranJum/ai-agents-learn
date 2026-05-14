// SettingsScreen - 设置页 (P12)
// 参考: docs/specs/frontend/modules/15-profile-module.md §P12
// UI 文稿: docs/prd/v1/ui-design/12-profile-and-settings.md §C

import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { ConfirmDialog } from '@shared/feedback/ConfirmDialog';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList } from '@app/navigation/types';
import { useGlobalStore } from '@core/store/globalStore';

import { SettingsList, type SettingsListSection } from '../components/SettingsList';
import {
  useAppSettings,
  useDeleteAccount,
  useExportData,
  useUpdateAppSettings,
} from '../hooks/useProfile';
import type { InteractionMode } from '../types/profile.types';

type Nav = NativeStackNavigationProp<MainStackParamList, 'Settings'>;

const APP_VERSION = 'v1.0.0';

const MODE_DESCRIPTIONS: Record<InteractionMode, string> = {
  efficiency: '最少确认，AI 直接执行操作',
  confirmation: '关键操作需要二次确认（推荐）',
  learning: '提供操作提示和引导',
};

const MODE_LABELS: Record<InteractionMode, string> = {
  efficiency: '效率模式',
  confirmation: '确认模式',
  learning: '学习模式',
};

export function SettingsScreen() {
  const navigation = useNavigation<Nav>();
  const toast = useToast();
  const logout = useGlobalStore((s) => s.logout);
  const setGlobalMode = useGlobalStore((s) => s.setInteractionMode);

  const { data: settings, isLoading } = useAppSettings();
  const updateMutation = useUpdateAppSettings();
  const deleteMutation = useDeleteAccount();
  const exportMutation = useExportData();

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleSelectMode = useCallback(
    (mode: InteractionMode) => {
      setGlobalMode(mode);
      updateMutation.mutate({ interactionMode: mode });
    },
    [setGlobalMode, updateMutation]
  );

  const handleToggleNotification = useCallback(
    (key: 'planReminder' | 'dietReminder') => (v: boolean) => {
      if (!settings) return;
      updateMutation.mutate({
        notifications: { ...settings.notifications, [key]: v },
      });
    },
    [settings, updateMutation]
  );

  const handleExport = useCallback(async () => {
    try {
      const json = await exportMutation.mutateAsync();
      toast.show({
        type: 'success',
        message: `数据已导出 (${json.length} 字节)`,
      });
    } catch {
      toast.show({ type: 'error', message: '导出失败，请重试' });
    }
  }, [exportMutation, toast]);

  const handleDeleteAccount = useCallback(async () => {
    try {
      await deleteMutation.mutateAsync();
      logout();
      toast.show({ type: 'success', message: '账号已删除' });
    } catch {
      toast.show({ type: 'error', message: '操作失败，请重试' });
    } finally {
      setShowDeleteConfirm(false);
    }
  }, [deleteMutation, logout, toast]);

  const handleBack = useCallback(() => navigation.goBack(), [navigation]);

  if (isLoading || !settings) {
    return (
      <PageContainer useSafeArea>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      </PageContainer>
    );
  }

  const sections: SettingsListSection[] = [
    {
      title: '交互模式',
      items: (['efficiency', 'confirmation', 'learning'] as InteractionMode[]).map(
        (mode) => ({
          type: 'radio' as const,
          key: mode,
          label: MODE_LABELS[mode],
          description: MODE_DESCRIPTIONS[mode],
          selected: settings.interactionMode === mode,
          onPress: () => handleSelectMode(mode),
        })
      ),
    },
    {
      title: '通知设置',
      items: [
        {
          type: 'switch',
          key: 'planReminder',
          label: '计划提醒',
          icon: 'bell',
          value: settings.notifications.planReminder,
          onChange: handleToggleNotification('planReminder'),
        },
        {
          type: 'switch',
          key: 'dietReminder',
          label: '饮食提醒',
          icon: 'coffee',
          value: settings.notifications.dietReminder,
          onChange: handleToggleNotification('dietReminder'),
        },
      ],
    },
    {
      title: '隐私设置',
      items: [
        {
          type: 'link',
          key: 'export',
          label: '数据导出',
          icon: 'download',
          onPress: handleExport,
        },
        {
          type: 'link',
          key: 'delete',
          label: '删除账号 (V2)',
          icon: 'trash-2',
          danger: true,
          onPress: () => toast.show({ type: 'info', message: '删除账号功能将在 V2 版本上线' }),
        },
      ],
    },
    {
      title: '关于',
      items: [
        {
          type: 'link',
          key: 'version',
          label: '版本号',
          icon: 'info',
          rightText: APP_VERSION,
        },
        {
          type: 'link',
          key: 'terms',
          label: '用户协议',
          icon: 'file-text',
          onPress: () =>
            toast.show({ type: 'info', message: '用户协议 - 即将上线' }),
        },
        {
          type: 'link',
          key: 'privacy',
          label: '隐私政策',
          icon: 'shield',
          onPress: () =>
            toast.show({ type: 'info', message: '隐私政策 - 即将上线' }),
        },
      ],
    },
  ];

  return (
    <PageContainer useSafeArea>
      {/* 顶部导航栏 */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
          <Feather name="chevron-left" size={24} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>设置</Text>
        <View style={styles.backBtn} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <SettingsList sections={sections} />
      </ScrollView>

      <ConfirmDialog
        visible={showDeleteConfirm}
        title="确定删除账号？"
        message="删除后所有数据将永久清除，无法恢复。"
        confirmText="确认删除"
        cancelText="取消"
        variant="danger"
        onConfirm={handleDeleteAccount}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
    backgroundColor: theme.colors.bgPage,
  },
  backBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  scrollContent: {
    padding: theme.layout.pageHorizontalPadding,
    paddingBottom: theme.layout.bottomSafeArea,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
