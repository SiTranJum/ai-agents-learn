// LoginScreen - 登录页 (P13)
// 参考: docs/specs/frontend/modules/10-auth-module.md §P13
// UI 文稿: docs/prd/v1/ui-design/13-auth-and-onboarding.md (页面 A)

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

import { theme } from '@app/styles/theme';
import { Button } from '@shared/ui/Button';
import { TextInput } from '@shared/forms/TextInput';
import { PasswordInput } from '@shared/forms/PasswordInput';
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import type { AuthStackParamList } from '@app/navigation/types';
import { useAuth } from '../hooks/useAuth';

const schema = z.object({
  email: z
    .string()
    .min(1, '请输入有效的邮箱地址')
    .email('请输入有效的邮箱地址'),
  password: z.string().min(1, '请输入密码'),
});

type FormValues = z.infer<typeof schema>;

type Nav = NativeStackNavigationProp<AuthStackParamList, 'Login'>;

export function LoginScreen() {
  const navigation = useNavigation<Nav>();
  const { login, isLoading } = useAuth();
  const [topError, setTopError] = React.useState<string | null>(null);

  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: 'onChange',
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (values: FormValues) => {
    setTopError(null);
    const res = await login(values.email, values.password);
    if (!res.success) {
      setTopError('邮箱或密码错误，请重试');
      setValue('password', '');
      return;
    }
    if (!res.onboardingCompleted) {
      navigation.navigate('Onboarding');
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
          <View style={styles.header}>
            <View style={styles.logo}>
              <Text style={styles.logoText}>健</Text>
            </View>
            <Text style={styles.brand}>健康管家</Text>
          </View>

          <Text style={styles.title}>欢迎回来</Text>
          <Text style={styles.subtitle}>像朋友一样，陪你管理健康</Text>

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
              <PasswordInput
                value={value}
                onChangeText={onChange}
                placeholder="请输入密码"
                error={errors.password?.message}
              />
            )}
          />

          <TouchableOpacity
            style={styles.forgotWrap}
            onPress={() => navigation.navigate('ForgotPassword')}
          >
            <Text style={styles.linkSm}>忘记密码？</Text>
          </TouchableOpacity>

          <Button
            variant="primary"
            size="large"
            disabled={!isValid}
            loading={isLoading}
            onPress={handleSubmit(onSubmit)}
            style={styles.submitBtn}
          >
            {isLoading ? '登录中...' : '登录'}
          </Button>

          <TouchableOpacity
            style={styles.bottomLinkWrap}
            onPress={() => navigation.navigate('Register')}
          >
            <Text style={styles.bottomLinkText}>
              还没有账号？<Text style={styles.bottomLinkAccent}>去注册</Text>
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
    paddingTop: theme.spacing.xxl,
    paddingBottom: theme.spacing.xxl,
  },
  header: {
    alignItems: 'center',
    marginBottom: theme.spacing.xxl,
  },
  logo: {
    width: 64,
    height: 64,
    borderRadius: theme.radius.lg,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.md,
  },
  logoText: {
    color: '#FFFFFF',
    fontSize: 28,
    fontWeight: '700',
  },
  brand: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  title: {
    ...theme.typography.hero,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
  },
  subtitle: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
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
  forgotWrap: {
    alignSelf: 'flex-end',
    marginTop: -theme.spacing.sm,
    marginBottom: theme.spacing.xl,
    paddingVertical: theme.spacing.xs,
  },
  linkSm: {
    ...theme.typography.bodySm,
    color: theme.colors.primary,
  },
  submitBtn: {
    borderRadius: theme.radius.pill,
    height: 48,
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
