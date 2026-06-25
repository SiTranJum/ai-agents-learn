import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { QueryClientProvider } from '@tanstack/react-query';
import { NavigationContainer, LinkingOptions } from '@react-navigation/native';
import * as Linking from 'expo-linking';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { queryClient } from '@core/query/queryClient';
import { ToastProvider } from '@shared/feedback/Toast/Toast';
import { initApiBaseUrl } from '@core/api/apiBaseUrl';
import { supabase } from '@core/supabase/client';
import { useGlobalStore } from '@core/store/globalStore';
import { authService } from '@features/auth/services/authService';
import type { RootStackParamList } from '@app/navigation/types';

interface AppProvidersProps {
  children: React.ReactNode;
}

// deep link 路由表：把 healthagent://reset-password 映射到 Auth 栈内的 ResetPassword 页。
// 恢复密码期间 isAuthenticated 为 false，RootNavigator 展示 Auth 栈，因此能命中该页。
const linking: LinkingOptions<RootStackParamList> = {
  prefixes: [Linking.createURL('/')],
  config: {
    screens: {
      Auth: {
        screens: {
          ResetPassword: 'reset-password',
        },
      },
    },
  },
};

export function AppProviders({ children }: AppProvidersProps) {
  const [ready, setReady] = useState(false);
  const setToken = useGlobalStore((s) => s.setToken);
  const setRecoveringPassword = useGlobalStore((s) => s.setRecoveringPassword);

  useEffect(() => {
    async function init() {
      // 1. 加载持久化的 API base URL
      await initApiBaseUrl();

      // 2. 从 AsyncStorage 恢复 Supabase session（F5 刷新后不丢登录态）
      const { data } = await supabase.auth.getSession();
      if (data.session?.access_token) {
        setToken(data.session.access_token);
      }

      // 3. 处理冷启动时携带的 deep link（app 未运行时点重置邮件链接）
      const initialUrl = await Linking.getInitialURL();
      if (initialUrl) {
        await handleDeepLink(initialUrl);
      }

      setReady(true);
    }
    init();

    // 4. 监听 auth 状态变化（token 刷新、登出等），保持 globalStore 同步
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        // PASSWORD_RECOVERY: 用户处于密码恢复流程，需停在设密页而非进入主页
        if (event === 'PASSWORD_RECOVERY') {
          setRecoveringPassword(true);
        }
        setToken(session?.access_token ?? null);
      }
    );

    // 5. 监听 app 运行期间到来的 deep link（热启动）
    const linkSub = Linking.addEventListener('url', ({ url }) => {
      handleDeepLink(url);
    });

    return () => {
      subscription.unsubscribe();
      linkSub.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 解析重置邮件链接：先进入恢复模式（确保后续 setSession 不触发自动登录），
  // 再用链接中的 token 建立临时 session。
  async function handleDeepLink(url: string) {
    if (!url.includes('reset-password')) return;
    setRecoveringPassword(true);
    try {
      const ok = await authService.setSessionFromUrl(url);
      if (!ok) {
        // 链接里没有有效 token，退出恢复模式让设密页提示「链接失效」
        setRecoveringPassword(false);
      }
    } catch {
      setRecoveringPassword(false);
    }
  }

  if (!ready) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <ToastProvider>
            <NavigationContainer linking={linking}>
              {children}
            </NavigationContainer>
          </ToastProvider>
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
