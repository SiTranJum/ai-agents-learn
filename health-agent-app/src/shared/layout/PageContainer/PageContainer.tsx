import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { theme } from '@app/styles/theme';

export interface PageContainerProps {
  children: React.ReactNode;
  style?: ViewStyle;
  useSafeArea?: boolean;
}

export function PageContainer({ children, style, useSafeArea = true }: PageContainerProps) {
  const Container = useSafeArea ? SafeAreaView : View;

  return (
    <Container style={[styles.container, style]}>
      {children}
    </Container>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.bgPage,
  },
});
