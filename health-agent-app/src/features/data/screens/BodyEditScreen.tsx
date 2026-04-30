// BodyEditScreen - 身体数据编辑页 (P05)
// 4 种表单：weight / measurement / sleep / exercise
// 排便/饮水也通过此页编辑（complement: bowel 用简单单选）
// 参考: docs/specs/frontend/modules/13-data-module.md §P05
// UI 文稿: docs/prd/v1/ui-design/07-body-edit-page.md

import React, { useCallback, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { Button } from '@shared/ui/Button';
import { TextInput } from '@shared/forms/TextInput';
import { Picker } from '@shared/forms/Picker';
import { ConfirmDialog } from '@shared/feedback/ConfirmDialog';
import { useToast } from '@shared/feedback/Toast';
import type { MainStackParamList } from '@app/navigation/types';

import { useTodayRecords, useSaveBodyData } from '../hooks/useDataTrend';
import {
  EXERCISE_TYPES,
  calculateExerciseCalories,
  calculateSleepDuration,
} from '../services/dataService';
import type {
  BowelStatus,
  DataTabType,
  ExerciseRecord,
  MeasurementRecord,
  SleepQuality,
  SleepRecord,
  WeightRecord,
  BowelRecord,
} from '../types/data.types';

type Nav = NativeStackNavigationProp<MainStackParamList, 'BodyEdit'>;
type R = RouteProp<MainStackParamList, 'BodyEdit'>;

const TYPE_TITLES: Record<DataTabType, string> = {
  weight: '体重',
  measurement: '围度',
  sleep: '睡眠',
  exercise: '运动',
  water: '饮水',
  bowel: '排便',
};

const SLEEP_QUALITY_OPTIONS: { label: string; value: SleepQuality }[] = [
  { label: '优秀', value: 'excellent' },
  { label: '良好', value: 'good' },
  { label: '一般', value: 'fair' },
  { label: '较差', value: 'poor' },
];

const BOWEL_STATUS_OPTIONS: { label: string; value: BowelStatus }[] = [
  { label: '正常', value: 'normal' },
  { label: '便秘', value: 'constipation' },
  { label: '腹泻', value: 'diarrhea' },
];

const todayStr = (): string => new Date().toISOString().slice(0, 10);

export function BodyEditScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<R>();
  const toast = useToast();

  const recordType = (route.params?.recordType as DataTabType) ?? 'weight';
  const recordId = route.params?.recordId;
  const isEdit = !!recordId;

  const todayQuery = useTodayRecords();
  const saveMutation = useSaveBodyData();

  // 用于运动消耗计算的体重
  const userWeight = todayQuery.data?.weight?.weight ?? 65;

  // ===== 通用表单状态 =====
  const [date, setDate] = useState<string>(() => {
    const t = todayQuery.data;
    if (recordType === 'sleep' && !isEdit) {
      // 睡眠默认昨天
      const d = new Date();
      d.setDate(d.getDate() - 1);
      return d.toISOString().slice(0, 10);
    }
    return (
      (recordType === 'weight' && t?.weight?.date) ||
      (recordType === 'measurement' && t?.measurement?.date) ||
      (recordType === 'sleep' && t?.sleep?.date) ||
      (recordType === 'exercise' && t?.exercise?.date) ||
      (recordType === 'bowel' && t?.bowel?.date) ||
      todayStr()
    );
  });
  const [note, setNote] = useState<string>('');

  // 各类型字段
  const initial = useMemo(() => {
    const t = todayQuery.data;
    if (!isEdit) return null;
    if (recordType === 'weight' && t?.weight?.id === recordId) return t.weight;
    if (recordType === 'measurement' && t?.measurement?.id === recordId) return t.measurement;
    if (recordType === 'sleep' && t?.sleep?.id === recordId) return t.sleep;
    if (recordType === 'exercise' && t?.exercise?.id === recordId) return t.exercise;
    if (recordType === 'bowel' && t?.bowel?.id === recordId) return t.bowel;
    return null;
  }, [recordType, recordId, isEdit, todayQuery.data]);

  // 体重
  const [weight, setWeight] = useState<string>(
    initial && recordType === 'weight' ? String((initial as WeightRecord).weight) : ''
  );

  // 围度
  const [waist, setWaist] = useState<string>(
    initial && recordType === 'measurement' && (initial as MeasurementRecord).waist != null
      ? String((initial as MeasurementRecord).waist)
      : ''
  );
  const [hip, setHip] = useState<string>(
    initial && recordType === 'measurement' && (initial as MeasurementRecord).hip != null
      ? String((initial as MeasurementRecord).hip)
      : ''
  );
  const [thigh, setThigh] = useState<string>(
    initial && recordType === 'measurement' && (initial as MeasurementRecord).thigh != null
      ? String((initial as MeasurementRecord).thigh)
      : ''
  );
  const [arm, setArm] = useState<string>(
    initial && recordType === 'measurement' && (initial as MeasurementRecord).arm != null
      ? String((initial as MeasurementRecord).arm)
      : ''
  );

  // 睡眠
  const [bedTime, setBedTime] = useState<string>(
    initial && recordType === 'sleep' ? (initial as SleepRecord).bedTime : '23:30'
  );
  const [wakeTime, setWakeTime] = useState<string>(
    initial && recordType === 'sleep' ? (initial as SleepRecord).wakeTime : '07:00'
  );
  const [sleepQuality, setSleepQuality] = useState<SleepQuality>(
    initial && recordType === 'sleep' ? (initial as SleepRecord).quality : 'good'
  );

  // 运动
  const [exerciseType, setExerciseType] = useState<string>(
    initial && recordType === 'exercise' ? (initial as ExerciseRecord).type : '跑步'
  );
  const [exerciseDuration, setExerciseDuration] = useState<string>(
    initial && recordType === 'exercise'
      ? String((initial as ExerciseRecord).duration)
      : ''
  );

  // 排便
  const [bowelTime, setBowelTime] = useState<string>(
    initial && recordType === 'bowel' ? (initial as BowelRecord).time : '09:30'
  );
  const [bowelStatus, setBowelStatus] = useState<BowelStatus>(
    initial && recordType === 'bowel' ? (initial as BowelRecord).status : 'normal'
  );

  // ===== Dirty / 离开确认 =====
  const [dirty, setDirty] = useState(false);
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);
  const markDirty = () => {
    if (!dirty) setDirty(true);
  };
  const set = <T,>(setter: (v: T) => void) => (v: T) => {
    setter(v);
    markDirty();
  };

  // ===== 自动计算 =====
  const sleepDurationMinutes = useMemo(
    () => calculateSleepDuration(bedTime, wakeTime),
    [bedTime, wakeTime]
  );
  const exerciseCalories = useMemo(() => {
    const dur = parseFloat(exerciseDuration);
    if (!Number.isFinite(dur) || dur <= 0) return 0;
    return calculateExerciseCalories(exerciseType, dur, userWeight);
  }, [exerciseType, exerciseDuration, userWeight]);

  // ===== 校验 + 保存 =====
  const handleSave = useCallback(async () => {
    let payload: Record<string, unknown> = { date };

    switch (recordType) {
      case 'weight': {
        const w = parseFloat(weight);
        if (!(w >= 20 && w <= 300)) {
          toast.show({ type: 'error', message: '体重需在 20-300 kg 之间' });
          return;
        }
        payload = {
          ...payload,
          id: recordId,
          weight: Math.round(w * 10) / 10,
          bmi: Math.round((w / (1.7 * 1.7)) * 10) / 10,
          change: 0,
          note,
        } as Partial<WeightRecord>;
        break;
      }
      case 'measurement': {
        const m: Partial<MeasurementRecord> = { date, id: recordId, note };
        if (waist) m.waist = parseFloat(waist);
        if (hip) m.hip = parseFloat(hip);
        if (thigh) m.thigh = parseFloat(thigh);
        if (arm) m.arm = parseFloat(arm);
        if (m.waist == null && m.hip == null && m.thigh == null && m.arm == null) {
          toast.show({ type: 'error', message: '至少填写一项围度' });
          return;
        }
        payload = m as typeof payload;
        break;
      }
      case 'sleep': {
        if (sleepDurationMinutes <= 0) {
          toast.show({ type: 'error', message: '请检查入睡/起床时间' });
          return;
        }
        payload = {
          ...payload,
          id: recordId,
          bedTime,
          wakeTime,
          duration: sleepDurationMinutes,
          quality: sleepQuality,
          note,
        } as Partial<SleepRecord>;
        break;
      }
      case 'exercise': {
        const dur = parseFloat(exerciseDuration);
        if (!(dur >= 1 && dur <= 300)) {
          toast.show({ type: 'error', message: '时长需在 1-300 分钟之间' });
          return;
        }
        payload = {
          ...payload,
          id: recordId,
          type: exerciseType,
          duration: Math.round(dur),
          calories: exerciseCalories,
          note,
        } as Partial<ExerciseRecord>;
        break;
      }
      case 'bowel': {
        payload = {
          ...payload,
          id: recordId,
          time: bowelTime,
          status: bowelStatus,
          note,
        } as Partial<BowelRecord>;
        break;
      }
      case 'water': {
        toast.show({ type: 'info', message: '饮水请直接在数据页快捷添加' });
        return;
      }
    }

    try {
      await saveMutation.mutateAsync({ type: recordType, record: payload });
      toast.show({ type: 'success', message: `已保存${TYPE_TITLES[recordType]}记录` });
      navigation.goBack();
    } catch {
      toast.show({ type: 'error', message: '保存失败，请稍后重试' });
    }
  }, [
    recordType, recordId, date, note, weight, waist, hip, thigh, arm,
    bedTime, wakeTime, sleepQuality, sleepDurationMinutes,
    exerciseType, exerciseDuration, exerciseCalories,
    bowelTime, bowelStatus,
    saveMutation, toast, navigation,
  ]);

  const handleCancel = () => {
    if (dirty) setShowLeaveConfirm(true);
    else navigation.goBack();
  };

  const title = `${isEdit ? '编辑' : '新增'}${TYPE_TITLES[recordType]}记录`;

  return (
    <PageContainer useSafeArea>
      {/* 顶部导航栏 */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={handleCancel} style={styles.backBtn}>
          <Feather name="chevron-left" size={24} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>{title}</Text>
        <View style={styles.backBtn} />
      </View>

      <KeyboardAvoidingView
        style={styles.flex1}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          style={styles.flex1}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* 日期 */}
          <Text style={styles.sectionTitle}>记录日期</Text>
          <View style={styles.dateBox}>
            <Text style={styles.dateText}>{date}</Text>
            {isEdit && (
              <Text style={styles.dateHint}>编辑模式下日期锁定</Text>
            )}
          </View>

          {/* 动态表单 */}
          {recordType === 'weight' && (
            <TextInput
              label="体重 (kg)"
              value={weight}
              onChangeText={set(setWeight)}
              placeholder="请输入体重"
              keyboardType="decimal-pad"
            />
          )}

          {recordType === 'measurement' && (
            <>
              <TextInput label="腰围 (cm)" value={waist} onChangeText={set(setWaist)} keyboardType="decimal-pad" placeholder="可选" />
              <TextInput label="臀围 (cm)" value={hip} onChangeText={set(setHip)} keyboardType="decimal-pad" placeholder="可选" />
              <TextInput label="大腿围 (cm)" value={thigh} onChangeText={set(setThigh)} keyboardType="decimal-pad" placeholder="可选" />
              <TextInput label="上臂围 (cm)" value={arm} onChangeText={set(setArm)} keyboardType="decimal-pad" placeholder="可选" />
            </>
          )}

          {recordType === 'sleep' && (
            <>
              <TextInput
                label="入睡时间 (HH:mm)"
                value={bedTime}
                onChangeText={set(setBedTime)}
                placeholder="23:30"
              />
              <TextInput
                label="起床时间 (HH:mm)"
                value={wakeTime}
                onChangeText={set(setWakeTime)}
                placeholder="07:00"
              />
              <Text style={styles.autoCalc}>
                睡眠时长：
                <Text style={styles.autoCalcValue}>
                  {Math.floor(sleepDurationMinutes / 60)}小时
                  {sleepDurationMinutes % 60}分
                </Text>
                （自动计算）
              </Text>
              <Picker
                label="睡眠质量"
                value={sleepQuality}
                onChange={(v) => set(setSleepQuality)(v as SleepQuality)}
                options={SLEEP_QUALITY_OPTIONS}
              />
            </>
          )}

          {recordType === 'exercise' && (
            <>
              <Picker
                label="运动类型"
                value={exerciseType}
                onChange={set(setExerciseType)}
                options={EXERCISE_TYPES.map((t) => ({ label: t, value: t }))}
              />
              <TextInput
                label="运动时长（分钟）"
                value={exerciseDuration}
                onChangeText={set(setExerciseDuration)}
                placeholder="如 30"
                keyboardType="numeric"
              />
              <Text style={styles.autoCalc}>
                预估消耗：
                <Text style={styles.autoCalcValue}>
                  ~{exerciseCalories} kcal
                </Text>
                （基于体重 {userWeight}kg）
              </Text>
            </>
          )}

          {recordType === 'bowel' && (
            <>
              <TextInput
                label="时间 (HH:mm)"
                value={bowelTime}
                onChangeText={set(setBowelTime)}
                placeholder="09:30"
              />
              <Picker
                label="状态"
                value={bowelStatus}
                onChange={(v) => set(setBowelStatus)(v as BowelStatus)}
                options={BOWEL_STATUS_OPTIONS}
              />
            </>
          )}

          {recordType !== 'water' && (
            <TextInput
              label="备注（可选）"
              value={note}
              onChangeText={set(setNote)}
              placeholder="补充信息"
              multiline
              maxLength={100}
            />
          )}
        </ScrollView>

        {/* 底部操作栏 */}
        <View style={styles.actionBar}>
          <View style={styles.actionBtnWrap}>
            <Button variant="secondary" onPress={handleCancel} size="medium">
              取消
            </Button>
          </View>
          <View style={styles.actionBtnWrap}>
            <Button
              variant="primary"
              onPress={handleSave}
              loading={saveMutation.isPending}
              size="medium"
            >
              保存
            </Button>
          </View>
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
    gap: theme.spacing.sm,
  },
  sectionTitle: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.sm,
  },
  dateBox: {
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.colors.divider,
    marginBottom: theme.spacing.sm,
  },
  dateText: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
  },
  dateHint: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
    marginTop: 2,
  },
  autoCalc: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: -theme.spacing.xs,
    marginBottom: theme.spacing.sm,
  },
  autoCalcValue: {
    color: theme.colors.primary,
    fontWeight: '600',
  },
  actionBar: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    padding: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: theme.colors.divider,
    backgroundColor: theme.colors.bgPage,
  },
  actionBtnWrap: {
    flex: 1,
  },
});
