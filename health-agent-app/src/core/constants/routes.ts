// 路由名称常量
export const ROUTES = {
  // Auth
  AUTH: {
    LOGIN: 'Login',
    REGISTER: 'Register',
    FORGOT_PASSWORD: 'ForgotPassword',
    ONBOARDING: 'Onboarding',
  },

  // Main Tabs
  TABS: {
    HOME: 'HomeTab',
    DIET: 'DietTab',
    DATA: 'DataTab',
    PROFILE: 'ProfileTab',
  },

  // Stack Screens
  MAIN: {
    DIET_EDIT: 'DietEdit',
    BODY_EDIT: 'BodyEdit',
    ANALYSIS: 'Analysis',
    PLAN_LIST: 'PlanList',
    PLAN_DETAIL: 'PlanDetail',
    PLAN_CREATE: 'PlanCreate',
    EDIT_PROFILE: 'EditProfile',
    SETTINGS: 'Settings',
    AI_DIALOG: 'AIDialog',
  },
} as const;
