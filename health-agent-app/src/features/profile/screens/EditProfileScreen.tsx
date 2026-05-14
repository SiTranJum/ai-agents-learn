// EditProfileScreen - 编辑档案页 (P11)
// 三个分组：基础信息 / 饮食偏好 / 疾病信息
// 参考: docs/specs/frontend/modules/15-profile-module.md §P11
// UI 文稿: docs/prd/v1/ui-design/12-profile-and-settings.md §B

import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { Card } from '@shared/ui/Card';
import { Button } from '@shared/ui/Button';
import { TextInput } from '@shared/forms/TextInput';
import { Picker } from '@shared/forms/Picker';
import { MultiSelectTags } from '@shared/forms/MultiSelectTags';
import { ConfirmDialog } from '@shared/feedback/ConfirmDialog';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList } from '@app/navigation/types';

import { useUpdateUserProfile, useUserProfile } from '../hooks/useProfile';
import {
  ACTIVITY_LEVEL_OPTIONS,
  ALLERGY_OPTIONS,
  DIET_TYPE_OPTIONS,
  DISEASE_OPTIONS,
  DISLIKED_FOOD_OPTIONS,
  GENDER_OPTIONS,
  GOAL_TYPE_OPTIONS,
  RESTRICTION_OPTIONS,
} from '../mocks/profileMocks';
import type { ActivityLevel, Gender } from '../types/profile.types';

type Nav = NativeStackNavigationProp<MainStackParamList, 'EditProfile'>;

