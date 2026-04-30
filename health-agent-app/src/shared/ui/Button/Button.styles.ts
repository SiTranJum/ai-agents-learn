import { StyleSheet } from 'react-native';
import { colors, radius, shadows } from '@app/styles/tokens';

export const styles = StyleSheet.create({
  // 基础容器
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
  },

  // Variant 样式
  primary: {
    backgroundColor: colors.primary,
    ...shadows.brandButton,
  },
  primaryPressed: {
    backgroundColor: colors.primaryDark,
  },
  primaryDisabled: {
    backgroundColor: colors.textTertiary,
    shadowOpacity: 0,
  },

  secondary: {
    backgroundColor: colors.bgCard,
    borderWidth: 1,
    borderColor: colors.divider,
  },
  secondaryPressed: {
    backgroundColor: colors.bgPage,
  },
  secondaryDisabled: {
    borderColor: colors.divider,
    opacity: 0.5,
  },

  text: {
    backgroundColor: 'transparent',
  },
  textPressed: {
    opacity: 0.6,
  },
  textDisabled: {
    opacity: 0.3,
  },

  // Size 样式
  small: {
    height: 32,
    paddingHorizontal: 12,
  },
  medium: {
    height: 44,
    paddingHorizontal: 20,
  },
  large: {
    height: 52,
    paddingHorizontal: 24,
  },

  // 文字样式
  textBase: {
    fontWeight: '600',
  },
  textPrimary: {
    color: colors.bgCard,
    fontSize: 16,
  },
  textSecondary: {
    color: colors.textPrimary,
    fontSize: 16,
  },
  textVariant: {
    color: colors.primary,
    fontSize: 16,
  },
  textSmall: {
    fontSize: 14,
  },
  textMedium: {
    fontSize: 16,
  },
  textLarge: {
    fontSize: 18,
  },
});
