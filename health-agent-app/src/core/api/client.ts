// API 客户端 - 调用后端 REST API（FastAPI）
// 自动注入 Supabase access_token 作为 Bearer 鉴权头。
// 参考: docs/specs/backend/00-architecture/api-design.md

import { supabase } from '@core/supabase/client';

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

const REQUEST_TIMEOUT = 15000; // 15s

export interface ApiError {
  status: number;
  code?: string;
  message: string;
}

async function buildHeaders(extra?: HeadersInit): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

async function fetchWithTimeout(url: string, options: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `请求失败 (${res.status})`;
    let code: string | undefined;
    try {
      const body = await res.json();
      // 后端统一错误格式：{ error: { code, message, details } }
      // 契约见 docs/specs/shared/api-contract.md §1.3
      if (body?.error) {
        message = body.error.message ?? message;
        code = body.error.code;
      } else {
        message = body.message ?? body.detail ?? message;
        code = body.code;
      }
    } catch {
      // ignore
    }
    const err: ApiError = { status: res.status, code, message };
    throw err;
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json();
  // 统一响应信封：{ data, message } / { data, pagination, message }
  // 契约见 docs/specs/shared/api-contract.md §1。
  // 存在 data 字段时剥壳返回，UI/service 层拿到的永远是裸 T。
  if (body && typeof body === 'object' && 'data' in body) {
    return (body as { data: T }).data;
  }
  return body as T;
}

async function requestWithRetry<T>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> {
  const doRequest = async (): Promise<Response> => {
    const headers = await buildHeaders();
    const options: RequestInit = { method, headers };
    if (body !== undefined) options.body = JSON.stringify(body);
    return fetchWithTimeout(`${API_BASE_URL}${path}`, options);
  };

  let res = await doRequest();

  // 401 → 刷新 token 重试一次
  if (res.status === 401) {
    const { error } = await supabase.auth.refreshSession();
    if (!error) {
      res = await doRequest();
    } else {
      // 刷新也失败 → 强制登出
      const { useGlobalStore } = await import('@core/store/globalStore');
      useGlobalStore.getState().logout();
    }
  }

  // 5xx → 重试一次
  if (res.status >= 500) {
    await new Promise((r) => setTimeout(r, 500));
    res = await doRequest();
  }

  return handleResponse<T>(res);
}

export const apiClient = {
  async get<T>(path: string): Promise<T> {
    return requestWithRetry<T>('GET', path);
  },

  async post<T>(path: string, body?: unknown): Promise<T> {
    return requestWithRetry<T>('POST', path, body);
  },

  async put<T>(path: string, body?: unknown): Promise<T> {
    return requestWithRetry<T>('PUT', path, body);
  },

  async delete<T>(path: string): Promise<T> {
    return requestWithRetry<T>('DELETE', path);
  },

  async getPaginated<T>(path: string): Promise<{ data: T[]; pagination: { total: number; page: number; page_size: number; total_pages: number } }> {
    const doRequest = async (): Promise<Response> => {
      const headers = await buildHeaders();
      return fetchWithTimeout(`${API_BASE_URL}${path}`, { method: 'GET', headers });
    };

    let res = await doRequest();

    // 401 → 刷新 token 重试一次
    if (res.status === 401) {
      const { error } = await supabase.auth.refreshSession();
      if (!error) {
        res = await doRequest();
      } else {
        const { useGlobalStore } = await import('@core/store/globalStore');
        useGlobalStore.getState().logout();
      }
    }

    // 5xx → 重试一次
    if (res.status >= 500) {
      await new Promise((r) => setTimeout(r, 500));
      res = await doRequest();
    }

    if (!res.ok) {
      let message = `请求失败 (${res.status})`;
      let code: string | undefined;
      try {
        const b = await res.json();
        message = b.error?.message ?? b.message ?? b.detail ?? message;
        code = b.error?.code ?? b.code;
      } catch { /* ignore */ }
      throw { status: res.status, code, message } as ApiError;
    }
    const responseBody = await res.json();
    return {
      data: responseBody.data ?? [],
      pagination: responseBody.pagination ?? { total: 0, page: 1, page_size: 20, total_pages: 0 },
    };
  },
};
