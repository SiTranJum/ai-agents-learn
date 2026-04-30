import React from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { theme } from '@app/styles/theme';

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'text';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  onPress: () => void;
  children: React.ReactNode;
  style?: ViewStyle;
}

export function Button({
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  onPress,
  children,
  style,
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <TouchableOpacity
      style={[
        styles.base,
        styles[variant],
        styles[size],
        isDisabled && styles.disabled,
        style,
      ]}
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={variant === 'primary' ? '#fff' : theme.colors.primary}
        />
      ) : (
        <Text style={[styles.text, styles[`${variant}Text`], styles[`${size}Text`]]}>
          {children}
        </Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  // Variants
  primary: {
    backgroundColor: theme.colors.primary,
  },
  secondary: {
    backgroundColor: theme.colors.bgCard,
    borderWidth: 1,
    borderColor: theme.colors.divider,
  },
  text: {
    backgroundColor: 'transparent',
  },
  // Sizes
  small: { height: 32, paddingHorizontal: 12 },
  medium: { height: 44, paddingHorizontal: 20 },
  large: { height: 52, paddingHorizontal: 24 },
  // Disabled
  disabled: { opacity: 0.5 },
  // Text styles
  primaryText: { color: '#FFFFFF', fontWeight: '600' } as TextStyle,
  secondaryText: { color: theme.colors.textPrimary, fontWeight: '500' } as TextStyle,
  textText: { color: theme.colors.primary, fontWeight: '500' } as TextStyle,
  smallText: { fontSize: 13 } as TextStyle,
  mediumText: { fontSize: 15 } as TextStyle,
  largeText: { fontSize: 17 } as TextStyle,
});
