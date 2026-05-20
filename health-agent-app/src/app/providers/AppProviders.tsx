import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { QueryClientProvider } from '@tanstack/react-query';
import { NavigationContainer } from '@react-navigation/native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { queryClient } from '@core/query/queryClient';
import { ToastProvider } from '@shared/feedback/Toast/Toast';
import { initApiBaseUrl } from '@core/api/apiBaseUrl';
import { supabase } from '@core/supabase/client';
import { useGlobalStore } from '@core/store/globalStore';

interface AppProvidersProps {
  children: React.ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  const [ready, setReady] = useState(false);
  const setToken = useGlobalStore((s) => s.setToken);

  useEffect(() => {
    async function init() {
      // 1. 加载持久化的 API base URL
      await initApiBaseUrl();

      // 2. 从 AsyncStorage 恢复 Supabase session（F5 刷新后不丢登录态）
      const { data } = await supabase.auth.getSession();
      if (data.session?.access_token) {
        setToken(data.session.access_token);
      }

      setReady(true);
    }
    init();

    // 3. 监听 auth 状态变化（token 刷新、登出等），保持 globalStore 同步
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setToken(session?.access_token ?? null);
      }
    );

    return () => subscription.unsubscribe();
  }, [setToken]);

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
            <NavigationContainer>
              {children}
            </NavigationContainer>
          </ToastProvider>
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