export function EditProfileScreen() {
  const navigation = useNavigation<Nav>();
  const toast = useToast();
  const { data: profile, isLoading } = useUserProfile();
  const updateMutation = useUpdateUserProfile();

  // 表单状态（profile 加载完成后初始化）
  const [nickname, setNickname] = useState('');
  const [gender, setGender] = useState<Gender>('male');
  const [birthDate, setBirthDate] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [targetWeight, setTargetWeight] = useState('');
  const [activityLevel, setActivityLevel] = useState<ActivityLevel>('moderate');
  const [goalType, setGoalType] = useState('');
  const [dailyCalorie, setDailyCalorie] = useState('');
  const [dietType, setDietType] = useState('均衡饮食');
  const [allergies, setAllergies] = useState<string[]>([]);
  const [restrictions, setRestrictions] = useState<string[]>([]);
  const [dislikedFoods, setDislikedFoods] = useState<string[]>([]);
  const [diseases, setDiseases] = useState<string[]>([]);
  const [medications, setMedications] = useState<string>('');
  const [medicalAdvice, setMedicalAdvice] = useState('');

  const [dirty, setDirty] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);

  // 数据就绪后初始化表单
  React.useEffect(() => {
    if (profile && !initialized) {
      setNickname(profile.nickname);
      setGender(profile.gender);
      setBirthDate(profile.birthDate);
      setHeight(String(profile.height));
      setWeight(String(profile.weight));
      setTargetWeight(String(profile.targetWeight));
      setActivityLevel(profile.activityLevel);
      setGoalType(profile.goalType ?? '');
      setDailyCalorie(
        profile.dailyCalorieTarget != null
          ? String(profile.dailyCalorieTarget)
          : ''
      );
      setDietType(profile.dietType);
      setAllergies(profile.allergies);
      setRestrictions(profile.restrictions);
      setDislikedFoods(profile.dislikedFoods);
      setDiseases(profile.diseases);
      setMedications(profile.medications);
      setMedicalAdvice(profile.medicalAdvice ?? '');
      setInitialized(true);
    }
  }, [profile, initialized]);

  const markDirty = () => {
    if (!dirty) setDirty(true);
  };
  const set = <T,>(setter: (v: T) => void) => (v: T) => {
    setter(v);
    markDirty();
  };

  // 校验 + 保存
  const handleSave = useCallback(async () => {
    // 必填校验
    if (!nickname.trim() || nickname.trim().length > 20) {
      toast.show({ type: 'error', message: '昵称需 1-20 字符' });
      return;
    }
    const h = parseFloat(height);
    if (!(h >= 50 && h <= 250)) {
      toast.show({ type: 'error', message: '身高需在 50-250 cm 之间' });
      return;
    }
    const w = parseFloat(weight);
    if (!(w >= 20 && w <= 300)) {
      toast.show({ type: 'error', message: '体重需在 20-300 kg 之间' });
      return;
    }
    const tw = parseFloat(targetWeight);
    if (!(tw >= 20 && tw <= 300)) {
      toast.show({ type: 'error', message: '目标体重需在 20-300 kg 之间' });
      return;
    }
    if (!birthDate) {
      toast.show({ type: 'error', message: '请填写出生日期' });
      return;
    }

    try {
      await updateMutation.mutateAsync({
        nickname: nickname.trim(),
        gender,
        birthDate,
        height: h,
        weight: w,
        targetWeight: tw,
        activityLevel,
        goalType: goalType || undefined,
        dailyCalorieTarget: dailyCalorie ? parseInt(dailyCalorie, 10) : undefined,
        dietType,
        allergies,
        restrictions,
        dislikedFoods,
        diseases,
        medications,
        medicalAdvice: medicalAdvice.trim() || undefined,
      });
      toast.show({ type: 'success', message: '档案已保存' });
      navigation.goBack();
    } catch {
      toast.show({ type: 'error', message: '保存失败，请重试' });
    }
  }, [
    nickname, gender, birthDate, height, weight, targetWeight,
    activityLevel, goalType, dailyCalorie, dietType,
    allergies, restrictions, dislikedFoods,
    diseases, medications, medicalAdvice,
    updateMutation, toast, navigation,
  ]);

  const handleBack = () => {
    if (dirty) setShowLeaveConfirm(true);
    else navigation.goBack();
  };

  if (isLoading || !initialized) {
    return (
      <PageContainer useSafeArea>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      </PageContainer>
    );
  }

  return (
    <PageContainer useSafeArea>
      {/* 顶部导航栏 */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
          <Feather name="chevron-left" size={24} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>编辑档案</Text>
        <View style={styles.backBtn} />
      </View>

      <KeyboardAvoidingView
        style={styles.flex1}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* 基础信息 */}
          <Section title="基础信息">
            <TextInput
              label="昵称"
              value={nickname}
              onChangeText={set(setNickname)}
              maxLength={20}
              placeholder="请输入昵称"
            />
            <Picker
              label="性别"
              value={gender}
              onChange={(v) => set(setGender)(v as Gender)}
              options={[...GENDER_OPTIONS]}
            />
            <TextInput
              label="出生日期 (YYYY-MM-DD)"
              value={birthDate}
              onChangeText={set(setBirthDate)}
              placeholder="1995-06-15"
            />
            <TextInput
              label="身高 (cm)"
              value={height}
              onChangeText={set(setHeight)}
              keyboardType="numeric"
            />
            <TextInput
              label="体重 (kg)"
              value={weight}
              onChangeText={set(setWeight)}
              keyboardType="decimal-pad"
            />
            <Picker
              label="活动量"
              value={activityLevel}
              onChange={(v) => set(setActivityLevel)(v as ActivityLevel)}
              options={[...ACTIVITY_LEVEL_OPTIONS]}
            />
          </Section>

          {/* 健康目标 */}
          <Section title="健康目标">
            <Picker
              label="目标类型"
              value={goalType || '减脂'}
              onChange={set(setGoalType)}
              options={GOAL_TYPE_OPTIONS}
            />
            <TextInput
              label="目标体重 (kg)"
              value={targetWeight}
              onChangeText={set(setTargetWeight)}
              keyboardType="decimal-pad"
            />
            <TextInput
              label="每日热量目标 (kcal)"
              value={dailyCalorie}
              onChangeText={set(setDailyCalorie)}
              keyboardType="numeric"
              placeholder="可选，如 2100"
            />
          </Section>

          {/* 饮食偏好 */}
          <Section title="饮食偏好">
            <Picker
              label="饮食类型"
              value={dietType}
              onChange={set(setDietType)}
              options={DIET_TYPE_OPTIONS}
            />
            <MultiSelectTags
              label="过敏原"
              value={allergies}
              onChange={set(setAllergies)}
              options={ALLERGY_OPTIONS}
            />
            <MultiSelectTags
              label="忌口"
              value={restrictions}
              onChange={set(setRestrictions)}
              options={RESTRICTION_OPTIONS}
            />
            <MultiSelectTags
              label="不喜欢的食物"
              value={dislikedFoods}
              onChange={set(setDislikedFoods)}
              options={DISLIKED_FOOD_OPTIONS}
            />
          </Section>

          {/* 疾病信息 */}
          <Section title="疾病信息">
            <MultiSelectTags
              label="基础疾病"
              value={diseases}
              onChange={set(setDiseases)}
              options={DISEASE_OPTIONS}
            />
            <TextInput
              label="服用药物"
              value={medications}
              onChangeText={set(setMedications)}
              multiline
              maxLength={500}
              placeholder="如 氨氯地平 5mg/日"
            />
            <TextInput
              label="医嘱限制"
              value={medicalAdvice}
              onChangeText={set(setMedicalAdvice)}
              multiline
              maxLength={200}
              placeholder="如 低盐饮食、每日盐摄入不超过 6g"
            />
          </Section>
        </ScrollView>

        {/* 底部保存按钮 */}
        <View style={styles.actionBar}>
          <Button
            variant="primary"
            onPress={handleSave}
            loading={updateMutation.isPending}
          >
            保存
          </Button>
        </View>
      </KeyboardAvoidingView>

      <ConfirmDialog
        visible={showLeaveConfirm}
        title="放弃修改？"
        message="当前修改尚未保存，确认离开吗？"
        confirmText="放弃修改"
        cancelText="继续编辑"
        variant="danger"
        onConfirm={() => {
          setShowLeaveConfirm(false);
          navigation.goBack();
        }}
        onCancel={() => setShowLeaveConfirm(false)}
      />
    </PageContainer>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={sectionStyles.section}>
      <Text style={sectionStyles.title}>{title}</Text>
      <Card>{children}</Card>
    </View>
  );
}

const sectionStyles = StyleSheet.create({
  section: {
    marginBottom: theme.spacing.md,
  },
  title: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
    marginLeft: theme.spacing.xs,
  },
});

const styles = StyleSheet.create({
  flex1: { flex: 1 },
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
    paddingBottom: theme.spacing.xxl,
  },
  actionBar: {
    padding: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
    backgroundColor: theme.colors.bgPage,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
