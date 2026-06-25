// ResetPasswordScreen - 设置新密码页（密码重置流程的第 4-5 步）
// 用户从重置邮件链接(deep link)回到 app，AppProviders 已建立恢复 session
// 并进入 isRecoveringPassword 模式，本页负责输入新密码并提交。
// 参考: docs/prd/v1/01-user-system.md §2.1.3

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Feather } from '@expo/vector-icons';

import { theme } from '@app/styles/theme';
import { Button } from '@shared/ui/Button';
import { PasswordInput } from '@shared/forms/PasswordInput';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import { useGlobalStore } from '@core/store/globalStore';
import type { AuthStackParamList } from '@app/navigation/types';
import { useAuth } from '../hooks/useAuth';

// 密码规则：至少 8 位，且需包含字母与数字（与注册页保持一致的强度要求）
const schema = z
  .object({
    password: z
      .string()
      .min(8, '密码至少 8 位')
      .regex(/[A-Za-z]/, '密码需包含字母')
      .regex(/[0-9]/, '密码需包含数字'),
    confirmPassword: z.string().min(1, '请再次输入新密码'),
  })
  .refine((v) => v.password === v.confirmPassword, {
    message: '两次输入的密码不一致',
    path: ['confirmPassword'],
  });

type FormValues = z.infer<typeof schema>;
type Nav = NativeStackNavigationProp<AuthStackParamList, 'ResetPassword'>;

export function ResetPasswordScreen() {
  const navigation = useNavigation<Nav>();
  const { resetPassword, isLoading, error, setError } = useAuth();
  const [done, setDone] = React.useState(false);
  // 是否处于有效的恢复 session：没有它就无法改密（链接失效或直接进入本页）
  const isRecovering = useGlobalStore((s) => s.isRecoveringPassword);

  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: 'onChange',
    defaultValues: { password: '', confirmPassword: '' },
  });

  const onSubmit = async (values: FormValues) => {
    setError(null);
    const ok = await resetPassword(values.password);
    if (ok) setDone(true);
  };

  const goLogin = () => navigation.navigate('Login');

  return (
    <PageContainer>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          {done ? (
            <View style={styles.successWrap}>
              <View style={styles.successIcon}>
                <Feather name="check" size={36} color="#FFFFFF" />
              </View>
              <Text style={styles.title}>密码重置成功</Text>
              <Text style={styles.subtitle}>请使用新密码登录</Text>
              <Button
                variant="primary"
                size="large"
                onPress={goLogin}
                style={styles.submitBtn}
              >
                去登录
              </Button>
            </View>
          ) : !isRecovering ? (
            // 链接失效 / 未通过邮件进入：无恢复 session，引导重新发起
            <View style={styles.successWrap}>
              <View style={[styles.successIcon, styles.warnIcon]}>
                <Feather name="alert-triangle" size={32} color="#FFFFFF" />
              </View>
              <Text style={styles.title}>链接已失效</Text>
              <Text style={styles.subtitle}>
                重置链接可能已过期，请重新发送重置邮件。
              </Text>
              <Button
                variant="primary"
                size="large"
                onPress={() => navigation.navigate('ForgotPassword')}
                style={styles.submitBtn}
              >
                重新发送
              </Button>
            </View>
          ) : (
            <>
              <Text style={styles.title}>设置新密码</Text>
              <Text style={styles.description}>
                请输入你的新密码，密码至少 8 位且包含字母和数字。
              </Text>

              {error && (
                <View style={styles.errorBanner}>
                  <Text style={styles.errorBannerText}>{error}</Text>
                </View>
              )}

              <Controller
                control={control}
                name="password"
                render={({ field: { value, onChange } }) => (
                  <PasswordInput
                    value={value}
                    onChangeText={onChange}
                    placeholder="请输入新密码"
                    error={errors.password?.message}
                  />
                )}
              />
              <Controller
                control={control}
                name="confirmPassword"
                render={({ field: { value, onChange } }) => (
                  <PasswordInput
                    value={value}
                    onChangeText={onChange}
                    placeholder="请再次输入新密码"
                    error={errors.confirmPassword?.message}
                  />
                )}
              />

              <Button
                variant="primary"
                size="large"
                disabled={!isValid}
                loading={isLoading}
                onPress={handleSubmit(onSubmit)}
                style={styles.submitBtn}
              >
                {isLoading ? '提交中...' : '确认重置'}
              </Button>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: theme.spacing.xl,
    paddingTop: theme.spacing.xxl,
    paddingBottom: theme.spacing.xxl,
  },
  title: {
    ...theme.typography.hero,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
    textAlign: 'center',
  },
  description: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xxl,
  },
  subtitle: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xxl,
    textAlign: 'center',
  },
  errorBanner: {
    backgroundColor: '#FFE5E5',
    borderRadius: theme.radius.sm,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.lg,
  },
  errorBannerText: {
    ...theme.typography.bodySm,
    color: theme.colors.error,
    textAlign: 'center',
  },
  submitBtn: {
    borderRadius: theme.radius.pill,
    height: 48,
    marginTop: theme.spacing.sm,
    alignSelf: 'stretch',
  },
  successWrap: {
    alignItems: 'center',
    paddingTop: theme.spacing.xxl,
  },
  successIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: theme.colors.success,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.xl,
  },
  warnIcon: {
    backgroundColor: theme.colors.error,
  },
});
