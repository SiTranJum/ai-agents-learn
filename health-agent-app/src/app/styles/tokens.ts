// Design Tokens - 颜色、字体、间距、圆角、阴影、动效
// 参考: docs/specs/frontend/04-design-system-mapping.md

// ============ 颜色系统 ============
export const colors = {
  // 品牌色
  primary: '#FF7A5C',
  primaryDark: '#E96345',
  primaryLight: '#FFE7E1',

  // 功能色
  success: '#4CD964',
  warning: '#FFC94D',
  info: '#5AC8FA',
  error: '#FF5A5F',

  // 中性色
  bgPage: '#F7F8FA',
  bgCard: '#FFFFFF',
  textPrimary: '#222222',
  textSecondary: '#666666',
  textTertiary: '#999999',
  divider: '#EEEEEE',
  inputBg: '#F7F8FA',

  // 透明色
  overlay: 'rgba(0,0,0,0.4)',
} as const;

// ============ 字体系统 ============
export const typography = {
  hero: { fontSize: 36, fontWeight: '700' as const },
  pageTitle: { fontSize: 24, fontWeight: '700' as const },
  cardTitle: { fontSize: 18, fontWeight: '600' as const },
  body: { fontSize: 16, fontWeight: '400' as const },
  bodySm: { fontSize: 14, fontWeight: '400' as const },
  caption: { fontSize: 13, fontWeight: '400' as const },
  tag: { fontSize: 12, fontWeight: '500' as const },
} as const;

// ============ 间距系统 ============
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

// 页面布局常量
export const layout = {
  pageHorizontalPadding: 16,
  cardPadding: 16,
  cardGap: 12,
  bottomSafeArea: 116, // Tab(60) + AIInput(56)
} as const;

// ============ 圆角系统 ============
export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  pill: 24,
  full: 999,
} as const;

// ============ 阴影系统 ============
export const shadows = {
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  input: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 1,
  },
  modal: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 8,
  },
  brandButton: {
    shadowColor: '#FF7A5C',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 4,
  },
} as const;

// ============ 图标系统 ============
export const iconSizes = {
  nav: 24,
  list: 20,
  inline: 16,
  action: 28,
} as const;

// ============ 动效系统 ============
export const animation = {
  pageTransition: 300,
  cardStateChange: 200,
  modalShow: 250,
  buttonPress: 100,
  progressFill: 500,
  toastShow: 200,
  toastHide: 150,
  skeletonPulse: 1500,
} as const;
