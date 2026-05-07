// AuthService - 直接调用 Supabase Auth SDK
// 参考: docs/specs/frontend/modules/10-auth-module.md §7.2 / §7.3

import { supabase } from '@core/supabase/client';

export interface AuthService {
  /** 邮箱+密码登录，返回 access_token */
  login(email: string, password: string): Promise<string>;
  /** 邮箱+密码注册，返回 access_token（若开启邮箱确认可能为空字符串） */
  register(email: string, password: string): Promise<string>;
  /** 发送密码重置邮件 */
  forgotPassword(email: string): Promise<void>;
  /** 登出 */
  logout(): Promise<void>;
  /** 获取当前 session 的 access_token */
  getSession(): Promise<string | null>;
}

/** 将 Supabase 错误映射为面向用户的中文错误（基于 message 关键词）。 */
function mapAuthError(message: string): string {
  const m = message.toLowerCase();
  if (m.includes('invalid login credentials') || m.includes('invalid email or password')) {
    return '邮箱或密码错误，请重试';
  }
  if (m.includes('user already registered') || m.includes('already registered')) {
    return '该邮箱已注册，请直接登录';
  }
  if (m.includes('email not confirmed')) {
    return '邮箱未验证，请先查看邮箱完成验证';
  }
  if (m.includes('password should be at least')) {
    return '密码至少 8 位，建议包含字母和数字';
  }
  if (m.includes('network') || m.includes('failed to fetch')) {
    return '网络连接失败，请检查网络后重试';
  }
  return message || '操作失败，请稍后重试';
}

export const authService: AuthService = {
  async login(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw new Error(mapAuthError(error.message));
    if (!data.session) throw new Error('登录失败');
    return data.session.access_token;
  },

  async register(email, password) {
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) throw new Error(mapAuthError(error.message));
    // 若 Supabase 项目启用邮箱确认，session 为 null
    return data.session?.access_token ?? '';
  },

  async forgotPassword(email) {
    const { error } = await supabase.auth.resetPasswordForEmail(email);
    if (error) throw new Error(mapAuthError(error.message));
  },

  async logout() {
    const { error } = await supabase.auth.signOut();
    if (error) throw new Error(mapAuthError(error.message));
  },

  async getSession() {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  },
};
