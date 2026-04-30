// OnboardingScreen - Onboarding 引导页 (P16)
// 参考: docs/specs/frontend/modules/10-auth-module.md §P16
// UI 文稿: docs/prd/v1/ui-design/13-auth-and-onboarding.md (页面 D)

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';
import { format, parseISO } from 'date-fns';

import { theme } from '@app/styles/theme';
import { Button } from '@shared/ui/Button';
import { TextInput } from '@shared/forms/TextInput';
import { DatePicker } from '@shared/forms/DatePicker';
import { Slider } from '@shared/forms/Slider';
import { MultiSelectTags } from '@shared/forms/MultiSelectTags';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { useToast } from '@shared/feedback/Toast/Toast';
import type { AuthStackParamList } from '@app/navigation/types';

import { useAuthStore } from '../store/authStore';
import { useAuth } from '../hooks/useAuth';
import { OnboardingProgress } from '../components/OnboardingProgress';
import { OnboardingStep } from '../components/OnboardingStep';
import { SelectionCards } from '../components/SelectionCards';
import type {
  ActivityLevel,
  DietType,
  Gender,
  GoalType,
  OnboardingData,
} from '../types/auth.types';

type Nav = NativeStackNavigationProp<AuthStackParamList, 'Onboarding'>;

const TOTAL_STEPS = 5;

const GENDER_OPTIONS = [
  { value: 'male' as Gender, label: '男' },
  { value: 'female' as Gender, label: '女' },
];

const ACTIVITY_OPTIONS = [
  { value: 'sedentary' as ActivityLevel, label: '久坐', description: '办公室工作，很少运动' },
  { value: 'light' as ActivityLevel, label: '轻度', description: '每周运动 1-3 次' },
  { value: 'moderate' as ActivityLevel, label: '中度', description: '每周运动 3-5 次' },
  { value: 'heavy' as ActivityLevel, label: '重度', description: '每周运动 6-7 次或体力劳动' },
];

const GOAL_OPTIONS = [
  { value: 'lose_fat' as GoalType, label: '减脂' },
  { value: 'gain_muscle' as GoalType, label: '增肌' },
  { value: 'maintain' as GoalType, label: '维持' },
  { value: 'healthy_diet' as GoalType, label: '健康饮食' },
];

const DIET_OPTIONS = [
  { value: 'balanced' as DietType, label: '均衡饮食' },
  { value: 'low_carb' as DietType, label: '低碳水' },
  { value: 'high_protein' as DietType, label: '高蛋白' },
  { value: 'vegetarian' as DietType, label: '素食' },
  { value: 'mediterranean' as DietType, label: '地中海' },
];

const ALLERGY_OPTIONS = [
  { value: '海鲜', label: '海鲜' },
  { value: '花生', label: '花生' },
  { value: '牛奶', label: '牛奶' },
  { value: '鸡蛋', label: '鸡蛋' },
  { value: '大豆', label: '大豆' },
  { value: '小麦', label: '小麦' },
  { value: '其他', label: '其他' },
];

const RESTRICTION_OPTIONS = [
  { value: '猪肉', label: '猪肉' },
  { value: '牛肉', label: '牛肉' },
  { value: '辣椒', label: '辣椒' },
  { value: '其他', label: '其他' },
];

const DISEASE_OPTIONS = [
  { value: '高血压', label: '高血压' },
  { value: '糖尿病', label: '糖尿病' },
  { value: '高血脂', label: '高血脂' },
  { value: '痛风', label: '痛风' },
  { value: '其他', label: '其他' },
];

const GOAL_LABELS: Record<GoalType, string> = {
  lose_fat: '减脂',
  gain_muscle: '增肌',
  maintain: '维持',
  healthy_diet: '健康饮食',
};

const DIET_LABELS: Record<DietType, string> = {
  balanced: '均衡饮食',
  low_carb: '低碳水',
  high_protein: '高蛋白',
  vegetarian: '素食',
  mediterranean: '地中海',
};

