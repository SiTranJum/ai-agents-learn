// Home Store - Zustand
// 参考: docs/specs/frontend/modules/11-home-module.md §6
// 首页主要数据通过 TanStack Query 管理，本 store 只保留最小本地 UI 状态占位。

import { create } from 'zustand';

interface HomeStore {
  // 选中的日期，默认今天（YYYY-MM-DD）
  selectedDate: string;
  setSelectedDate: (date: string) => void;
}

const today = (): string => {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
};

export const useHomeStore = create<HomeStore>((set) => ({
  selectedDate: today(),
  setSelectedDate: (date) => set({ selectedDate: date }),
}));
