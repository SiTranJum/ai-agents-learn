import { animation, colors, iconSizes, layout, radius, shadows, spacing, typography } from './tokens';

export const theme = {
  colors,
  typography,
  spacing,
  layout,
  radius,
  shadows,
  iconSizes,
  animation,
} as const;

export type Theme = typeof theme;
