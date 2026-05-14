// 开发者：API 地址动态配置面板（Modal）
//
// 用途：手机在 Expo Go 里运行时，无法重启就改后端 IP。
// 在登录页 / 设置页都能调起本面板，输入新 IP 立即生效（保存到 AsyncStorage）。
//
// 上线前删除：
// 1. 删除本文件
// 2. 删除 LoginScreen / SettingsScreen 中的入口
// 3. 删除 src/core/api/apiBaseUrl.ts
// 4. apiClient 改回直接读 process.env.EXPO_PUBLIC_API_BASE_URL

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ActivityIndicator,
  TextInput as RNTextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { theme } from '@app/styles/theme';
import { Button } from '@shared/ui/Button';
import {
  getApiBaseUrl,
  getEnvApiBaseUrl,
  resetApiBaseUrl,
  setApiBaseUrl,
} from '@core/api/apiBaseUrl';

interface DevApiSettingsModalProps {
  visible: boolean;
  onClose: () => void;
}

type PingStatus =
  | { kind: 'idle' }
  | { kind: 'pinging' }
  | { kind: 'ok'; ms: number; status: number }
  | { kind: 'fail'; reason: string };

export function DevApiSettingsModal({ visible, onClose }: DevApiSettingsModalProps) {
  const [url, setUrl] = useState('');
  const [saving, setSaving] = useState(false);
  const [ping, setPing] = useState<PingStatus>({ kind: 'idle' });
  const [savedHint, setSavedHint] = useState<string | null>(null);

  useEffect(() => {
    if (visible) {
      setUrl(getApiBaseUrl());
      setPing({ kind: 'idle' });
      setSavedHint(null);
    }
  }, [visible]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await setApiBaseUrl(url);
      setSavedHint('已保存，新请求生效');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setSaving(true);
    try {
      await resetApiBaseUrl();
      setUrl(getEnvApiBaseUrl());
      setSavedHint('已重置为默认值');
    } finally {
      setSaving(false);
    }
  };

  const handlePing = async () => {
    setPing({ kind: 'pinging' });
    const target = url.trim().replace(/\/$/, '');
    if (!target) {
      setPing({ kind: 'fail', reason: '地址为空' });
      return;
    }
    // 去掉 /api/v1 后缀拿到根 URL，访问 /docs（FastAPI 默认开启）
    const rootUrl = target.replace(/\/api\/v\d+\/?$/, '');
    const docsUrl = `${rootUrl}/docs`;
    const started = Date.now();
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 5000);
      const res = await fetch(docsUrl, { method: 'GET', signal: controller.signal });
      clearTimeout(timer);
      setPing({ kind: 'ok', ms: Date.now() - started, status: res.status });
    } catch (e) {
      const reason = e instanceof Error ? e.message : 'unknown';
      setPing({ kind: 'fail', reason });
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.kav}
        >
          <View style={styles.card}>
            <View style={styles.header}>
              <Text style={styles.title}>开发者：API 地址</Text>
              <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
                <Text style={styles.closeText}>✕</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.hint}>
              修改后立即生效，重启 App 仍保留（AsyncStorage）。
              {'\n'}格式示例：http://192.168.1.100:8100/api/v1
            </Text>

            <Text style={styles.label}>当前生效</Text>
            <View style={styles.currentBox}>
              <Text style={styles.currentText} numberOfLines={2} ellipsizeMode="middle">
                {getApiBaseUrl()}
              </Text>
            </View>

            <Text style={styles.label}>编辑</Text>
            <RNTextInput
              style={styles.input}
              value={url}
              onChangeText={setUrl}
              placeholder="http://192.168.x.x:8100/api/v1"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
              placeholderTextColor={theme.colors.textTertiary}
            />

            <View style={styles.row}>
              <Button
                variant="secondary"
                size="small"
                onPress={handlePing}
                disabled={ping.kind === 'pinging'}
              >
                {ping.kind === 'pinging' ? '测试中…' : '测试连通性'}
              </Button>
              <View style={{ flex: 1, marginLeft: theme.spacing.md }}>
                <PingResult status={ping} />
              </View>
            </View>

            <Text style={styles.label}>默认值（来自 .env）</Text>
            <Text style={styles.envText}>{getEnvApiBaseUrl()}</Text>

            {savedHint && <Text style={styles.savedHint}>✓ {savedHint}</Text>}

            <View style={styles.actions}>
              <View style={{ flex: 1 }}>
                <Button variant="secondary" onPress={handleReset} disabled={saving}>
                  重置
                </Button>
              </View>
              <View style={{ width: theme.spacing.md }} />
              <View style={{ flex: 1 }}>
                <Button variant="primary" onPress={handleSave} disabled={saving}>
                  {saving ? '保存中…' : '保存'}
                </Button>
              </View>
            </View>
          </View>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
}

function PingResult({ status }: { status: PingStatus }) {
  if (status.kind === 'idle') return null;
  if (status.kind === 'pinging') {
    return <ActivityIndicator size="small" color={theme.colors.primary} />;
  }
  if (status.kind === 'ok') {
    return (
      <Text style={styles.pingOk}>
        ✓ 连通 ({status.status}, {status.ms}ms)
      </Text>
    );
  }
  return <Text style={styles.pingFail}>✗ {status.reason}</Text>;
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  kav: { width: '100%', alignItems: 'center' },
  card: {
    width: '88%',
    maxWidth: 480,
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.lg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.sm,
  },
  title: {
    ...theme.typography.cardTitle,
    color: theme.colors.textPrimary,
  },
  closeBtn: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeText: {
    fontSize: 20,
    color: theme.colors.textSecondary,
  },
  hint: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.md,
  },
  label: {
    ...theme.typography.bodySm,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.md,
    marginBottom: theme.spacing.xs,
  },
  currentBox: {
    backgroundColor: theme.colors.inputBg,
    borderRadius: theme.radius.sm,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
  },
  currentText: {
    ...theme.typography.body,
    color: theme.colors.textPrimary,
  },
  input: {
    backgroundColor: theme.colors.inputBg,
    borderRadius: theme.radius.sm,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    fontSize: 14,
    color: theme.colors.textPrimary,
    borderWidth: 1,
    borderColor: theme.colors.divider,
  },
  envText: {
    ...theme.typography.caption,
    color: theme.colors.textTertiary,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: theme.spacing.md,
  },
  pingOk: {
    ...theme.typography.bodySm,
    color: theme.colors.success,
  },
  pingFail: {
    ...theme.typography.bodySm,
    color: theme.colors.error,
  },
  savedHint: {
    ...theme.typography.bodySm,
    color: theme.colors.success,
    marginTop: theme.spacing.md,
    textAlign: 'center',
  },
  actions: {
    flexDirection: 'row',
    marginTop: theme.spacing.lg,
  },
});
