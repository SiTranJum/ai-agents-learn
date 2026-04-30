// ForgotPasswordScreen - 忘记密码页 (P15)
// 参考: docs/specs/frontend/modules/10-auth-module.md §P15
// UI 文稿: docs/prd/v1/ui-design/13-auth-and-onboarding.md (页面 C)

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
import { PageContainer } from '@shared/layout/PageContainer/PageContainer';
import type { AuthStackParamList } from '@app/navigation/types';
import { useAuth } from '../hooks/useAuth';

const schema = z.object({
  email: z.string().min(1, '请输入有效的邮箱地址').email('请输入有效的邮箱地址'),
});

type FormValues = z.infer<typeof schema>;
type Nav = NativeStackNavigationProp<AuthStackParamList, 'ForgotPassword'>;

const RESEND_SECONDS = 60;

export function ForgotPasswordScreen() {
  const navigation = useNavigation<Nav>();
  const { forgotPassword, isLoading } = useAuth();
  const [submitted, setSubmitted] = React.useState(false);
  const [submittedEmail, setSubmittedEmail] = React.useState('');
  const [countdown, setCountdown] = React.useState(0);

  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: 'onChange',
    defaultValues: { email: '' },
  });

  React.useEffect(() => {
    if (countdown <= 0) return;
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  const onSubmit = async (values: FormValues) => {
    const ok = await forgotPassword(values.email);
    if (ok) {
      setSubmittedEmail(values.email);
      setSubmitted(true);
      setCountdown(RESEND_SECONDS);
    }
  };

  const onResend = async () => {
    if (countdown > 0) return;
    const ok = await forgotPassword(submittedEmail);
    if (ok) setCountdown(RESEND_SECONDS);
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

          {submitted ? (
            <View style={styles.successWrap}>
              <View style={styles.successIcon}>
                <Feather name="check" size={36} color="#FFFFFF" />
              </View>
              <Text style={styles.title}>重置邮件已发送</Text>
              <Text style={styles.subtitle}>请查看你的邮箱 {submittedEmail}</Text>

              <Button
                variant="primary"
                size="large"
                disabled={countdown > 0}
                loading={isLoading}
                onPress={onResend}
                style={styles.submitBtn}
              >
                {countdown > 0 ? `重新发送（${countdown}s）` : '重新发送'}
              </Button>

              <TouchableOpacity
                style={styles.bottomLinkWrap}
                onPress={() => navigation.navigate('Login')}
              >
                <Text style={styles.bottomLinkText}>
                  想起密码了？<Text style={styles.bottomLinkAccent}>去登录</Text>
                </Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              <Text style={styles.title}>重置密码</Text>
              <Text style={styles.description}>
                输入你的注册邮箱，我们将发送重置密码的链接到你的邮箱。
              </Text>

              <Controller
                control={control}
                name="email"
                render={({ field: { value, onChange } }) => (
                  <TextInput
                    value={value}
                    onChangeText={onChange}
                    placeholder="请输入注册邮箱"
                    keyboardType="email-address"
                    error={errors.email?.message}
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
                {isLoading ? '发送中...' : '发送重置邮件'}
              </Button>

              <TouchableOpacity
                style={styles.bottomLinkWrap}
                onPress={() => navigation.navigate('Login')}
              >
                <Text style={styles.bottomLinkText}>
                  想起密码了？<Text style={styles.bottomLinkAccent}>去登录</Text>
                </Text>
              </TouchableOpacity>
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
    marginBottom: theme.spacing.md,
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
});
