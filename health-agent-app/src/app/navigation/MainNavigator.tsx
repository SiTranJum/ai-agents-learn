import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { MainStackParamList } from './types';
import { TabNavigator } from './TabNavigator';
import { theme } from '@app/styles/theme';

// 占位页面（后续替换为真实页面）
import { PlaceholderScreen } from '@shared/ui/PlaceholderScreen';

const Stack = createNativeStackNavigator<MainStackParamList>();

export function MainNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerTintColor: theme.colors.textPrimary,
        headerStyle: { backgroundColor: theme.colors.bgPage },
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen
        name="Tabs"
        component={TabNavigator}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="DietEdit"
        component={PlaceholderScreen}
        options={{ title: '编辑饮食' }}
      />
      <Stack.Screen
        name="BodyEdit"
        component={PlaceholderScreen}
        options={{ title: '编辑数据' }}
      />
      <Stack.Screen
        name="Analysis"
        component={PlaceholderScreen}
        options={{ title: '数据分析' }}
      />
      <Stack.Screen
        name="PlanList"
        component={PlaceholderScreen}
        options={{ title: '我的计划' }}
      />
      <Stack.Screen
        name="PlanDetail"
        component={PlaceholderScreen}
        options={{ title: '计划详情' }}
      />
      <Stack.Screen
        name="PlanCreate"
        component={PlaceholderScreen}
        options={{ title: '创建计划' }}
      />
      <Stack.Screen
        name="EditProfile"
        component={PlaceholderScreen}
        options={{ title: '编辑档案' }}
      />
      <Stack.Screen
        name="Settings"
        component={PlaceholderScreen}
        options={{ title: '设置' }}
      />
      <Stack.Screen
        name="AIDialog"
        component={PlaceholderScreen}
        options={{ title: 'AI 对话' }}
      />
    </Stack.Navigator>
  );
}
