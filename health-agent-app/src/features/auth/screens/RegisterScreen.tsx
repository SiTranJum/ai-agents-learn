// RegisterScreen - 注册页 (P14)
// 参考: docs/specs/frontend/modules/10-auth-module.md §P14
// UI 文稿: docs/prd/v1/ui-design/13-auth-and-onboarding.md (页面 B)

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
import { TextInput } from '@shared/forms/TextInput';
import { PasswordInput } from '@shared/forms/PasswordInput';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import type { AuthStackParamList } from '@app/navigation/types';
import { useAuth } from '../hooks/useAuth';

const passwordRule = z
  .string()
  .min(8, '密码至少 8 位，建议包含字母和数字')
  .regex(/[A-Za-z]/, '密码至少 8 位，建议包含字母和数字')
  .regex(/[0-9]/, '密码至少 8 位，建议包含字母和数字');

const schema = z
  .object({
    email: z.string().min(1, '请输入有效的邮箱地址').email('请输入有效的邮箱地址'),
    password: passwordRule,
    confirmPassword: z.string().min(1, '请再次输入密码'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: '两次输入的密码不一致',
    path: ['confirmPassword'],
  });

type FormValues = z.infer<typeof schema>;

type Nav = NativeStackNavigationProp<AuthStackParamList, 'Register'>;

function getPasswordStrength(pw: string): { label: string; color: string } | null {
  if (!pw) return null;
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Za-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  if (score <= 1) return { label: '密码强度：弱', color: theme.colors.error };
  if (score === 2) return { label: '密码强度：中', color: theme.colors.warning };
  return { label: '密码强度：强', color: theme.colors.success };
}

export function RegisterScreen() {
  const navigation = useNavigation<Nav>();
  const { register, isLoading } = useAuth();
  const [topError, setTopError] = React.useState<string | null>(null);

  const {
    control,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: 'onChange',
    defaultValues: { email: '', password: '', confirmPassword: '' },
  });

  const passwordValue = watch('password');
  const strength = getPasswordStrength(passwordValue);

  const onSubmit = async (values: FormValues) => {
    setTopError(null);
    const ok = await register(values.email, values.password);
    if (ok) {
      navigation.navigate('Onboarding');
    } else {
      setTopError('该邮箱已注册，请直接登录');
    }
  };

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
          <TouchableOpacity
            style={styles.backBtn}
            onPress={() => navigation.goBack()}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Feather name="arrow-left" size={24} color={theme.colors.textPrimary} />
          </TouchableOpacity>

          <Text style={styles.title}>创建你的健康档案</Text>

          {topError && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorBannerText}>{topError}</Text>
            </View>
          )}

          <Controller
            control={control}
            name="email"
            render={({ field: { value, onChange } }) => (
              <TextInput
                value={value}
                onChangeText={onChange}
                placeholder="请输入邮箱"
                keyboardType="email-address"
                error={errors.email?.message}
              />
            )}
          />

          <Controller
            control={control}
            name="password"
            render={({ field: { value, onChange } }) => (
              <View>
                <PasswordInput
                  value={value}
                  onChangeText={onChange}
                  placeholder="请输入密码"
                  error={errors.password?.message}
                />
                {!errors.password && strength && (
                  <Text style={[styles.strengthText, { color: strength.color }]}>
                    {strength.label}
                  </Text>
                )}
              </View>
            )}
          />

          <Controller
            control={control}
            name="confirmPassword"
            render={({ field: { value, onChange } }) => (
              <PasswordInput
                value={value}
                onChangeText={onChange}
                placeholder="请再次输入密码"
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
            {isLoading ? '注册中...' : '注册'}
          </Button>

          <TouchableOpacity
            style={styles.bottomLinkWrap}
            onPress={() => navigation.navigate('Login')}
          >
            <Text style={styles.bottomLinkText}>
              已有账号？<Text style={styles.bottomLinkAccent}>去登录</Text>
            </Text>
          </TouchableOpacity>
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
    paddingTop: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
  backBtn: {
    width: 32,
    height: 32,
    justifyContent: 'center',
    marginBottom: theme.spacing.xl,
  },
  title: {
    ...theme.typography.hero,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.xxl,
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
  strengthText: {
    ...theme.typography.caption,
    marginTop: -theme.spacing.md,
    marginBottom: theme.spacing.lg,
  },
  submitBtn: {
    borderRadius: theme.radius.pill,
    height: 48,
    marginTop: theme.spacing.sm,
  },
  bottomLinkWrap: {
    marginTop: theme.spacing.xl,
    alignItems: 'center',
    paddingVertical: theme.spacing.sm,
  },
  bottomLinkText: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
  },
  bottomLinkAccent: {
    color: theme.colors.primary,
    fontWeight: '500',
  },
});