const ACTIVITY_LABELS: Record<ActivityLevel, string> = {
  sedentary: '久坐',
  light: '轻度',
  moderate: '中度',
  heavy: '重度',
};

export function OnboardingScreen() {
  const navigation = useNavigation<Nav>();
  const toast = useToast();
  const { submitOnboarding, isLoading } = useAuth();

  const onboardingStep = useAuthStore((s) => s.onboardingStep);
  const onboardingData = useAuthStore((s) => s.onboardingData);
  const skippedSteps = useAuthStore((s) => s.skippedSteps);
  const setOnboardingStep = useAuthStore((s) => s.setOnboardingStep);
  const updateOnboardingData = useAuthStore((s) => s.updateOnboardingData);
  const skipStep = useAuthStore((s) => s.skipStep);

  const [previewMode, setPreviewMode] = React.useState(false);

  // 默认值
  const data: Partial<OnboardingData> = {
    activityLevel: 'moderate',
    height: 170,
    weight: 65,
    ...onboardingData,
  };

  const update = (patch: Partial<OnboardingData>) => updateOnboardingData(patch);

  // 当前步骤是否可以下一步（必填项校验）
  const canProceed = (): boolean => {
    switch (onboardingStep) {
      case 1:
        return !!(
          data.nickname &&
          data.nickname.length >= 2 &&
          data.nickname.length <= 20 &&
          data.gender &&
          data.birthDate
        );
      case 2:
        return !!(data.height && data.weight && data.activityLevel);
      case 3:
        return !!data.goalType;
      case 4:
      case 5:
        return true; // 选填
      default:
        return false;
    }
  };

  const canSkip = onboardingStep >= 4; // 仅 4/5 步可跳过

  const handleBack = () => {
    if (previewMode) {
      setPreviewMode(false);
      setOnboardingStep(TOTAL_STEPS);
      return;
    }
    if (onboardingStep === 1) {
      navigation.goBack();
      return;
    }
    setOnboardingStep(onboardingStep - 1);
  };

  const handleNext = () => {
    if (!canProceed()) {
      toast.show({ type: 'error', message: '请完善必填信息' });
      return;
    }
    if (onboardingStep < TOTAL_STEPS) {
      setOnboardingStep(onboardingStep + 1);
    } else {
      setPreviewMode(true);
    }
  };

  const handleSkip = () => {
    skipStep(onboardingStep);
    if (onboardingStep < TOTAL_STEPS) {
      setOnboardingStep(onboardingStep + 1);
    } else {
      setPreviewMode(true);
    }
  };

  const handleFinish = async () => {
    // 必填项已通过校验，构建完整数据
    const payload: OnboardingData = {
      nickname: data.nickname!,
      gender: data.gender!,
      birthDate: data.birthDate!,
      height: data.height!,
      weight: data.weight!,
      activityLevel: data.activityLevel!,
      goalType: data.goalType!,
      targetWeight: data.targetWeight,
      dailyCalorieTarget: data.dailyCalorieTarget,
      dietType: data.dietType,
      allergies: data.allergies,
      restrictions: data.restrictions,
      diseases: data.diseases,
      medications: data.medications,
      medicalAdvice: data.medicalAdvice,
    };
    const ok = await submitOnboarding(payload);
    if (ok) {
      toast.show({ type: 'success', message: '档案保存成功' });
      // RootNavigator 会因 token 设置而切换到 Main
    } else {
      toast.show({ type: 'error', message: '保存失败，请重试' });
    }
  };

  if (previewMode) {
    return (
      <PreviewView
        data={data}
        skippedSteps={skippedSteps}
        isLoading={isLoading}
        onBack={() => {
          setPreviewMode(false);
          setOnboardingStep(1);
        }}
        onFinish={handleFinish}
      />
    );
  }

  const birthDateValue = data.birthDate ? parseISO(data.birthDate) : undefined;

  return (
    <PageContainer>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.headerRow}>
          {onboardingStep > 1 ? (
            <TouchableOpacity onPress={handleBack} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              <Feather name="arrow-left" size={24} color={theme.colors.textPrimary} />
            </TouchableOpacity>
          ) : (
            <View style={{ width: 24 }} />
          )}
        </View>

        <View style={styles.progressWrap}>
          <OnboardingProgress
            totalSteps={TOTAL_STEPS}
            currentStep={onboardingStep}
            skippedSteps={skippedSteps}
          />
        </View>

        <ScrollView
          style={styles.flex}
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          {onboardingStep === 1 && (
            <OnboardingStep title="先认识一下你" subtitle="这些信息帮助 AI 更好地了解你">
              <TextInput
                label="昵称"
                value={data.nickname ?? ''}
                onChangeText={(v) => update({ nickname: v })}
                placeholder="请输入昵称（2-20 字符）"
                maxLength={20}
              />
              <SelectionCards<Gender>
                label="性别"
                value={data.gender}
                onChange={(v) => update({ gender: v })}
                options={GENDER_OPTIONS}
                columns={2}
              />
              <DatePicker
                label="出生日期"
                value={birthDateValue}
                onChange={(d) => update({ birthDate: format(d, 'yyyy-MM-dd') })}
                placeholder="请选择出生日期"
              />
            </OnboardingStep>
          )}

          {onboardingStep === 2 && (
            <OnboardingStep title="你的身体数据" subtitle="用于计算每日营养需求">
              <Slider
                label="身高"
                value={data.height ?? 170}
                onChange={(v) => update({ height: v })}
                min={100}
                max={250}
                step={1}
                unit="cm"
              />
              <Slider
                label="体重"
                value={data.weight ?? 65}
                onChange={(v) => update({ weight: v })}
                min={30}
                max={300}
                step={1}
                unit="kg"
              />
              <SelectionCards<ActivityLevel>
                label="活动量"
                value={data.activityLevel}
                onChange={(v) => update({ activityLevel: v })}
                options={ACTIVITY_OPTIONS}
                columns={2}
              />
            </OnboardingStep>
          )}

          {onboardingStep === 3 && (
            <OnboardingStep
              title="你的健康目标是什么？"
              subtitle="设定目标帮助 AI 给你更精准的建议"
            >
              <SelectionCards<GoalType>
                label="目标类型"
                value={data.goalType}
                onChange={(v) => update({ goalType: v })}
                options={GOAL_OPTIONS}
                columns={2}
              />
              <TextInput
                label="目标体重 (kg)"
                value={data.targetWeight !== undefined ? String(data.targetWeight) : ''}
                onChangeText={(v) => {
                  const n = Number(v);
                  update({ targetWeight: v === '' ? undefined : (Number.isFinite(n) ? n : data.targetWeight) });
                }}
                placeholder="选填"
                keyboardType="numeric"
              />
              <TextInput
                label="每日热量目标 (kcal)"
                value={
                  data.dailyCalorieTarget !== undefined
                    ? String(data.dailyCalorieTarget)
                    : ''
                }
                onChangeText={(v) => {
                  const n = Number(v);
                  update({
                    dailyCalorieTarget:
                      v === '' ? undefined : Number.isFinite(n) ? n : data.dailyCalorieTarget,
                  });
                }}
                placeholder="选填，可由 AI 自动计算"
                keyboardType="numeric"
              />
            </OnboardingStep>
          )}

          {onboardingStep === 4 && (
            <OnboardingStep title="你的饮食习惯" subtitle="帮助 AI 推荐适合你的食物">
              <SelectionCards<DietType>
                label="偏好类型"
                value={data.dietType}
                onChange={(v) => update({ dietType: v })}
                options={DIET_OPTIONS}
                columns={2}
              />
              <MultiSelectTags
                label="过敏原"
                value={data.allergies ?? []}
                onChange={(v) => update({ allergies: v })}
                options={ALLERGY_OPTIONS}
              />
              <MultiSelectTags
                label="忌口"
                value={data.restrictions ?? []}
                onChange={(v) => update({ restrictions: v })}
                options={RESTRICTION_OPTIONS}
              />
            </OnboardingStep>
          )}

          {onboardingStep === 5 && (
            <OnboardingStep
              title="健康状况（选填）"
              subtitle="如有慢性病，AI 会特别注意饮食禁忌"
            >
              <MultiSelectTags
                label="基础疾病"
                value={data.diseases ?? []}
                onChange={(v) => update({ diseases: v })}
                options={DISEASE_OPTIONS}
              />
              <TextInput
                label="服用药物"
                value={data.medications ?? ''}
                onChangeText={(v) => update({ medications: v })}
                placeholder="选填"
              />
              <TextInput
                label="医嘱限制"
                value={data.medicalAdvice ?? ''}
                onChangeText={(v) => update({ medicalAdvice: v })}
                placeholder="选填"
              />
            </OnboardingStep>
          )}
        </ScrollView>

        {/* 底部操作栏 */}
        <View style={styles.bottomBar}>
          {onboardingStep > 1 ? (
            <TouchableOpacity style={styles.bottomTextBtn} onPress={handleBack}>
              <Text style={styles.bottomTextBtnText}>上一步</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.bottomTextBtn} />
          )}

          {canSkip ? (
            <TouchableOpacity style={styles.bottomTextBtn} onPress={handleSkip}>
              <Text style={styles.bottomSkipText}>跳过</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.bottomTextBtn} />
          )}

          <Button
            variant="primary"
            size="medium"
            onPress={handleNext}
            disabled={!canProceed()}
            style={styles.bottomNextBtn}
          >
            {onboardingStep === TOTAL_STEPS ? '完成' : '下一步'}
          </Button>
        </View>
      </KeyboardAvoidingView>
    </PageContainer>
  );
}

