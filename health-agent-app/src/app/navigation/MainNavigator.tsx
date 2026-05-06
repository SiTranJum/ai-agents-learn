import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { MainStackParamList } from './types';
import { TabNavigator } from './TabNavigator';
import { theme } from '@app/styles/theme';

// 占位页面（后续替换为真实页面）
import { PlaceholderScreen } from '@shared/ui/PlaceholderScreen';
import { DietEditScreen } from '@features/diet/screens/DietEditScreen';
import { BodyEditScreen } from '@features/data/screens/BodyEditScreen';
import { AnalysisScreen } from '@features/data/screens/AnalysisScreen';
import { PlanListScreen } from '@features/plan/screens/PlanListScreen';
import { PlanDetailScreen } from '@features/plan/screens/PlanDetailScreen';
import { PlanCreateChatScreen } from '@features/plan/screens/PlanCreateChatScreen';
import { EditProfileScreen } from '@features/profile/screens/EditProfileScreen';
import { SettingsScreen } from '@features/profile/screens/SettingsScreen';

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
        component={DietEditScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="BodyEdit"
        component={BodyEditScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="Analysis"
        component={AnalysisScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="PlanList"
        component={PlanListScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="PlanDetail"
        component={PlanDetailScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="PlanCreate"
        component={PlanCreateChatScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="EditProfile"
        component={EditProfileScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="Settings"
        component={SettingsScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="AIDialog"
        component={PlaceholderScreen}
        options={{ title: 'AI 对话' }}
      />
    </Stack.Navigator>
  );
}
