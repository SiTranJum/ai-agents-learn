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
import { DatePicker } from '@shared/forms/DatePicker';
import { RulerPicker } from '@shared/forms/RulerPicker';
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
  const [age, setAge] = useState(0);
  const [height, setHeight] = useState(0);
  const [weight, setWeight] = useState(0);
  const [targetWeight, setTargetWeight] = useState(0);
  const [activityLevel, setActivityLevel] = useState<ActivityLevel>('moderate');
  const [goalType, setGoalType] = useState('');
  const [dailyCalorie, setDailyCalorie] = useState(0);
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
      // 从 birthDate 计算年龄
      const birthDate = new Date(profile.birthDate);
      const today = new Date();
      let calculatedAge = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        calculatedAge--;
      }
      setAge(calculatedAge > 0 ? calculatedAge : 25);
      setHeight(profile.height);
      setWeight(profile.weight);
      setTargetWeight(profile.targetWeight);
      setActivityLevel(profile.activityLevel);
      setGoalType(profile.goalType ?? '');
      setDailyCalorie(profile.dailyCalorieTarget ?? 0);
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
    if (age < 18 || age > 100) {
      toast.show({ type: 'error', message: '请选择年龄 (18-100 岁)' });
      return;
    }
    if (!height || height < 50 || height > 250) {
      toast.show({ type: 'error', message: '请选择身高 (50-250 cm)' });
      return;
    }
    if (!weight || weight < 20 || weight > 300) {
      toast.show({ type: 'error', message: '请选择体重 (20-300 kg)' });
      return;
    }
    if (!targetWeight || targetWeight < 20 || targetWeight > 300) {
      toast.show({ type: 'error', message: '请选择目标体重 (20-300 kg)' });
      return;
    }

    // 从年龄计算出生日期（假设生日是今年的今天）
    const today = new Date();
    const birthYear = today.getFullYear() - age;
    const birthDate = new Date(birthYear, today.getMonth(), today.getDate());
    const birthDateStr = birthDate.toISOString().split('T')[0];

    try {
      await updateMutation.mutateAsync({
        nickname: nickname.trim(),
        gender,
        birthDate: birthDateStr,
        height,
        weight,
        targetWeight,
        activityLevel,
        goalType: goalType || undefined,
        dailyCalorieTarget: dailyCalorie || undefined,
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
    nickname, gender, age, height, weight, targetWeight,
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
            <Picker
              label="年龄"
              value={age.toString()}
              onChange={(v) => set(setAge)(parseInt(v, 10))}
              options={Array.from({ length: 83 }, (_, i) => ({
                label: `${i + 18} 岁`,
                value: (i + 18).toString(),
              }))}
            />
            <RulerPicker
              label="身高"
              value={height}
              onChange={set(setHeight)}
              min={50}
              max={250}
              step={1}
              unit="cm"
            />
            <RulerPicker
              label="体重"
              value={weight}
              onChange={set(setWeight)}
              min={20}
              max={300}
              step={0.1}
              unit="kg"
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
            <RulerPicker
              label="目标体重"
              value={targetWeight}
              onChange={set(setTargetWeight)}
              min={20}
              max={300}
              step={0.1}
              unit="kg"
            />
            <TextInput
              label="每日热量目标"
              value={dailyCalorie > 0 ? dailyCalorie.toString() : ''}
              onChangeText={(v) => {
                const num = parseInt(v, 10);
                set(setDailyCalorie)(isNaN(num) ? 0 : num);
              }}
              keyboardType="numeric"
              placeholder="如 2000"
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
