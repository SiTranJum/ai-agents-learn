// 日期工具函数
// 所有 service 层统一使用，避免 UTC 偏移问题

/**
 * 返回本地时区的今天日期字符串 YYYY-MM-DD。
 * 不使用 toISOString()（UTC），避免凌晨 0:00-08:00 日期偏移。
 */
export function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/**
 * 格式化 Date 为 YYYY-MM-DD（本地时区）
 */
export function formatDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export function parseLocalDate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, (month || 1) - 1, day || 1);
}

export function formatFriendlyDate(value: string | Date): string {
  const date = typeof value === 'string' ? parseLocalDate(value) : value;
  const today = parseLocalDate(todayStr());
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  if (formatDate(date) === formatDate(today)) return '今天';
  if (formatDate(date) === formatDate(yesterday)) return '昨天';

  const monthDay = `${date.getMonth() + 1}月${date.getDate()}日`;
  if (date.getFullYear() === today.getFullYear()) return monthDay;
  return `${date.getFullYear()}年${monthDay}`;
}
