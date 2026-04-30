// 导航类型定义
// 参考: docs/specs/frontend/02-navigation-and-routing.md

export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
};

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  Onboarding: undefined;
};

export type TabParamList = {
  HomeTab: undefined;
  DietTab: undefined;
  DataTab: undefined;
  ProfileTab: undefined;
};

export type MainStackParamList = {
  Tabs: undefined;
  DietEdit: { mealType?: string; date?: string; recordId?: string };
  BodyEdit: { recordType: string; recordId?: string };
  Analysis: undefined;
  PlanList: undefined;
  PlanDetail: { planId: string };
  PlanCreate: undefined;
  EditProfile: undefined;
  Settings: undefined;
  AIDialog: { initialMessage?: string };
};
