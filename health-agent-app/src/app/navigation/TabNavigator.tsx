import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Feather } from '@expo/vector-icons';
import { TabParamList } from './types';
import { HomeScreen } from '@features/home/screens/HomeScreen';
import { DietRecordScreen } from '@features/diet/screens/DietRecordScreen';
import { DataScreen } from '@features/data/screens/DataScreen';
import { ProfileScreen } from '@features/profile/screens/ProfileScreen';
import { theme } from '@app/styles/theme';

const Tab = createBottomTabNavigator<TabParamList>();

export function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textTertiary,
        tabBarStyle: {
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '500',
        },
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeScreen}
        options={{
          tabBarLabel: '首页',
          tabBarIcon: ({ color, size }) => (
            <Feather name="home" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="DietTab"
        component={DietRecordScreen}
        options={{
          tabBarLabel: '饮食',
          tabBarIcon: ({ color, size }) => (
            <Feather name="coffee" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="DataTab"
        component={DataScreen}
        options={{
          tabBarLabel: '数据',
          tabBarIcon: ({ color, size }) => (
            <Feather name="bar-chart-2" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileScreen}
        options={{
          tabBarLabel: '我的',
          tabBarIcon: ({ color, size }) => (
            <Feather name="user" size={size} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}
