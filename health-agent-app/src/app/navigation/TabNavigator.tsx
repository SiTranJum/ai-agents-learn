import React from 'react';
import { View, StyleSheet } from 'react-native';
import {
  createBottomTabNavigator,
  BottomTabBar,
  type BottomTabBarProps,
} from '@react-navigation/bottom-tabs';
import { Feather } from '@expo/vector-icons';
import { TabParamList } from './types';
import { HomeScreen } from '@features/home/screens/HomeScreen';
import { DietRecordScreen } from '@features/diet/screens/DietRecordScreen';
import { DataScreen } from '@features/data/screens/DataScreen';
import { ProfileScreen } from '@features/profile/screens/ProfileScreen';
import { GlobalAIInputBar } from '@features/ai/components/GlobalAIInputBar';
import { theme } from '@app/styles/theme';

const Tab = createBottomTabNavigator<TabParamList>();

/**
 * 自定义 tabBar：将 GlobalAIInputBar 放在系统 Tab Bar 之上
 * 布局：[ Tab 内容 ] → [ AIInputBar 56px ] → [ Tab Bar 60px ]
 */
function TabBarWithAIInput(props: BottomTabBarProps) {
  return (
    <View style={styles.bottomGroup}>
      <GlobalAIInputBar />
      <BottomTabBar {...props} />
    </View>
  );
}

export function TabNavigator() {
  return (
    <Tab.Navigator
      tabBar={TabBarWithAIInput}
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

const styles = StyleSheet.create({
  bottomGroup: {
    backgroundColor: theme.colors.bgPage,
  },
});

