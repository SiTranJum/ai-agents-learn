// AuthService - 直接调用 Supabase Auth SDK
// 参考: docs/specs/frontend/modules/10-auth-module.md §7.2 / §7.3

import * as Linking from 'expo-linking';
import { supabase } from '@core/supabase/client';

// 密码重置邮件里链接点击后回跳到 app 的 deep link 地址。
// Linking.createURL 会按当前运行环境（Expo Go / dev build / 正式包）
// 生成对应的 scheme://path，例如 healthagent://reset-password。
// 该地址必须加入 Supabase 控制台的 Redirect URLs 白名单，否则邮件链接不生效。
export const RESET_PASSWORD_REDIRECT = Linking.createURL('reset-password');

export interface AuthService {
  /** 邮箱+密码登录，返回 access_token */
  login(email: string, password: string): Promise<string>;
  /** 邮箱+密码注册，返回 access_token（若开启邮箱确认可能为空字符串） */
  register(email: string, password: string): Promise<string>;
  /** 发送密码重置邮件（邮件内链接回跳到 RESET_PASSWORD_REDIRECT） */
  forgotPassword(email: string): Promise<void>;
  /**
   * 解析重置邮件链接中的 token 并建立临时 session。
   * @returns 解析成功返回 true；链接里不含恢复 token 返回 false
   */
  setSessionFromUrl(url: string): Promise<boolean>;
  /** 在已建立的（恢复）session 下设置新密码 */
  resetPassword(newPassword: string): Promise<void>;
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
  if (
    m.includes('expired') ||
    m.includes('invalid') && m.includes('token') ||
    m.includes('otp')
  ) {
    return '重置链接已失效，请重新发送重置邮件';
  }
  if (m.includes('same') && m.includes('password')) {
    return '新密码不能与旧密码相同';
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
    // redirectTo: 用户点邮件链接后回跳的地址。Supabase 会把恢复 token
    // 拼到该 URL 的 fragment（#access_token=...&type=recovery）后面。
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: RESET_PASSWORD_REDIRECT,
    });
    if (error) throw new Error(mapAuthError(error.message));
  },

  async setSessionFromUrl(url) {
    // 邮件链接形如 healthagent://reset-password#access_token=xxx&refresh_token=yyy&type=recovery
    // expo-linking 的 parse 不解析 fragment(#)，这里手动取 # 后面的参数。
    const fragment = url.includes('#') ? url.split('#')[1] : '';
    const params = new URLSearchParams(fragment);
    const access_token = params.get('access_token');
    const refresh_token = params.get('refresh_token');
    if (!access_token || !refresh_token) return false;

    // setSession: 用链接里的 token 建立一个（临时）登录态，
    // 之后才能调用 updateUser 修改密码。
    const { error } = await supabase.auth.setSession({ access_token, refresh_token });
    if (error) throw new Error(mapAuthError(error.message));
    return true;
  },

  async resetPassword(newPassword) {
    // updateUser: 修改当前已登录用户的属性，这里只改密码。
    const { error } = await supabase.auth.updateUser({ password: newPassword });
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
