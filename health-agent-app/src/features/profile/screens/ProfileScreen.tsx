// ProfileScreen - 个人中心页 (P10)
// 参考: docs/specs/frontend/modules/15-profile-module.md §P10
// UI 文稿: docs/prd/v1/ui-design/12-profile-and-settings.md §A

import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { CompositeNavigationProp } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { Avatar } from '@shared/ui/Avatar';
import { Card } from '@shared/ui/Card';
import { ConfirmDialog } from '@shared/feedback/ConfirmDialog';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList, TabParamList } from '@app/navigation/types';
import { useGlobalStore } from '@core/store/globalStore';

import { useUserProfile } from '../hooks/useProfile';
import { ProfileInfoCard } from '../components/ProfileInfoCard';
import { ACTIVITY_LEVEL_LABEL } from '../mocks/profileMocks';

type Nav = CompositeNavigationProp<
  BottomTabNavigationProp<TabParamList, 'ProfileTab'>,
  NativeStackNavigationProp<MainStackParamList>
>;

function calcAge(birthDate: string): number {
  const b = new Date(birthDate);
  if (Number.isNaN(b.getTime())) return 0;
  const now = new Date();
  let age = now.getFullYear() - b.getFullYear();
  const m = now.getMonth() - b.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < b.getDate())) age -= 1;
  return age;
}

function genderLabel(g: string): string {
  return ({ male: '男', female: '女', other: '其他' } as Record<string, string>)[g] ?? '未设置';
}

export function ProfileScreen() {
  const navigation = useNavigation<Nav>();
  const toast = useToast();
  const logout = useGlobalStore((s) => s.logout);

  const { data: profile, isLoading } = useUserProfile();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const handleEdit = useCallback(
    () => navigation.navigate('EditProfile'),
    [navigation]
  );
  const handleSettings = useCallback(
    () => navigation.navigate('Settings'),
    [navigation]
  );
  const handleLogout = useCallback(() => {
    logout();
    toast.show({ type: 'success', message: '已退出登录' });
  }, [logout, toast]);

  if (isLoading || !profile) {
    return (
      <PageContainer>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      </PageContainer>
    );
  }

  const age = calcAge(profile.birthDate);
  const bmi = profile.height
    ? Math.round((profile.weight / Math.pow(profile.height / 100, 2)) * 10) / 10
    : 0;

  return (
    <PageContainer>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* 用户信息区 */}
        <TouchableOpacity
          style={styles.userSection}
          onPress={handleEdit}
          activeOpacity={0.7}
        >
          <Avatar uri={profile.avatar} name={profile.nickname} size={64} />
          <Text style={styles.nickname}>{profile.nickname}</Text>
          <Text style={styles.email}>{profile.email}</Text>
        </TouchableOpacity>

        {/* 健康档案卡片 */}
        <ProfileInfoCard
          title="健康档案"
          icon="target"
          layout="grid"
          onPress={handleEdit}
          items={[
            { label: '目标', value: profile.goalType ?? '未设置' },
            { label: '身高', value: `${profile.height} cm` },
            { label: '体重', value: `${profile.weight} kg` },
            {
              label: '活动量',
              value: ACTIVITY_LEVEL_LABEL[profile.activityLevel] ?? '未设置',
            },
            { label: '目标体重', value: `${profile.targetWeight} kg` },
            { label: 'BMI', value: bmi ? `${bmi}` : '--' },
            { label: '性别', value: genderLabel(profile.gender) },
            { label: '年龄', value: age ? `${age}岁` : '--' },
          ]}
        />

        {/* 饮食偏好卡片 */}
        <ProfileInfoCard
          title="饮食偏好"
          icon="coffee"
          onPress={handleEdit}
          items={[
            { label: '偏好', value: profile.dietType },
            { label: '过敏', value: profile.allergies.join('、') || '无' },
            { label: '忌口', value: profile.restrictions.join('、') || '无' },
            {
              label: '不爱',
              value: profile.dislikedFoods.join('、') || '无',
            },
          ]}
        />

        {/* 疾病信息卡片 */}
        <ProfileInfoCard
          title="疾病信息"
          icon="activity"
          onPress={handleEdit}
          emptyHint="暂无疾病信息"
          items={[
            { label: '疾病', value: profile.diseases.join('、') },
            { label: '药物', value: profile.medications.join('、') },
            { label: '医嘱', value: profile.medicalAdvice ?? '' },
          ]}
        />

        {/* 功能列表 */}
        <Card style={styles.menuCard}>
          <MenuRow label="编辑档案" onPress={handleEdit} />
          <MenuRow label="设置" onPress={handleSettings} />
          <MenuRow
            label="关于我们"
            last
            onPress={() =>
              toast.show({ type: 'info', message: '关于我们 - 即将上线' })
            }
          />
        </Card>

        {/* 退出登录 */}
        <TouchableOpacity
          style={styles.logoutBtn}
          onPress={() => setShowLogoutConfirm(true)}
          activeOpacity={0.7}
        >
          <Text style={styles.logoutText}>退出登录</Text>
        </TouchableOpacity>
      </ScrollView>

      <ConfirmDialog
        visible={showLogoutConfirm}
        title="确定退出登录？"
        message="退出后需要重新登录，本地缓存数据将被清除。"
        confirmText="确定"
        cancelText="取消"
        variant="danger"
        onConfirm={() => {
          setShowLogoutConfirm(false);
          handleLogout();
        }}
        onCancel={() => setShowLogoutConfirm(false)}
      />
    </PageContainer>
  );
}

function MenuRow({
  label,
  onPress,
  last,
}: {
  label: string;
  onPress?: () => void;
  last?: boolean;
}) {
  return (
    <TouchableOpacity
      style={[menuStyles.row, !last && menuStyles.rowBorder]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Text style={menuStyles.label}>{label}</Text>
      <Text style={menuStyles.chev}>›</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  scrollContent: {
    paddingHorizontal: theme.layout.pageHorizontalPadding,
    paddingTop: theme.spacing.md,
    paddingBottom: theme.layout.bottomSafeArea,
    gap: theme.spacing.md,
  },
  userSection: {
    alignItems: 'center',
    paddingVertical: theme.spacing.lg,
  },
  nickname: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginTop: theme.spacing.sm,
  },
  email: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  menuCard: {
    padding: 0,
  },
  logoutBtn: {
    alignItems: 'center',
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    marginTop: theme.spacing.sm,
    ...theme.shadows.card,
  },
  logoutText: {
    ...theme.typography.body,
    color: theme.colors.error,
    fontWeight: '600',
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

const menuStyles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    minHeight: 52,
  },
  rowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.divider,
  },
  label: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
    flex: 1,
  },
  chev: {
    fontSize: 22,
    color: theme.colors.textTertiary,
    lineHeight: 22,
  },
});