// ============ 预览页 ============

interface PreviewProps {
  data: Partial<OnboardingData>;
  skippedSteps: number[];
  isLoading: boolean;
  onBack: () => void;
  onFinish: () => void;
}

function PreviewView({ data, skippedSteps, isLoading, onBack, onFinish }: PreviewProps) {
  const NA = <Text style={styles.previewNA}>未填写</Text>;

  const renderRow = (label: string, value: React.ReactNode) => (
    <View style={styles.previewRow}>
      <Text style={styles.previewLabel}>{label}</Text>
      <View style={styles.previewValue}>
        {typeof value === 'string' || typeof value === 'number' ? (
          <Text style={styles.previewValueText}>{value}</Text>
        ) : (
          value
        )}
      </View>
    </View>
  );

  const renderList = (arr?: string[]) =>
    arr && arr.length > 0 ? arr.join('、') : null;

  return (
    <PageContainer>
      <ScrollView contentContainerStyle={styles.previewScroll}>
        <View style={styles.previewHeader}>
          <View style={styles.successIcon}>
            <Feather name="check" size={36} color="#FFFFFF" />
          </View>
          <Text style={styles.previewTitle}>档案已完成！</Text>
        </View>

        {/* Section: 基础信息 */}
        <View style={styles.previewCard}>
          <Text style={styles.previewSection}>基础信息</Text>
          {skippedSteps.includes(1) ? (
            NA
          ) : (
            <>
              {renderRow('昵称', data.nickname ?? NA)}
              {renderRow('性别', data.gender === 'male' ? '男' : data.gender === 'female' ? '女' : NA)}
              {renderRow('出生日期', data.birthDate ?? NA)}
            </>
          )}
        </View>

        <View style={styles.previewCard}>
          <Text style={styles.previewSection}>身体信息</Text>
          {skippedSteps.includes(2) ? (
            NA
          ) : (
            <>
              {renderRow('身高', data.height ? `${data.height} cm` : NA)}
              {renderRow('体重', data.weight ? `${data.weight} kg` : NA)}
              {renderRow(
                '活动量',
                data.activityLevel ? ACTIVITY_LABELS[data.activityLevel] : NA,
              )}
            </>
          )}
        </View>

        <View style={styles.previewCard}>
          <Text style={styles.previewSection}>健康目标</Text>
          {skippedSteps.includes(3) ? (
            NA
          ) : (
            <>
              {renderRow('目标类型', data.goalType ? GOAL_LABELS[data.goalType] : NA)}
              {renderRow('目标体重', data.targetWeight ? `${data.targetWeight} kg` : NA)}
              {renderRow(
                '每日热量',
                data.dailyCalorieTarget ? `${data.dailyCalorieTarget} kcal` : NA,
              )}
            </>
          )}
        </View>

        <View style={styles.previewCard}>
          <Text style={styles.previewSection}>饮食偏好</Text>
          {skippedSteps.includes(4) ? (
            NA
          ) : (
            <>
              {renderRow(
                '偏好类型',
                data.dietType ? DIET_LABELS[data.dietType] : NA,
              )}
              {renderRow('过敏原', renderList(data.allergies) ?? NA)}
              {renderRow('忌口', renderList(data.restrictions) ?? NA)}
            </>
          )}
        </View>

        <View style={styles.previewCard}>
          <Text style={styles.previewSection}>疾病信息</Text>
          {skippedSteps.includes(5) ? (
            NA
          ) : (
            <>
              {renderRow('基础疾病', renderList(data.diseases) ?? NA)}
              {renderRow('服用药物', data.medications || NA)}
              {renderRow('医嘱限制', data.medicalAdvice || NA)}
            </>
          )}
        </View>

        <Button
          variant="primary"
          size="large"
          loading={isLoading}
          onPress={onFinish}
          style={styles.finishBtn}
        >
          开始使用健康管家
        </Button>

        <TouchableOpacity style={styles.backLinkWrap} onPress={onBack}>
          <Text style={styles.backLinkText}>返回修改</Text>
        </TouchableOpacity>
      </ScrollView>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  headerRow: {
    flexDirection: 'row',
    paddingHorizontal: theme.spacing.xl,
    paddingTop: theme.spacing.sm,
    paddingBottom: theme.spacing.sm,
  },
  progressWrap: {
    paddingHorizontal: theme.spacing.xl,
  },
  scroll: {
    paddingHorizontal: theme.spacing.xl,
    paddingBottom: theme.spacing.xl,
  },
  bottomBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.xl,
    paddingVertical: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
    backgroundColor: theme.colors.bgCard,
    gap: theme.spacing.md,
  },
  bottomTextBtn: {
    minWidth: 60,
    paddingVertical: theme.spacing.sm,
  },
  bottomTextBtnText: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
  bottomSkipText: {
    ...theme.typography.body,
    color: theme.colors.textTertiary,
  },
  bottomNextBtn: {
    flex: 1,
    borderRadius: theme.radius.pill,
    height: 44,
  },
  // 预览
  previewScroll: {
    padding: theme.spacing.xl,
    paddingBottom: theme.spacing.xxl,
  },
  previewHeader: {
    alignItems: 'center',
    marginBottom: theme.spacing.xl,
  },
  successIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: theme.colors.success,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.lg,
  },
  previewTitle: {
    ...theme.typography.pageTitle,
    color: theme.colors.textPrimary,
  },
  previewCard: {
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.md,
  },
  previewSection: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
  },
  previewRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.sm,
  },
  previewLabel: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  previewValue: {
    flex: 1,
    alignItems: 'flex-end',
  },
  previewValueText: {
    ...theme.typography.bodySm,
    color: theme.colors.textPrimary,
  },
  previewNA: {
    ...theme.typography.bodySm,
    color: theme.colors.textTertiary,
  },
  finishBtn: {
    borderRadius: theme.radius.pill,
    height: 48,
    marginTop: theme.spacing.lg,
  },
  backLinkWrap: {
    marginTop: theme.spacing.lg,
    alignItems: 'center',
  },
  backLinkText: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
  },
});
