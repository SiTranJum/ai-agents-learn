import 'react-native-gesture-handler';
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { AppProviders } from '@app/providers/AppProviders';
import { RootNavigator } from '@app/navigation/RootNavigator';

export default function App() {
  return (
    <AppProviders>
      <RootNavigator />
      <StatusBar style="auto" />
    </AppProviders>
  );
}
